
import unittest

from auth import check_access
from risk_engine import calculate_risk
from session_monitoring import create_session, monitor_session, end_session


class TestTrustJuggler(unittest.TestCase):

    def test_verified_rider_gets_access(self):
        result = check_access(True)
        self.assertTrue(result["access_granted"])

    def test_unverified_rider_is_denied(self):
        result = check_access(False)
        self.assertFalse(result["access_granted"])

    def test_high_risk_is_capped_at_100(self):
        result = calculate_risk(
            failed_verifications=5,
            unusual_device=True,
            unusual_location=True,
            rapid_account_switching=True,
        )
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["level"], "HIGH")

    def test_low_risk_score_is_low(self):
        result = calculate_risk()
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "LOW")

    def test_multiple_risk_signals_raise_score(self):
        result = calculate_risk(
            failed_verifications=3,
            unusual_device=True,
            unusual_location=True,
            rapid_account_switching=True,
        )
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["level"], "HIGH")

    def test_device_change_is_flagged(self):
        session = create_session("RIDER001", "DEVICE_A")
        result = monitor_session(
            session,
            current_device_id="DEVICE_B",
        )
        self.assertTrue(result["suspicious"])

    def test_ended_session_is_inactive(self):
        session = create_session("RIDER001", "DEVICE_A")
        end_session(session)
        result = monitor_session(
            session,
            current_device_id="DEVICE_A",
        )
        self.assertTrue(result["suspicious"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
