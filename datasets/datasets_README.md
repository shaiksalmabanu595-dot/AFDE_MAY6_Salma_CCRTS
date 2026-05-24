# CCRTS Sample Dataset

## File: complaints_sample.csv

Synthetic complaint dataset for Phase 2 ETL pipeline testing.

## Schema

| Column | Type | Description |
|---|---|---|
| complaint_id | int | Unique complaint identifier |
| complaint_code | string | Auto-generated code (e.g. CMP-2026-00001) |
| customer_name | string | Customer full name |
| customer_email | string | Customer email address |
| category | string | Complaint category |
| priority | string | Low / Medium / High / Critical |
| status | string | Open / Assigned / In Progress / Resolved / Closed / Escalated |
| title | string | Short complaint title |
| sla_hours | int | SLA target hours based on priority |
| sla_breached | bool | Whether SLA was breached |
| assigned_to | string | Agent ID assigned to complaint |
| assigned_at | datetime | When complaint was assigned |
| created_at | datetime | When complaint was submitted |
| resolved_at | datetime | When complaint was resolved (null if unresolved) |
| resolution_time_hours | float | Actual hours taken to resolve |
| resolution_comment | string | Agent resolution notes |
| feedback_rating | int | Customer rating 1-5 (null if not provided) |

## Intentional Data Quality Issues (for ETL to handle)

| Issue | Count | ETL Action |
|---|---|---|
| Duplicate records | ~200 | Deduplicate |
| Invalid resolution times (< 0) | ~266 | Drop / null out |
| Priority casing noise (MEDIUM, LOW) | ~322 | Normalize to Title Case |
| Category whitespace | ~208 | Strip whitespace |
| Invalid feedback ratings (0) | ~varies | Drop invalid |

## Statistics

- Total records: 10,400
- Date range: May 2025 – May 2026 (13 months)
- SLA breach rate: ~29%
- Categories: 10
- Agents: 10
