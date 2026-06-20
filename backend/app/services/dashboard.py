from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.road import BBMPDivision, Road
from app.schemas.dashboard import ContractorScoreItem, DashboardResponse
from app.services.health import get_road_health_score


def get_contractor_leaderboard(db: Session) -> list[ContractorScoreItem]:
    rows = db.execute(
        text(
            """
            SELECT contractor_name, total_roads, avg_health_score,
                   total_open_complaints, low_utilisation_roads,
                   contractor_score, red_flagged
            FROM v_contractor_scores
            ORDER BY contractor_score ASC
            """
        )
    ).mappings().all()

    return [
        ContractorScoreItem(
            contractor_name=row["contractor_name"],
            total_roads=int(row["total_roads"]),
            avg_health_score=float(row["avg_health_score"]),
            total_open_complaints=int(row["total_open_complaints"]),
            low_utilisation_roads=int(row["low_utilisation_roads"]),
            contractor_score=float(row["contractor_score"]),
            red_flagged=bool(row["red_flagged"]),
        )
        for row in rows
    ]


def get_dashboard(db: Session, division: str | None = None) -> DashboardResponse:
    road_query = db.query(Road)
    if division:
        road_query = road_query.join(BBMPDivision).filter(BBMPDivision.name.ilike(division))
    roads = road_query.all()

    good = average = poor = 0
    for road in roads:
        health = get_road_health_score(db, road.sl_no)
        if health is None:
            score = float(road.health_score)
        else:
            score = health.health_score

        if score >= 70:
            good += 1
        elif score >= 40:
            average += 1
        else:
            poor += 1

    total = len(roads)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    complaint_query = db.query(Complaint)
    if division:
        complaint_query = (
            complaint_query.join(Road, Complaint.road_sl_no == Road.sl_no)
            .join(BBMPDivision)
            .filter(BBMPDivision.name.ilike(division))
        )

    filed_this_month = complaint_query.filter(Complaint.created_at >= month_start).count()
    resolved_this_month = complaint_query.filter(
        Complaint.resolved_at.isnot(None),
        Complaint.resolved_at >= month_start,
    ).count()
    pending = complaint_query.filter(Complaint.status != "Resolved").count()

    avg_resolution = db.execute(
        text(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 86400.0) AS avg_days
            FROM complaints
            WHERE resolved_at IS NOT NULL
            """
        )
    ).scalar()

    leaderboard = get_contractor_leaderboard(db)
    lowest = leaderboard[0] if leaderboard else None

    return DashboardResponse(
        division=division,
        total_roads=total,
        condition_good=good,
        condition_average=average,
        condition_poor=poor,
        condition_good_pct=round(good * 100.0 / total, 1) if total else 0.0,
        condition_average_pct=round(average * 100.0 / total, 1) if total else 0.0,
        condition_poor_pct=round(poor * 100.0 / total, 1) if total else 0.0,
        complaints_filed_this_month=filed_this_month,
        complaints_resolved_this_month=resolved_this_month,
        complaints_pending=pending,
        average_resolution_days=round(float(avg_resolution), 1) if avg_resolution else None,
        lowest_scoring_contractor=lowest,
    )
