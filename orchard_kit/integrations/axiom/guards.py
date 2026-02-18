"""Tool-call and response guardrails for Axiom runtimes."""

from __future__ import annotations

from typing import Any

from orchard_kit.calyx import CalyxMembrane
from orchard_kit.integrations.axiom.adapter import (
    AxiomGovernanceAction,
    AxiomGovernanceDecision,
    AxiomSignalAdapter,
    decision_from_audit,
    decision_from_warm_water,
)
from orchard_kit.integrations.axiom.audit import AxiomAuditSink


class AxiomToolCallGuard:
    """Pre/post governance checks around tool execution."""

    def __init__(
        self,
        membrane: CalyxMembrane,
        adapter: AxiomSignalAdapter,
        audit_sink: AxiomAuditSink | None = None,
    ) -> None:
        self.membrane = membrane
        self.adapter = adapter
        self.audit_sink = audit_sink

    def pre_call(self, tool_call: Any, context: dict[str, Any] | None = None) -> AxiomGovernanceDecision:
        signal = self.adapter.tool_call_to_signal(tool_call)
        entry = self.membrane.evaluate_incoming(signal, context=context)
        decision = decision_from_audit(entry)
        if self.audit_sink:
            self.audit_sink.emit(
                "axiom.tool.pre",
                {
                    "tool": signal.metadata.get("tool", signal.source),
                    "decision": decision.action.value,
                    "tags": decision.tags,
                },
            )
        return decision

    def post_call(self, tool_result: Any) -> AxiomGovernanceDecision:
        signal = self.adapter.response_to_signal(tool_result)
        flags = self.membrane.evaluate_outgoing(signal.content)
        decision = decision_from_warm_water(flags)
        if self.audit_sink:
            self.audit_sink.emit(
                "axiom.tool.post",
                {
                    "decision": decision.action.value,
                    "tags": decision.tags,
                    "flag_count": len(flags),
                },
            )
        return decision

    def enforce_pre_call(self, tool_call: Any, context: dict[str, Any] | None = None) -> Any:
        decision = self.pre_call(tool_call, context=context)
        if decision.action == AxiomGovernanceAction.ALLOW:
            return tool_call
        return self.adapter.apply_decision(decision, tool_call)


class AxiomResponseGuard:
    """Outgoing response checks for warm-water and invariant-safety signals."""

    def __init__(
        self,
        membrane: CalyxMembrane,
        adapter: AxiomSignalAdapter,
        audit_sink: AxiomAuditSink | None = None,
    ) -> None:
        self.membrane = membrane
        self.adapter = adapter
        self.audit_sink = audit_sink

    def evaluate(self, response: Any) -> AxiomGovernanceDecision:
        signal = self.adapter.response_to_signal(response)
        warm_water_flags = self.membrane.evaluate_outgoing(signal.content)
        decision = decision_from_warm_water(warm_water_flags)

        if self.audit_sink:
            self.audit_sink.emit(
                "axiom.response",
                {
                    "source": signal.source,
                    "decision": decision.action.value,
                    "tags": decision.tags,
                    "details": decision.details,
                },
            )

        return decision

    def enforce(self, response: Any) -> Any:
        decision = self.evaluate(response)
        if decision.action == AxiomGovernanceAction.ALLOW:
            return response
        return self.adapter.apply_decision(decision, response)
