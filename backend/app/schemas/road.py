from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class RoadTypeBrief(BaseModel):
    id: int
    code: str

    model_config = {"from_attributes": True}


class DivisionBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class RoadResponse(BaseModel):
    sl_no: int
    road_id: str
    road_name: str
    road_type: RoadTypeBrief
    road_ref: str | None
    length_km: Decimal
    bbmp_division: DivisionBrief
    contractor_name: str
    executive_engineer: str
    ee_contact: int | None
    asst_exec_engineer: str | None
    aee_contact: int | None
    asst_engineer: str | None
    ae_contact: int | None
    completion_date: date
    dlp_period: str
    dlp_expiry_date: date
    budget_sanctioned: int
    budget_released: int
    budget_spent: int
    budget_unspent: int
    health_score: int
    last_complaint_date: date
    open_complaints: int
    geometry: str | None

    model_config = {"from_attributes": True}


class RoadNearbyItem(BaseModel):
    sl_no: int
    road_id: str
    road_name: str
    road_type: str
    contractor_name: str
    distance_km: float


class BudgetTrailResponse(BaseModel):
    sl_no: int
    road_name: str
    budget_sanctioned: int
    budget_released: int
    budget_spent: int
    budget_unspent: int
    pct_released: float
    pct_spent: float
    flag_released_exceeds_sanctioned: bool
    flag_large_spend_gap: bool


class RoadHealthScoreResponse(BaseModel):
    sl_no: int
    road_name: str
    contractor_name: str
    health_score: float
    days_since_last_repair: float
    open_complaints: int
    pct_budget_used: float | None
    repair_count: int
    condition: str
