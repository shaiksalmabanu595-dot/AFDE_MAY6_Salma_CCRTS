# CCRTS API Documentation

**Base URL:** `http://127.0.0.1:8000`
**Interactive Docs:** `http://127.0.0.1:8000/docs` (Swagger UI)

All authenticated endpoints require an `Authorization: Bearer <token>` header.

---

## Authentication

### POST `/api/auth/register`

**Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "secure123",
  "phone": "+91-9000000000",
  "role": "Customer"
}
```
Valid roles: `Customer`, `Agent`, `Supervisor`, `Admin`.

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { "user_id": 4, "name": "Jane Doe", "email": "jane@example.com", "role": "Customer" }
}
```

### POST `/api/auth/login`

**Body:**
```json
{ "email": "customer@ccrts.com", "password": "customer123" }
```

**Response (200):** Same shape as register.

---

## Complaints

### POST `/api/complaints/` — Create

**Auth:** any authenticated user
**Body:**
```json
{
  "category_id": 1,
  "title": "Wrong bill amount",
  "description": "I was charged twice for September",
  "priority": "High"
}
```
Priority: `Low` | `Medium` | `High` | `Critical` (SLAs: 72h / 48h / 24h / 4h)

**Response (201):**
```json
{
  "complaint_id": 1,
  "complaint_code": "CMP-2026-00001",
  "customer_id": 3,
  "customer_name": "Jane Customer",
  "category_id": 1,
  "category_name": "Billing Issues",
  "assigned_to": null,
  "agent_name": null,
  "title": "Wrong bill amount",
  "description": "I was charged twice for September",
  "priority": "High",
  "status": "Open",
  "sla_hours": 24,
  "sla_breached": false,
  "created_at": "2026-05-16T10:00:00",
  "updated_at": "2026-05-16T10:00:00",
  "resolved_at": null,
  "closed_at": null
}
```

### GET `/api/complaints/` — List with filters

**Query parameters (all optional):**
- `status` — exact match (e.g. `Open`)
- `priority` — exact match
- `category_id` — integer
- `search` — substring match against title, description, complaint_code (case-insensitive)
- `assigned_to_me` — boolean (for agents)
- `my_complaints` — boolean (for customers)

**Example:** `GET /api/complaints/?status=Open&priority=High&search=billing`

Role-based visibility:
- **Customer** — sees only their own complaints.
- **Agent** — sees all unless `assigned_to_me=true`.
- **Admin / Supervisor** — sees all.

### GET `/api/complaints/{id}` — Get one

Returns the same shape as create. Customers can only view their own.

### PUT `/api/complaints/{id}/assign` — Assign

**Auth:** Admin or Supervisor only
**Body:**
```json
{ "agent_id": 2 }
```
Auto-transitions status from `Open` to `Assigned` if applicable.

### PUT `/api/complaints/{id}/status` — Update status

**Auth:** Admin, Supervisor, assigned Agent, or owning Customer (close only)
**Body:**
```json
{ "new_status": "Resolved", "comment": "Refund processed" }
```
Valid statuses: `Open`, `Assigned`, `In Progress`, `Pending Customer Response`, `Escalated`, `Resolved`, `Closed`

Customers can only set `Closed` on their own `Resolved` complaints.
Setting `Resolved` records `resolved_at`. Setting `Closed` records `closed_at`.

### GET `/api/complaints/{id}/history` — Audit trail

**Response:**
```json
[
  {
    "history_id": 4,
    "complaint_id": 1,
    "updated_by": 2,
    "updated_by_name": "John Agent",
    "old_status": "In Progress",
    "new_status": "Resolved",
    "comment": "Refund processed",
    "updated_at": "2026-05-16T11:30:00"
  }
]
```

### DELETE `/api/complaints/{id}` — Delete

**Auth:** Admin only. Returns 204.

---

## Categories

### GET `/api/categories/`
List all categories. Authenticated.

### POST `/api/categories/` — Admin only
**Body:** `{ "category_name": "Network Issues", "description": "..." }`

### DELETE `/api/categories/{id}` — Admin only

---

## Users

### GET `/api/users/` — Admin/Supervisor
Returns all users with role names.

### GET `/api/users/agents`
List of users with role `Agent`. Used for assignment dropdowns.

### GET `/api/users/me`
Current authenticated user.

### DELETE `/api/users/{id}` — Admin only

---

## Feedback

### POST `/api/feedback/{complaint_id}`

**Auth:** Owner of the complaint, only after `Resolved` or `Closed`, only once.
**Body:**
```json
{ "rating": 5, "comments": "Quick resolution, very satisfied" }
```

### GET `/api/feedback/{complaint_id}`
Returns the feedback object, or 404 if none.

---

## Dashboard

### GET `/api/dashboard/stats`

Role-aware aggregation:
- **Customer** — stats over their own complaints only.
- **Agent** — stats over complaints assigned to them.
- **Admin/Supervisor** — system-wide stats.

**Response:**
```json
{
  "total": 12,
  "open": 3,
  "assigned": 2,
  "in_progress": 4,
  "resolved": 2,
  "closed": 1,
  "escalated": 0,
  "sla_breached": 1,
  "avg_resolution_hours": 18.5,
  "by_priority": { "Low": 1, "Medium": 5, "High": 4, "Critical": 2 },
  "by_category": { "Billing Issues": 4, "Technical Problems": 3, ... }
}
```

---

## Common Error Responses

| Code | Meaning |
|------|---------|
| 400 | Bad request — validation failed, missing fields, invalid status transition |
| 401 | Missing or invalid JWT |
| 403 | Authenticated but lacks required role |
| 404 | Resource not found |
| 422 | Pydantic validation error (FastAPI default) |

All errors follow:
```json
{ "detail": "Human-readable error message" }
```

---

## Testing with cURL

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@ccrts.com","password":"customer123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Create complaint
curl -X POST http://127.0.0.1:8000/api/complaints/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category_id":1,"title":"Test","description":"Test desc","priority":"High"}'

# 3. List complaints
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/complaints/?priority=High"

# 4. Dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/dashboard/stats
```
