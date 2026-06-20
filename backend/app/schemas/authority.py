from pydantic import BaseModel


class AuthorityResponse(BaseModel):
    id: int
    name: str
    road_type_id: int
    road_type_code: str
    bbmp_division_id: int | None
    bbmp_division_name: str | None
    escalation_to: str | None
    contact_email: str | None
    contact_phone: str | None
