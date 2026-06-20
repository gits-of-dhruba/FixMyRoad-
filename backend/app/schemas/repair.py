from datetime import date

from pydantic import BaseModel, Field


class RepairCreate(BaseModel):
    event_type: str = Field(..., pattern="^(Built|Repaired|Complaint)$")
    event_date: date
    notes: str | None = None
    linked_complaint_id: int | None = None


class RepairResponse(BaseModel):
    id: int
    road_sl_no: int
    event_type: str
    event_date: date
    notes: str | None
    linked_complaint_id: int | None

    model_config = {"from_attributes": True}
