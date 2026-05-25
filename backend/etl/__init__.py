"""
CCRTS ETL Pipeline (Phase 2)
============================

A small ETL package that turns the messy `complaints_sample.csv` dataset
into clean, query-ready analytics tables in the same SQLite DB used by
Phase 1.

Modules
-------
- extract.py    : read the CSV with pandas, basic schema validation
- transform.py  : clean, normalize, dedupe, derive analytics columns
- load.py       : bulk-insert into analytics_* tables, log the run
- run_etl.py    : orchestrator -- call this script to run the full pipeline
"""

__version__ = "1.0.0"
