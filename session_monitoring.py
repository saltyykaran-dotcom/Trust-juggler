
from datetime import datetime, timezone


def create_session(rider_id, device_id):
    """Create a record for a rider's current session."""
    return {
        "rider_id": rider_id,
        "device_id": device_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
        "events": []
    }


def monitor_session(
    session,
    current_device_id,
    failed_verifications=0,
    unusual_location=False
):
    """Flag suspicious activity during a rider session."""
    alerts = []

    if not session.get("active", False):
        alerts.append("Session is inactive")

    if current_device_id != session["device_id"]:
        alerts.append("Device changed during session")

    if failed_verifications >= 3:
        alerts.append("Repeated verification failures")

    if unusual_location:
        alerts.append("Unusual location detected")

    session["events"].extend(alerts)

    return {
        "rider_id": session["rider_id"],
        "alerts": alerts,
        "suspicious": len(alerts) > 0
    }


def end_session(session):
    """End the rider's current session."""
    session["active"] = False
    return session


if __name__ == "__main__":
    demo = create_session("RIDER001", "DEVICE_A")

    result = monitor_session(
        demo,
        current_device_id="DEVICE_B",
        failed_verifications=3
    )

    print("Session monitoring result:")
    print(result)
