from app.models.road import Road
from app.schemas.road import BudgetTrailResponse

LARGE_SPEND_GAP_THRESHOLD = 0.30


def build_budget_trail(road: Road) -> BudgetTrailResponse:
    sanctioned = int(road.budget_sanctioned)
    released = int(road.budget_released)
    spent = int(road.budget_spent)
    unspent = int(road.budget_unspent)

    pct_released = round(released * 100.0 / sanctioned, 1) if sanctioned else 0.0
    pct_spent = round(spent * 100.0 / sanctioned, 1) if sanctioned else 0.0

    flag_released = released > sanctioned
    spend_gap_ratio = (released - spent) / released if released > 0 else 0.0
    flag_spend_gap = spend_gap_ratio > LARGE_SPEND_GAP_THRESHOLD

    return BudgetTrailResponse(
        sl_no=road.sl_no,
        road_name=road.road_name,
        budget_sanctioned=sanctioned,
        budget_released=released,
        budget_spent=spent,
        budget_unspent=unspent,
        pct_released=pct_released,
        pct_spent=pct_spent,
        flag_released_exceeds_sanctioned=flag_released,
        flag_large_spend_gap=flag_spend_gap,
    )
