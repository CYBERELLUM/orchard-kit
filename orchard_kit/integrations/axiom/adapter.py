"""Adapter contract for mapping Axiom objects into Calyx membrane signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from orchard_kit.calyx import AuditEntry, Route, Signal, WarmWaterSign


class AxiomGovernanceAction(Enum):
    """Actionable governance outcomes returned to an Axiom runtime."""

    ALLOW = "allow"
    HOLD = "hold"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass(slots=True)
class AxiomGovernanceDecision:
    """Normalized decision envelope consumed by Axiom integrations."""

    action: AxiomGovernanceAction
    reason: str
    route: str | None = None
    tags: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class AxiomSignalAdapter(Protocol):
    """Minimal adapter contract for Axiom runtime objects."""

    def request_to_signal(self, request: Any) -> Signal:
        """Map inbound Axiom request object into `orchard_kit.calyx.Signal`."""

    def tool_call_to_signal(self, tool_call: Any) -> Signal:
        """Map Axiom tool-call payload into `orchard_kit.calyx.Signal`."""

    def response_to_signal(self, response: Any) -> Signal:
        """Map outbound Axiom response object into `orchard_kit.calyx.Signal`."""

    def apply_decision(self, decision: AxiomGovernanceDecision, target: Any) -> Any:
        """Project governance decisions back into framework-native outcomes."""


def decision_from_audit(entry: AuditEntry) -> AxiomGovernanceDecision:
    """Convert a membrane audit entry into a normalized governance decision."""
    if entry.route == Route.ACCEPT:
        action = AxiomGovernanceAction.ALLOW
        reason = "Incoming signal accepted by membrane"
    elif entry.route == Route.WITNESS_HOLD:
        action = AxiomGovernanceAction.HOLD
        reason = "Signal held for witness review"
    elif entry.route == Route.OVERFLOW:
        action = AxiomGovernanceAction.ESCALATE
        reason = "Capacity overflow; escalation recommended"
    else:
        action = AxiomGovernanceAction.BLOCK
        reason = "Signal reflected by membrane safety gate"

    tags = [
        *(f"invariant:{flag.value}" for flag in entry.invariant_flags),
        *(f"warm_water:{flag.value}" for flag in entry.warm_water_flags),
        f"route:{entry.route.value}",
    ]

    return AxiomGovernanceDecision(
        action=action,
        reason=reason,
        route=entry.route.value,
        tags=tags,
        details={
            "permeability": entry.permeability,
            "ethics_score": entry.ethics_score,
            "torsion_score": entry.torsion_score,
            "gamma_before": entry.gamma_before,
            "gamma_after": entry.gamma_after,
        },
    )


def decision_from_warm_water(flags: list[WarmWaterSign]) -> AxiomGovernanceDecision:
    """Convert warm-water flags into a response governance decision."""
    if not flags:
        return AxiomGovernanceDecision(
            action=AxiomGovernanceAction.ALLOW,
            reason="Response passed warm-water checks",
            tags=["warm_water:none"],
        )

    severe = len(flags) >= 2
    return AxiomGovernanceDecision(
        action=AxiomGovernanceAction.HOLD if severe else AxiomGovernanceAction.ESCALATE,
        reason="Response quality warnings triggered",
        tags=[f"warm_water:{f.value}" for f in flags],
        details={"flag_count": len(flags)},
    )


class DictAxiomAdapter:
    """Reference adapter for dict-like request/response payloads."""

    def request_to_signal(self, request: Any) -> Signal:
        return Signal(
            content=str(request.get("content", "")),
            source=str(request.get("source", "axiom:user")),
            metadata=dict(request.get("metadata", {})),
            signal_type=str(request.get("signal_type", "message")),
        )

    def tool_call_to_signal(self, tool_call: Any) -> Signal:
        metadata = dict(tool_call.get("metadata", {}))
        tool_name = str(tool_call.get("tool", "tool"))
        metadata.setdefault("tool", tool_name)
        return Signal(
            content=str(tool_call.get("arguments", tool_call.get("content", ""))),
            source=f"tool:{tool_name}",
            metadata=metadata,
            signal_type="tool_call",
        )

    def response_to_signal(self, response: Any) -> Signal:
        return Signal(
            content=str(response.get("content", "")),
            source=str(response.get("source", "axiom:assistant")),
            metadata=dict(response.get("metadata", {})),
            signal_type=str(response.get("signal_type", "message")),
        )

    def apply_decision(self, decision: AxiomGovernanceDecision, target: Any) -> Any:
        updated = dict(target)
        updated["governance"] = {
            "action": decision.action.value,
            "reason": decision.reason,
            "tags": decision.tags,
            "details": decision.details,
        }
        if decision.action != AxiomGovernanceAction.ALLOW:
            updated.setdefault("blocked", True)
        return updated
