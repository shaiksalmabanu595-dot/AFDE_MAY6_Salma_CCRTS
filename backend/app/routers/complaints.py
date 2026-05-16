from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import Complaint, ComplaintHistory, User, Category, Role
from app.schemas import (
    ComplaintCreate, ComplaintOut, ComplaintAssign,
    ComplaintStatusUpdate, HistoryOut
)
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

SLA_MAP = {"Low": 72, "Medium": 48, "High": 24, "Critical": 4}
VALID_STATUSES = [
    "Open", "Assigned", "In Progress",
    "Pending Customer Response", "Escalated", "Resolved", "Closed"
]


def _generate_complaint_code(db: Session) -> str:
    year = datetime.now().year
    count = db.query(Complaint).count() + 1
    return f"CMP-{year}-{count:05d}"


def _is_sla_breached(complaint: Complaint) -> bool:
    if complaint.status in ("Resolved", "Closed"):
        return False
    created = complaint.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    deadline = created + timedelta(hours=complaint.sla_hours)
    return datetime.now(timezone.utc) > deadline


def _to_out(c: Complaint, db: Session) -> dict:
    customer = db.query(User).filter(User.user_id == c.customer_id).first()
    agent = db.query(User).filter(User.user_id == c.assigned_to).first() if c.assigned_to else None
    category = db.query(Category).filter(Category.category_id == c.category_id).first()
    return {
        "complaint_id": c.complaint_id,
        "complaint_code": c.complaint_code,
        "customer_id": c.customer_id,
        "customer_name": customer.name if customer else None,
        "category_id": c.category_id,
        "category_name": category.category_name if category else None,
        "assigned_to": c.assigned_to,
        "agent_name": agent.name if agent else None,
        "title": c.title,
        "description": c.description,
        "priority": c.priority,
        "status": c.status,
        "sla_hours": c.sla_hours,
        "sla_breached": _is_sla_breached(c),
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "resolved_at": c.resolved_at,
        "closed_at": c.closed_at,
    }


def _get_role_name(user: User, db: Session) -> str:
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return role.role_name if role else ""


# ---------- Create ----------
@router.post("/", response_model=ComplaintOut, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if payload.priority not in SLA_MAP:
        raise HTTPException(status_code=400, detail=f"Priority must be one of {list(SLA_MAP.keys())}")

    if not db.query(Category).filter(Category.category_id == payload.category_id).first():
        raise HTTPException(status_code=400, detail="Invalid category_id")

    complaint = Complaint(
        complaint_code=_generate_complaint_code(db),
        customer_id=current.user_id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status="Open",
        sla_hours=SLA_MAP[payload.priority],
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # initial history entry
    history = ComplaintHistory(
        complaint_id=complaint.complaint_id,
        updated_by=current.user_id,
        old_status=None,
        new_status="Open",
        comment="Complaint registered",
    )
    db.add(history)
    db.commit()

    return _to_out(complaint, db)


# ---------- List with filters / search ----------
@router.get("/", response_model=List[ComplaintOut])
def list_complaints(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Search in title/description/code"),
    assigned_to_me: bool = Query(False),
    my_complaints: bool = Query(False),
):
    role = _get_role_name(current, db)
    q = db.query(Complaint)

    # role-based visibility
    if role == "Customer":
        q = q.filter(Complaint.customer_id == current.user_id)
    elif role == "Agent" and assigned_to_me:
        q = q.filter(Complaint.assigned_to == current.user_id)

    if my_complaints:
        q = q.filter(Complaint.customer_id == current.user_id)

    if status:
        q = q.filter(Complaint.status == status)
    if priority:
        q = q.filter(Complaint.priority == priority)
    if category_id:
        q = q.filter(Complaint.category_id == category_id)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(
            Complaint.title.ilike(like),
            Complaint.description.ilike(like),
            Complaint.complaint_code.ilike(like),
        ))

    complaints = q.order_by(Complaint.created_at.desc()).all()
    return [_to_out(c, db) for c in complaints]


# ---------- Get one ----------
@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    role = _get_role_name(current, db)
    if role == "Customer" and c.customer_id != current.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this complaint")
    return _to_out(c, db)


# ---------- Assign to agent ----------
@router.put("/{complaint_id}/assign", response_model=ComplaintOut)
def assign_complaint(
    complaint_id: int,
    payload: ComplaintAssign,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("Admin", "Supervisor")),
):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    agent = db.query(User).filter(User.user_id == payload.agent_id).first()
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not found")
    agent_role = db.query(Role).filter(Role.role_id == agent.role_id).first()
    if not agent_role or agent_role.role_name != "Agent":
        raise HTTPException(status_code=400, detail="User is not an Agent")

    old_status = c.status
    c.assigned_to = payload.agent_id
    if c.status == "Open":
        c.status = "Assigned"

    db.add(ComplaintHistory(
        complaint_id=c.complaint_id,
        updated_by=current.user_id,
        old_status=old_status,
        new_status=c.status,
        comment=f"Assigned to agent {agent.name}",
    ))
    db.commit()
    db.refresh(c)
    return _to_out(c, db)


# ---------- Update status ----------
@router.put("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(
    complaint_id: int,
    payload: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if payload.new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of {VALID_STATUSES}")

    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    role = _get_role_name(current, db)
    # Authorization: customer can only close their own resolved complaints; agents/admins/supervisors can do more
    if role == "Customer":
        if c.customer_id != current.user_id:
            raise HTTPException(status_code=403, detail="Not your complaint")
        if payload.new_status not in ("Closed",):
            raise HTTPException(status_code=403, detail="Customers can only close resolved complaints")
        if c.status != "Resolved":
            raise HTTPException(status_code=400, detail="Can only close a Resolved complaint")

    old_status = c.status
    c.status = payload.new_status
    now = datetime.now(timezone.utc)
    if payload.new_status == "Resolved" and not c.resolved_at:
        c.resolved_at = now
    if payload.new_status == "Closed" and not c.closed_at:
        c.closed_at = now

    db.add(ComplaintHistory(
        complaint_id=c.complaint_id,
        updated_by=current.user_id,
        old_status=old_status,
        new_status=payload.new_status,
        comment=payload.comment,
    ))
    db.commit()
    db.refresh(c)
    return _to_out(c, db)


# ---------- History ----------
@router.get("/{complaint_id}/history", response_model=List[HistoryOut])
def get_history(complaint_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    role = _get_role_name(current, db)
    if role == "Customer" and c.customer_id != current.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    history = db.query(ComplaintHistory).filter(
        ComplaintHistory.complaint_id == complaint_id
    ).order_by(ComplaintHistory.updated_at.desc()).all()

    out = []
    for h in history:
        user = db.query(User).filter(User.user_id == h.updated_by).first()
        out.append({
            "history_id": h.history_id,
            "complaint_id": h.complaint_id,
            "updated_by": h.updated_by,
            "updated_by_name": user.name if user else None,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "comment": h.comment,
            "updated_at": h.updated_at,
        })
    return out


# ---------- Delete (admin only) ----------
@router.delete("/{complaint_id}", status_code=204)
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    db.delete(c)
    db.commit()
