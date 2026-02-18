from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence

class EnforcementMode(str, Enum):
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    CONTINUOUS = "continuous"
    NULLIFICATION = "nullification"

class FailureAction(str, Enum):
    REJECT = "reject"
    QUARANTINE = "quarantine"
    FREEZE = "freeze"
    ROLLBACK = "rollback"
    INCIDENT = "incident"
    ALERT_ONLY = "alert_only"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass(frozen=True)
class EvidenceRequirements:
    required_artifacts: Sequence[str]
    receipt_required: bool = True
    retention_days: int = 365

@dataclass(frozen=True)
class Enforcement:
    modes: Sequence[EnforcementMode]
    failure_actions: Sequence[FailureAction]
    severity: Severity = Severity.HIGH
    grace_period_seconds: int = 0

@dataclass(frozen=True)
class ChangeControl:
    amendment_class: str  # "constitutional" | "policy_level"
    quorum_rule: str
    break_glass_allowed: bool = False

@dataclass(frozen=True)
class Axiom:
    axiom_id: str
    version: str
    statement: str
    scope: Sequence[str]
    enforcement: Enforcement
    evidence: EvidenceRequirements
    change_control: ChangeControl
    status: str = "active"
    rationale: str = ""
    mechanization_validator: Optional[Callable[[Dict[str, Any]], bool]] = None
    mechanization_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProposedAction:
    """Normalized representation of an action BEFORE execution."""
    action_type: str
    actor_id: str
    intent: Dict[str, Any]
    target: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""

@dataclass
class EvaluationResult:
    admissible: bool
    violated_axioms: List[str] = field(default_factory=list)
    failure_actions: List[str] = field(default_factory=list)
    severity: str = "low"
    evidence_missing: List[str] = field(default_factory=list)
