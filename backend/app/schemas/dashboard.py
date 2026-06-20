from pydantic import BaseModel


class ContractorScoreItem(BaseModel):
    contractor_name: str
    total_roads: int
    avg_health_score: float
    total_open_complaints: int
    low_utilisation_roads: int
    contractor_score: float
    red_flagged: bool


class DashboardResponse(BaseModel):
    division: str | None
    total_roads: int
    condition_good: int
    condition_average: int
    condition_poor: int
    condition_good_pct: float
    condition_average_pct: float
    condition_poor_pct: float
    complaints_filed_this_month: int
    complaints_resolved_this_month: int
    complaints_pending: int
    average_resolution_days: float | None
    lowest_scoring_contractor: ContractorScoreItem | None
