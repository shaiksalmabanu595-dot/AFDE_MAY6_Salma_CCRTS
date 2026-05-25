"""
ETL Stage 3: LOAD
=================

Loads the cleaned DataFrame into analytics tables alongside the existing
Phase 1 tables in the same SQLite database.

Tables created
--------------
1. analytics_complaints     - fact table, one row per complaint
2. sla_breach_summary       - pre-aggregated SLA stats by priority + category
3. category_summary         - per-category counts and avg resolution
4. agent_performance        - per-agent counts, avg resolution, breach rate
5. monthly_trends           - per-month complaint volume and resolution stats
6. etl_runs                 - audit log: when ETL ran, how many rows, stats
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analytics_complaints (
    complaint_code        TEXT PRIMARY KEY,
    customer_name         TEXT,
    customer_email        TEXT,
    category              TEXT,
    priority              TEXT,
    status                TEXT,
    title                 TEXT,
    sla_hours             INTEGER,
    sla_breached          INTEGER,
    assigned_to           TEXT,
    assigned_at           TIMESTAMP,
    created_at            TIMESTAMP NOT NULL,
    resolved_at           TIMESTAMP,
    resolution_time_hours REAL,
    feedback_rating       REAL,
    year                  INTEGER,
    month                 INTEGER,
    year_month            TEXT,
    is_resolved           INTEGER,
    resolution_bucket     TEXT,
    loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_complaints_priority   ON analytics_complaints(priority);
CREATE INDEX IF NOT EXISTS idx_analytics_complaints_status     ON analytics_complaints(status);
CREATE INDEX IF NOT EXISTS idx_analytics_complaints_category   ON analytics_complaints(category);
CREATE INDEX IF NOT EXISTS idx_analytics_complaints_ym         ON analytics_complaints(year_month);
CREATE INDEX IF NOT EXISTS idx_analytics_complaints_agent      ON analytics_complaints(assigned_to);

CREATE TABLE IF NOT EXISTS sla_breach_summary (
    priority           TEXT,
    category           TEXT,
    total_complaints   INTEGER,
    breached_count     INTEGER,
    breach_rate_pct    REAL,
    PRIMARY KEY (priority, category)
);

CREATE TABLE IF NOT EXISTS category_summary (
    category               TEXT PRIMARY KEY,
    total_complaints       INTEGER,
    resolved_count         INTEGER,
    open_count             INTEGER,
    avg_resolution_hours   REAL,
    avg_feedback_rating    REAL,
    sla_breach_rate_pct    REAL
);

CREATE TABLE IF NOT EXISTS agent_performance (
    agent_id              TEXT PRIMARY KEY,
    total_handled         INTEGER,
    resolved_count        INTEGER,
    resolution_rate_pct   REAL,
    avg_resolution_hours  REAL,
    breach_count          INTEGER,
    breach_rate_pct       REAL,
    avg_feedback_rating   REAL
);

CREATE TABLE IF NOT EXISTS monthly_trends (
    year_month             TEXT PRIMARY KEY,
    total_complaints       INTEGER,
    resolved_count         INTEGER,
    avg_resolution_hours   REAL,
    sla_breach_count       INTEGER
);

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at       TIMESTAMP,
    finished_at      TIMESTAMP,
    status           TEXT,
    source_file      TEXT,
    rows_extracted   INTEGER,
    rows_loaded      INTEGER,
    stats_json       TEXT,
    error_message    TEXT
);
"""


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create analytics tables and indexes if they don't already exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info("LOAD | analytics schema ready")


def _load_fact_table(df: pd.DataFrame, conn: sqlite3.Connection) -> int:
    """Replace analytics_complaints with the freshly transformed data."""
    cols = [
        "complaint_code", "customer_name", "customer_email", "category",
        "priority", "status", "title", "sla_hours", "sla_breached",
        "assigned_to", "assigned_at", "created_at", "resolved_at",
        "resolution_time_hours", "feedback_rating", "year", "month",
        "year_month", "is_resolved", "resolution_bucket",
    ]
    subset = df[cols].copy()

    # SQLite doesn't have native bool -- store as 0/1
    subset["sla_breached"] = subset["sla_breached"].astype(int)
    subset["is_resolved"] = subset["is_resolved"].astype(int)

    # Wipe and bulk insert
    conn.execute("DELETE FROM analytics_complaints")
    subset.to_sql("analytics_complaints", conn, if_exists="append", index=False)
    conn.commit()
    rows_loaded = len(subset)
    logger.info("LOAD | wrote %d rows into analytics_complaints", rows_loaded)
    return rows_loaded


