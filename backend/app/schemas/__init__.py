from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ---------- Auth ----------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    phone: Optional[str] = None
    role: str = "Customer"  # Customer/Agent/Admin/Supervisor


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ---------- User ----------
class UserOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Category ----------
class CategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True


# ---------- Complaint ----------
class ComplaintCreate(BaseModel):
    category_id: int
    title: str
    description: str
    priority: str = "Medium"  # Low / Medium / High / Critical


class ComplaintAssign(BaseModel):
    agent_id: int


class ComplaintStatusUpdate(BaseModel):
    new_status: str  # Open / Assigned / In Progress / Pending Customer Response / Escalated / Resolved / Closed
    comment: Optional[str] = None


class ComplaintOut(BaseModel):
    complaint_id: int
    complaint_code: str
    customer_id: int
    customer_name: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    assigned_to: Optional[int] = None
    agent_name: Optional[str] = None
    title: str
    description: str
    priority: str
    status: str
    sla_hours: int
    sla_breached: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- History ----------
class HistoryOut(BaseModel):
    history_id: int
    complaint_id: int
    updated_by: int
    updated_by_name: Optional[str] = None
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Feedback ----------
class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comments: Optional[str] = None


class FeedbackOut(BaseModel):
    feedback_id: int
    complaint_id: int
    rating: int
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Dashboard ----------
class DashboardStats(BaseModel):
    total: int
    open: int
    assigned: int
    in_progress: int
    resolved: int
    closed: int
    escalated: int
    sla_breached: int
    avg_resolution_hours: float
    by_priority: dict
    by_category: dict
