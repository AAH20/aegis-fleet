"""Unit tests for Mission Swarm Coordinator and fail-safe triggers."""

import unittest
from aegis_fleet.grc import PolicyEngine
from aegis_fleet.grc.policies import faa_altitude_rule, faa_geofence_rule
from aegis_fleet.swarm import FleetCoordinator, SortieStatus


class TestSwarmCoordinator(unittest.TestCase):

    def setUp(self):
        self.engine = PolicyEngine()
        self.engine.register_rule("FAA-ALTITUDE", faa_altitude_rule)
        self.engine.register_rule("FAA-GEOFENCE", faa_geofence_rule)
        self.coordinator = FleetCoordinator(self.engine)

    def test_sortie_registration_and_nominal_tick(self):
        sortie = self.coordinator.register_sortie(
            mission_id="mission_alpha",
            vehicle_id="drone_01",
            vehicle_type="drone",
        )
        self.assertEqual(sortie.status, SortieStatus.IN_TRANSIT)

        res = self.coordinator.process_telemetry_tick(
            "drone_01",
            {"altitude_agl_m": 80.0, "geofence_breached": False},
        )
        self.assertTrue(res["compliant"])
        self.assertEqual(res["command_issued"], "CONTINUE_MISSION")
        self.assertEqual(self.coordinator.sorties["drone_01"].status, SortieStatus.IN_TRANSIT)

    def test_failsafe_rtl_on_critical_geofence_breach(self):
        self.coordinator.register_sortie(
            mission_id="mission_beta",
            vehicle_id="drone_02",
            vehicle_type="drone",
        )

        res = self.coordinator.process_telemetry_tick(
            "drone_02",
            {"altitude_agl_m": 80.0, "geofence_breached": True},  # Critical breach!
        )
        self.assertFalse(res["compliant"])
        self.assertEqual(res["command_issued"], "RETURN_TO_LAUNCH")
        self.assertEqual(self.coordinator.sorties["drone_02"].status, SortieStatus.EMERGENCY_RTL)


if __name__ == "__main__":
    unittest.main()
