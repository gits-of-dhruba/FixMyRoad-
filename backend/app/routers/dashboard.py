from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import get_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def public_dashboard(
    division: str | None = Query(None, description="BBMP division name filter"),
    db: Session = Depends(get_db),
):
    return get_dashboard(db, division=division)
