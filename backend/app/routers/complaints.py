from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.complaint import ComplaintResponse, EscalationResult
from app.services.complaint import create_complaint, escalate_overdue_complaints

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    road_sl_no: int = Form(...),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed",
        )

    image_bytes = await file.read()
    complaint = create_complaint(
        db,
        user_id=current_user.id,
        road_sl_no=road_sl_no,
        latitude=latitude,
        longitude=longitude,
        image_bytes=image_bytes,
        original_filename=file.filename,
    )
    return complaint


@router.get("", response_model=list[ComplaintResponse])
def list_complaints(
    road_sl_no: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint).order_by(Complaint.created_at.desc())
    if road_sl_no is not None:
        query = query.filter(Complaint.road_sl_no == road_sl_no)
    return query.all()


@router.post("/escalate-overdue", response_model=EscalationResult)
def escalate_overdue(db: Session = Depends(get_db)):
    tracking_ids = escalate_overdue_complaints(db)
    return EscalationResult(escalated_count=len(tracking_ids), tracking_ids=tracking_ids)


@router.get("/{tracking_id}", response_model=ComplaintResponse)
def get_complaint_by_tracking_id(tracking_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.tracking_id == tracking_id).first()
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return complaint
