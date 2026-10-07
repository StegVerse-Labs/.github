# SDK-MANIFEST-IDENTITY-ROUTING-REGRESSION-GATE-001 — Mirror Handoff

Updated: 2026-10-07
Goal Task ID: `SDK-MANIFEST-IDENTITY-ROUTING-REGRESSION-GATE-001`
Parent Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
COSV ID: `71000000100125`
Status: `ACTIVE / CHECKED_OUT`

## Goal

Install ecosystem regression coverage that detects identity/source/provider/type-driven processor-selection shortcuts and manifest capability/route mismatch across representative actionable surfaces.

## Inherited invariants

- Every ACTION is a manifest-bound state transition.
- Processing semantics are selected only by admitted `processing.capability` + `processing.route_id` and installed route resolution.
- Terminal attempted-boundary disposition is `ALLOW | DENY | FAIL_CLOSED`.
- Organization ledger append is runtime reality when Organization state changes.
- Master Records is limited to organization records and reconstruction evidence and never gates Organization runtime reality.
- No external machine, listener, session, receiver liveness, hosted service, scheduler, or later observer may be awaited as a transition/completion predicate.
- Receiver unavailability follows `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`.

## Remaining predicates

- `IDENTITY_DRIVEN_PROCESSOR_SELECTION_REGRESSION_GATE_INSTALLED`

## Completion discipline

Close only from exact source/runtime evidence appropriate to each predicate. Source/CI/merge evidence must not be promoted to runtime execution. Preserve historical evidence and use registered exemptions only for genuine nonconformance that cannot be repaired; reachability is not an exemption justification.