def _build_sla_breach_summary(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Aggregate SLA breaches by (priority, category)."""
    g = df.groupby(["priority", "category"]).agg(
        total_complaints=("complaint_code", "count"),
        breached_count=("sla_breached", "sum"),
    ).reset_index()
    g["breach_rate_pct"] = (g["breached_count"] / g["total_complaints"] * 100).round(2)

    conn.execute("DELETE FROM sla_breach_summary")
    g.to_sql("sla_breach_summary", conn, if_exists="append", index=False)
    conn.commit()
    logger.info("LOAD | wrote %d rows into sla_breach_summary", len(g))


def _build_category_summary(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Aggregate per-category stats."""
    g = df.groupby("category").agg(
        total_complaints=("complaint_code", "count"),
        resolved_count=("is_resolved", "sum"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        avg_feedback_rating=("feedback_rating", "mean"),
        breach_count=("sla_breached", "sum"),
    ).reset_index()
    g["open_count"] = g["total_complaints"] - g["resolved_count"]
    g["sla_breach_rate_pct"] = (g["breach_count"] / g["total_complaints"] * 100).round(2)
    g["avg_resolution_hours"] = g["avg_resolution_hours"].round(2)
    g["avg_feedback_rating"] = g["avg_feedback_rating"].round(2)

    g = g[["category", "total_complaints", "resolved_count", "open_count",
           "avg_resolution_hours", "avg_feedback_rating", "sla_breach_rate_pct"]]

    conn.execute("DELETE FROM category_summary")
    g.to_sql("category_summary", conn, if_exists="append", index=False)
    conn.commit()
    logger.info("LOAD | wrote %d rows into category_summary", len(g))


def _build_agent_performance(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Aggregate per-agent performance metrics. Skip unassigned complaints."""
    agent_df = df[df["assigned_to"].notna()].copy()
    g = agent_df.groupby("assigned_to").agg(
        total_handled=("complaint_code", "count"),
        resolved_count=("is_resolved", "sum"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        breach_count=("sla_breached", "sum"),
        avg_feedback_rating=("feedback_rating", "mean"),
    ).reset_index().rename(columns={"assigned_to": "agent_id"})

    g["resolution_rate_pct"] = (g["resolved_count"] / g["total_handled"] * 100).round(2)
    g["breach_rate_pct"] = (g["breach_count"] / g["total_handled"] * 100).round(2)
    g["avg_resolution_hours"] = g["avg_resolution_hours"].round(2)
    g["avg_feedback_rating"] = g["avg_feedback_rating"].round(2)

    g = g[["agent_id", "total_handled", "resolved_count", "resolution_rate_pct",
           "avg_resolution_hours", "breach_count", "breach_rate_pct",
           "avg_feedback_rating"]]

    conn.execute("DELETE FROM agent_performance")
    g.to_sql("agent_performance", conn, if_exists="append", index=False)
    conn.commit()
    logger.info("LOAD | wrote %d rows into agent_performance", len(g))


def _build_monthly_trends(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Aggregate monthly volume + resolution + SLA stats."""
    g = df.groupby("year_month").agg(
        total_complaints=("complaint_code", "count"),
        resolved_count=("is_resolved", "sum"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        sla_breach_count=("sla_breached", "sum"),
    ).reset_index()
    g["avg_resolution_hours"] = g["avg_resolution_hours"].round(2)
    g = g.sort_values("year_month")

    conn.execute("DELETE FROM monthly_trends")
    g.to_sql("monthly_trends", conn, if_exists="append", index=False)
    conn.commit()
    logger.info("LOAD | wrote %d rows into monthly_trends", len(g))


def _log_etl_run(
    conn: sqlite3.Connection,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    source_file: str,
    rows_extracted: int,
    rows_loaded: int,
    stats: Dict,
    error_message: str = None,
) -> int:
    """Insert an audit row into etl_runs and return the run_id."""
    cur = conn.execute(
        """
        INSERT INTO etl_runs (
            started_at, finished_at, status, source_file,
            rows_extracted, rows_loaded, stats_json, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            started_at.isoformat(),
            finished_at.isoformat(),
            status,
            source_file,
            rows_extracted,
            rows_loaded,
            json.dumps(stats),
            error_message,
        ),
    )
    conn.commit()
    return cur.lastrowid


def load(
    df: pd.DataFrame,
    db_path: str,
    source_file: str,
    rows_extracted: int,
    stats: Dict,
    started_at: datetime,
) -> Dict:
    """
    Load the transformed DataFrame into all analytics tables.

    Returns a dict with the run_id and the row counts written to each table.
    """
    logger.info("LOAD | opening connection to %s", db_path)
    conn = sqlite3.connect(db_path)
    try:
        _create_schema(conn)
        rows_loaded = _load_fact_table(df, conn)
        _build_sla_breach_summary(df, conn)
        _build_category_summary(df, conn)
        _build_agent_performance(df, conn)
        _build_monthly_trends(df, conn)

        finished_at = datetime.utcnow()
        run_id = _log_etl_run(
            conn,
            started_at=started_at,
            finished_at=finished_at,
            status="SUCCESS",
            source_file=source_file,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            stats=stats,
        )
        logger.info("LOAD | ETL run #%d recorded as SUCCESS", run_id)
        return {"run_id": run_id, "rows_loaded": rows_loaded}
    except Exception as exc:
        finished_at = datetime.utcnow()
        _log_etl_run(
            conn,
            started_at=started_at,
            finished_at=finished_at,
            status="FAILED",
            source_file=source_file,
            rows_extracted=rows_extracted,
            rows_loaded=0,
            stats=stats,
            error_message=str(exc),
        )
        logger.exception("LOAD | failed: %s", exc)
        raise
    finally:
        conn.close()
