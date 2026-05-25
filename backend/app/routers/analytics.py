"""
Analytics router (Phase 2)
==========================

Exposes the pre-aggregated analytics tables produced by the ETL pipeline
as JSON REST endpoints. Frontend dashboards consume these endpoints to
render charts.

All endpoints require an Admin or Supervisor token.
"""

from typing import List, Optional
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db, DB_PATH
from app.utils.auth import require_roles

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ---------- Response schemas (kept inline for clarity) ----------

class CategorySummary(BaseModel):
    category: str
    total_complaints: int
    resolved_count: int
    open_count: int
    avg_resolution_hours: Optional[float]
    avg_feedback_rating: Optional[float]
    sla_breach_rate_pct: Optional[float]


class SlaBreachRow(BaseModel):
    priority: str
    category: str
    total_complaints: int
    breached_count: int
    breach_rate_pct: float


class AgentPerformanceRow(BaseModel):
    agent_id: str
    total_handled: int
    resolved_count: int
    resolution_rate_pct: float
    avg_resolution_hours: Optional[float]
    breach_count: int
    breach_rate_pct: float
    avg_feedback_rating: Optional[float]


class MonthlyTrendRow(BaseModel):
    year_month: str
    total_complaints: int
    resolved_count: int
    avg_resolution_hours: Optional[float]
    sla_breach_count: int


class EtlRunRow(BaseModel):
    run_id: int
    started_at: str
    finished_at: Optional[str]
    status: str
    source_file: str
    rows_extracted: int
    rows_loaded: int
    error_message: Optional[str]


class AnalyticsOverview(BaseModel):
    total_complaints: int
    resolved_count: int
    open_count: int
    sla_breach_count: int
    sla_breach_rate_pct: float
    avg_resolution_hours: Optional[float]
    avg_feedback_rating: Optional[float]
    last_etl_run: Optional[str]


# ---------- Helper to read directly from sqlite (no ORM needed) ----------

def _query_all(sql: str, params: tuple = ()) -> List[dict]:
    """Run a SELECT and return a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    rows = _query_all(sql, params)
    return rows[0] if rows else None


def _table_exists(table: str) -> bool:
    """Check if a table exists. Helpful when ETL hasn't been run yet."""
    row = _query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return row is not None


def _require_etl_ran():
    """Return 404 if the analytics tables don't exist yet."""
    if not _table_exists("analytics_complaints"):
        raise HTTPException(
            status_code=404,
            detail="Analytics tables not found. Run the ETL pipeline first: "
                   "`python -m backend.etl.run_etl`",
        )


# ---------------- Endpoints ----------------

@router.get("/overview", response_model=AnalyticsOverview)
def overview(_: dict = Depends(require_roles("Admin", "Supervisor"))):
    """High-level KPIs across all complaints in the analytics fact table."""
    _require_etl_ran()

    summary = _query_one("""
        SELECT
            COUNT(*) AS total,
            SUM(is_resolved) AS resolved,
            SUM(sla_breached) AS breaches,
            ROUND(AVG(resolution_time_hours), 2) AS avg_res,
            ROUND(AVG(feedback_rating), 2) AS avg_rating
        FROM analytics_complaints
    """)
    last_run = _query_one("""
        SELECT finished_at FROM etl_runs WHERE status='SUCCESS'
        ORDER BY run_id DESC LIMIT 1
    """)

    total = summary["total"] or 0
    resolved = summary["resolved"] or 0
    breaches = summary["breaches"] or 0
    rate = round((breaches / total * 100), 2) if total else 0.0

    return AnalyticsOverview(
        total_complaints=total,
        resolved_count=resolved,
        open_count=total - resolved,
        sla_breach_count=breaches,
        sla_breach_rate_pct=rate,
        avg_resolution_hours=summary["avg_res"],
        avg_feedback_rating=summary["avg_rating"],
        last_etl_run=last_run["finished_at"] if last_run else None,
    )


@router.get("/categories", response_model=List[CategorySummary])
def categories(_: dict = Depends(require_roles("Admin", "Supervisor"))):
    """Per-category counts, avg resolution, avg rating, SLA breach rate."""
    _require_etl_ran()
    rows = _query_all("""
        SELECT category, total_complaints, resolved_count, open_count,
               avg_resolution_hours, avg_feedback_rating, sla_breach_rate_pct
        FROM category_summary
        ORDER BY total_complaints DESC
    """)
    return rows


@router.get("/sla", response_model=List[SlaBreachRow])
def sla_breaches(
    priority: Optional[str] = Query(None),
    _: dict = Depends(require_roles("Admin", "Supervisor")),
):
    """SLA breach analysis by (priority, category)."""
    _require_etl_ran()
    sql = """
        SELECT priority, category, total_complaints, breached_count, breach_rate_pct
        FROM sla_breach_summary
    """
    params: tuple = ()
    if priority:
        sql += " WHERE priority = ?"
        params = (priority,)
    sql += " ORDER BY breach_rate_pct DESC"
    return _query_all(sql, params)


@router.get("/agents", response_model=List[AgentPerformanceRow])
def agents(_: dict = Depends(require_roles("Admin", "Supervisor"))):
    """Per-agent performance metrics (excluding unassigned complaints)."""
    _require_etl_ran()
    rows = _query_all("""
        SELECT agent_id, total_handled, resolved_count, resolution_rate_pct,
               avg_resolution_hours, breach_count, breach_rate_pct,
               avg_feedback_rating
        FROM agent_performance
        ORDER BY resolution_rate_pct DESC
    """)
    return rows


@router.get("/trends", response_model=List[MonthlyTrendRow])
def trends(_: dict = Depends(require_roles("Admin", "Supervisor"))):
    """Monthly complaint volume, resolution, and SLA breach counts."""
    _require_etl_ran()
    return _query_all("""
        SELECT year_month, total_complaints, resolved_count,
               avg_resolution_hours, sla_breach_count
        FROM monthly_trends
        ORDER BY year_month
    """)


@router.get("/etl-runs", response_model=List[EtlRunRow])
def etl_runs(
    limit: int = Query(10, ge=1, le=100),
    _: dict = Depends(require_roles("Admin", "Supervisor")),
):
    """Show recent ETL run history -- proves ETL has executed."""
    if not _table_exists("etl_runs"):
        return []
    return _query_all(
        "SELECT run_id, started_at, finished_at, status, source_file, "
        "rows_extracted, rows_loaded, error_message "
        "FROM etl_runs ORDER BY run_id DESC LIMIT ?",
        (limit,),
    )
