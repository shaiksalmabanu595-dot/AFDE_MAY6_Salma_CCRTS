from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Role
from app.schemas import UserOut
from app.utils.auth import require_roles, get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


def _to_out(user: User, db: Session) -> dict:
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role_id": user.role_id,
        "role_name": role.role_name if role else None,
        "created_at": user.created_at,
    }


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: dict = Depends(require_roles("Admin", "Supervisor"))):
    users = db.query(User).all()
    return [_to_out(u, db) for u in users]


@router.get("/agents", response_model=List[UserOut])
def list_agents(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    agent_role = db.query(Role).filter(Role.role_name == "Agent").first()
    if not agent_role:
        return []
    users = db.query(User).filter(User.role_id == agent_role.role_id).all()
    return [_to_out(u, db) for u in users]


@router.get("/me", response_model=UserOut)
def get_me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    return _to_out(current, db)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), _: dict = Depends(require_roles("Admin"))):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
