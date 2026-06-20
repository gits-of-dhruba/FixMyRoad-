from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ComplaintResponse(BaseModel):
    id: int
    tracking_id: str
    road_sl_no: int
    user_id: int | None
    authority_id: int | None
    issue_type: str
    severity: str
    confidence_score: Decimal | None
    latitude: Decimal | None
    longitude: Decimal | None
    image_url: str | None
    status: str
    response_deadline: datetime | None
    escalated: bool
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class EscalationResult(BaseModel):
    escalated_count: int
    tracking_ids: list[str]
