from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class EvidenceBundle:
    """
    EvidenceBundle is the machine-checked payload that allows ACIP to prove
    why an action was admitted or vetoed. It is NOT a post-hoc log; it is an
    admissibility artifact.
    """
    signature_chain: Optional[Dict[str, Any]] = None
    authority_snapshot: Optional[Dict[str, Any]] = None
    intent_hash: Optional[str] = None
    state_delta_hash: Optional[str] = None
    receipt_hash: Optional[str] = None
    attestation: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    trace_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def has(self, artifact: str) -> bool:
        return getattr(self, artifact, None) is not None or artifact in self.extra

    def missing(self, required_artifacts) -> list[str]:
        return [a for a in required_artifacts if not self.has(a)]
