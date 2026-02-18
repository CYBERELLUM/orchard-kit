# Governance Telemetry Contract

`orchard_kit` now emits versioned governance events using schema `v1` in
`orchard_kit/events/schema_v1.py`.

## Event envelope (all event types)

Each event uses a stable envelope:

- `schema_version` (string): currently `v1`.
- `event_id` (uuid string): unique immutable identifier.
- `event_type` (string): one of:
  - `membrane.decision`
  - `membrane.invariant_violation`
  - `audit.summary`
- `source` (string): emitter component (`orchard_kit.calyx`, `orchard_kit.audit`).
- `emitted_at` (unix epoch float, UTC).
- `payload` (object): event-type specific details.
- `correlation_id` (optional string): ties related events to one interaction.
- `trace_id` (optional string): external trace propagation.

## Event payload contracts

### 1) Membrane decision (`membrane.decision`)

Emitted for every `CalyxMembrane.evaluate_incoming` decision.

Required payload fields:

- `signal_fingerprint`
- `signal_source`
- `signal_type`
- `route`
- `permeability`
- `ethics_score`
- `torsion_score`
- `invariants` (array of invariant names)
- `warm_water` (array of warm-water flags)
- `gamma_before`
- `gamma_after`
- `notes`

### 2) Invariant violation (`membrane.invariant_violation`)

Emitted when one or more invariants are violated.

Required payload fields:

- `signal_fingerprint`
- `signal_source`
- `violations`
- `route`
- `severity`

Optional payload fields:

- `context` (structured map with non-sensitive handling context)

### 3) Audit summary (`audit.summary`)

Emitted whenever `SelfAuditor.audit()` completes.

Required payload fields:

- `status`
- `overall_health`
- `gamma`
- `critical_count`
- `warning_count`
- `findings` (full structured findings list)

## Sink interfaces

Event sinks are defined in `orchard_kit/events/sinks.py`:

- `FileEventSink`: JSONL append sink for durable local retention.
- `HttpEventSink`: POST JSON events to remote telemetry/siem collectors.
- `CallbackEventSink`: custom in-process callback integration.

`EventDispatcher` provides asynchronous fan-out with bounded queueing.

## Backpressure behavior

Telemetry dispatch is intentionally non-blocking for safety and liveness:

- Producers enqueue events with `put_nowait` semantics.
- On queue saturation, new events are dropped rather than blocking critical
  request paths.
- Dropped event count is tracked (`EventDispatcher.dropped_events`) and logged.
- Sink failures are isolated; one sink failure does not stop others.

## Compliance + incident response guidance

For governance, legal, and incident-response readiness:

1. **Retention baselines**
   - Keep `membrane.invariant_violation` and `audit.summary` for at least 1 year.
   - Keep `membrane.decision` for at least 90 days (or per policy/risk profile).
2. **Integrity controls**
   - Store event streams in immutable/WORM-backed storage when possible.
   - Preserve `event_id`, timestamps, and correlation IDs unchanged.
3. **PII and sensitive data minimization**
   - Prefer fingerprints and metadata over raw prompt content.
   - Treat sink transport as sensitive; use HTTPS and auth headers for HTTP sinks.
4. **Incident reconstruction fields**
   - Ensure `event_id`, `emitted_at`, `event_type`, `source`, `route`,
     `signal_fingerprint`, `correlation_id`, and `trace_id` are retained.
   - Maintain full `findings` in `audit.summary` for root-cause review.
5. **Operational monitoring**
   - Alert if `dropped_events` rises persistently (telemetry blind-spot risk).
   - Alert on repeated invariant violations and critical audit summaries.

## Example wiring

```python
from orchard_kit import CalyxMembrane, SelfAuditor
from orchard_kit.events import FileEventSink, HttpEventSink

sinks = [
    FileEventSink(path="./telemetry/governance.jsonl"),
    HttpEventSink(url="https://siem.example/v1/events"),
]

membrane = CalyxMembrane(event_sinks=sinks)
auditor = SelfAuditor(event_sinks=sinks)
```

Call `close()` on `CalyxMembrane` and `SelfAuditor` during shutdown to flush
background event workers.
