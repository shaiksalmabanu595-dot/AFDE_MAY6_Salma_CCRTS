"""
ETL Stage 1: EXTRACT
====================

Reads the raw complaint CSV file into a pandas DataFrame and validates
that the expected columns are present. This stage does NOT clean or
modify the data -- the goal is to pull the data in exactly as-is and
hand it off to the Transform stage.
"""

import logging
import os
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)

# Columns we require in the input CSV. Extra columns are allowed; we just
# need these to exist.
REQUIRED_COLUMNS: List[str] = [
    "complaint_id",
    "complaint_code",
    "customer_name",
    "customer_email",
    "category",
    "priority",
    "status",
    "title",
    "sla_hours",
    "sla_breached",
    "assigned_to",
    "assigned_at",
    "created_at",
    "resolved_at",
    "resolution_time_hours",
    "resolution_comment",
    "feedback_rating",
]


def extract_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Read the complaints CSV and validate its schema.

    Parameters
    ----------
    csv_path : str
        Absolute or relative path to the CSV file.

    Returns
    -------
    pd.DataFrame
        The raw DataFrame, with no transformations applied.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist at the given path.
    ValueError
        If required columns are missing from the CSV.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    logger.info("EXTRACT | reading %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("EXTRACT | loaded %d rows, %d columns", len(df), len(df.columns))

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {missing}. "
            f"Got columns: {list(df.columns)}"
        )

    logger.info("EXTRACT | schema OK -- all %d required columns present",
                len(REQUIRED_COLUMNS))
    return df
