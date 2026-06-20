from datetime import datetime, timedelta, timezone


def compute_response_deadline(severity: str) -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    sla_hours = {
        "Critical": 48,
        "High": 7 * 24,
        "Medium": 15 * 24,
        "Low": 30 * 24,
    }
    hours = sla_hours.get(severity, 30 * 24)
    return now + timedelta(hours=hours)
