"""Unit tests for GRC Policy Engine and regulatory compliance rules."""

import unittest
from aegis_fleet.grc import PolicyEngine, Severity
from aegis_fleet.grc.policies import (
    faa_altitude_rule,
    faa_speed_rule,
    faa_battery_reserve_rule,
    faa_geofence_rule,
    iso_driver_attention_rule,
    iso_steering_rate_rule,
    eu_ai_confidence_threshold_rule,
    eu_ai_odd_envelope_rule,
)


class TestGRCPolicies(unittest.TestCase):

    def setUp(self):
        self.engine = PolicyEngine()
        self.engine.register_rule("FAA-ALTITUDE", faa_altitude_rule)
        self.engine.register_rule("FAA-SPEED", faa_speed_rule)
        self.engine.register_rule("FAA-BATTERY", faa_battery_reserve_rule)
        self.engine.register_rule("FAA-GEOFENCE", faa_geofence_rule)
        self.engine.register_rule("ISO-DRIVER", iso_driver_attention_rule)
        self.engine.register_rule("ISO-STEER", iso_steering_rate_rule)
        self.engine.register_rule("EU-CONFIDENCE", eu_ai_confidence_threshold_rule)
        self.engine.register_rule("EU-ODD", eu_ai_odd_envelope_rule)

    def test_faa_altitude_ceiling_enforcement(self):
        # 100m is compliant
        res_safe = self.engine.evaluate_telemetry({"altitude_agl_m": 100.0})
        self.assertTrue(res_safe.compliant)

        # 130m breaches 121.92m ceiling
        res_breach = self.engine.evaluate_telemetry({"altitude_agl_m": 130.0})
        self.assertFalse(res_breach.compliant)
        self.assertTrue(res_breach.critical_halt_required)
        self.assertEqual(res_breach.violations[0].rule_id, "FAA-107.51b-ALTITUDE")

    def test_iso_driver_attention_enforcement(self):
        # 2.0s is compliant
        res_safe = self.engine.evaluate_telemetry({
            "autopilot_engaged": True,
            "time_without_driver_attention_s": 2.0,
        })
        self.assertTrue(res_safe.compliant)

        # 3.5s breaches 3.0s threshold
        res_distracted = self.engine.evaluate_telemetry({
            "autopilot_engaged": True,
            "time_without_driver_attention_s": 3.5,
        })
        self.assertFalse(res_distracted.compliant)
        self.assertTrue(res_distracted.critical_halt_required)
        self.assertEqual(res_distracted.violations[0].rule_id, "ISO-26262-DRIVER-MONITOR")

    def test_eu_ai_act_odd_envelope(self):
        res_breach = self.engine.evaluate_telemetry({
            "odd_boundary_breached": True,
            "odd_violation_reason": "Heavy snow occluding camera lens",
        })
        self.assertFalse(res_breach.compliant)
        self.assertEqual(res_breach.violations[0].framework, "EU_AI_ACT_ANNEX_III")


if __name__ == "__main__":
    unittest.main()
