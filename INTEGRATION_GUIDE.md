# Phase 2 Integration Guide

This Phase 2 bundle adds an ETL pipeline + analytics dashboards to your
existing Phase 1 CCRTS project. **Phase 1 files are NOT modified** -- only
new files are added, plus 3 tiny edits to existing files (router register,
nav link, route registration).

## Folder Layout (in your repo)

After integration, your repo will have:

```
AFDE_May6_Salma_CCRTS/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── analytics.py         <-- NEW (rename app_analytics_router.py)
│   │   └── main.py                  <-- TINY EDIT (one import + one include)
│   ├── etl/                         <-- NEW FOLDER
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   └── run_etl.py
│   ├── scripts/
│   │   └── generate_sample_data.py  (already exists)
│   └── requirements.txt             <-- ADD: pandas
├── frontend/
│   ├── package.json                 <-- ADD: recharts
│   └── src/
│       ├── App.jsx                  <-- TINY EDIT (one route)
│       ├── components/
│       │   └── Navbar.jsx           <-- TINY EDIT (one nav link)
│       └── pages/
│           └── Analytics.jsx        <-- NEW
├── datasets/
│   └── complaints_sample.csv        (already exists)
└── docs/
    └── ETL.md                       <-- NEW
```

---

## Step 1 — Copy New Files

From this `phase2/` bundle into your repo:

| Source (in this bundle) | Destination (in your repo) |
|---|---|
| `backend/etl/` (whole folder) | `backend/etl/` |
| `backend/app_analytics_router.py` | `backend/app/routers/analytics.py` |
| `frontend/src/pages/Analytics.jsx` | `frontend/src/pages/Analytics.jsx` |
| `docs/ETL.md` | `docs/ETL.md` |
| `README_PHASE2.md` | append its content into your existing `README.md` |

## Step 2 — Edit `backend/app/main.py`

Add two lines.

Find this block near the top:

```python
from app.routers import auth, users, categories, complaints, feedback, dashboard
```

Change it to:

```python
from app.routers import auth, users, categories, complaints, feedback, dashboard, analytics
```

Then find the existing router registrations at the bottom:

```python
app.include_router(auth.router)
app.include_router(users.router)
# ... etc
app.include_router(dashboard.router)
```

Add at the end:

```python
app.include_router(analytics.router)
```

## Step 3 — Edit `frontend/src/App.jsx`

Add the Analytics import and route.

At the top of the file, add:

```jsx
import Analytics from './pages/Analytics'
```

In the `<Routes>` block, add this line near the other protected routes:

```jsx
<Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
```

## Step 4 — Edit `frontend/src/components/Navbar.jsx`

Add an Analytics link that only Admin/Supervisor see.

Find this block inside the `<div className="navbar-links">`:

```jsx
{user.role === 'Admin' && <Link to="/users">Users</Link>}
```

Add this right after it:

```jsx
{(user.role === 'Admin' || user.role === 'Supervisor') && (
  <Link to="/analytics">Analytics</Link>
)}
```

## Step 5 — Update backend dependencies

Edit `backend/requirements.txt` and add:

```
pandas==2.2.3
```

Then in your backend Git Bash terminal (with venv active):

```bash
pip install pandas==2.2.3
```

## Step 6 — Update frontend dependencies

Edit `frontend/package.json`, under `dependencies` add:

```json
"recharts": "^2.13.0"
```

Then:

```bash
cd frontend
npm install
```

(or `npm install recharts@^2.13.0` directly)

## Step 7 — Run the ETL pipeline

From the **project root** (`AFDE_May6_Salma_CCRTS/`):

```bash
# Make sure venv is active
source backend/venv/Scripts/activate    # Git Bash on Windows

# Run the ETL
python -m backend.etl.run_etl
```

You should see output ending with:

```
ETL run #1 complete in 0.67s
  Rows extracted:      10400
  Rows loaded:         10200
  Duplicates removed:  200
  ...
```

This creates 6 new analytics tables in your existing `backend/ccrts.db`.

## Step 8 — Restart backend + frontend

In one terminal:
```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

In another terminal:
```bash
cd frontend
npm run dev
```

## Step 9 — View the Analytics dashboard

1. Open http://localhost:5173
2. Log in as `admin@ccrts.com / admin123`
3. Click **Analytics** in the navbar (only visible to Admin/Supervisor)
4. You should see all 4 charts + tables populated with data from the ETL

## Step 10 — Verify analytics APIs work

In Git Bash with backend running:

```bash
# Get token
TOKEN=$(curl -s -X POST http://127.0.0.1:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ccrts.com","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

# Hit analytics endpoints
curl -s http://127.0.0.1:8001/api/analytics/overview     -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8001/api/analytics/categories   -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8001/api/analytics/sla          -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8001/api/analytics/agents       -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8001/api/analytics/trends       -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8001/api/analytics/etl-runs     -H "Authorization: Bearer $TOKEN"
```

Each should return valid JSON.

---

## Troubleshooting

**"Analytics tables not found"** — you haven't run the ETL yet. Do step 7.

**"ModuleNotFoundError: No module named 'pandas'"** — you didn't install pandas. Do step 5.

**Charts don't appear / blank Analytics page** — recharts not installed. Do step 6.

**Analytics link not in navbar** — you didn't edit Navbar.jsx. Do step 4. Also confirm you're logged in as Admin or Supervisor (not Customer or Agent).

**ETL fails: "CSV not found"** — your CSV is at a different path. Run with explicit path:
```bash
python -m backend.etl.run_etl --csv datasets/complaints_sample.csv
```

---

## What this adds to your rubric

Phase 2 evaluation criteria are typically:
- ETL implementation (Extract / Transform / Load) — fully covered
- Data cleaning quality — 5 distinct cleanups logged per run
- Analytics tables — 5 pre-aggregated reporting tables
- Frontend dashboards — Analytics page with line/bar/pie charts + tables
- ETL audit trail — `etl_runs` table records every run
