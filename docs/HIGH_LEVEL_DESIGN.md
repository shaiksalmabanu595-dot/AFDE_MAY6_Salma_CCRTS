# CCRTS - High Level Design Document

## 1. Architecture Overview

CCRTS follows a classic **3-tier architecture**:

```
┌─────────────────────────────────────┐
│   Presentation Layer (Frontend)     │
│   React 18 + Vite + React Router    │
│   (http://localhost:5173)           │
└─────────────┬───────────────────────┘
              │ HTTPS/JSON (Axios)
              │ Bearer JWT
              ▼
┌─────────────────────────────────────┐
│   Application Layer (Backend API)   │
│   FastAPI + Pydantic + SQLAlchemy   │
│   (http://127.0.0.1:8000)           │
│                                     │
│  ┌──────────┐  ┌──────────────┐    │
│  │ Routers  │→ │ Auth/RBAC    │    │
│  │ (REST)   │  │ Middleware   │    │
│  └──────────┘  └──────────────┘    │
│         │                           │
│         ▼                           │
│  ┌──────────────────────┐           │
│  │ ORM Models           │           │
│  │ (SQLAlchemy)         │           │
│  └──────────────────────┘           │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Data Layer                        │
│   SQLite (file-based, ccrts.db)     │
│   Schema-compatible with            │
│   PostgreSQL / MySQL                │
└─────────────────────────────────────┘
```

## 2. Module Breakdown

### Frontend Modules
1. **Auth** — Login, Register, token persistence, AuthContext
2. **Dashboard** — Stats cards, priority/category breakdowns
3. **Complaints** — List with search/filters, detail view, registration, workflow actions
4. **Users** — Admin user management

### Backend Modules
1. **Authentication** (`routers/auth.py`) — Register, login, JWT issuance
2. **Authorization** (`utils/auth.py`) — Role-based guards
3. **Complaints** (`routers/complaints.py`) — Core CRUD, workflow, assignment, history
4. **Categories** (`routers/categories.py`)
5. **Users** (`routers/users.py`)
6. **Feedback** (`routers/feedback.py`)
7. **Dashboard** (`routers/dashboard.py`) — Aggregated statistics

## 3. Workflow State Machine

```
   ┌───────┐
   │ Open  │ ←── (Customer registers complaint)
   └───┬───┘
       │ (Admin assigns to agent)
       ▼
  ┌──────────┐
  │ Assigned │
  └────┬─────┘
       │ (Agent picks up)
       ▼
  ┌─────────────┐    ┌─────────────────────────┐
  │ In Progress │ ↔  │ Pending Customer Resp.  │
  └──────┬──────┘    └─────────────────────────┘
         │
         │ (Cannot resolve / SLA risk)
         ├──────────────────────┐
         │                      ▼
         │              ┌──────────────┐
         │              │  Escalated   │
         │              └──────┬───────┘
         │ (Agent resolves)    │ (Handled)
         ▼                     ▼
   ┌──────────┐  ←─────────────┘
   │ Resolved │
   └────┬─────┘
        │ (Customer confirms)
        ▼
   ┌────────┐
   │ Closed │
   └────────┘
```

## 4. Authentication & Authorization Flow

1. User POSTs credentials to `/api/auth/login`
2. Backend verifies password against bcrypt hash
3. Backend issues JWT (24h expiry) containing `sub=user_id` and `role`
4. Frontend stores JWT in localStorage
5. Every API call attaches `Authorization: Bearer <token>` via Axios interceptor
6. FastAPI dependency `get_current_user` decodes JWT and loads user
7. Route-level dependency `require_roles("Admin", "Supervisor")` enforces authorization

## 5. SLA Computation

SLA breach is computed **on-read** (no cron job needed):
```python
deadline = complaint.created_at + timedelta(hours=complaint.sla_hours)
sla_breached = (now > deadline) and (status not in ["Resolved", "Closed"])
```

SLA hours by priority:
- Low: 72h, Medium: 48h, High: 24h, Critical: 4h

## 6. Audit Trail

Every state change (creation, assignment, status update) inserts a row in `complaint_history`:
- `old_status`, `new_status`, `updated_by`, `comment`, `updated_at`

This gives a complete, immutable timeline per complaint.

## 7. Why These Choices?

| Decision | Rationale |
|----------|-----------|
| **FastAPI** | Auto-generated OpenAPI docs; native async; tight Pydantic integration; minimal boilerplate |
| **SQLite** | Zero setup; portable; perfectly adequate for a Phase 1 capstone; schema portable to Postgres/MySQL |
| **JWT** | Stateless; no server-side session store needed; standard pattern |
| **React + Vite** | Industry-standard frontend; instant HMR; small bundle; familiar to evaluators |
| **bcrypt direct (not passlib)** | Avoids a known passlib 1.7 + bcrypt 4.x incompatibility bug |
| **Audit table over event log** | Simpler queries; sufficient for capstone scope; can later be replaced by event-sourcing |
