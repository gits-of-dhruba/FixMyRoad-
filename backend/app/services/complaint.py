import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR
from app.ml.analyzer import analyze_image
from app.models.complaint import Complaint
from app.models.repair import Repair
from app.models.road import Road
from app.services.routing import find_authority_for_road
from app.services.sla import compute_response_deadline
from app.services.tracking import generate_tracking_id

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def map_damage_to_issue_type(damage_type: str) -> str:
    normalized = damage_type.lower()
    if "pothole" in normalized:
        return "Pothole"
    if "crack" in normalized:
        return "Crack"
    return "Crack"


def save_complaint_image(image_bytes: bytes, original_filename: str | None) -> str:
    suffix = Path(original_filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(image_bytes)
    return f"uploads/complaints/{filename}"


def count_open_complaints_on_road(db: Session, road_sl_no: int) -> int:
    return (
        db.query(Complaint)
        .filter(
            Complaint.road_sl_no == road_sl_no,
            Complaint.status.in_(["Open", "In Progress", "Escalated"]),
        )
        .count()
    )


def create_complaint(
    db: Session,
    *,
    user_id: int,
    road_sl_no: int,
    latitude: float | None,
    longitude: float | None,
    image_bytes: bytes,
    original_filename: str | None,
) -> Complaint:
    road = db.query(Road).filter(Road.sl_no == road_sl_no).first()
    if road is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Road not found")

    ml_result = analyze_image(image_bytes)
    if ml_result.get("status") == "no_damage_detected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No road damage detected in the uploaded image",
        )

    detections = ml_result.get("detections", [])
    if not detections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No road damage detected in the uploaded image",
        )

    worst = max(detections, key=lambda d: SEVERITY_ORDER[d["severity"]])
    issue_type = map_damage_to_issue_type(worst["damage_type"])
    severity = worst["severity"]
    confidence = worst["confidence"]

    authority = find_authority_for_road(db, road)
    open_count = count_open_complaints_on_road(db, road_sl_no)
    escalated = open_count >= 2

    complaint = Complaint(
        tracking_id=generate_tracking_id(db),
        road_sl_no=road_sl_no,
        user_id=user_id,
        authority_id=authority.id if authority else None,
        issue_type=issue_type,
        severity=severity,
        confidence_score=confidence,
        latitude=latitude,
        longitude=longitude,
        image_url=save_complaint_image(image_bytes, original_filename),
        status="Open",
        response_deadline=compute_response_deadline(severity),
        escalated=escalated,
    )
    db.add(complaint)
    db.flush()

    repair_event = Repair(
        road_sl_no=road_sl_no,
        event_type="Complaint",
        event_date=date.today(),
        notes=f"Complaint filed: {issue_type} ({severity}) — {complaint.tracking_id}",
        linked_complaint_id=complaint.id,
    )
    db.add(repair_event)

    road.open_complaints = (road.open_complaints or 0) + 1
    road.last_complaint_date = date.today()

    db.commit()
    db.refresh(complaint)
    return complaint


def escalate_overdue_complaints(db: Session) -> list[str]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overdue = (
        db.query(Complaint)
        .filter(
            Complaint.response_deadline < now,
            Complaint.status.notin_(["Resolved", "Escalated"]),
        )
        .all()
    )

    tracking_ids: list[str] = []
    for complaint in overdue:
        complaint.escalated = True
        complaint.status = "Escalated"
        tracking_ids.append(complaint.tracking_id)

    if overdue:
        db.commit()

    return tracking_ids
