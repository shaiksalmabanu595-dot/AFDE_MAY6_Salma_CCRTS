from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import Role, Category, User
from app.utils.auth import hash_password
from app.routers import auth, users, categories, complaints, feedback, dashboard, analytics, admin

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Customer Complaint & Resolution Tracking System",
    description="CCRTS - Capstone Project API",
    version="1.0.0",
)

# CORS — must list explicit origins when allow_credentials=True
# (browsers reject Access-Control-Allow-Origin: * for credentialed requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_data():
    db: Session = SessionLocal()
    try:
        # Seed roles
        if db.query(Role).count() == 0:
            for r in ["Admin", "Agent", "Customer", "Supervisor"]:
                db.add(Role(role_name=r))
            db.commit()

        # Seed categories
        if db.query(Category).count() == 0:
            cats = [
                ("Billing Issues", "Issues related to billing and invoices"),
                ("Service Disruption", "Service downtime or outages"),
                ("Product Defects", "Defective product issues"),
                ("Technical Problems", "Technical errors and bugs"),
                ("Delivery Delays", "Issues with order delivery"),
                ("Account Issues", "Account access and management issues"),
                ("Customer Service Complaints", "Complaints about service quality"),
            ]
            for name, desc in cats:
                db.add(Category(category_name=name, description=desc))
            db.commit()

        # Seed default users
        if db.query(User).count() == 0:
            admin_role = db.query(Role).filter(Role.role_name == "Admin").first()
            agent_role = db.query(Role).filter(Role.role_name == "Agent").first()
            customer_role = db.query(Role).filter(Role.role_name == "Customer").first()

            db.add(User(name="Admin User", email="admin@ccrts.com",
                        password_hash=hash_password("admin123"), role_id=admin_role.role_id))
            db.add(User(name="John Agent", email="agent@ccrts.com",
                        password_hash=hash_password("agent123"), role_id=agent_role.role_id))
            db.add(User(name="Jane Customer", email="customer@ccrts.com",
                        password_hash=hash_password("customer123"), role_id=customer_role.role_id))
            db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "Customer Complaint & Resolution Tracking System API",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(complaints.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(admin.router)
