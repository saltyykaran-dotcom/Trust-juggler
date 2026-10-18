
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
# EXTENDED BEHAVIORAL PROFILE (in‑memory for demo)
# --------------------------------------------------
# In a production system this would be persisted. Here we keep a simple dict.
_rider_profiles: dict[str, dict] = {}

def _ensure_profile(rider_id: str) -> dict:
    """Make sure a profile exists for the given rider and return it."""
    if rider_id not in _rider_profiles:
        _rider_profiles[rider_id] = {
            "failed_verifications": 0,
            "device_history": [],  # list of device_id strings
            "city_history": [],    # list of city strings
            "consecutive_changes": 0,
        }
    return _rider_profiles[rider_id]

def update_profile(rider_id: str, result: dict, device_id: str | None = None, city: str | None = None):
    """Update the behavioral profile after a verification or session event.
    * result – dict from verification containing keys "success" and "verified".
    * device_id / city – optional current context.
    """
    profile = _ensure_profile(rider_id)
    # Track verification failures
    if not result.get("success") or not result.get("verified"):
        profile["failed_verifications"] += 1
    # Track device changes
    if device_id:
        if not profile["device_history"] or profile["device_history"][-1] != device_id:
            profile["device_history"].append(device_id)
            profile["consecutive_changes"] += 1
    # Track city changes
    if city:
        if not profile["city_history"] or profile["city_history"][-1] != city:
            profile["city_history"].append(city)
            profile["consecutive_changes"] += 1
    # Simple false‑positive mitigation: reset counter after 2 consecutive good sessions
    if result.get("success") and result.get("verified") and profile["consecutive_changes"] > 0:
        profile["consecutive_changes"] = max(0, profile["consecutive_changes"] - 1)

def detect_hand_off(rider_id: str, current_device: str | None = None, current_city: str | None = None) -> bool:
    """Detect account hand‑off. Returns True if a different rider is using the same device or city.
    For demo we flag when the current device or city does NOT match the most recent entry for the rider.
    """
    profile = _ensure_profile(rider_id)
    hand_off = False
    if current_device and profile["device_history"] and profile["device_history"][-1] != current_device:
        hand_off = True
    if current_city and profile["city_history"] and profile["city_history"][-1] != current_city:
        hand_off = True
    return hand_off

def compute_score(rider_id: str) -> dict:
    """Combine static risk_engine.calculate_risk with behavioral profile.
    Returns a dict with total score and a breakdown of points.
    """
    profile = _ensure_profile(rider_id)
    # Base risk from static indicators (using current profile values)
    base = calculate_risk(
        failed_verifications=profile["failed_verifications"],
        unusual_device=len(profile["device_history"]) > 1,
        unusual_location=len(profile["city_history"]) > 1,
        rapid_account_switching=profile["consecutive_changes"] >= 2,
    )
    # Add hand‑off penalty if detected (10 points)
    hand_off = detect_hand_off(rider_id)
    extra = 10 if hand_off else 0
    total_score = min(100, base["score"] + extra)
    breakdown = {
        "base_score": base["score"],
        "hand_off": extra,
        "total": total_score,
        "level": base["level"] if extra == 0 else ("HIGH" if total_score >= 60 else base["level"]),
        "reasons": base["reasons"],
    }
    return breakdown

def get_profile(rider_id: str) -> dict:
    """Expose the raw profile for admin inspection."""
    return _ensure_profile(rider_id)


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
