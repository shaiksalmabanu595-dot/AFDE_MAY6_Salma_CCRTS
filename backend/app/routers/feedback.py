from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Complaint, Feedback, User
from app.schemas import FeedbackCreate, FeedbackOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("/{complaint_id}", response_model=FeedbackOut, status_code=201)
def submit_feedback(
    complaint_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if c.customer_id != current.user_id:
        raise HTTPException(status_code=403, detail="Only the complaint owner can submit feedback")
    if c.status not in ("Resolved", "Closed"):
        raise HTTPException(status_code=400, detail="Feedback only on Resolved/Closed complaints")
    if db.query(Feedback).filter(Feedback.complaint_id == complaint_id).first():
        raise HTTPException(status_code=400, detail="Feedback already submitted")

    fb = Feedback(complaint_id=complaint_id, rating=payload.rating, comments=payload.comments)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("/{complaint_id}", response_model=FeedbackOut)
def get_feedback(complaint_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    fb = db.query(Feedback).filter(Feedback.complaint_id == complaint_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="No feedback for this complaint")
    return fb
