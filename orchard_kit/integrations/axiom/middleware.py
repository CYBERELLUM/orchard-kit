"""Ingress governance middleware for Axiom runtimes."""

from __future__ import annotations

from typing import Any, Callable

from orchard_kit.calyx import CalyxMembrane
from orchard_kit.integrations.axiom.adapter import (
    AxiomGovernanceAction,
    AxiomGovernanceDecision,
    AxiomSignalAdapter,
    decision_from_audit,
)
from orchard_kit.integrations.axiom.audit import AxiomAuditSink


class AxiomGovernanceMiddleware:
    """Evaluates inbound signals before they enter an Axiom execution path."""

    def __init__(
        self,
        membrane: CalyxMembrane,
        adapter: AxiomSignalAdapter,
        policy_profile: str = "default",
        audit_sink: AxiomAuditSink | None = None,
    ) -> None:
        self.membrane = membrane
        self.adapter = adapter
        self.policy_profile = policy_profile
        self.audit_sink = audit_sink

    def evaluate(self, request: Any, context: dict[str, Any] | None = None) -> AxiomGovernanceDecision:
        """Evaluate inbound request and return an actionable governance decision."""
        signal = self.adapter.request_to_signal(request)
        context_data = {"policy_profile": self.policy_profile, **(context or {})}
        entry = self.membrane.evaluate_incoming(signal, context=context_data)
        decision = decision_from_audit(entry)

        if self.audit_sink:
            self.audit_sink.emit(
                "axiom.ingress",
                {
                    "policy_profile": self.policy_profile,
                    "signal": {
                        "source": signal.source,
                        "signal_type": signal.signal_type,
                        "fingerprint": signal.fingerprint,
                    },
                    "decision": {
                        "action": decision.action.value,
                        "reason": decision.reason,
                        "tags": decision.tags,
                        "details": decision.details,
                    },
                },
            )

        return decision

    def __call__(self, request: Any, next_handler: Callable[[Any], Any], context: dict[str, Any] | None = None) -> Any:
        """Middleware-style execution where blocked requests are short-circuited."""
        decision = self.evaluate(request, context=context)
        if decision.action != AxiomGovernanceAction.ALLOW:
            return self.adapter.apply_decision(decision, request)

        return next_handler(request)
