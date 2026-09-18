"""
Causal Flight & Drive Black-Box Recorder.

Implements the robot-black-box pattern by binding:
  [Observation] -> [Agent Cognition] -> [Autopilot Actuation]
into an atomic, monotonic, tamper-evident SQLite WAL stream.
"""

from __future__ import annotations
import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CausalEvent:
    """
    An indivisible causal event record from an autonomous vehicle or drone.
    """
    event_id: str
    sequence_number: int
    timestamp_ns: int
    vehicle_id: str
    observation: Dict[str, Any]       # Sensors, camera hash, obstacles, GPS
    cognition: Dict[str, Any]         # AI agent prompt, internal thought, confidence
    actuation: Dict[str, Any]         # Autopilot command issued (throttle, roll, steer)
    previous_event_hash: str
    event_hash: str = ""

    def calculate_hash(self) -> str:
        payload = (
            f"{self.event_id}:{self.sequence_number}:{self.timestamp_ns}:"
            f"{self.vehicle_id}:{json.dumps(self.observation, sort_keys=True)}:"
            f"{json.dumps(self.cognition, sort_keys=True)}:"
            f"{json.dumps(self.actuation, sort_keys=True)}:"
            f"{self.previous_event_hash}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class BlackBoxBundle:
    """A sealed, exportable bundle of flight/drive black-box events."""
    bundle_id: str
    vehicle_id: str
    start_time_ns: int
    end_time_ns: int
    event_count: int
    events: List[CausalEvent]
    merkle_root: str
    witness_signature: str = ""


class BlackBoxRecorder:
    """
    High-frequency, crash-resilient SQLite WAL black-box flight recorder.
    """

    def __init__(self, db_path: str = ":memory:", vehicle_id: str = "fleet_agent_01"):
        self.db_path = db_path
        self.vehicle_id = vehicle_id
        self._seq = 0
        self._last_hash = "0" * 64
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self._conn:
            # Enable WAL mode if using on-disk file
            if self.db_path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL;")
                self._conn.execute("PRAGMA synchronous=NORMAL;")

            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS blackbox_events (
                    event_id TEXT PRIMARY KEY,
                    sequence_number INTEGER UNIQUE,
                    timestamp_ns INTEGER,
                    vehicle_id TEXT,
                    observation_json TEXT,
                    cognition_json TEXT,
                    actuation_json TEXT,
                    previous_event_hash TEXT,
                    event_hash TEXT
                )
                """
            )

    def record_event(
        self,
        observation: Dict[str, Any],
        cognition: Dict[str, Any],
        actuation: Dict[str, Any],
        timestamp_ns: Optional[int] = None,
    ) -> CausalEvent:
        """
        Commit a new causal event into the black box with cryptographic hash linking.
        """
        self._seq += 1
        now_ns = timestamp_ns or time.time_ns()
        event_id = f"evt_{uuid.uuid4().hex[:12]}"

        event = CausalEvent(
            event_id=event_id,
            sequence_number=self._seq,
            timestamp_ns=now_ns,
            vehicle_id=self.vehicle_id,
            observation=observation,
            cognition=cognition,
            actuation=actuation,
            previous_event_hash=self._last_hash,
        )
        event.event_hash = event.calculate_hash()
        self._last_hash = event.event_hash

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO blackbox_events (
                    event_id, sequence_number, timestamp_ns, vehicle_id,
                    observation_json, cognition_json, actuation_json,
                    previous_event_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.sequence_number,
                    event.timestamp_ns,
                    event.vehicle_id,
                    json.dumps(event.observation),
                    json.dumps(event.cognition),
                    json.dumps(event.actuation),
                    event.previous_event_hash,
                    event.event_hash,
                ),
            )

        return event

    def export_bundle(self) -> BlackBoxBundle:
        """Export all recorded events into an immutable, verifiable bundle."""
        with self._conn:
            cur = self._conn.execute("SELECT * FROM blackbox_events ORDER BY sequence_number ASC")
            rows = cur.fetchall()

        events = []
        hashes = []
        for r in rows:
            evt = CausalEvent(
                event_id=r["event_id"],
                sequence_number=r["sequence_number"],
                timestamp_ns=r["timestamp_ns"],
                vehicle_id=r["vehicle_id"],
                observation=json.loads(r["observation_json"]),
                cognition=json.loads(r["cognition_json"]),
                actuation=json.loads(r["actuation_json"]),
                previous_event_hash=r["previous_event_hash"],
                event_hash=r["event_hash"],
            )
            events.append(evt)
            hashes.append(evt.event_hash)

        # Compute simple Merkle root over event hashes
        combined = ":".join(hashes)
        merkle_root = hashlib.sha256(combined.encode()).hexdigest() if hashes else "0" * 64

        start_time = events[0].timestamp_ns if events else 0
        end_time = events[-1].timestamp_ns if events else 0

        return BlackBoxBundle(
            bundle_id=f"bundle_{uuid.uuid4().hex[:8]}",
            vehicle_id=self.vehicle_id,
            start_time_ns=start_time,
            end_time_ns=end_time,
            event_count=len(events),
            events=events,
            merkle_root=merkle_root,
        )
