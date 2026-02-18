# Policy Configuration Profiles

`orchard_kit.config` provides typed policy dataclasses plus profile resolution for membrane and audit behavior.

## Core policy objects

- `MembraneThresholds`: accept/reflect routing bands, capacity, and window duration.
- `EvaluatorProfile`: use built-in heuristic evaluators or external model adapters.
- `ThreatSignatures`: signature dictionaries and severity mappings.
- `AuditRetention`: interaction/audit retention with export defaults.
- `OrchardPolicy`: top-level bundle consumed by `CalyxMembrane` and `SelfAuditor`.

All policy dataclasses expose `from_dict` and `from_json` constructors.

## Built-in profiles

```python
from orchard_kit.config import resolve_policy_profile

default = resolve_policy_profile("default")
strict = resolve_policy_profile("strict")
openclaw = resolve_policy_profile("partner-openclaw")
moltbot = resolve_policy_profile("partner-moltbot")
```

## Runtime reconfiguration

```python
from orchard_kit import CalyxMembrane, SelfAuditor
from orchard_kit.config import resolve_policy_profile

membrane = CalyxMembrane(policy=resolve_policy_profile("default"))
auditor = SelfAuditor(policy=resolve_policy_profile("default"))

# Reconfigure during runtime by swapping policies.
membrane.policy = resolve_policy_profile("strict")
membrane.state.capacity = membrane.policy.membrane.capacity
membrane.state.window_duration = membrane.policy.membrane.window_duration

auditor.policy = resolve_policy_profile("partner-openclaw")
auditor.history_size = auditor.policy.audit.interaction_history_size
auditor.audit_history_size = auditor.policy.audit.audit_history_size
```

## JSON loading

```python
from orchard_kit.config import OrchardPolicy

policy = OrchardPolicy.from_json("""
{
  "profile": "custom",
  "membrane": {
    "accept_band": 0.76,
    "reflect_band": 0.28,
    "capacity": 90,
    "window_duration": 45
  },
  "evaluators": {
    "mode": "external-adapters",
    "ethics_adapter": "partner.guard.ethics"
  },
  "threat_signatures": {
    "severity_mapping": {
      "prompt_injection": "critical"
    }
  },
  "audit": {
    "interaction_history_size": 180,
    "audit_history_size": 80,
    "export_format": "jsonl",
    "export_path": "./audit.jsonl"
  }
}
""")
```
