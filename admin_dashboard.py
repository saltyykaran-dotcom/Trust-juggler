
from database import (
    get_riders,
    get_verification_logs,
    get_security_alerts,
)


def get_dashboard_data():
    """Load current dashboard data from the SQLite database."""
    riders = get_riders()
    logs = get_verification_logs()
    alerts = get_security_alerts()

    failed_logs = [
        log for log in logs
        if log["result"].lower() == "failed"
    ]

    unresolved_alerts = [
        alert for alert in alerts
        if not alert["resolved"]
    ]

    high_risk_alerts = [
        alert for alert in unresolved_alerts
        if alert["risk_score"] >= 60
    ]

    return {
        "total_riders": len(riders),
        "total_verifications": len(logs),
        "failed_verifications": len(failed_logs),
        "unresolved_alerts": len(unresolved_alerts),
        "high_risk_alerts": len(high_risk_alerts),
        "riders": riders,
        "verification_logs": logs,
        "security_alerts": alerts,
    }
