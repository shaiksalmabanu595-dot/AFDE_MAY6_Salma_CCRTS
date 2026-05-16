from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import Complaint, Category, User, Role
from app.schemas import DashboardStats
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.role_id == current.role_id).first()
    role_name = role.role_name if role else ""

    q = db.query(Complaint)
    if role_name == "Customer":
        q = q.filter(Complaint.customer_id == current.user_id)
    elif role_name == "Agent":
        q = q.filter(Complaint.assigned_to == current.user_id)

    complaints = q.all()

    total = len(complaints)
    counts = {s: 0 for s in ["Open", "Assigned", "In Progress", "Resolved", "Closed", "Escalated"]}
    sla_breached = 0
    resolution_hours_sum = 0.0
    resolved_count = 0
    by_priority = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    by_category = {}

    now = datetime.now(timezone.utc)

    for c in complaints:
        if c.status in counts:
            counts[c.status] += 1
        by_priority[c.priority] = by_priority.get(c.priority, 0) + 1

        cat = db.query(Category).filter(Category.category_id == c.category_id).first()
        cat_name = cat.category_name if cat else "Unknown"
        by_category[cat_name] = by_category.get(cat_name, 0) + 1

        # SLA breach
        if c.status not in ("Resolved", "Closed"):
            created = c.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            deadline = created + timedelta(hours=c.sla_hours)
            if now > deadline:
                sla_breached += 1

        if c.resolved_at:
            created = c.created_at
            resolved = c.resolved_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if resolved.tzinfo is None:
                resolved = resolved.replace(tzinfo=timezone.utc)
            hours = (resolved - created).total_seconds() / 3600.0
            resolution_hours_sum += hours
            resolved_count += 1

    avg_resolution = round(resolution_hours_sum / resolved_count, 2) if resolved_count else 0.0

    return {
        "total": total,
        "open": counts["Open"],
        "assigned": counts["Assigned"],
        "in_progress": counts["In Progress"],
        "resolved": counts["Resolved"],
        "closed": counts["Closed"],
        "escalated": counts["Escalated"],
        "sla_breached": sla_breached,
        "avg_resolution_hours": avg_resolution,
        "by_priority": by_priority,
        "by_category": by_category,
    }
