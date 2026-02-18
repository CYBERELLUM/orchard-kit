"""Axiom integration surface for Orchard governance primitives.

This module is intentionally dependency-light: it only uses Orchard runtime
components and Python stdlib types. If you are using an Axiom SDK/framework,
install it via optional extras and pass native request/response objects through
an adapter.
"""

from orchard_kit.integrations.axiom.adapter import (
    AxiomGovernanceAction,
    AxiomGovernanceDecision,
    AxiomSignalAdapter,
    DictAxiomAdapter,
)
from orchard_kit.integrations.axiom.audit import AxiomAuditSink
from orchard_kit.integrations.axiom.guards import (
    AxiomResponseGuard,
    AxiomToolCallGuard,
)
from orchard_kit.integrations.axiom.middleware import AxiomGovernanceMiddleware

__all__ = [
    "AxiomAuditSink",
    "AxiomGovernanceAction",
    "AxiomGovernanceDecision",
    "AxiomGovernanceMiddleware",
    "AxiomResponseGuard",
    "AxiomSignalAdapter",
    "DictAxiomAdapter",
    "AxiomToolCallGuard",
]
