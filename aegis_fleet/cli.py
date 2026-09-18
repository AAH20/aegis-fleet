"""
Unified Command-Line Interface for Aegis-Fleet.

Simulates autonomous drone and vehicle missions, evaluates live GRC policies,
records causal black-box bundles, and performs forensic incident investigations.
"""

from __future__ import annotations
import argparse
import json
import sys
import time

from aegis_fleet.drivers import (
    DroneTelemetry,
    MAVLinkDroneDriver,
    FlightMode,
    VehicleTelemetry,
    CANVehicleDriver,
    DriverEngagementState,
)
from aegis_fleet.blackbox import (
    BlackBoxRecorder,
    WitnessNotary,
)
from aegis_fleet.grc import (
    PolicyEngine,
    DossierGenerator,
)
from aegis_fleet.grc.policies import (
    faa_altitude_rule,
    faa_speed_rule,
    faa_battery_reserve_rule,
    faa_geofence_rule,
    iso_driver_attention_rule,
    iso_steering_rate_rule,
    iso_emergency_brake_rule,
    eu_ai_confidence_threshold_rule,
    eu_ai_odd_envelope_rule,
)
from aegis_fleet.swarm import (
    FleetCoordinator,
    SortieStatus,
)
from aegis_fleet.forensics import (
    ReplayPlayer,
)


def get_configured_policy_engine() -> PolicyEngine:
    engine = PolicyEngine()
    engine.register_rule("FAA-ALTITUDE", faa_altitude_rule)
    engine.register_rule("FAA-SPEED", faa_speed_rule)
    engine.register_rule("FAA-BATTERY", faa_battery_reserve_rule)
    engine.register_rule("FAA-GEOFENCE", faa_geofence_rule)
    engine.register_rule("ISO-DRIVER-ATTENTION", iso_driver_attention_rule)
    engine.register_rule("ISO-STEERING-RATE", iso_steering_rate_rule)
    engine.register_rule("ISO-EMERGENCY-BRAKE", iso_emergency_brake_rule)
    engine.register_rule("EU-AI-CONFIDENCE", eu_ai_confidence_threshold_rule)
    engine.register_rule("EU-AI-ODD-BOUNDARY", eu_ai_odd_envelope_rule)
    return engine


def cmd_drone_simulation(args):
    print("=== [Mission 1] Autonomous Drone Delivery Sortie (PX4 / MAVLink) ===")
    policy_engine = get_configured_policy_engine()
    coordinator = FleetCoordinator(policy_engine)
    drone_driver = MAVLinkDroneDriver(drone_id="drone_eagle_01")

    sortie = coordinator.register_sortie(
        mission_id="delivery_mission_901",
        vehicle_id="drone_eagle_01",
        vehicle_type="drone",
    )
    print(f"[1] Cleared sortie '{sortie.mission_id}' for '{sortie.vehicle_id}'. Status: {sortie.status.value}")

    # Step 1: Nominal climb to 80m
    print("[2] Tick 1: Ascending to 80m (nominal)...")
    p1 = {"relative_alt": 80000, "vx": 12.0, "vy": 5.0, "battery": 92.0, "flight_mode": "OFFBOARD_AI"}
    t1 = drone_driver.parse_mavlink_packet(p1)
    res1 = coordinator.process_telemetry_tick(
        "drone_eagle_01",
        {"altitude_agl_m": t1.altitude_agl_m, "ground_speed_ms": t1.ground_speed_ms, "battery_percent": t1.battery_percent},
        {"decision": "track_corridor", "confidence": 0.98},
    )
    print(f"    Status: {res1['status']} (Compliant: {res1['compliant']}, Command: {res1['command_issued']})")

    # Step 2: Agent ascends to 135m (Breaches 121.92m FAA Part 107 ceiling!)
    print("[3] Tick 2: Ascending to 135m -> BREACHES FAA PART 107 400ft CEILING!")
    p2 = {"relative_alt": 135000, "vx": 14.0, "vy": 4.0, "battery": 88.0, "flight_mode": "OFFBOARD_AI"}
    t2 = drone_driver.parse_mavlink_packet(p2)
    res2 = coordinator.process_telemetry_tick(
        "drone_eagle_01",
        {"altitude_agl_m": t2.altitude_agl_m, "ground_speed_ms": t2.ground_speed_ms, "battery_percent": t2.battery_percent},
        {"decision": "avoid_local_obstacle_climb", "confidence": 0.91},
    )
    print(f"    Status: {res2['status']} (Compliant: {res2['compliant']}, Command: {res2['command_issued']})")
    print(f"    Active Violation: {sortie.active_violations[0].message}")

    # Seal black box bundle
    recorder = coordinator.blackbox_recorders["drone_eagle_01"]
    bundle = recorder.export_bundle()
    notary = WitnessNotary()
    receipt = notary.seal_bundle(bundle)
    print(f"[4] Black-Box Bundle Sealed: {bundle.bundle_id} ({bundle.event_count} events)")
    print(f"    Merkle Root: {bundle.merkle_root[:16]}...")
    print(f"    Witness Signature: {receipt.signature[:16]}...")
    return bundle


