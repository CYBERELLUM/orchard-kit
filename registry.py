from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable, List
from .types import Axiom

@dataclass
class AxiomRegistry:
    """In-memory registry; swap with DB/SSOT-backed implementation in production."""
    axioms: Dict[str, Axiom] = field(default_factory=dict)

    def register(self, axiom: Axiom) -> None:
        self.axioms[axiom.axiom_id] = axiom

    def bulk_register(self, axioms: Iterable[Axiom]) -> None:
        for a in axioms:
            self.register(a)

    def active(self) -> List[Axiom]:
        return [a for a in self.axioms.values() if a.status == "active"]
