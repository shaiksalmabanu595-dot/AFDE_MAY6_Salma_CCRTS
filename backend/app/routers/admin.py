"""
Admin utility routes — import sample CSV data, etc.
"""
import csv
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User, Category, Complaint, Feedback
from app.utils.auth import hash_password, require_roles

router = APIRouter(prefix="/api/admin", tags=["Admin"])

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "datasets", "complaints_sample.csv"
)


def _parse_dt(value: str):
    if not value or not value.strip():
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


@router.post("/import-csv", dependencies=[Depends(require_roles("Admin"))])
def import_csv(db: Session = Depends(get_db)):
    """Load complaints_sample.csv into the database (idempotent — skips existing codes)."""
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail=f"CSV not found at {CSV_PATH}")

    # Pre-hash passwords once to avoid bcrypt cost per user
    customer_pw = hash_password("customer123")
    agent_pw = hash_password("agent123")

    rows = []
    unique_categories: set = set()
    unique_customers: dict = {}
    unique_agents: set = set()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
            unique_categories.add(row["category"].strip())
            unique_customers[row["customer_email"].strip()] = row["customer_name"].strip()
            if row["assigned_to"].strip():
                unique_agents.add(row["assigned_to"].strip())

    customer_role = db.query(Role).filter(Role.role_name == "Customer").first()
    agent_role = db.query(Role).filter(Role.role_name == "Agent").first()

    # Ensure categories exist
    cat_map: dict = {}
    for name in unique_categories:
        cat = db.query(Category).filter(Category.category_name == name).first()
        if not cat:
            cat = Category(category_name=name, description=f"Category: {name}")
            db.add(cat)
            db.flush()
        cat_map[name] = cat.category_id

    # Ensure customer users exist
    customer_map: dict = {}
    for email, full_name in unique_customers.items():
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=full_name,
                email=email,
                password_hash=customer_pw,
                role_id=customer_role.role_id,
            )
            db.add(user)
            db.flush()
        customer_map[email] = user.user_id

    # Ensure agent users exist
    agent_map: dict = {}
    for code in unique_agents:
        agent_email = f"{code}@ccrts.com"
        user = db.query(User).filter(User.email == agent_email).first()
        if not user:
            user = User(
                name=code.capitalize(),
                email=agent_email,
                password_hash=agent_pw,
                role_id=agent_role.role_id,
            )
            db.add(user)
            db.flush()
        agent_map[code] = user.user_id

    db.commit()

    # Import complaints
    imported = skipped = 0
    for row in rows:
        code = row["complaint_code"].strip()
        if db.query(Complaint).filter(Complaint.complaint_code == code).first():
            skipped += 1
            continue

        email = row["customer_email"].strip()
        cat_name = row["category"].strip()
        agent_code = row["assigned_to"].strip()
        status = row["status"].strip()
        resolved_at = _parse_dt(row.get("resolved_at", ""))
        closed_at = resolved_at if status == "Closed" else None

        complaint = Complaint(
            complaint_code=code,
            customer_id=customer_map[email],
            category_id=cat_map[cat_name],
            assigned_to=agent_map.get(agent_code) if agent_code else None,
            title=row["title"].strip(),
            description=row["title"].strip(),
            priority=row["priority"].strip(),
            status=status,
            sla_hours=int(row["sla_hours"]) if row["sla_hours"] else 48,
            created_at=_parse_dt(row.get("created_at", "")),
            resolved_at=resolved_at,
            closed_at=closed_at,
        )
        db.add(complaint)
        db.flush()

        rating_str = row.get("feedback_rating", "").strip()
        if rating_str:
            try:
                rating = int(float(rating_str))
                if 1 <= rating <= 5:
                    db.add(Feedback(
                        complaint_id=complaint.complaint_id,
                        rating=rating,
                        comments=row.get("resolution_comment", "").strip() or None,
                    ))
            except ValueError:
                pass

        imported += 1

    db.commit()
    return {
        "status": "ok",
        "imported": imported,
        "skipped": skipped,
        "categories_ensured": len(unique_categories),
        "customer_accounts": len(unique_customers),
        "agent_accounts": len(unique_agents),
    }
