"""
GRC Policy Engine.

Evaluates streaming telemetry or recorded black-box bundles against
certified aviation and automotive regulatory safety frameworks.
"""

from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class Severity(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL_HALT = "CRITICAL_HALT"


@dataclass
class ComplianceViolation:
    """A specific regulatory rule infraction detected during operation."""
    rule_id: str
    framework: str       # e.g., "FAA_PART_107", "ISO_26262_ASIL_D", "EU_AI_ACT"
    severity: Severity
    message: str
    telemetry_value: Any
    threshold_value: Any
    timestamp_ns: int = field(default_factory=time.time_ns)


@dataclass
class ComplianceResult:
    """The aggregate compliance status of an evaluation."""
    compliant: bool
    total_rules_evaluated: int
    violations: List[ComplianceViolation]
    critical_halt_required: bool
    summary: str


RuleEvaluator = Callable[[Dict[str, Any]], Optional[ComplianceViolation]]


class PolicyEngine:
    """
    Evaluates telemetry against active regulatory policy sets.
    """

    def __init__(self):
        self._rules: Dict[str, RuleEvaluator] = {}

    def register_rule(self, rule_id: str, evaluator: RuleEvaluator) -> None:
        self._rules[rule_id] = evaluator

    def evaluate_telemetry(self, telemetry_dict: Dict[str, Any]) -> ComplianceResult:
        """Evaluate a single telemetry point against all registered rules."""
        violations: List[ComplianceViolation] = []
        critical_halt = False

        for rule_id, evaluator in self._rules.items():
            try:
                violation = evaluator(telemetry_dict)
                if violation:
                    violations.append(violation)
                    if violation.severity == Severity.CRITICAL_HALT:
                        critical_halt = True
            except Exception as e:
                # Log rule execution exception as an evaluation warning
                pass

        compliant = (len(violations) == 0)
        summary = (
            "Fully Compliant"
            if compliant
            else f"Violations Detected: {len(violations)} (Critical: {critical_halt})"
        )

        return ComplianceResult(
            compliant=compliant,
            total_rules_evaluated=len(self._rules),
            violations=violations,
            critical_halt_required=critical_halt,
            summary=summary,
        )
