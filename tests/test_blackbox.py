"""Unit tests for Causal Black-Box Flight Recorder and Cryptographic Witness."""

import unittest
from aegis_fleet.blackbox import (
    BlackBoxRecorder,
    CausalEvent,
    BlackBoxBundle,
    WitnessNotary,
    TamperReport,
)


class TestBlackBox(unittest.TestCase):

    def test_causal_event_hash_chaining(self):
        recorder = BlackBoxRecorder(vehicle_id="drone_test")

        # Step 1: Nominal observation and command
        e1 = recorder.record_event(
            observation={"alt": 50.0},
            cognition={"thought": "fly_forward"},
            actuation={"motor": "spin"},
        )
        self.assertEqual(e1.sequence_number, 1)
        self.assertEqual(e1.previous_event_hash, "0" * 64)
        self.assertIsNotNone(e1.event_hash)

        # Step 2: Next event must link to e1
        e2 = recorder.record_event(
            observation={"alt": 60.0},
            cognition={"thought": "continue"},
            actuation={"motor": "spin"},
        )
        self.assertEqual(e2.sequence_number, 2)
        self.assertEqual(e2.previous_event_hash, e1.event_hash)

    def test_bundle_export_and_witness_verification(self):
        recorder = BlackBoxRecorder(vehicle_id="vehicle_test")
        recorder.record_event({"speed": 20}, {"action": "cruise"}, {"throttle": 15})
        recorder.record_event({"speed": 22}, {"action": "cruise"}, {"throttle": 15})

        bundle = recorder.export_bundle()
        self.assertEqual(bundle.event_count, 2)
        self.assertIsNotNone(bundle.merkle_root)

        notary = WitnessNotary()
        receipt = notary.seal_bundle(bundle)
        self.assertEqual(receipt.bundle_id, bundle.bundle_id)

        # Verify integrity of untampered bundle
        report = notary.verify_bundle_integrity(bundle)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.total_events_checked, 2)

    def test_tamper_detection_in_blackbox_bundle(self):
        recorder = BlackBoxRecorder(vehicle_id="tamper_test")
        recorder.record_event({"speed": 30}, {"action": "brake"}, {"brake": 20})
        recorder.record_event({"speed": 10}, {"action": "stopped"}, {"brake": 30})

        bundle = recorder.export_bundle()
        notary = WitnessNotary()

        # Malicious attacker tries modifying an event's recorded observation
        bundle.events[0].observation["speed"] = 999  # Tamper with recorded speed!

        report = notary.verify_bundle_integrity(bundle)
        self.assertFalse(report.is_valid)
        self.assertIn("Payload tampered", report.reason)


if __name__ == "__main__":
    unittest.main()