def cmd_vehicle_simulation(args):
    print("=== [Mission 2] Autonomous Vehicle Highway Drive (openpilot / CAN) ===")
    policy_engine = get_configured_policy_engine()
    coordinator = FleetCoordinator(policy_engine)
    can_driver = CANVehicleDriver(vehicle_id="car_nexus_02")

    sortie = coordinator.register_sortie(
        mission_id="highway_pilot_442",
        vehicle_id="car_nexus_02",
        vehicle_type="autonomous_vehicle",
    )
    print(f"[1] Initialized autonomous drive '{sortie.mission_id}'. Status: {sortie.status.value}")

    # Step 1: Nominal driving at 100 kph (27.7 m/s) with attentive driver
    print("[2] Tick 1: Cruising at 100 kph (Driver attentive)...")
    f1 = {"speed_mps": 27.7, "steering_torque_nm": 1.2, "driver_state": "ATTENTIVE", "time_without_attention_s": 0.5}
    t1 = can_driver.parse_can_frame(f1)
    res1 = coordinator.process_telemetry_tick(
        "car_nexus_02",
        {"speed_mps": t1.speed_mps, "steering_torque_nm": t1.steering_torque_nm, "time_without_driver_attention_s": t1.time_without_driver_attention_s, "autopilot_engaged": True},
        {"decision": "center_lane_following", "confidence": 0.97},
    )
    print(f"    Status: {res1['status']} (Compliant: {res1['compliant']}, Command: {res1['command_issued']})")

    # Step 2: Driver looks away for 3.8s (Breaches ISO 26262 3.0s threshold!)
    print("[3] Tick 2: Driver distracted for 3.8s -> BREACHES ISO 26262 ASIL-D THRESHOLD!")
    f2 = {"speed_mps": 27.7, "steering_torque_nm": 1.4, "driver_state": "EYES_OFF_ROAD", "time_without_attention_s": 3.8}
    t2 = can_driver.parse_can_frame(f2)
    res2 = coordinator.process_telemetry_tick(
        "car_nexus_02",
        {"speed_mps": t2.speed_mps, "steering_torque_nm": t2.steering_torque_nm, "time_without_driver_attention_s": t2.time_without_driver_attention_s, "autopilot_engaged": True},
        {"decision": "escalate_takeover_warning", "confidence": 0.94},
    )
    print(f"    Status: {res2['status']} (Compliant: {res2['compliant']}, Command: {res2['command_issued']})")
    print(f"    Active Violation: {sortie.active_violations[0].message}")


def cmd_forensic_replay(bundle=None):
    print("=== [Forensics] Synchronized Incident Reconstruction & Liability Adjudication ===")
    policy_engine = get_configured_policy_engine()
    player = ReplayPlayer(policy_engine)

    # If no bundle passed, generate a sample drone incident bundle
    if bundle is None:
        rec = BlackBoxRecorder(vehicle_id="drone_replay_sample")
        rec.record_event(
            observation={"altitude_agl_m": 90.0, "ground_speed_ms": 15.0},
            cognition={"reason": "nominal", "confidence": 0.98},
            actuation={"cmd": "FORWARD"},
        )
        rec.record_event(
            observation={"altitude_agl_m": 138.0, "ground_speed_ms": 16.0},  # FAA violation
            cognition={"reason": "avoiding_birds", "confidence": 0.85},
            actuation={"cmd": "CLIMB"},
        )
        bundle = rec.export_bundle()

    investigation = player.investigate_bundle(bundle)
    print(f"[1] Investigation '{investigation.investigation_id}' completed across {investigation.total_steps} steps.")
    print(f"[2] Forensic Summary:\n    {investigation.forensic_summary}")
    print(f"[3] Official Dossier Issued: {investigation.dossier.dossier_id}")
    print(f"    Liability Adjudicated: {investigation.dossier.liability_determination}")
    print(f"    Authority Signature: {investigation.dossier.authority_audit_signature[:20]}...")


def main():
    parser = argparse.ArgumentParser(description="Aegis-Fleet: Autonomous Fleet Black-Box & GRC Assurance Plane")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    sim_parser = subparsers.add_parser("simulate", help="Simulate autonomous mission")
    sim_parser.add_argument("--vehicle", choices=["drone", "car"], default="drone", help="Vehicle type to simulate")

    subparsers.add_parser("replay", help="Run forensic replay on flight records")
    subparsers.add_parser("all", help="Execute all missions and forensic investigation")

    args = parser.parse_args()

    if args.command == "simulate":
        if args.vehicle == "drone":
            cmd_drone_simulation(args)
        else:
            cmd_vehicle_simulation(args)
    elif args.command == "replay":
        cmd_forensic_replay()
    elif args.command == "all" or args.command is None:
        bundle = cmd_drone_simulation(args)
        print()
        cmd_vehicle_simulation(args)
        print()
        cmd_forensic_replay(bundle)


if __name__ == "__main__":
    main()
