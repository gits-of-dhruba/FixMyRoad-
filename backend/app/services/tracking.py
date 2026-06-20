from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.complaint import Complaint


def generate_tracking_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"RW-{year}-"
    last = (
        db.query(Complaint)
        .filter(Complaint.tracking_id.like(f"{prefix}%"))
        .order_by(Complaint.tracking_id.desc())
        .first()
    )
    if last:
        seq = int(last.tracking_id.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"
