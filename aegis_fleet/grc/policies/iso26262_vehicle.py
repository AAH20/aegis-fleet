"""
ISO 26262 (ASIL-D) & ISO 21448 (SOTIF) Autonomous Vehicle Policies.

Codifies functional safety and driver monitoring requirements for
Level 2+ and Level 3 automated driving systems.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from ..policy_engine import ComplianceViolation, Severity


def iso_driver_attention_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    ISO 26262 / UNECE R157: While autopilot is engaged, driver inattention exceeding
    3.0 seconds requires immediate acoustic takeover alert and minimal risk maneuver.
    """
    engaged = telemetry.get("autopilot_engaged", True)
    if not engaged:
        return None

    unattended_seconds = telemetry.get("time_without_driver_attention_s", 0.0)
    MAX_UNATTENDED_S = 3.0

    if unattended_seconds > MAX_UNATTENDED_S:
        return ComplianceViolation(
            rule_id="ISO-26262-DRIVER-MONITOR",
            framework="ISO_26262_ASIL_D",
            severity=Severity.CRITICAL_HALT,
            message=(
                f"Driver inattentive for {unattended_seconds:.1f}s while autopilot engaged. "
                f"Exceeds ISO 26262 threshold of {MAX_UNATTENDED_S:.1f}s"
            ),
            telemetry_value=unattended_seconds,
            threshold_value=MAX_UNATTENDED_S,
        )
    return None


def iso_steering_rate_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    ISO 21448 (SOTIF): Steering torque cannot abruptly exceed certified actuator authority
    without corresponding driver torque intervention (prevents phantom lane departures).
    """
    torque = abs(telemetry.get("steering_torque_nm", 0.0))
    MAX_AUTOPILOT_TORQUE_NM = 3.5  # Typical steer actuator limit for L2/L3

    if torque > MAX_AUTOPILOT_TORQUE_NM:
        return ComplianceViolation(
            rule_id="ISO-21448-STEER-TORQUE-BOUND",
            framework="ISO_21448_SOTIF",
            severity=Severity.HIGH,
            message=f"Steering torque request {torque:.2f} Nm exceeds certified safe limit {MAX_AUTOPILOT_TORQUE_NM:.2f} Nm",
            telemetry_value=torque,
            threshold_value=MAX_AUTOPILOT_TORQUE_NM,
        )
    return None


def iso_emergency_brake_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    Euro NCAP / ISO 22839: Forward collision warning & autonomous emergency braking (AEB)
    must engage if Time-To-Collision (TTC) is critically compromised.
    """
    lead_dist = telemetry.get("lead_vehicle_distance_m")
    speed_mps = telemetry.get("speed_mps", 0.0)
    brake_bar = telemetry.get("brake_pressure_bar", 0.0)

    if lead_dist is not None and speed_mps > 10.0:
        # Simple TTC estimate
        ttc = lead_dist / max(1.0, speed_mps)
        if ttc < 1.2 and brake_bar < 5.0:
            return ComplianceViolation(
                rule_id="ISO-22839-FORWARD-COLLISION-AEB",
                framework="ISO_26262_ASIL_D",
                severity=Severity.CRITICAL_HALT,
                message=f"Time-to-Collision ({ttc:.2f}s) critical with insufficient braking ({brake_bar:.1f} bar)",
                telemetry_value=ttc,
                threshold_value=1.2,
            )
    return None
