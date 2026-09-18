"""
CAN-Bus Autopilot Driver (comma.ai openpilot / Autoware).

Decodes vehicle dynamics, steer/torque requests, brake pressures, and
driver monitoring states from CAN frames (e.g. via comma Panda hardware).
"""

from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class DriverEngagementState(enum.Enum):
    ATTENTIVE = "ATTENTIVE"
    DISTRACTED = "DISTRACTED"
    EYES_OFF_ROAD = "EYES_OFF_ROAD"
    SLEEPING_UNRESPONSIVE = "SLEEPING_UNRESPONSIVE"
    OVERRIDE_TAKEOVER = "OVERRIDE_TAKEOVER"


@dataclass
class VehicleTelemetry:
    """Standardized autonomous vehicle telemetry record."""
    vehicle_id: str
    timestamp_ns: int
    speed_mps: float
    steering_angle_deg: float
    steering_torque_nm: float
    brake_pressure_bar: float
    throttle_percent: float
    driver_state: DriverEngagementState
    time_without_driver_attention_s: float
    autopilot_engaged: bool
    lead_vehicle_distance_m: Optional[float] = None
    lane_departure_warning: bool = False

    @property
    def speed_kph(self) -> float:
        return self.speed_mps * 3.6

    @property
    def speed_mph(self) -> float:
        return self.speed_mps * 2.23694


VehicleTelemetryCallback = Callable[[VehicleTelemetry], None]


class CANVehicleDriver:
    """
    Interface for CAN-bus autonomous vehicle systems.
    """

    def __init__(self, vehicle_id: str = "vehicle_alpha"):
        self.vehicle_id = vehicle_id
        self._listeners: List[VehicleTelemetryCallback] = []
        self.last_telemetry: Optional[VehicleTelemetry] = None
        self.autopilot_engaged: bool = True

    def register_callback(self, callback: VehicleTelemetryCallback) -> None:
        self._listeners.append(callback)

    def parse_can_frame(self, frame_dict: Dict[str, Any]) -> VehicleTelemetry:
        """Decode dictionary representation of CAN payload."""
        now_ns = frame_dict.get("timestamp_ns", time.time_ns())
        speed_mps = float(frame_dict.get("speed_mps", 0.0))
        steer_deg = float(frame_dict.get("steering_angle_deg", 0.0))
        steer_torque = float(frame_dict.get("steering_torque_nm", 0.0))
        brake = float(frame_dict.get("brake_pressure_bar", 0.0))
        throttle = float(frame_dict.get("throttle_percent", 0.0))

        state_str = frame_dict.get("driver_state", DriverEngagementState.ATTENTIVE.value)
        try:
            driver_state = DriverEngagementState(state_str)
        except ValueError:
            driver_state = DriverEngagementState.DISTRACTED

        telem = VehicleTelemetry(
            vehicle_id=self.vehicle_id,
            timestamp_ns=now_ns,
            speed_mps=speed_mps,
            steering_angle_deg=steer_deg,
            steering_torque_nm=steer_torque,
            brake_pressure_bar=brake,
            throttle_percent=throttle,
            driver_state=driver_state,
            time_without_driver_attention_s=float(frame_dict.get("time_without_attention_s", 0.0)),
            autopilot_engaged=bool(frame_dict.get("autopilot_engaged", self.autopilot_engaged)),
            lead_vehicle_distance_m=frame_dict.get("lead_dist_m"),
            lane_departure_warning=bool(frame_dict.get("lane_departure", False)),
        )

        self.last_telemetry = telem
        for cb in self._listeners:
            cb(telem)

        return telem

    def command_emergency_brake(self, deceleration_mps2: float = 6.5) -> Dict[str, Any]:
        """Dispatch highest-priority CAN brake message."""
        return {
            "can_bus": "chassis",
            "message_id": 0x200,  # Standard emergency brake arbitration ID
            "vehicle_id": self.vehicle_id,
            "target_deceleration_mps2": deceleration_mps2,
            "action": "EMERGENCY_AUTONOMOUS_BRAKE",
            "timestamp_ns": time.time_ns(),
        }

    def command_takeover_warning(self, urgency: str = "CRITICAL_AUDIO_VISUAL") -> Dict[str, Any]:
        """Trigger driver alert acoustic & visual chime on dashboard cluster."""
        return {
            "can_bus": "cabin",
            "message_id": 0x310,  # Cabin cluster alert ID
            "urgency": urgency,
            "action": "DRIVER_TAKEOVER_REQUEST",
            "timestamp_ns": time.time_ns(),
        }
