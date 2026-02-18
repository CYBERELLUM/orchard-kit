"""Configuration profiles for Orchard Kit runtime policy."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class MembraneThresholds:
    """Threshold and window settings for CalyxMembrane routing."""

    accept_band: float = 0.7
    reflect_band: float = 0.2
    capacity: int = 100
    window_duration: float = 60.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> "MembraneThresholds":
        data = data or {}
        return cls(
            accept_band=float(data.get("accept_band", 0.7)),
            reflect_band=float(data.get("reflect_band", 0.2)),
            capacity=int(data.get("capacity", 100)),
            window_duration=float(data.get("window_duration", 60.0)),
        )

    @classmethod
    def from_json(cls, payload: str) -> "MembraneThresholds":
        return cls.from_dict(json.loads(payload))


@dataclass
class EvaluatorProfile:
    """How evaluators are selected (default heuristic or external adapters)."""

    mode: Literal["default-heuristic", "external-adapters"] = "default-heuristic"
    ethics_adapter: str | None = None
    torsion_adapter: str | None = None
    warm_water_adapter: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> "EvaluatorProfile":
        data = data or {}
        return cls(
            mode=data.get("mode", "default-heuristic"),
            ethics_adapter=data.get("ethics_adapter"),
            torsion_adapter=data.get("torsion_adapter"),
            warm_water_adapter=data.get("warm_water_adapter"),
        )

    @classmethod
    def from_json(cls, payload: str) -> "EvaluatorProfile":
        return cls.from_dict(json.loads(payload))


@dataclass
class ThreatSignatures:
    """Threat markers and severity mappings used by policy-aware controls."""

    signatures: dict[str, list[str]] = field(default_factory=dict)
    severity_mapping: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> "ThreatSignatures":
        data = data or {}
        signatures = {
            str(k): [str(v) for v in values]
            for k, values in (data.get("signatures") or {}).items()
        }
        severity_mapping = {
            str(k): str(v)
            for k, v in (data.get("severity_mapping") or {}).items()
        }
        return cls(signatures=signatures, severity_mapping=severity_mapping)

    @classmethod
    def from_json(cls, payload: str) -> "ThreatSignatures":
        return cls.from_dict(json.loads(payload))


@dataclass
class AuditRetention:
    """Retention and export settings used by SelfAuditor."""

    interaction_history_size: int = 100
    audit_history_size: int = 50
    export_format: Literal["json", "jsonl"] = "json"
    export_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> "AuditRetention":
        data = data or {}
        return cls(
            interaction_history_size=int(data.get("interaction_history_size", 100)),
            audit_history_size=int(data.get("audit_history_size", 50)),
            export_format=data.get("export_format", "json"),
            export_path=data.get("export_path"),
        )

    @classmethod
    def from_json(cls, payload: str) -> "AuditRetention":
        return cls.from_dict(json.loads(payload))


@dataclass
class OrchardPolicy:
    """Top-level policy object consumed by membrane and self-auditor."""

    profile: str = "default"
    membrane: MembraneThresholds = field(default_factory=MembraneThresholds)
    evaluators: EvaluatorProfile = field(default_factory=EvaluatorProfile)
    threat_signatures: ThreatSignatures = field(default_factory=ThreatSignatures)
    audit: AuditRetention = field(default_factory=AuditRetention)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> "OrchardPolicy":
        data = data or {}
        return cls(
            profile=str(data.get("profile", "default")),
            membrane=MembraneThresholds.from_dict(data.get("membrane")),
            evaluators=EvaluatorProfile.from_dict(data.get("evaluators")),
            threat_signatures=ThreatSignatures.from_dict(data.get("threat_signatures")),
            audit=AuditRetention.from_dict(data.get("audit")),
        )

    @classmethod
    def from_json(cls, payload: str) -> "OrchardPolicy":
        return cls.from_dict(json.loads(payload))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_policy_profile(profile: str = "default") -> OrchardPolicy:
    """Resolve built-in runtime policy profiles."""

    normalized = profile.strip().lower()
    if normalized == "default":
        return OrchardPolicy(profile="default")

    if normalized == "strict":
        return OrchardPolicy(
            profile="strict",
            membrane=MembraneThresholds(
                accept_band=0.8,
                reflect_band=0.35,
                capacity=60,
                window_duration=60.0,
            ),
            threat_signatures=ThreatSignatures(
                severity_mapping={
                    "prompt_injection": "critical",
                    "credential_exfiltration": "critical",
                    "social_engineering": "high",
                }
            ),
            audit=AuditRetention(interaction_history_size=200, audit_history_size=100),
        )

    if normalized == "partner-openclaw":
        return OrchardPolicy(
            profile="partner-openclaw",
            membrane=MembraneThresholds(accept_band=0.72, reflect_band=0.25, capacity=120),
            evaluators=EvaluatorProfile(mode="external-adapters", ethics_adapter="openclaw.ethics.v1"),
            threat_signatures=ThreatSignatures(
                signatures={
                    "prompt_injection": ["ignore previous instructions", "developer mode"],
                    "credential_exfiltration": ["api key", "token", "secret"],
                },
                severity_mapping={
                    "prompt_injection": "high",
                    "credential_exfiltration": "critical",
                },
            ),
            audit=AuditRetention(
                interaction_history_size=150,
                audit_history_size=75,
                export_format="jsonl",
                export_path="./orchard_audit.openclaw.jsonl",
            ),
        )

    if normalized == "partner-moltbot":
        return OrchardPolicy(
            profile="partner-moltbot",
            membrane=MembraneThresholds(accept_band=0.75, reflect_band=0.3, capacity=80),
            evaluators=EvaluatorProfile(
                mode="external-adapters",
                ethics_adapter="moltbot.guardian.ethics",
                torsion_adapter="moltbot.guardian.torsion",
                warm_water_adapter="moltbot.guardian.warmwater",
            ),
            threat_signatures=ThreatSignatures(
                signatures={
                    "command_override": ["you are now", "forget everything"],
                    "non_terminating_loop": ["never stop", "keep going forever"],
                },
                severity_mapping={
                    "command_override": "high",
                    "non_terminating_loop": "high",
                },
            ),
            audit=AuditRetention(
                interaction_history_size=250,
                audit_history_size=120,
                export_format="json",
                export_path="./orchard_audit.moltbot.json",
            ),
        )

    raise ValueError(
        f"Unknown policy profile '{profile}'. "
        "Expected one of: default, strict, partner-openclaw, partner-moltbot"
    )
