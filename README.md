# Customer Complaint & Resolution Tracking System (CCRTS)

**Capstone Project — Phase 1**
**Repository:** `AFDE_May6_Salma_CCRTS`
**Participant:** Salma | **Batch:** AFDE_May6 | **Project Code:** CCRTS

---

## 1. Project Overview

The **Customer Complaint & Resolution Tracking System (CCRTS)** is a centralized full-stack web application that helps organizations log, monitor, assign, escalate, and resolve customer complaints efficiently. It replaces fragmented email and spreadsheet-based complaint tracking with a single platform that maintains a structured workflow from complaint initiation to closure.

The system supports four roles — **Customer**, **Agent**, **Supervisor**, and **Admin** — each with role-based access control, and produces a complete audit trail for every complaint.

### Applicable Industries

Telecom · Banking · Retail · E-Commerce · Healthcare · Logistics · Education · Utility Services · IT Support

---

## 2. Features Implemented (Phase 1)

### Authentication & Authorization
- JWT-based secure login & registration
- Password hashing using bcrypt
- Role-based access control (Admin / Agent / Supervisor / Customer)
- Token persistence across page refreshes

### Complaint Registration
- Customers register complaints with title, description, category, and priority
- Auto-generated complaint codes (e.g., `CMP-2026-00001`)
- SLA hours automatically calculated based on priority

### Complaint Workflow
- 7 workflow statuses: `Open → Assigned → In Progress → Pending Customer Response → Escalated → Resolved → Closed`
- Admin/Supervisor assigns complaints to Agents
- Agents update status and add resolution comments
- Customers confirm resolution to close the complaint
- Complete audit trail of all status changes (who, when, what, why)

### SLA & Escalation Management
- SLA tracking per priority: **Low** (72h), **Medium** (48h), **High** (24h), **Critical** (4h)
- Automatic SLA breach detection (visible on every complaint)
- Manual escalation by updating status to `Escalated`

### Search & Filtering
- Search complaints by title, description, or complaint code
- Filter by status, priority, category
- Agent-specific "Assigned to me" filter
- Customer-specific "My complaints" filter

### Dashboard & Analytics
- Total / Open / In Progress / Resolved / Closed / Escalated counts
- SLA breach count and average resolution time
- Breakdown by priority (with visual bars)
- Breakdown by category
- Role-aware: customers see only their data, agents see assigned data

### Feedback Management
- Customer feedback collection (1-5 star rating + comments)
- Feedback restricted to Resolved/Closed complaints
- One feedback per complaint

### User Management
- Admin views all users with role and registration date
- Search users by name/email and filter by role
- List agents available for assignment

---

## 3. Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, React Router 6, Axios, plain CSS |
| **Backend** | FastAPI (Python 3.10+), SQLAlchemy 2.x, Pydantic v2 |
| **Database** | SQLite (portable; schema is compatible with PostgreSQL/MySQL) |
| **Authentication** | JWT (python-jose) + bcrypt password hashing |
| **API Documentation** | Swagger UI (auto-generated at `/docs`) |
| **Tools** | GitHub, Postman, VS Code |

---

## 4. Project Structure

```
AFDE_May6_Salma_CCRTS/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry; CORS; seeding
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/__init__.py   # ORM models
│   │   ├── schemas/__init__.py  # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py          # /api/auth/* (login, register)
│   │   │   ├── users.py         # /api/users/*
│   │   │   ├── categories.py    # /api/categories/*
│   │   │   ├── complaints.py    # /api/complaints/* (core CRUD + workflow)
│   │   │   ├── feedback.py      # /api/feedback/*
│   │   │   └── dashboard.py     # /api/dashboard/stats
│   │   └── utils/auth.py        # JWT, hashing, role guards
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router + protected routes
│   │   ├── main.jsx             # React entry
│   │   ├── styles.css           # Global styles
│   │   ├── context/AuthContext.jsx
│   │   ├── services/api.js      # Axios client + API helpers
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   └── Badges.jsx
│   │   └── pages/
│   │       ├── Login.jsx
│   │       ├── Register.jsx
│   │       ├── Dashboard.jsx
│   │       ├── ComplaintsList.jsx
│   │       ├── ComplaintDetail.jsx
│   │       ├── NewComplaint.jsx
│   │       └── Users.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── database/
│   └── schema.sql               # Full schema + seed data (portable)
│
├── docs/
│   └── API.md                   # API endpoint reference
│
├── screenshots/                 # UI + API testing screenshots
├── README.md
├── requirements.txt             # Top-level Python deps (mirrors backend)
└── .gitignore
```

---

## 5. Setup Instructions

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and npm
- **Git**

### Backend Setup

