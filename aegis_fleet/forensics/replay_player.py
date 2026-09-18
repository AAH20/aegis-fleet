"""
Forensic Incident Replay Engine.

Reconstructs incident timelines from sealed black-box bundles, performing
frame-by-frame synchronization of sensor observations, AI cognitive reasoning,
autopilot actuations, and regulatory violations.
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..blackbox.recorder import BlackBoxBundle, CausalEvent
from ..grc.policy_engine import ComplianceResult, PolicyEngine
from ..grc.dossier_generator import DossierGenerator, RegulatoryDossier


@dataclass
class ReplayStep:
    """A synchronized step in a forensic investigation replay."""
    step: int
    timestamp_ns: int
    observation: Dict[str, Any]
    cognition: Dict[str, Any]
    actuation: Dict[str, Any]
    violations: List[str]


@dataclass
class IncidentInvestigation:
    """The complete forensic breakdown of an operational incident."""
    investigation_id: str
    bundle_id: str
    vehicle_id: str
    total_steps: int
    incident_occurred: bool
    first_infraction_step: Optional[int]
    timeline: List[ReplayStep]
    dossier: RegulatoryDossier
    forensic_summary: str


class ReplayPlayer:
    """
    Executes post-mission forensic investigation on exported flight bundles.
    """

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine
        self.dossier_generator = DossierGenerator()

    def investigate_bundle(self, bundle: BlackBoxBundle) -> IncidentInvestigation:
        """
        Step through all causal events in the bundle, track regulatory compliance,
        and synthesize root-cause liability conclusions.
        """
        investigation_id = f"inv_{uuid.uuid4().hex[:8]}"
        timeline: List[ReplayStep] = []
        all_violations = []
        first_infraction_step = None

        for idx, evt in enumerate(bundle.events):
            compliance = self.policy_engine.evaluate_telemetry(evt.observation)
            step_violation_msgs = [v.message for v in compliance.violations]

            if compliance.violations:
                all_violations.extend(compliance.violations)
                if first_infraction_step is None:
                    first_infraction_step = idx + 1

            timeline.append(
                ReplayStep(
                    step=idx + 1,
                    timestamp_ns=evt.timestamp_ns,
                    observation=evt.observation,
                    cognition=evt.cognition,
                    actuation=evt.actuation,
                    violations=step_violation_msgs,
                )
            )

        # Generate official compliance and liability dossier
        dossier = self.dossier_generator.generate_dossier(bundle, all_violations)

        incident_occurred = len(all_violations) > 0
        if incident_occurred:
            summary = (
                f"Incident Confirmed: {len(all_violations)} infractions detected starting at step {first_infraction_step}. "
                f"Liability Assigned: {dossier.liability_determination}."
            )
        else:
            summary = "Clean Flight/Drive: All mission phases fully compliant with certified regulations."

        return IncidentInvestigation(
            investigation_id=investigation_id,
            bundle_id=bundle.bundle_id,
            vehicle_id=bundle.vehicle_id,
            total_steps=len(timeline),
            incident_occurred=incident_occurred,
            first_infraction_step=first_infraction_step,
            timeline=timeline,
            dossier=dossier,
            forensic_summary=summary,
        )
