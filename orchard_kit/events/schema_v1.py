"""
schema_v1.py — Orchard event schema v1.

Versioned event envelope and payload definitions for governance telemetry.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = "v1"


class EventType(Enum):
    """Canonical event categories emitted by orchard telemetry."""

    MEMBRANE_DECISION = "membrane.decision"
    INVARIANT_VIOLATION = "membrane.invariant_violation"
    AUDIT_SUMMARY = "audit.summary"


@dataclass(frozen=True)
class EventEnvelope:
    """Versioned event envelope for all telemetry streams."""

    event_type: EventType
    source: str
    payload: dict[str, Any]
    schema_version: str = SCHEMA_VERSION
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    emitted_at: float = field(default_factory=time.time)
    correlation_id: str | None = None
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize event for sink transport."""
        event = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "emitted_at": self.emitted_at,
            "payload": self.payload,
        }
        if self.correlation_id:
            event["correlation_id"] = self.correlation_id
        if self.trace_id:
            event["trace_id"] = self.trace_id
        return event


def membrane_decision_payload(
    *,
    signal_fingerprint: str,
    signal_source: str,
    signal_type: str,
    route: str,
    permeability: float,
    ethics_score: float,
    torsion_score: float,
    invariants: list[str],
    warm_water: list[str],
    gamma_before: float,
    gamma_after: float,
    notes: str = "",
) -> dict[str, Any]:
    """Payload contract for membrane decision events."""
    return {
        "signal_fingerprint": signal_fingerprint,
        "signal_source": signal_source,
        "signal_type": signal_type,
        "route": route,
        "permeability": round(permeability, 6),
        "ethics_score": round(ethics_score, 6),
        "torsion_score": round(torsion_score, 6),
        "invariants": invariants,
        "warm_water": warm_water,
        "gamma_before": round(gamma_before, 6),
        "gamma_after": round(gamma_after, 6),
        "notes": notes,
    }


def invariant_violation_payload(
    *,
    signal_fingerprint: str,
    signal_source: str,
    violations: list[str],
    route: str,
    severity: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Payload contract for invariant violations."""
    payload = {
        "signal_fingerprint": signal_fingerprint,
        "signal_source": signal_source,
        "violations": violations,
        "route": route,
        "severity": severity,
    }
    if context:
        payload["context"] = context
    return payload


def audit_summary_payload(
    *,
    status: str,
    overall_health: float,
    gamma: float,
    critical_count: int,
    warning_count: int,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Payload contract for self-audit summary events."""
    return {
        "status": status,
        "overall_health": round(overall_health, 6),
        "gamma": round(gamma, 6),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "findings": findings,
    }
