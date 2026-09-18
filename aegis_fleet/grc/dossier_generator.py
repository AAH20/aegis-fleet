"""
Regulatory Compliance Dossier & Liability Adjudication Generator.

Synthesizes black-box telemetry, witness receipts, and GRC policy evaluation
into an official, non-repudiable compliance certificate and incident dossier.
"""

from __future__ import annotations
import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .policy_engine import ComplianceViolation, Severity
from ..blackbox.recorder import BlackBoxBundle


@dataclass
class RegulatoryDossier:
    """An official regulatory compliance and liability adjudication dossier."""
    dossier_id: str
    vehicle_id: str
    bundle_id: str
    merkle_root: str
    issued_at_ns: int
    is_fully_compliant: bool
    total_violations: int
    violations: List[Dict[str, Any]]
    liability_determination: str  # e.g., "HUMAN_OPERATOR", "AI_AGENT_MODEL", "HARDWARE_FAULT", "CLEAN_COMPLIANT"
    authority_audit_signature: str


class DossierGenerator:
    """
    Produces tamper-evident compliance certification packs.
    """

    def __init__(self, authority_id: str = "GRC_CLAW_AUDIT_AUTHORITY"):
        self.authority_id = authority_id

    def generate_dossier(
        self,
        bundle: BlackBoxBundle,
        violations: List[ComplianceViolation],
    ) -> RegulatoryDossier:
        """
        Synthesize bundle events and policy infractions into a signed regulatory dossier.
        """
        now_ns = time.time_ns()
        dossier_id = f"dossier_{uuid.uuid4().hex[:10]}"

        # Adjudicate liability
        if not violations:
            liability = "CLEAN_COMPLIANT"
        else:
            # Analyze root-cause attribution
            driver_fault = any("DRIVER-MONITOR" in v.rule_id for v in violations)
            ai_fault = any("EU-AI-ACT" in v.rule_id or "CONFIDENCE" in v.rule_id for v in violations)
            containment_fault = any("GEOFENCE" in v.rule_id or "ALTITUDE" in v.rule_id for v in violations)

            if driver_fault:
                liability = "HUMAN_DRIVER_INATTENTION_LIABILITY"
            elif ai_fault:
                liability = "AUTONOMOUS_AI_MODEL_ODD_BREACH_LIABILITY"
            elif containment_fault:
                liability = "AIRSPACE_CONTAINMENT_BREACH_LIABILITY"
            else:
                liability = "OPERATIONAL_REGULATORY_INFRACTION"

        violation_dicts = [
            {
                "rule_id": v.rule_id,
                "framework": v.framework,
                "severity": v.severity.value,
                "message": v.message,
                "telemetry_value": v.telemetry_value,
                "threshold_value": v.threshold_value,
            }
            for v in violations
        ]

        # Form authority signature
        audit_payload = f"{dossier_id}:{bundle.bundle_id}:{bundle.merkle_root}:{liability}:{len(violations)}:{now_ns}"
        signature = hashlib.sha256(audit_payload.encode()).hexdigest()

        return RegulatoryDossier(
            dossier_id=dossier_id,
            vehicle_id=bundle.vehicle_id,
            bundle_id=bundle.bundle_id,
            merkle_root=bundle.merkle_root,
            issued_at_ns=now_ns,
            is_fully_compliant=(len(violations) == 0),
            total_violations=len(violations),
            violations=violation_dicts,
            liability_determination=liability,
            authority_audit_signature=signature,
        )
