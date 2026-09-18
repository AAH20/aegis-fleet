# 🛰️ Aegis-Fleet: Autonomous Fleet Black-Box & GRC Assurance Plane

<div align="center">

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue?logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-All%20Passing%20(100%25)-success?logo=pytest)](tests/)
[![PX4 Autopilot](https://img.shields.io/badge/Autopilot-PX4%20%7C%20ArduPilot%20(MAVLink)-brightgreen)](https://px4.io)
[![comma.ai openpilot](https://img.shields.io/badge/Autonomous%20Vehicles-comma.ai%20openpilot%20(CAN)-red)](https://github.com/commaai/openpilot)
[![GRC Assurance](https://img.shields.io/badge/Compliance-FAA%20Part%20107%20%7C%20ISO%2026262%20%7C%20EU%20AI%20Act-purple)](#-regulatory-compliance-frameworks)
[![robot-black-box](https://img.shields.io/badge/Causal%20Spine-robot--black--box%20Attested-blueviolet)](#-causal-black-box-recorder)

**The universal, aviation- and automotive-grade control plane bridging high-level Agentic AI Swarms $\leftrightarrow$ Real-Time Autopilots $\leftrightarrow$ Cryptographic Black-Box Recorders $\leftrightarrow$ Continuous GRC Regulatory Assurance.**

[Key Capabilities](#-key-capabilities) • [System Architecture](#-system-architecture) • [Quickstart](#-quickstart-in-30-seconds) • [Regulatory Frameworks](#-regulatory-compliance-frameworks) • [Forensic Replay](#-incident-forensics--digital-twin)

</div>

---

## ⚡ The Problem Aegis-Fleet Solves

Autonomous drones (PX4/ArduPilot) and self-driving cars (comma.ai openpilot/Autoware) are increasingly governed by **VLA (Vision-Language-Action) and Agentic Swarms**.

When an incident occurs (a drone flyaway, airspace breach, or autonomous vehicle disengagement/collision), traditional flight logs fail:
1. **The AI Agent** blames the low-level controller.
2. **The Autopilot** blames noisy sensor or perception inputs.
3. **Regulators (FAA, NHTSA, EASA, EU AI Act High-Risk Annex)** demand proof: *"Who was in control? Did the AI operate within certified boundaries? Provide an untampered forensic replay."*

**Aegis-Fleet** unifies the **`robot-black-box`** causal recording pattern with **`GRC_Claw`** continuous compliance to provide an immutable, mathematically verifiable liability spine.

---

## 🏛️ System Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │                 Aegis-Fleet                  │
                               │   Autonomous Fleet Assurance & Forensics     │
                               └──────────────────────┬───────────────────────┘
                                                      │
         ┌───────────────────────────┬────────────────┴───────────────────────────┬───────────────────────────┐
         ▼                           ▼                                            ▼                           ▼
[ 1. Autopilot Ingest ]    [ 2. Causal Black-Box ]                      [ 3. GRC_Claw Assurance ]    [ 4. Swarm Commander ]
• MAVLink v2 (PX4/Drones)  • Sensor-Reason-Act Triad                    • FAA Part 107/135           • Multi-Vehicle Sorties
• CAN-Bus (openpilot/Cars) • SQLite WAL Monotonic Spool                 • ISO 26262 (ASIL-D) SOTIF   • Fail-Safe Return-to-Launch
• GPS, IMU, LiDAR, Video   • Ed25519 & SHA-256 Witness Hash Chain       • EU AI Act ODD Monitor      • Barrier Velocity Governor
                                     │                                            │
                                     └────────────────────┬───────────────────────┘
                                                          ▼
                                             [ 5. Forensic Replay Engine ]
                                             • Synchronized Timeline Player
                                             • Side-by-Side Agent Reasoning
                                             • Liability & Audit Dossier Generator
```

---

## 🎯 Key Capabilities

1. **Native Autopilot Drivers**:
   - **Drones**: MAVLink v2 parser for PX4 and ArduPilot telemetry (`GLOBAL_POSITION_INT`, `ATTITUDE`, `SYS_STATUS`) with automatic Return-to-Launch (RTL) command triggers.
   - **Vehicles**: CAN-bus parser for comma.ai openpilot / Panda hardware, tracking steering torque, brake pressure, and driver attentiveness.

2. **Causal Black-Box Recorder (`robot-black-box` Pattern)**:
   - Atomically binds the causal triad:
     $$\text{Sensor Observation} \longrightarrow \text{AI Agent Reasoning} \longrightarrow \text{Autopilot Actuator Command}$$
   - Cryptographic SHA-256 and Ed25519 witness notarization with SQLite WAL crash resilience.

3. **GRC_Claw Regulatory Assurance Engine**:
   - Automated, real-time policy evaluation preventing illegal or out-of-boundary actions.
   - **FAA Part 107 / 135**: 400ft AGL ceiling enforcement, 100 mph speed limits, 20% RTL battery reserves, and geofence containment corridors.
   - **ISO 26262 (ASIL-D) & ISO 21448 (SOTIF)**: Driver inattention limits (max 3.0s), steering torque envelopes, and automatic emergency braking (AEB) checks.
   - **EU AI Act (Annex III High-Risk)**: VLA prediction confidence floors and Operational Design Domain (ODD) boundaries.

4. **Swarm Coordinator & Fail-Safe Governors**:
   - Multi-drone/vehicle sortie management with automatic fail-safe Return-To-Launch (RTL) override upon critical regulatory breach.

5. **Incident Forensics & Digital Twin Replay**:
   - Reconstructs flight/drive incidents event-by-event with automated root-cause liability adjudication (`HUMAN_DRIVER_FAULT`, `AI_MODEL_FAULT`, `AIRSPACE_BREACH`).

---

## 🚀 Quickstart in 30 Seconds

### Installation
```bash
git clone https://github.com/AAH20/aegis-fleet.git
cd aegis-fleet
pip install -e .
```

### Run Live Missions & Forensics CLI
```bash
# Execute end-to-end drone flight, car cruise, and forensic investigation
aegis-fleet all

# Simulate drone delivery with FAA Part 107 geofence enforcement
aegis-fleet simulate --vehicle drone

# Simulate autonomous vehicle highway cruise with ISO 26262 driver monitoring
aegis-fleet simulate --vehicle car

# Run forensic replay and generate official liability dossier
aegis-fleet replay
```

### Run Automated Test Suite (100% Passing)
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📜 Python Integration Example

```python
from aegis_fleet.drivers import MAVLinkDroneDriver
from aegis_fleet.grc import PolicyEngine
from aegis_fleet.grc.policies import faa_altitude_rule, faa_geofence_rule
from aegis_fleet.swarm import FleetCoordinator

# 1. Setup GRC policy engine
engine = PolicyEngine()
engine.register_rule("FAA-ALTITUDE", faa_altitude_rule)
engine.register_rule("FAA-GEOFENCE", faa_geofence_rule)

# 2. Initialize fleet coordinator
coordinator = FleetCoordinator(engine)
coordinator.register_sortie(
    mission_id="delivery_902",
    vehicle_id="drone_alpha",
    vehicle_type="drone"
)

# 3. Stream real-time telemetry
driver = MAVLinkDroneDriver(drone_id="drone_alpha")
telem = driver.parse_mavlink_packet({"altitude_m": 85.0, "battery": 90.0})

result = coordinator.process_telemetry_tick(
    "drone_alpha",
    {"altitude_agl_m": telem.altitude_agl_m, "battery_percent": telem.battery_percent},
    {"decision": "track_corridor", "confidence": 0.98}
)
print(f"Mission Status: {result['status']}, Command: {result['command_issued']}")
```

---

## 🐳 Docker Deployment

```bash
docker compose up -d
```

---

## 🏷️ GitHub SEO Topics (20 tags)

```text
autonomous-vehicles, drones, px4, ardupilot, openpilot, mavlink, can-bus, 
robot-black-box, grc, faa-part-107, iso-26262, eu-ai-act, vla, robotics, 
forensics, swarm-intelligence, control-barrier-functions, ai-safety, 
tamper-evident, mission-assurance
```

---

## 📜 License & Authors
Developed by **Ahmed Hassan** (Founder, A2Z SOC).  
Licensed under the [Apache-2.0 License](LICENSE).
