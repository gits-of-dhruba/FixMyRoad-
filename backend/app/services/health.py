from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.road import RoadHealthScoreResponse


def compute_health_score(
    days_since_last_repair: float,
    open_complaints: int,
    pct_budget_used: float | None,
    repair_count: int,
) -> float:
    days_score = max(0.0, 100.0 - (float(days_since_last_repair) / 365.0 * 100.0))
    complaint_score = max(0.0, 100.0 - open_complaints * 20.0)

    if pct_budget_used is None:
        budget_score = 50.0
    elif 70.0 <= pct_budget_used <= 100.0:
        budget_score = 100.0
    elif pct_budget_used < 70.0:
        budget_score = (pct_budget_used / 70.0) * 100.0
    else:
        budget_score = max(0.0, 100.0 - (pct_budget_used - 100.0) * 2.0)

    durability_score = max(0.0, 100.0 - repair_count * 25.0)

    return round(
        days_score * 0.25
        + complaint_score * 0.25
        + budget_score * 0.20
        + durability_score * 0.30,
        1,
    )


def condition_label(score: float) -> str:
    if score >= 70:
        return "Good"
    if score >= 40:
        return "Average"
    return "Poor"


def get_road_health_score(db: Session, sl_no: int) -> RoadHealthScoreResponse | None:
    row = db.execute(
        text(
            """
            SELECT sl_no, road_name, contractor_name,
                   days_since_last_repair, open_complaints,
                   pct_budget_used, repair_count
            FROM v_road_health_live
            WHERE sl_no = :sl_no
            """
        ),
        {"sl_no": sl_no},
    ).mappings().first()

    if row is None:
        return None

    score = compute_health_score(
        float(row["days_since_last_repair"] or 0),
        int(row["open_complaints"] or 0),
        float(row["pct_budget_used"]) if row["pct_budget_used"] is not None else None,
        int(row["repair_count"] or 0),
    )

    return RoadHealthScoreResponse(
        sl_no=row["sl_no"],
        road_name=row["road_name"],
        contractor_name=row["contractor_name"],
        health_score=score,
        days_since_last_repair=float(row["days_since_last_repair"] or 0),
        open_complaints=int(row["open_complaints"] or 0),
        pct_budget_used=float(row["pct_budget_used"]) if row["pct_budget_used"] is not None else None,
        repair_count=int(row["repair_count"] or 0),
        condition=condition_label(score),
    )
