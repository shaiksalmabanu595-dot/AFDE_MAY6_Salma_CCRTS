# CCRTS Phase 2 — ETL Pipeline Documentation

## Overview

The Phase 2 ETL pipeline transforms a raw complaint dataset
(`datasets/complaints_sample.csv`, ~10,400 rows) into clean, query-ready
analytics tables stored alongside the operational Phase 1 data in
`backend/ccrts.db`.

It runs in three discrete stages — **Extract → Transform → Load** — and
records every run in an `etl_runs` audit table.

```
   CSV (raw, messy)
        │
        ▼
   ┌──────────┐
   │ EXTRACT  │  pandas.read_csv + schema validation
   └────┬─────┘
        ▼
   ┌──────────┐
   │TRANSFORM │  whitespace strip, priority normalize, dedupe,
   │          │  fix negative resolutions, fix invalid ratings,
   │          │  parse datetimes, derive year/month/bucket
   └────┬─────┘
        ▼
   ┌──────────┐
   │   LOAD   │  bulk insert into 5 analytics tables
   │          │  + audit log in etl_runs
   └────┬─────┘
        ▼
   SQLite (ccrts.db) — analytics_* tables
```

---

## Stage 1: Extract

**File:** `backend/etl/extract.py`

- Reads the CSV with `pandas.read_csv()`
- Validates that all 17 required columns are present
- Does **not** clean or modify data — passes raw DataFrame to Transform

**Input:** path to a CSV file
**Output:** a `pandas.DataFrame`

Fails fast with a clear error if:
- File doesn't exist (FileNotFoundError)
- Required columns are missing (ValueError)

---

## Stage 2: Transform

**File:** `backend/etl/transform.py`

This is the heart of the pipeline. It cleans known data quality issues
in the raw dataset and adds derived columns for analytics.

### Cleaning operations

| # | Operation | What it does | Typical count on 10.4K rows |
|---|-----------|--------------|------------------------------|
| 1 | Whitespace strip | Trim leading/trailing spaces on every string column | ~3,860 cells |
| 2 | Priority normalize | `"MEDIUM"` / `"medium"` → `"Medium"` | ~322 rows |
| 3 | Status validate | Warn on unknown statuses | 0 (data is good) |
| 4 | Deduplicate | Drop rows with duplicate `complaint_code` | ~200 rows |
| 5 | Negative resolutions | Set `resolution_time_hours < 0` to NULL | ~263 rows |
| 6 | Invalid ratings | Set `feedback_rating` outside [1,5] to NULL | ~95 rows |
| 7 | Datetime parse | Convert string dates to `datetime` | all 3 datetime cols |
| 8 | Boolean normalize | `sla_breached` → real bool | all rows |

### Derived columns

After cleaning, Transform adds these columns:

| Column | Type | Derived from | Used in |
|--------|------|--------------|---------|
| `year` | int | `created_at.year` | trends grouping |
| `month` | int | `created_at.month` | trends grouping |
| `year_month` | str ("YYYY-MM") | `created_at` | monthly_trends table |
| `is_resolved` | bool | `status in (Resolved, Closed)` | resolution rate |
| `resolution_bucket` | str | `resolution_time_hours` | speed categorization |

`resolution_bucket` values:
- `fast` — under 4 hours
- `normal` — 4 to 24 hours
- `slow` — 24 to 72 hours
- `very_slow` — over 72 hours
- `None` — complaint not resolved yet

---

## Stage 3: Load

**File:** `backend/etl/load.py`

Bulk-inserts the cleaned DataFrame into 6 SQLite tables, then logs the run.

### Analytics tables created

#### 1. `analytics_complaints` (fact table)
One row per cleaned complaint. PK: `complaint_code`.
Indexed on priority, status, category, year_month, and assigned_to for
fast analytical queries. Replaced on every ETL run (`DELETE; INSERT`).

#### 2. `sla_breach_summary`
Pre-aggregated breach counts grouped by `(priority, category)`.
Powers the SLA Breach Rate table on the frontend.

| Column | Type |
|--------|------|
| priority | TEXT |
| category | TEXT |
| total_complaints | INTEGER |
| breached_count | INTEGER |
| breach_rate_pct | REAL |

#### 3. `category_summary`
One row per category with counts, avg resolution time, avg rating, and
SLA breach rate.

#### 4. `agent_performance`
One row per agent with resolution rate, avg resolution time, breach rate,
and avg feedback rating. Excludes unassigned complaints.

#### 5. `monthly_trends`
One row per `YYYY-MM` with monthly volume, resolved count, avg resolution
time, and breach count. Powers the line chart on the frontend.

#### 6. `etl_runs` (audit log)
Append-only. One row per ETL execution.

| Column | Description |
|--------|-------------|
| run_id | auto-increment PK |
| started_at | when ETL began |
| finished_at | when ETL finished |
| status | "SUCCESS" or "FAILED" |
| source_file | CSV file name |
| rows_extracted | row count before transform |
| rows_loaded | row count after transform |
| stats_json | full transform statistics as JSON |
| error_message | populated only when status="FAILED" |

If Load throws an exception, an `etl_runs` row is still recorded with
status="FAILED" and the error message, so the failure is auditable.

---

## How to run it

```bash
# From project root, with backend venv active
python -m backend.etl.run_etl

# With custom paths
python -m backend.etl.run_etl --csv my_data.csv --db /tmp/test.db
```

Typical full run on 10,400 rows: **~0.7 seconds**.

---

## How the frontend consumes this

The `/analytics` page in the React frontend calls 6 endpoints (all in
`backend/app/routers/analytics.py`):

| Endpoint | Returns | Used in chart |
|----------|---------|---------------|
| `GET /api/analytics/overview` | KPI summary | Top stat cards |
| `GET /api/analytics/trends` | monthly_trends rows | Line chart |
| `GET /api/analytics/categories` | category_summary rows | Bar + pie chart |
| `GET /api/analytics/sla` | sla_breach_summary rows | Heatmap table |
| `GET /api/analytics/agents` | agent_performance rows | Performance table |
| `GET /api/analytics/etl-runs` | recent etl_runs rows | Audit table |

All require an **Admin or Supervisor** JWT token.

---

## Why this design?

| Decision | Rationale |
|----------|-----------|
| Pre-aggregate in Load, not in API | Fast read path; complex aggregations done once per ETL run, not per request |
| Replace fact table each run | Simpler than incremental loads; perfectly OK for ~10K rows; predictable state |
| Append-only `etl_runs` | Audit trail; lets you compare runs over time |
| `stats_json` blob | Future-proof: new stats added in Transform appear in audit log without schema migration |
| Same SQLite DB as Phase 1 | Single connection, easy joins between operational and analytical data, no second DB to manage |

## Future enhancements (out of Phase 2 scope)

- Incremental ETL (only process new complaints since last run)
- Real-time ETL triggered by INSERT on `complaints` table
- Materialized views in PostgreSQL when migrating off SQLite
- Streaming analytics with Kafka + Spark
- ML-based complaint categorization
- Anomaly detection on SLA breach patterns
