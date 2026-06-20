from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.authority import Authority
from app.models.road import BBMPDivision, RoadType
from app.schemas.authority import AuthorityResponse

router = APIRouter(prefix="/authorities", tags=["Authorities"])


@router.get("", response_model=list[AuthorityResponse])
def list_authorities(db: Session = Depends(get_db)):
    authorities = db.query(Authority).all()
    road_types = {rt.id: rt for rt in db.query(RoadType).all()}
    divisions = {d.id: d for d in db.query(BBMPDivision).all()}

    return [
        AuthorityResponse(
            id=auth.id,
            name=auth.name,
            road_type_id=auth.road_type_id,
            road_type_code=road_types[auth.road_type_id].code,
            bbmp_division_id=auth.bbmp_division_id,
            bbmp_division_name=divisions[auth.bbmp_division_id].name
            if auth.bbmp_division_id in divisions
            else None,
            escalation_to=auth.escalation_to,
            contact_email=auth.contact_email,
            contact_phone=auth.contact_phone,
        )
        for auth in authorities
    ]
