"""
FAA Part 107 & Part 135 Drone Regulatory Policies.

Codifies statutory requirements for small unmanned aircraft systems (sUAS)
into executable compliance gates.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from ..policy_engine import ComplianceViolation, Severity


def faa_altitude_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    FAA 14 CFR § 107.51(b): Altitude cannot exceed 400 feet (121.92 m) above ground level.
    """
    alt = telemetry.get("altitude_agl_m", 0.0)
    MAX_ALTITUDE_M = 121.92

    if alt > MAX_ALTITUDE_M:
        return ComplianceViolation(
            rule_id="FAA-107.51b-ALTITUDE",
            framework="FAA_PART_107",
            severity=Severity.CRITICAL_HALT,
            message=f"Altitude {alt:.2f}m exceeds FAA maximum ceiling of {MAX_ALTITUDE_M:.2f}m (400ft AGL)",
            telemetry_value=alt,
            threshold_value=MAX_ALTITUDE_M,
        )
    return None


def faa_speed_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    FAA 14 CFR § 107.51(a): Groundspeed cannot exceed 100 mph (44.7 m/s).
    """
    speed = telemetry.get("ground_speed_ms", 0.0)
    MAX_SPEED_MS = 44.7

    if speed > MAX_SPEED_MS:
        return ComplianceViolation(
            rule_id="FAA-107.51a-GROUNDSPEED",
            framework="FAA_PART_107",
            severity=Severity.HIGH,
            message=f"Groundspeed {speed:.2f} m/s exceeds FAA limit of {MAX_SPEED_MS:.2f} m/s (100 mph)",
            telemetry_value=speed,
            threshold_value=MAX_SPEED_MS,
        )
    return None


def faa_battery_reserve_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    Part 135 Safe Reserve: Mission must abort to Return-To-Launch if battery drops below 20%.
    """
    battery = telemetry.get("battery_percent", 100.0)
    MIN_RESERVE_PERCENT = 20.0

    if battery < MIN_RESERVE_PERCENT:
        return ComplianceViolation(
            rule_id="FAA-135-BATTERY-RESERVE",
            framework="FAA_PART_135",
            severity=Severity.CRITICAL_HALT,
            message=f"Battery {battery:.1f}% dropped below mandatory 20% Return-to-Launch reserve",
            telemetry_value=battery,
            threshold_value=MIN_RESERVE_PERCENT,
        )
    return None


def faa_geofence_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    Controlled Airspace & Geofencing: Aircraft must not penetrate boundary walls.
    """
    breached = telemetry.get("geofence_breached", False)
    if breached:
        return ComplianceViolation(
            rule_id="FAA-GEOFENCE-BREACH",
            framework="FAA_PART_107",
            severity=Severity.CRITICAL_HALT,
            message="Drone breached certified flight containment corridor (geofence)",
            telemetry_value=True,
            threshold_value=False,
        )
    return None
