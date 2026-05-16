# Screenshots

Place screenshots of the running application here. Per the capstone submission guidelines, include:

## Required Screenshots

- `01-login-page.png` — Login screen with demo accounts visible
- `02-register-page.png` — Customer registration form
- `03-dashboard-customer.png` — Dashboard from a customer's view
- `04-dashboard-admin.png` — Dashboard from an admin's view (full system stats)
- `05-new-complaint.png` — New complaint registration form
- `06-complaints-list.png` — Complaints list with filters applied
- `07-complaints-search.png` — Search functionality demonstration
- `08-complaint-detail.png` — Single complaint with history timeline
- `09-assign-complaint.png` — Admin assigning a complaint to an agent
- `10-status-update.png` — Agent updating status to "In Progress" or "Resolved"
- `11-feedback-form.png` — Customer submitting feedback
- `12-users-page.png` — Admin's user management page
- `13-postman-login.png` — Postman: login endpoint
- `14-postman-create-complaint.png` — Postman: creating a complaint
- `15-postman-dashboard-stats.png` — Postman: dashboard stats response
- `16-swagger-docs.png` — Auto-generated Swagger UI at `/docs`

## How to Capture

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to `http://localhost:5173`
4. Use the demo accounts (or browser DevTools' device toolbar for responsive captures)
5. For Postman screenshots, import a collection or build requests against `http://127.0.0.1:8000`
6. Save all `.png` files into this folder

## Notes
- Capture at 1280×800 or larger
- Make sure no personal/sensitive data is visible
- Both light/empty states and populated states are useful
