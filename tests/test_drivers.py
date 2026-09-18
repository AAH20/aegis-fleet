"""Unit tests for Drone (MAVLink) and Vehicle (CAN-bus) autopilot drivers."""

import unittest
from aegis_fleet.drivers import (
    MAVLinkDroneDriver,
    DroneTelemetry,
    FlightMode,
    CANVehicleDriver,
    VehicleTelemetry,
    DriverEngagementState,
)


class TestDrivers(unittest.TestCase):

    def test_mavlink_drone_driver_parsing(self):
        driver = MAVLinkDroneDriver(drone_id="drone_test_01")
        packet = {
            "relative_alt": 95000,  # 95 meters in mm
            "vx": 10.0,
            "vy": 0.0,
            "battery": 88.5,
            "flight_mode": "OFFBOARD_AI",
            "lat": 37.7749,
            "lon": -122.4194,
        }
        telem = driver.parse_mavlink_packet(packet)

        self.assertEqual(telem.drone_id, "drone_test_01")
        self.assertEqual(telem.altitude_agl_m, 95.0)
        self.assertEqual(telem.ground_speed_ms, 10.0)
        self.assertEqual(telem.battery_percent, 88.5)
        self.assertEqual(telem.flight_mode, FlightMode.OFFBOARD_AI)

    def test_mavlink_drone_rtl_command(self):
        driver = MAVLinkDroneDriver(drone_id="drone_test_01")
        cmd = driver.command_rtl(reason="GEOFENCE_BREACH")

        self.assertEqual(driver.current_mode, FlightMode.RETURN_TO_LAUNCH)
        self.assertEqual(cmd["target_mode"], "RETURN_TO_LAUNCH")
        self.assertEqual(cmd["reason"], "GEOFENCE_BREACH")

    def test_can_vehicle_driver_parsing(self):
        driver = CANVehicleDriver(vehicle_id="car_test_01")
        frame = {
            "speed_mps": 25.0,
            "steering_angle_deg": 2.5,
            "steering_torque_nm": 1.1,
            "brake_pressure_bar": 0.0,
            "throttle_percent": 30.0,
            "driver_state": "ATTENTIVE",
            "time_without_attention_s": 0.2,
        }
        telem = driver.parse_can_frame(frame)

        self.assertEqual(telem.vehicle_id, "car_test_01")
        self.assertEqual(telem.speed_mps, 25.0)
        self.assertEqual(telem.speed_kph, 90.0)
        self.assertEqual(telem.driver_state, DriverEngagementState.ATTENTIVE)

    def test_can_vehicle_emergency_brake(self):
        driver = CANVehicleDriver(vehicle_id="car_test_01")
        cmd = driver.command_emergency_brake(deceleration_mps2=7.0)

        self.assertEqual(cmd["message_id"], 0x200)
        self.assertEqual(cmd["target_deceleration_mps2"], 7.0)


if __name__ == "__main__":
    unittest.main()