```bash
# From repository root
cd backend

# (Recommended) create and activate a virtualenv
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server (auto-creates SQLite DB + seeds data on first run)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend is now live at **http://127.0.0.1:8000**
Auto-generated API docs: **http://127.0.0.1:8000/docs**

### Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is now live at **http://localhost:5173** and the browser should open automatically.

### Database Setup
The SQLite database is created automatically on first backend startup. The full schema (and seed data) is also available in `database/schema.sql` for reference or for porting to PostgreSQL/MySQL.

---

## 6. Demo Accounts

On first startup, three demo users are seeded:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@ccrts.com | admin123 |
| Agent | agent@ccrts.com | agent123 |
| Customer | customer@ccrts.com | customer123 |

Click any of these on the login screen to auto-fill the form.

---

## 7. API Overview

Full request/response reference: see [`docs/API.md`](docs/API.md)

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create new user account |
| POST | `/api/auth/login` | Authenticate and receive JWT |

### Complaints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/complaints/` | List with filters (status, priority, category_id, search) |
| POST | `/api/complaints/` | Create complaint (customer) |
| GET | `/api/complaints/{id}` | Get one |
| PUT | `/api/complaints/{id}/assign` | Assign to agent (admin/supervisor) |
| PUT | `/api/complaints/{id}/status` | Update status |
| GET | `/api/complaints/{id}/history` | Audit trail |
| DELETE | `/api/complaints/{id}` | Delete (admin) |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories/` | List complaint categories |
| POST | `/api/categories/` | Create category (admin) |
| GET | `/api/users/` | List all users (admin/supervisor) |
| GET | `/api/users/agents` | List agents for assignment |
| GET | `/api/users/me` | Current user info |
| POST | `/api/feedback/{complaint_id}` | Submit feedback |
| GET | `/api/feedback/{complaint_id}` | Get feedback |
| GET | `/api/dashboard/stats` | Aggregated stats |

---

## 8. Database Design

### Entities

- **roles** — `role_id`, `role_name`
- **users** — `user_id`, `name`, `email`, `password_hash`, `phone`, `role_id`, `created_at`
- **categories** — `category_id`, `category_name`, `description`
- **complaints** — `complaint_id`, `complaint_code`, `customer_id`, `category_id`, `assigned_to`, `title`, `description`, `priority`, `status`, `sla_hours`, `created_at`, `updated_at`, `resolved_at`, `closed_at`
- **complaint_history** — `history_id`, `complaint_id`, `updated_by`, `old_status`, `new_status`, `comment`, `updated_at`
- **feedback** — `feedback_id`, `complaint_id`, `rating` (1-5), `comments`, `created_at`

### Key Relationships
- `users.role_id` → `roles.role_id`
- `complaints.customer_id` → `users.user_id`
- `complaints.category_id` → `categories.category_id`
- `complaints.assigned_to` → `users.user_id` (nullable)
- `complaint_history.complaint_id` → `complaints.complaint_id`
- `feedback.complaint_id` → `complaints.complaint_id` (1:1)

The full schema with constraints is in [`database/schema.sql`](database/schema.sql).

---

## 9. Workflow Walkthrough

1. **Customer** logs in and registers a new complaint (Billing Issue, High priority).
   - System generates `CMP-2026-00001`, sets status to `Open`, SLA to 24h.
2. **Admin** sees the new complaint on the list, opens it, and assigns it to an Agent.
   - Status auto-transitions to `Assigned`. History logs the transition.
3. **Agent** opens the complaint from their queue, updates status to `In Progress`, adds an investigation comment.
4. Agent updates status to `Resolved` with a resolution comment.
   - `resolved_at` timestamp recorded.
5. **Customer** sees the resolved complaint, confirms by changing status to `Closed`, and submits a 5-star rating.
6. **Dashboard** updates instantly — resolved count goes up, average resolution time recomputed.

---

## 10. Testing

### Manual API Testing
Use Postman or the interactive Swagger UI at `http://127.0.0.1:8000/docs`:

1. POST `/api/auth/login` with one of the demo accounts.
2. Copy the returned `access_token`.
3. Click "Authorize" in Swagger and paste `Bearer <token>`.
4. Try the protected endpoints.

### End-to-End Workflow Verified
- Register / Login (3 roles) ✅
- Create complaint with auto-generated code ✅
- Assign to agent (admin action) ✅
- Status transitions: Open → Assigned → In Progress → Resolved ✅
- History audit trail (4 entries logged) ✅
- Customer closes complaint ✅
- Feedback submission ✅
- Dashboard stats aggregation (by priority, by category, SLA breaches) ✅

Screenshots of the working application are available in the [`screenshots/`](screenshots/) folder.

---

## 11. Evaluation Mapping

| Criteria | Weight | Where Demonstrated |
|----------|--------|--------------------|
| Frontend Development | 20% | `frontend/src/pages/*`, responsive design, validations, role-aware UI |
| Backend API Development | 25% | 25 REST endpoints across 6 routers, proper status codes, error handling |
| Database Integration | 15% | SQLAlchemy ORM, 6 tables with foreign-key relationships, audit trail |
| CRUD Functionality | 15% | Users, Categories, Complaints, Feedback — full CRUD |
| Search/Filtering | 10% | Complaint search + 4 filter dimensions; user search + role filter |
| Code Quality & Structure | 10% | Layered architecture, separation of concerns, modular routers/services |
| Documentation | 5% | This README, API.md, inline code comments |

---

