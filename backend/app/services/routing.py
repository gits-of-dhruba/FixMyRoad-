from sqlalchemy.orm import Session

from app.models.authority import Authority
from app.models.road import Road


def find_authority_for_road(db: Session, road: Road) -> Authority | None:
    authority = (
        db.query(Authority)
        .filter(
            Authority.road_type_id == road.road_type_id,
            Authority.bbmp_division_id == road.bbmp_division_id,
        )
        .first()
    )
    if authority:
        return authority

    return (
        db.query(Authority)
        .filter(
            Authority.road_type_id == road.road_type_id,
            Authority.bbmp_division_id.is_(None),
        )
        .first()
    )
