
import unittest
from unittest.mock import patch

from security import record_verification


class TestSecurity(unittest.TestCase):

    @patch("security.add_security_alert")
    @patch("security.add_verification_log")
    def test_failed_verification_is_recorded(
        self, mock_log, mock_alert
    ):
        result = record_verification(
            rider_id="RIDER001",
            method="face",
            verified=False,
        )

        self.assertFalse(result["verified"])
        self.assertEqual(result["result"], "failed")
        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertTrue(result["alert_created"])

        mock_log.assert_called_once()
        mock_alert.assert_called_once()

    @patch("security.add_security_alert")
    @patch("security.add_verification_log")
    def test_successful_low_risk_verification(
        self, mock_log, mock_alert
    ):
        result = record_verification(
            rider_id="RIDER001",
            method="face",
            verified=True,
        )

        self.assertTrue(result["verified"])
        self.assertEqual(result["result"], "passed")
        self.assertEqual(result["risk_score"], 0)
        self.assertEqual(result["risk_level"], "LOW")
        self.assertFalse(result["alert_created"])

        mock_log.assert_called_once()
        mock_alert.assert_not_called()

    @patch("security.add_security_alert")
    @patch("security.add_verification_log")
    def test_high_risk_activity_creates_alert(
        self, mock_log, mock_alert
    ):
        result = record_verification(
            rider_id="RIDER001",
            method="face",
            verified=True,
            risk_inputs={
                "failed_verifications": 3,
                "unusual_device": True,
                "rapid_account_switching": True,
            },
        )

        self.assertEqual(result["risk_score"], 85)
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertTrue(result["alert_created"])
        self.assertEqual(
            result["recommended_action"],
            "Flag for urgent administrator review",
        )

        mock_log.assert_called_once()
        mock_alert.assert_called_once()

    @patch("security.add_security_alert")
    @patch("security.add_verification_log")
    def test_medium_risk_does_not_create_alert_for_success(
        self, mock_log, mock_alert
    ):
        result = record_verification(
            rider_id="RIDER001",
            method="face",
            verified=True,
            risk_inputs={
                "failed_verifications": 3,
            },
        )

        self.assertEqual(result["risk_score"], 35)
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertFalse(result["alert_created"])

        mock_log.assert_called_once()
        mock_alert.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
