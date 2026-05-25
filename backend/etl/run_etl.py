"""
ETL Orchestrator
================

Run the full Extract -> Transform -> Load pipeline.

Usage from the project root:

    python -m backend.etl.run_etl
    python -m backend.etl.run_etl --csv datasets/complaints_sample.csv
    python -m backend.etl.run_etl --csv mydata.csv --db backend/ccrts.db

If --csv or --db are omitted, sensible defaults are used.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# When run as a script (not a module), make sure parent dirs are importable
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.etl.extract import extract_from_csv  # noqa: E402
from backend.etl.transform import transform        # noqa: E402
from backend.etl.load import load                  # noqa: E402


DEFAULT_CSV = os.path.join(PROJECT_ROOT, "datasets", "complaints_sample.csv")
DEFAULT_DB = os.path.join(BACKEND_DIR, "ccrts.db")


def setup_logging() -> None:
    """Configure root logging once, in a readable format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def run_etl(csv_path: str, db_path: str) -> dict:
    """
    Execute the full ETL pipeline.

    Returns a dict with run_id, rows_extracted, rows_loaded, and the
    transform statistics.
    """
    started_at = datetime.utcnow()
    logger = logging.getLogger("run_etl")

    logger.info("=" * 60)
    logger.info("CCRTS ETL Pipeline -- Phase 2")
    logger.info("=" * 60)
    logger.info("Source CSV:  %s", csv_path)
    logger.info("Target DB:   %s", db_path)
    logger.info("Started at:  %s UTC", started_at.isoformat(timespec="seconds"))
    logger.info("")

    # 1. EXTRACT --------------------------------------------------------
    raw_df = extract_from_csv(csv_path)
    rows_extracted = len(raw_df)

    # 2. TRANSFORM ------------------------------------------------------
    result = transform(raw_df)
    clean_df = result["df"]
    stats = result["stats"]

    # 3. LOAD -----------------------------------------------------------
    load_result = load(
        df=clean_df,
        db_path=db_path,
        source_file=os.path.basename(csv_path),
        rows_extracted=rows_extracted,
        stats=stats,
        started_at=started_at,
    )

    finished_at = datetime.utcnow()
    duration = (finished_at - started_at).total_seconds()
    logger.info("")
    logger.info("=" * 60)
    logger.info("ETL run #%d complete in %.2fs", load_result["run_id"], duration)
    logger.info("  Rows extracted:      %d", rows_extracted)
    logger.info("  Rows loaded:         %d", load_result["rows_loaded"])
    logger.info("  Duplicates removed:  %d", stats["duplicates_removed"])
    logger.info("  Whitespace fixed:    %d cells", stats["whitespace_fixed"])
    logger.info("  Priorities normalized: %d", stats["priority_normalized"])
    logger.info("  Negative resolutions nulled: %d", stats["negative_resolution_nulled"])
    logger.info("  Invalid feedback nulled: %d", stats["invalid_feedback_nulled"])
    logger.info("=" * 60)

    return {
        "run_id": load_result["run_id"],
        "rows_extracted": rows_extracted,
        "rows_loaded": load_result["rows_loaded"],
        "duration_seconds": duration,
        "stats": stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CCRTS ETL pipeline.")
    parser.add_argument("--csv", default=DEFAULT_CSV,
                        help="Path to the input CSV (default: %(default)s)")
    parser.add_argument("--db", default=DEFAULT_DB,
                        help="Path to the SQLite DB (default: %(default)s)")
    args = parser.parse_args()

    setup_logging()

    try:
        run_etl(args.csv, args.db)
        return 0
    except Exception as exc:
        logging.exception("ETL FAILED: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
