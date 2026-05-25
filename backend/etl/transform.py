"""
ETL Stage 2: TRANSFORM
======================

Cleans the raw complaint DataFrame and derives the columns needed for
analytics. Every step is logged so the ETL run can be audited end-to-end.

Cleaning steps
--------------
1. Strip whitespace from string columns
2. Normalize `priority` casing (e.g. "MEDIUM" -> "Medium")
3. Validate `status` against an allowed list
4. Drop full duplicates (same complaint_code)
5. Set negative `resolution_time_hours` to NaN (data error)
6. Set invalid `feedback_rating` (anything outside 1-5) to NaN
7. Parse all datetime columns
8. Cast booleans correctly

Derived columns
---------------
- year             : year of created_at
- month            : month of created_at (1-12)
- year_month       : "YYYY-MM" string for trend grouping
- is_resolved      : True if status in (Resolved, Closed)
- is_sla_breached  : bool version of sla_breached (already exists, but
                     normalized here)
- resolution_bucket: 'fast' (<4h), 'normal' (4-24h), 'slow' (24-72h),
                     'very_slow' (>72h), or None if not resolved
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES = {"Open", "Assigned", "In Progress",
                  "Pending Customer Response", "Escalated",
                  "Resolved", "Closed"}


def _normalize_priority(value: str) -> str:
    """Convert 'MEDIUM' / 'medium' / 'Medium' / ' Medium ' all to 'Medium'."""
    if pd.isna(value):
        return value
    cleaned = str(value).strip().title()
    return cleaned if cleaned in VALID_PRIORITIES else cleaned


def _resolution_bucket(hours) -> str:
    """Bucket resolution time into business-friendly categories."""
    if pd.isna(hours):
        return None
    if hours < 4:
        return "fast"
    if hours < 24:
        return "normal"
    if hours < 72:
        return "slow"
    return "very_slow"


def transform(df: pd.DataFrame) -> Dict[str, object]:
    """
    Clean the raw DataFrame and add derived analytics columns.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from the Extract stage.

    Returns
    -------
    dict
        {
            "df":      the cleaned DataFrame,
            "stats":   a dict of cleaning statistics for the ETL audit log,
        }
    """
    initial_rows = len(df)
    stats = {
        "initial_rows": initial_rows,
        "rows_after_dedup": None,
        "duplicates_removed": 0,
        "whitespace_fixed": 0,
        "priority_normalized": 0,
        "negative_resolution_nulled": 0,
        "invalid_feedback_nulled": 0,
        "final_rows": 0,
    }

    logger.info("TRANSFORM | starting with %d rows", initial_rows)

    # -- 1. Strip whitespace on every string column -----------------------
    str_columns = ["complaint_code", "customer_name", "customer_email",
                   "category", "priority", "status", "title",
                   "assigned_to", "resolution_comment"]
    whitespace_count = 0
    for col in str_columns:
        if col in df.columns:
            before = df[col].astype(str)
            after = before.str.strip()
            whitespace_count += int((before != after).sum())
            df[col] = after.where(df[col].notna(), other=np.nan)
    stats["whitespace_fixed"] = whitespace_count
    logger.info("TRANSFORM | stripped whitespace on %d cells", whitespace_count)

    # -- 2. Normalize priority casing ------------------------------------
    before_priority = df["priority"].copy()
    df["priority"] = df["priority"].apply(_normalize_priority)
    priority_changed = int((before_priority != df["priority"]).sum())
    stats["priority_normalized"] = priority_changed
    logger.info("TRANSFORM | normalized %d priority values", priority_changed)

    # -- 3. Validate status (no normalization needed, but warn on bad values)
    bad_status = df.loc[~df["status"].isin(VALID_STATUSES), "status"].unique()
    if len(bad_status):
        logger.warning("TRANSFORM | found %d unknown status values: %s",
                       len(bad_status), bad_status[:5])

    # -- 4. Drop duplicates by complaint_code ----------------------------
    df = df.drop_duplicates(subset=["complaint_code"], keep="first").reset_index(drop=True)
    stats["rows_after_dedup"] = len(df)
    stats["duplicates_removed"] = initial_rows - len(df)
    logger.info("TRANSFORM | dropped %d duplicate complaint_codes (%d -> %d rows)",
                stats["duplicates_removed"], initial_rows, len(df))

    # -- 5. Negative resolution times -> NaN -----------------------------
    neg_mask = df["resolution_time_hours"] < 0
    stats["negative_resolution_nulled"] = int(neg_mask.sum())
    df.loc[neg_mask, "resolution_time_hours"] = np.nan
    logger.info("TRANSFORM | nulled %d negative resolution_time_hours",
                stats["negative_resolution_nulled"])

    # -- 6. Invalid feedback ratings -> NaN ------------------------------
    invalid_feedback_mask = (
        df["feedback_rating"].notna()
        & ((df["feedback_rating"] < 1) | (df["feedback_rating"] > 5))
    )
    stats["invalid_feedback_nulled"] = int(invalid_feedback_mask.sum())
    df.loc[invalid_feedback_mask, "feedback_rating"] = np.nan
    logger.info("TRANSFORM | nulled %d invalid feedback_rating values",
                stats["invalid_feedback_nulled"])

    # -- 7. Parse datetime columns ---------------------------------------
    for col in ["assigned_at", "created_at", "resolved_at"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    logger.info("TRANSFORM | parsed datetime columns")

    # -- 8. Normalize sla_breached to bool -------------------------------
    df["sla_breached"] = df["sla_breached"].astype(str).str.strip().str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    ).fillna(False).astype(bool)

    # -- 9. Derived columns ----------------------------------------------
    df["year"] = df["created_at"].dt.year.astype("Int64")
    df["month"] = df["created_at"].dt.month.astype("Int64")
    df["year_month"] = df["created_at"].dt.strftime("%Y-%m")
    df["is_resolved"] = df["status"].isin(["Resolved", "Closed"])
    df["resolution_bucket"] = df["resolution_time_hours"].apply(_resolution_bucket)
    logger.info("TRANSFORM | added derived columns: year, month, year_month, "
                "is_resolved, resolution_bucket")

    stats["final_rows"] = len(df)
    logger.info("TRANSFORM | done -- %d clean rows ready for load", len(df))

    return {"df": df, "stats": stats}
