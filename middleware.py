from __future__ import annotations
from typing import Any, Callable, Dict, Tuple
from .types import ProposedAction
from .evidence import EvidenceBundle
from .engine import AxiomEngine

class AxiomGate:
    """
    Wraps an executor function with deterministic axiom admission control.

    Usage:
        gate = AxiomGate(engine)
        result, receipt, output = gate.call(action, evidence, executor)
    """
    def __init__(self, engine: AxiomEngine):
        self.engine = engine

    def call(self, action: ProposedAction, evidence: EvidenceBundle, executor: Callable[[], Any]) -> Tuple[Dict[str, Any], Any]:
        result, receipt = self.engine.evaluate(action, evidence)
        if not result.admissible:
            return {
                "admissible": False,
                "result": result,
                "receipt": receipt,
            }, None

        output = executor()
        return {
            "admissible": True,
            "result": result,
            "receipt": receipt,
        }, output
