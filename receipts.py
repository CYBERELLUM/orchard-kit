from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from typing import Any, Dict, List

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@dataclass(frozen=True)
class GovernanceReceipt:
    """
    Immutable receipt proving the admission decision.
    In production, bind this to your cryptographic anchoring / SSOT layer.
    """
    trace_id: str
    actor_id: str
    action_type: str
    decision: str  # "admit" | "veto"
    violated_axioms: List[str]
    evidence_hash: str
    decision_hash: str

    @staticmethod
    def from_payload(payload: Dict[str, Any]) -> "GovernanceReceipt":
        b = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        decision_hash = sha256_hex(b)
        return GovernanceReceipt(
            trace_id=payload["trace_id"],
            actor_id=payload["actor_id"],
            action_type=payload["action_type"],
            decision=payload["decision"],
            violated_axioms=payload.get("violated_axioms", []),
            evidence_hash=payload["evidence_hash"],
            decision_hash=decision_hash,
        )
