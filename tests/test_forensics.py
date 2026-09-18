"""Unit tests for Forensic Replay Player and Regulatory Dossier generation."""

import unittest
from aegis_fleet.blackbox import BlackBoxRecorder
from aegis_fleet.grc import PolicyEngine
from aegis_fleet.grc.policies import faa_altitude_rule
from aegis_fleet.forensics import ReplayPlayer


class TestForensics(unittest.TestCase):

    def test_incident_investigation_and_liability_attribution(self):
        engine = PolicyEngine()
        engine.register_rule("FAA-ALTITUDE", faa_altitude_rule)
        player = ReplayPlayer(engine)

        rec = BlackBoxRecorder(vehicle_id="drone_crash_test")

        # Step 1: Normal flight
        rec.record_event(
            observation={"altitude_agl_m": 80.0},
            cognition={"reason": "normal"},
            actuation={"cmd": "FORWARD"},
        )
        # Step 2: Altitude violation
        rec.record_event(
            observation={"altitude_agl_m": 140.0},  # Exceeds 121.92m
            cognition={"reason": "bad_climb"},
            actuation={"cmd": "CLIMB"},
        )

        bundle = rec.export_bundle()
        investigation = player.investigate_bundle(bundle)

        self.assertTrue(investigation.incident_occurred)
        self.assertEqual(investigation.first_infraction_step, 2)
        self.assertEqual(investigation.total_steps, 2)
        self.assertEqual(investigation.dossier.liability_determination, "AIRSPACE_CONTAINMENT_BREACH_LIABILITY")
        self.assertFalse(investigation.dossier.is_fully_compliant)
        self.assertIsNotNone(investigation.dossier.authority_audit_signature)


if __name__ == "__main__":
    unittest.main()