## 12. Future Enhancements (Out of Phase 1 Scope)

- File attachments on complaints
- Email/SMS notifications
- AI-based automatic complaint categorization
- Chatbot for first-line support
- Mobile app (React Native)
- Multi-language support
- Social media complaint integration
- Predictive analytics on complaint trends
- Real-time updates via WebSockets

---

## 13. License & Plagiarism Notice

This is an academic capstone project submitted by **Salma** for the **AFDE_May6** batch.
All code in this repository was written by the participant. Any third-party libraries used are listed in `requirements.txt` and `package.json` with their open-source licenses.

---

## Phase 2 — ETL Pipeline & Analytics Dashboard

Phase 2 extends the Phase 1 application with an **ETL (Extract-Transform-Load)
pipeline** and an **analytics dashboard** powered by it.

### What's new

- **ETL pipeline** in `backend/etl/` — reads a CSV of ~10,400 complaints,
  cleans it, derives analytics columns, and loads it into reporting tables
- **5 analytics tables** in the same SQLite DB (`analytics_complaints`,
  `sla_breach_summary`, `category_summary`, `agent_performance`,
  `monthly_trends`) + an `etl_runs` audit log
- **6 new analytics API endpoints** under `/api/analytics/*`
- **`/analytics` page** in the React frontend with charts (line, bar, pie)
  and aggregated tables, restricted to Admin/Supervisor
- **Dataset** in `datasets/complaints_sample.csv` (10,400 rows, intentionally
  messy so the Transform step has meaningful work)

### ETL workflow

```
   datasets/complaints_sample.csv  (10,400 rows, ~3,860 dirty cells)
                  │
                  ▼
   ┌──────────────────────────┐
   │   1. EXTRACT (pandas)    │   read CSV + validate schema
   └─────────────┬────────────┘
                 ▼
   ┌──────────────────────────┐
   │   2. TRANSFORM           │   ~200 duplicates removed
   │                          │   ~322 priority casings normalized
   │                          │   ~3,860 whitespace cells fixed
   │                          │   ~263 negative resolutions nulled
   │                          │   ~95 invalid feedback ratings nulled
   │                          │   + derived columns (year, month,
   │                          │     resolution_bucket, is_resolved)
   └─────────────┬────────────┘
                 ▼
   ┌──────────────────────────┐
   │   3. LOAD                │   bulk insert into analytics_complaints
   │                          │   pre-aggregate into 4 summary tables
   │                          │   log run in etl_runs audit table
   └──────────────────────────┘
```

End result: 10,400 raw rows → **10,200 clean rows** loaded in ~0.7 seconds.

### How to run the ETL

```bash
# From project root, with the backend venv active
source backend/venv/Scripts/activate   # Git Bash on Windows

# Run the full pipeline
python -m backend.etl.run_etl

# Or with custom CSV / DB paths
python -m backend.etl.run_etl --csv mydata.csv --db backend/ccrts.db
```

Expected output (final lines):

```
ETL run #1 complete in 0.67s
  Rows extracted:      10400
  Rows loaded:         10200
  Duplicates removed:  200
  Whitespace fixed:    3860 cells
  Priorities normalized: 322
  Negative resolutions nulled: 263
  Invalid feedback nulled: 95
```

### Analytics API endpoints

All endpoints require **Admin** or **Supervisor** JWT token.

| Endpoint | Description |
|----------|-------------|
| `GET /api/analytics/overview` | High-level KPIs (totals, breach rate, avg resolution) |
| `GET /api/analytics/categories` | Per-category counts, avg resolution, ratings, breach rate |
| `GET /api/analytics/sla` | SLA breach rate by (priority, category) |
| `GET /api/analytics/agents` | Per-agent performance metrics |
| `GET /api/analytics/trends` | Monthly complaint volume + resolution + breaches |
| `GET /api/analytics/etl-runs` | Recent ETL run history (audit log) |

### Analytics dashboard

After running the ETL and starting both servers:

1. Open http://localhost:5173
2. Log in as **Admin** (`admin@ccrts.com / admin123`)
3. Click **Analytics** in the navbar

You'll see:
- 8 KPI cards (total complaints, resolved, breaches, avg resolution, etc.)
- Monthly trends line chart (volume, resolved, breaches)
- Category breakdown — horizontal bar chart + pie chart
- SLA breach rate heatmap-style table (color-coded by severity)
- Agent performance leaderboard (sorted by resolution rate)
- Recent ETL runs audit table

### Phase 2 documentation

- `docs/ETL.md` — full pipeline technical reference
- `INTEGRATION_GUIDE.md` — step-by-step setup if integrating into a fresh repo

### Phase 2 deliverables checklist

- ✅ ETL scripts using pandas (`backend/etl/`)
- ✅ Reporting tables (5 analytics tables + audit log)
- ✅ Analytics dashboards (frontend `/analytics` page)
- ✅ Updated APIs (`/api/analytics/*`)
- ✅ Dataset with ≥200 records (`datasets/complaints_sample.csv`, 10,400 rows)
- ✅ README explaining ETL workflow (this section)
