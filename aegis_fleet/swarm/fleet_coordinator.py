"""
Mission Swarm Coordinator.

Supervises multi-agent drone and autonomous vehicle fleets, enforcing real-time
GRC assurance gates and dispatching fail-safe Return-To-Launch or Emergency Stop
commands when regulatory safety envelopes are violated.
"""

from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..grc.policy_engine import ComplianceResult, ComplianceViolation, PolicyEngine, Severity
from ..blackbox.recorder import BlackBoxRecorder


class SortieStatus(enum.Enum):
    PRE_FLIGHT_CLEARED = "PRE_FLIGHT_CLEARED"
    IN_TRANSIT = "IN_TRANSIT"
    MISSION_ACTIVE = "MISSION_ACTIVE"
    EMERGENCY_RTL = "EMERGENCY_RTL"
    SAFE_HALTED = "SAFE_HALTED"
    MISSION_COMPLETED = "MISSION_COMPLETED"


@dataclass
class VehicleSortie:
    """An operational mission assignment for a vehicle or drone in the fleet."""
    mission_id: str
    vehicle_id: str
    vehicle_type: str  # "drone" or "autonomous_vehicle"
    status: SortieStatus = SortieStatus.PRE_FLIGHT_CLEARED
    waypoints: List[Dict[str, float]] = field(default_factory=list)
    active_violations: List[ComplianceViolation] = field(default_factory=list)
    last_telemetry: Dict[str, Any] = field(default_factory=dict)


class FleetCoordinator:
    """
    Coordinates fleet operations and enforces GRC-governed safety interlocks.
    """

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine
        self.sorties: Dict[str, VehicleSortie] = {}
        self.blackbox_recorders: Dict[str, BlackBoxRecorder] = {}

    def register_sortie(
        self,
        mission_id: str,
        vehicle_id: str,
        vehicle_type: str,
        waypoints: Optional[List[Dict[str, float]]] = None,
    ) -> VehicleSortie:
        """Register a new autonomous sortie in the fleet."""
        sortie = VehicleSortie(
            mission_id=mission_id,
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            status=SortieStatus.IN_TRANSIT,
            waypoints=waypoints or [],
        )
        self.sorties[vehicle_id] = sortie
        self.blackbox_recorders[vehicle_id] = BlackBoxRecorder(vehicle_id=vehicle_id)
        return sortie

    def process_telemetry_tick(
        self,
        vehicle_id: str,
        telemetry: Dict[str, Any],
        ai_cognition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a real-time telemetry frame:
        1. Evaluates GRC policies.
        2. Logs causal triad into BlackBox.
        3. If critical violation, issues immediate fail-safe command.
        """
        if vehicle_id not in self.sorties:
            raise KeyError(f"Vehicle '{vehicle_id}' not registered in fleet.")

        sortie = self.sorties[vehicle_id]
        sortie.last_telemetry = telemetry

        # 1. Evaluate GRC policies
        compliance: ComplianceResult = self.policy_engine.evaluate_telemetry(telemetry)

        # 2. Determine actuation response
        actuation = {"status": "NORMAL_OPERATION", "command": "CONTINUE_MISSION"}

        if compliance.critical_halt_required:
            sortie.status = (
                SortieStatus.EMERGENCY_RTL
                if sortie.vehicle_type == "drone"
                else SortieStatus.SAFE_HALTED
            )
            actuation = {
                "status": "FAIL_SAFE_TRIGGERED",
                "command": "RETURN_TO_LAUNCH" if sortie.vehicle_type == "drone" else "EMERGENCY_STOP",
                "reason": compliance.violations[0].message if compliance.violations else "Safety breach",
            }

        sortie.active_violations = compliance.violations

        # 3. Log Causal Triad into BlackBox
        recorder = self.blackbox_recorders[vehicle_id]
        causal_event = recorder.record_event(
            observation=telemetry,
            cognition=ai_cognition or {"decision": "nominal_waypoint_tracking", "confidence": 0.95},
            actuation=actuation,
        )

        return {
            "vehicle_id": vehicle_id,
            "status": sortie.status.value,
            "compliant": compliance.compliant,
            "violations_count": len(compliance.violations),
            "command_issued": actuation["command"],
            "event_hash": causal_event.event_hash[:16],
        }
