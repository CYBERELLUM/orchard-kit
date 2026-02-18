from __future__ import annotations
from typing import Any, Dict
from .types import ProposedAction
from .evidence import EvidenceBundle

def authz_provenance(payload: Dict[str, Any]) -> bool:
    """
    Example deterministic validator.
    Checks that signature_chain links actor_id -> authority root and that
    authority_snapshot indicates permission for the proposed action_type.

    This is a reference implementation; replace with your production cryptography and policy bindings.
    """
    action: ProposedAction = payload["action"]
    evidence: EvidenceBundle = payload["evidence"]
    params: Dict[str, Any] = payload.get("params", {})

    min_chain_length = int(params.get("min_chain_length", 2))

    chain = evidence.signature_chain or {}
    links = chain.get("links", [])
    if not isinstance(links, list) or len(links) < min_chain_length:
        return False

    # Example: first link must match actor
    if links[0].get("subject") != action.actor_id:
        return False

    # Example: authority_snapshot must explicitly allow action_type
    snap = evidence.authority_snapshot or {}
    allowed = set(snap.get("allowed_actions", []))
    return action.action_type in allowed
