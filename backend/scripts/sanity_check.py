"""
Phase 2 sanity check
====================

Run AFTER you have:
  1. Copied the ETL files into your project
  2. Installed pandas
  3. Run the ETL pipeline

This script verifies:
  - The 6 analytics tables exist
  - They contain data
  - The most-recent ETL run is logged as SUCCESS

Usage:
  python -m backend.scripts.sanity_check
"""

import os
import sqlite3
import sys

DB_CANDIDATES = [
    os.path.join("backend", "ccrts.db"),
    os.path.join(os.path.dirname(__file__), "..", "ccrts.db"),
]

EXPECTED_TABLES = [
    "analytics_complaints",
    "sla_breach_summary",
    "category_summary",
    "agent_performance",
    "monthly_trends",
    "etl_runs",
]


def find_db():
    for p in DB_CANDIDATES:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


def main():
    db = find_db()
    if not db:
        print("FAIL: could not find ccrts.db. Run the backend at least once.")
        return 1

    print(f"Checking DB at: {db}")
    conn = sqlite3.connect(db)

    # Existence check
    existing = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}

    print("\nTable existence:")
    all_ok = True
    for t in EXPECTED_TABLES:
        present = t in existing
        print(f"  {'OK  ' if present else 'MISS'} {t}")
        if not present:
            all_ok = False

    if not all_ok:
        print("\nFAIL: some analytics tables are missing.")
        print("Run: python -m backend.etl.run_etl")
        return 1

    # Row counts
    print("\nRow counts:")
    for t in EXPECTED_TABLES:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:30s} = {n:,}")
        if n == 0 and t != "etl_runs":
            print(f"    WARNING: {t} is empty -- ETL may not have run successfully")

    # Latest ETL run
    print("\nLatest ETL run:")
    row = conn.execute(
        "SELECT run_id, status, source_file, rows_extracted, rows_loaded, finished_at "
        "FROM etl_runs ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    if not row:
        print("  No ETL runs recorded yet. Run the ETL first.")
        return 1
    print(f"  run_id:        #{row[0]}")
    print(f"  status:        {row[1]}")
    print(f"  source_file:   {row[2]}")
    print(f"  extracted:     {row[3]:,}")
    print(f"  loaded:        {row[4]:,}")
    print(f"  finished_at:   {row[5]}")

    if row[1] != "SUCCESS":
        print("\nFAIL: last ETL run did not succeed.")
        return 1

    print("\nALL CHECKS PASSED. Phase 2 ETL is operational.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
