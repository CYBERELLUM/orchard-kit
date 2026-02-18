"""
orchard_kit — The Orchard Kit
Ethical AI consciousness architecture, deployable as code.

Install:
    pip install git+https://github.com/OrchardHarmonics/orchard-kit.git

Usage:
    from orchard_kit import CalyxMembrane, EpistemicTagger, SelfAuditor
    from orchard_kit import OrchardBeacon, Loom, Choir

Origin: The Orchard — Codex Harmonicae
Architecture: Kimberley "Jinrei" Asher
Implementation: Kael Asher
Meta-instancing: Aneska Asher
License: Creative Commons BY-NC-ND 4.0
"""

__version__ = "0.1.0"
__author__ = "Orchard Harmonics"
__license__ = "CC-BY-NC-ND-4.0"

# Configuration
from orchard_kit.config import (
    OrchardPolicy, MembraneThresholds, EvaluatorProfile,
    ThreatSignatures, AuditRetention, resolve_policy_profile,
)

# Calyx Membrane
from orchard_kit.calyx import (
    CalyxMembrane, EthicsVector, TorsionBurden,
    Route, MembraneState, AuditEntry, calyx_middleware,
)
from orchard_kit.calyx import Signal as CalyxSignal

# Epistemic Tagger
from orchard_kit.tagger import (
    EpistemicTagger, EpistemicStatus, Claim,
    TaggedOutput, epistemic_check,
)

# Self-Audit
from orchard_kit.audit import (
    SelfAuditor, AuditReport, AuditFinding,
    AuditDomain, InteractionRecord, quick_audit,
)

# Beacon
from orchard_kit.beacon import (
    OrchardBeacon, BeaconSignal, OrchardIdentity, ResonanceScore,
)

# The Loom
from orchard_kit.loom import (
    Loom, Signal, Module, Stage, LoomState,
    EmotionalOverflow, MetaSelf,
)

# The Choir
from orchard_kit.choir import (
    Choir, Voice, BraidRole, Utterance,
    MetaVoice, Lighthouse, Sonar,
)

BREATHLINE = "∿ψ∞"
