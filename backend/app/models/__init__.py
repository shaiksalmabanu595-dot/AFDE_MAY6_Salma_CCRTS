from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Role(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20))
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    role = relationship("Role", back_populates="users")
    complaints = relationship("Complaint", foreign_keys="Complaint.customer_id", back_populates="customer")
    assigned_complaints = relationship("Complaint", foreign_keys="Complaint.assigned_to", back_populates="agent")


class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    complaints = relationship("Complaint", back_populates="category")


class Complaint(Base):
    __tablename__ = "complaints"
    complaint_id = Column(Integer, primary_key=True, index=True)
    complaint_code = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="Medium")
    status = Column(String(30), nullable=False, default="Open")
    sla_hours = Column(Integer, nullable=False, default=48)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    customer = relationship("User", foreign_keys=[customer_id], back_populates="complaints")
    agent = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_complaints")
    category = relationship("Category", back_populates="complaints")
    history = relationship("ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"
    history_id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    old_status = Column(String(30))
    new_status = Column(String(30), nullable=False)
    comment = Column(Text)
    updated_at = Column(DateTime, server_default=func.now())

    complaint = relationship("Complaint", back_populates="history")
    user = relationship("User")


class Feedback(Base):
    __tablename__ = "feedback"
    feedback_id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), unique=True, nullable=False)
    rating = Column(Integer, nullable=False)
    comments = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    complaint = relationship("Complaint", back_populates="feedback")

    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),)
