
def calculate_risk(
    failed_verifications=0,
    unusual_device=False,
    unusual_location=False,
    rapid_account_switching=False,
):
    """
    Calculate a demonstration risk score from 0 to 100.

    This heuristic score helps identify suspicious activity.
    It is not a probability of fraud and does not replace
    genuine biometric identity verification.
    """

    score = 0
    reasons = []

    # 1. Failed verification attempts
    failed_verifications = max(0, int(failed_verifications))

    if failed_verifications >= 3:
        score += 35
        reasons.append(
            f"{failed_verifications} failed verification attempts"
        )
    elif failed_verifications > 0:
        score += failed_verifications * 10
        reasons.append(
            f"{failed_verifications} failed verification attempt(s)"
        )

    # 2. Unrecognized device
    if unusual_device:
        score += 20
        reasons.append("Unrecognized device detected")

    # 3. Unusual login location
    if unusual_location:
        score += 25
        reasons.append("Unusual login location detected")

    # 4. Rapid account switching
    if rapid_account_switching:
        score += 30
        reasons.append("Rapid account switching detected")

    # Keep the score between 0 and 100
    score = min(score, 100)

    # 5. Classify risk and recommend an action
    if score >= 60:
        level = "HIGH"
        action = "Flag for urgent administrator review"

    elif score >= 30:
        level = "MEDIUM"
        action = "Request additional verification and review"

    else:
        level = "LOW"
        action = "Continue monitoring"

    # Explain why the score was assigned
    if not reasons:
        reasons.append("No configured risk indicators detected")

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
        "recommended_action": action,
    }


# --------------------------------------------------
# TEST SCENARIOS
# --------------------------------------------------
if __name__ == "__main__":

    test_cases = [
        {
            "name": "Normal activity",
            "inputs": {},
        },
        {
            "name": "Repeated verification failures",
            "inputs": {
                "failed_verifications": 3,
            },
        },
        {
            "name": "Suspicious account activity",
            "inputs": {
                "failed_verifications": 3,
                "unusual_device": True,
                "rapid_account_switching": True,
            },
        },
    ]

    print("=" * 45)
    print("       TRUST JUGGLER RISK ENGINE")
    print("=" * 45)

    for case in test_cases:
        result = calculate_risk(**case["inputs"])

        print(f"\nScenario: {case['name']}")
        print("-" * 45)
        print(f"Risk score : {result['score']}/100")
        print(f"Risk level : {result['level']}")
        print("Reasons    :")

        for reason in result["reasons"]:
            print(f"  - {reason}")

        print(f"Action     : {result['recommended_action']}")

    print("\n" + "=" * 45)
    print("Risk engine tests completed.")
