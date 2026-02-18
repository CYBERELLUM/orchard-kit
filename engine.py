from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .types import Axiom, EvaluationResult, ProposedAction
from .registry import AxiomRegistry
from .evidence import EvidenceBundle
from .receipts import GovernanceReceipt, sha256_hex

@dataclass
class AxiomEngine:
    """
    Deterministic Axiom evaluation engine.
    - Evaluates evidence requirements
    - Evaluates mechanized (deterministic) validators
    - Produces a governance receipt payload
    """
    registry: AxiomRegistry

    def evaluate(self, action: ProposedAction, evidence: EvidenceBundle) -> Tuple[EvaluationResult, GovernanceReceipt]:
        violated: List[str] = []
        failure_actions: List[str] = []
        missing_evidence: List[str] = []
        max_severity = "low"

        for ax in self.registry.active():
            # Evidence presence check
            miss = evidence.missing(ax.evidence.required_artifacts)
            if miss:
                violated.append(ax.axiom_id)
                missing_evidence.extend([f"{ax.axiom_id}:{m}" for m in miss])
                failure_actions.extend([fa.value for fa in ax.enforcement.failure_actions])
                max_severity = self._max_severity(max_severity, ax.enforcement.severity.value)
                continue

            # Mechanized validator check (optional)
            if ax.mechanization_validator is not None:
                ok = bool(ax.mechanization_validator({
                    "action": action,
                    "evidence": evidence,
                    "params": ax.mechanization_params,
                }))
                if not ok:
                    violated.append(ax.axiom_id)
                    failure_actions.extend([fa.value for fa in ax.enforcement.failure_actions])
                    max_severity = self._max_severity(max_severity, ax.enforcement.severity.value)

        admissible = len(violated) == 0
        decision = "admit" if admissible else "veto"

        # Evidence hash for receipt binding
        ev_payload = self._evidence_payload(evidence)
        evidence_hash = sha256_hex(json.dumps(ev_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))

        receipt_payload: Dict[str, Any] = {
            "trace_id": action.trace_id,
            "actor_id": action.actor_id,
            "action_type": action.action_type,
            "decision": decision,
            "violated_axioms": sorted(list(set(violated))),
            "evidence_hash": evidence_hash,
        }
        receipt = GovernanceReceipt.from_payload(receipt_payload)

        result = EvaluationResult(
            admissible=admissible,
            violated_axioms=receipt_payload["violated_axioms"],
            failure_actions=sorted(list(set(failure_actions))),
            severity=max_severity,
            evidence_missing=sorted(list(set(missing_evidence))),
        )
        return result, receipt

    @staticmethod
    def _evidence_payload(e: EvidenceBundle) -> Dict[str, Any]:
        # Keep receipt-stable: only include canonical fields + extra
        return {
            "signature_chain": e.signature_chain,
            "authority_snapshot": e.authority_snapshot,
            "intent_hash": e.intent_hash,
            "state_delta_hash": e.state_delta_hash,
            "receipt_hash": e.receipt_hash,
            "attestation": e.attestation,
            "timestamp": e.timestamp,
            "trace_id": e.trace_id,
            "extra": e.extra,
        }

    @staticmethod
    def _max_severity(a: str, b: str) -> str:
        order = {"low":0,"medium":1,"high":2,"critical":3}
        return a if order[a] >= order[b] else b
