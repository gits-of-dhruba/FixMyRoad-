from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import ContractorScoreItem
from app.services.dashboard import get_contractor_leaderboard

router = APIRouter(prefix="/contractors", tags=["Contractors"])


@router.get("/leaderboard", response_model=list[ContractorScoreItem])
def contractor_leaderboard(db: Session = Depends(get_db)):
    return get_contractor_leaderboard(db)
