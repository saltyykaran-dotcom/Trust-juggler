
from database import add_verification_log, add_security_alert
from risk_engine import calculate_risk


def record_verification(
    rider_id,
    method,
    verified,
    risk_inputs=None,
):
    """
    Record a verification attempt, calculate risk,
    and create security alerts when necessary.

    IMPORTANT:
    This function records the verification result provided
    by the caller. It does not perform biometric matching.
    """

    risk_inputs = risk_inputs or {}

    # 1. Normalize the verification result
    verified = bool(verified)
    result = "passed" if verified else "failed"

    # 2. Calculate the risk score
    risk = calculate_risk(
        failed_verifications=risk_inputs.get(
            "failed_verifications", 0
        ),
        unusual_device=risk_inputs.get(
            "unusual_device", False
        ),
        unusual_location=risk_inputs.get(
            "unusual_location", False
        ),
        rapid_account_switching=risk_inputs.get(
            "rapid_account_switching", False
        ),
    )

    risk_score = risk["score"]
    risk_level = risk["level"]
    reasons = risk["reasons"]

    # 3. Save the verification attempt to the database
    add_verification_log(
        rider_id=rider_id,
        method=method,
        result=result,
        risk_score=risk_score,
        details="; ".join(reasons),
    )

    # 4. Create an alert when verification fails
    # or when the calculated risk is HIGH
    if not verified or risk_score >= 60:

        if not verified:
            alert_type = "verification_failure"
            description = (
                f"{method} verification failed. "
                f"Risk level: {risk_level}. "
                f"Risk score: {risk_score}/100."
            )
        else:
            alert_type = "high_risk_activity"
            description = (
                "High-risk activity detected during verification. "
                f"Risk score: {risk_score}/100. "
                f"Indicators: {'; '.join(reasons)}"
            )

        add_security_alert(
            rider_id=rider_id,
            alert_type=alert_type,
            description=description,
            risk_score=risk_score,
        )

    # 5. Return the complete assessment
    return {
        "verified": verified,
        "result": result,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons,
        "recommended_action": risk["recommended_action"],
        "alert_created": not verified or risk_score >= 60,
    }


if __name__ == "__main__":
    print("Trust Juggler Security Module")
    print("-" * 35)
    print("Security module imported successfully.")
    print("Risk engine connection is available.")
    print(
        "Database writes have not been tested by this standalone check."
    )
