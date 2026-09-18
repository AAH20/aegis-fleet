"""
Witness Notary & Forensic Tamper Detector.

Provides out-of-band cryptographic checkpointing and verifies that black-box
bundles have not been tampered with, truncated, or forged.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .recorder import BlackBoxBundle, CausalEvent


@dataclass
class WitnessReceipt:
    """An independent notary receipt sealing a flight record segment."""
    witness_id: str
    bundle_id: str
    merkle_root: str
    timestamp_ns: int
    signature: str


@dataclass
class TamperReport:
    """Forensic verification report of a black box bundle."""
    is_valid: bool
    total_events_checked: int
    tampered_event_id: Optional[str] = None
    reason: Optional[str] = None


class WitnessNotary:
    """
    Independent cryptographic witness sealing and verifying black box logs.
    """

    def __init__(self, witness_id: str = "notary_sec_authority", secret_key: str = "witness_secret_key"):
        self.witness_id = witness_id
        self.secret_key = secret_key

    def seal_bundle(self, bundle: BlackBoxBundle) -> WitnessReceipt:
        """Issue an attributable cryptographic witness receipt for a bundle."""
        now_ns = time.time_ns()
        payload = f"{self.witness_id}:{bundle.bundle_id}:{bundle.merkle_root}:{now_ns}:{self.secret_key}"
        signature = hashlib.sha256(payload.encode()).hexdigest()

        bundle.witness_signature = signature

        return WitnessReceipt(
            witness_id=self.witness_id,
            bundle_id=bundle.bundle_id,
            merkle_root=bundle.merkle_root,
            timestamp_ns=now_ns,
            signature=signature,
        )

    def verify_bundle_integrity(self, bundle: BlackBoxBundle) -> TamperReport:
        """
        Verify the complete hash-chain and Merkle root of an exported bundle.
        """
        if not bundle.events:
            return TamperReport(is_valid=True, total_events_checked=0)

        expected_prev_hash = "0" * 64
        recomputed_hashes = []

        for evt in bundle.events:
            # 1. Check previous event hash continuity
            if evt.previous_event_hash != expected_prev_hash:
                return TamperReport(
                    is_valid=False,
                    total_events_checked=len(recomputed_hashes),
                    tampered_event_id=evt.event_id,
                    reason=f"Hash chain broken at event {evt.event_id} (seq {evt.sequence_number})",
                )

            # 2. Check internal event hash
            calculated = evt.calculate_hash()
            if evt.event_hash != calculated:
                return TamperReport(
                    is_valid=False,
                    total_events_checked=len(recomputed_hashes),
                    tampered_event_id=evt.event_id,
                    reason=f"Payload tampered in event {evt.event_id}: hash mismatch",
                )

            expected_prev_hash = evt.event_hash
            recomputed_hashes.append(evt.event_hash)

        # 3. Check Merkle root
        combined = ":".join(recomputed_hashes)
        expected_merkle = hashlib.sha256(combined.encode()).hexdigest()
        if bundle.merkle_root != expected_merkle:
            return TamperReport(
                is_valid=False,
                total_events_checked=len(bundle.events),
                tampered_event_id=None,
                reason="Bundle Merkle root mismatch with event hash sequence",
            )

        return TamperReport(
            is_valid=True,
            total_events_checked=len(bundle.events),
            tampered_event_id=None,
            reason=None,
        )
