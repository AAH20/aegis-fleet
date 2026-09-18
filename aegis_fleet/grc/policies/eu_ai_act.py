"""
EU AI Act (High-Risk Systems Annex III) Safety Policies.

Ensures that autonomous vision-language-action (VLA) models and robotic
planners operate strictly within certified Operational Design Domains (ODD)
and maintain human oversight thresholds.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from ..policy_engine import ComplianceViolation, Severity


def eu_ai_confidence_threshold_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    EU AI Act Article 14 (Human Oversight): If AI model confidence in perception/action
    drops below certified minimum, system must alert operator or enter safe state.
    """
    confidence = telemetry.get("ai_model_confidence")
    MIN_CONFIDENCE = 0.70

    if confidence is not None and confidence < MIN_CONFIDENCE:
        return ComplianceViolation(
            rule_id="EU-AI-ACT-ART14-CONFIDENCE",
            framework="EU_AI_ACT_ANNEX_III",
            severity=Severity.HIGH,
            message=(
                f"VLA model prediction confidence {confidence:.2f} dropped below "
                f"certified minimum threshold {MIN_CONFIDENCE:.2f}"
            ),
            telemetry_value=confidence,
            threshold_value=MIN_CONFIDENCE,
        )
    return None


def eu_ai_odd_envelope_rule(telemetry: Dict[str, Any]) -> Optional[ComplianceViolation]:
    """
    EU AI Act Article 15 (Accuracy, Robustness & Cybersecurity): Detects operational
    conditions outside the model's certified Operational Design Domain (ODD).
    """
    odd_violated = telemetry.get("odd_boundary_breached", False)
    odd_reason = telemetry.get("odd_violation_reason", "Sensor degradation or environmental envelope breach")

    if odd_violated:
        return ComplianceViolation(
            rule_id="EU-AI-ACT-ART15-ODD-BREACH",
            framework="EU_AI_ACT_ANNEX_III",
            severity=Severity.CRITICAL_HALT,
            message=f"Aircraft/vehicle operating outside certified ODD envelope: {odd_reason}",
            telemetry_value=True,
            threshold_value=False,
        )
    return None
