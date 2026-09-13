# SDK WorkSpace External-Collaboration Component Applicability Reconciliation

Goal Task: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
COSV: `71000000100110`
Model: `data/reusable-task-component-model.json`
Runtime truth: `docs/SDK_WORKSPACE_EXTCOLLAB_AUTHENTIC_RUNTIME_004_MIRROR_HANDOFF.md`

This projection narrows two applicability points in the already-merged component reconciliation without changing Goal identity, runtime truth, or completion predicates.

1. Owner-present external-provider consent is not a generic transport round trip. It remains a credential/session step: KV/SKAP Vault supplies the canonical user-verification authority and TV/TVC retains provider/session authority. The existing transport component remains responsible only for any actual governed data movement around that event.

2. `RTC-STEGVERSE-EGRESS-007`, `RTC-INTERLOCK-INTR-TRANSPORT-008`, and `RTC-FARSIDE-FINAL-009` are conditional per target. They are composed only when the applicable downstream route requires those transitions. The maximal transport chain is not mandatory for every target.

The reusable governed-round-trip component remains repeatable for the actual request/response stages: resident reseal, resident listener, sovereign callback, and authoritative provider probe.

No new reusable component is created. No authority is moved into component composition. No runtime evidence is created or upgraded.

The obsolete unmerged PR #1578 was closed because its persistent carrier/WorkerCoordinator self-heal framing conflicts with canonical ephemeral lifecycle semantics. Historical provenance is preserved.

Next admissible work remains the existing runtime-observation/runtime-resolution composition. Only authentic current runtime evidence may unlock the resident operations.
