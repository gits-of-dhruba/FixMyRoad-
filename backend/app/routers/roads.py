
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.repair import Repair
from app.models.road import Road
from app.models.user import User
from app.schemas.repair import RepairCreate, RepairResponse
from app.schemas.road import (
    BudgetTrailResponse,
    DivisionBrief,
    RoadHealthScoreResponse,
    RoadNearbyItem,
    RoadResponse,
    RoadTypeBrief,
)
from app.services.budget import build_budget_trail
from app.services.geo import find_nearby_roads
from app.services.health import get_road_health_score

router = APIRouter(prefix="/roads", tags=["Roads"])


def _road_to_response(road: Road) -> RoadResponse:
    return RoadResponse(
        sl_no=road.sl_no,
        road_id=road.road_id,
        road_name=road.road_name,
        road_type=RoadTypeBrief.model_validate(road.road_type),
        road_ref=road.road_ref,
        length_km=road.length_km,
        bbmp_division=DivisionBrief.model_validate(road.bbmp_division),
        contractor_name=road.contractor_name,
        executive_engineer=road.executive_engineer,
        ee_contact=road.ee_contact,
        asst_exec_engineer=road.asst_exec_engineer,
        aee_contact=road.aee_contact,
        asst_engineer=road.asst_engineer,
        ae_contact=road.ae_contact,
        completion_date=road.completion_date,
        dlp_period=road.dlp_period,
        dlp_expiry_date=road.dlp_expiry_date,
        budget_sanctioned=road.budget_sanctioned,
        budget_released=road.budget_released,
        budget_spent=road.budget_spent,
        budget_unspent=road.budget_unspent,
        health_score=road.health_score,
        last_complaint_date=road.last_complaint_date,
        open_complaints=road.open_complaints,
        geometry=road.geometry,
    )


def _get_road_or_404(db: Session, sl_no: int) -> Road:
    road = (
        db.query(Road)
        .options(joinedload(Road.road_type), joinedload(Road.bbmp_division))
        .filter(Road.sl_no == sl_no)
        .first()
    )
    if road is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Road not found")
    return road


@router.get("/nearby", response_model=list[RoadNearbyItem])
def nearby_roads(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(2.0, gt=0, le=50, description="Search radius in km"),
    db: Session = Depends(get_db),
):
    roads = db.query(Road).options(joinedload(Road.road_type)).all()
    matches = find_nearby_roads(roads, lat, lng, radius)

    return [
        RoadNearbyItem(
            sl_no=road.sl_no,
            road_id=road.road_id,
            road_name=road.road_name,
            road_type=road.road_type.code,
            contractor_name=road.contractor_name,
            distance_km=round(distance, 3),
        )
        for road, distance in matches
    ]


@router.get("/by-osm/{osm_id}", response_model=RoadResponse)
def get_road_by_osm_id(osm_id: str, db: Session = Depends(get_db)):
    road = (
        db.query(Road)
        .options(joinedload(Road.road_type), joinedload(Road.bbmp_division))
        .filter(Road.osm_id == osm_id)
        .first()
    )
    if road is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Road not found for this osm_id")
    return _road_to_response(road)
 
 
@router.get("/{sl_no}", response_model=RoadResponse)
def get_road(sl_no: int, db: Session = Depends(get_db)):
    road = _get_road_or_404(db, sl_no)
    return _road_to_response(road)


@router.get("/{sl_no}/budget", response_model=BudgetTrailResponse)
def get_road_budget(sl_no: int, db: Session = Depends(get_db)):
    road = _get_road_or_404(db, sl_no)
    return build_budget_trail(road)


@router.get("/{sl_no}/health-score", response_model=RoadHealthScoreResponse)
def get_road_health_score_endpoint(sl_no: int, db: Session = Depends(get_db)):
    health = get_road_health_score(db, sl_no)
    if health is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Road not found")
    return health


@router.get("/{sl_no}/timeline", response_model=list[RepairResponse])
def get_road_timeline(sl_no: int, db: Session = Depends(get_db)):
    _get_road_or_404(db, sl_no)
    events = (
        db.query(Repair)
        .filter(Repair.road_sl_no == sl_no)
        .order_by(Repair.event_date.asc(), Repair.id.asc())
        .all()
    )
    return events


@router.post("/{sl_no}/repairs", response_model=RepairResponse, status_code=status.HTTP_201_CREATED)
def add_repair_event(
    sl_no: int,
    payload: RepairCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("authority", "admin")),
):
    _get_road_or_404(db, sl_no)

    repair = Repair(
        road_sl_no=sl_no,
        event_type=payload.event_type,
        event_date=payload.event_date,
        notes=payload.notes,
        linked_complaint_id=payload.linked_complaint_id,
    )
    db.add(repair)
    db.commit()
    db.refresh(repair)
    return repair
