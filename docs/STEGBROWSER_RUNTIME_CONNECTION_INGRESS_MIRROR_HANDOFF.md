# StegBrowser Runtime Connection Ingress Mirror Handoff

Updated: 2026-09-17

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Root lineage: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SV002 EXECUTION LINEAGE REUSED / SV002-STYLE NODE-JOURNAL RETENTION MERGED+VALIDATED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Scope and terminal boundary

This child owns the A1 observation/projection surface and composes A2 through A4 through the existing canonical StegBrowser reusable invocation. It does not implement a second lease, runtime materializer, WorkerCoordinator path, or A4 ingress worker and stops before Round Trip 1 payload processing.

```text
A1 authentic invocation-bound connection-state observation
-> resolve canonical registered StegVerse Node Receipt #1 input
-> A2 bind validated Node/Interlock to exact manifest invocation
-> A2.1 establish existing bounded invocation lease/state binding
-> A2.2 materialize existing EVENT_EPHEMERAL StegOS runtime
-> retain exact runtime-readiness evidence through existing Node continuity journal
-> A3 existing organization-local WorkerCoordinator claim/fence
-> A4 existing exact manifest Interlock/InTr ingress
-> STOP CHILD / handoff to Round Trip 1 owner
```

## Canonical Node-binding representation

There is one concrete Node Receipt #1 input contract:

```text
parameter: node_genesis_receipt
environment: STEGVERSE_NODE_GENESIS_RECEIPT
schema: stegos.node_handoff_receipt.v1
receipt_number: 1
validator: StegOS stegos.network_manifold.validate_node_genesis_receipt
```

`CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING` is a selector name only. It is not a second receipt schema, path format, Node identity, or authority source. A plain `stegverse.sovereign-node-declaration/v0.4` declaration may not be promoted or inferred into Receipt #1. No external runtime/device/host discovery is permitted or performed.

## A1

The child reuses the existing shared Universal InTr profile and resolver. `callable`, `refreshable`, and `applicable_protocol_resolved` remain invocation-bound transition variables under Interlock/InTr; none are persistent source/runtime properties.

```text
callable=false -> no execution materialization
callable=true AND refreshable=true -> RT-SOVEREIGN-SOURCE-REFRESH-001
callable=true AND refreshable=false -> no refresh task
callable=true AND applicable_protocol_resolved=false -> RT-INTR-PROTOCOL-ESTABLISH-001
callable=true AND applicable_protocol_resolved=true -> continue through canonical Node-bound StegBrowser invocation
```

## A2 through A4 — single execution owner

The one execution owner remains `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` through `scripts/run_stegbrowser_manifest_bound_runtime.py`. The existing path validates the manifest and Receipt #1, binds exact Node/Interlock/registration state, establishes the bounded invocation lease, materializes the existing `EVENT_EPHEMERAL` runtime, retains execution-time identity, continues through existing WorkerCoordinator claim/fence, verifies exact A4 correlation, and stops before Round Trip 1.

Explicit predicates remain:

```text
A2.1: INVOCATION_SCOPED_LEASE_ESTABLISHED
A2.1: INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
A2.1: INTR_MATERIALIZATION_ADMITTED
A2.2: EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
A2.2: EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
A3: CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
A4: ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
A4: INTR_ADMISSION_OBSERVED
```

## Immutable current-iPhone invocation

The authorized same-device execution surface remains:

```text
https://stegverse.org/stegos-bootstrap/canonical-work-runtime-consumption.html?autostart=1
```

The immutable request remains exactly:

```text
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
invocation_request_nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested_invocation_count = 1
second_request_allowed = false
destination = StegBrowser:ManifestInvocation
```

Site PR `#1360` merged as `76af62f2befdfa7034d3dd00891bfe60a0990abb` and handoff reconciliation PR `#1361` merged as `7c483335f259d5eacf9a55dde923c0c4fefd660e`. They rebound the existing current-iPhone Node IndexedDB, write-once `intr_outbox`, root `/intr-service-worker.js`, and `CURRENT_USER_IPHONE_SERVICE_WORKER` to the immutable StegBrowser invocation without creating another request or runtime path.

The abandoned resident-dispatch transport branches remain non-gating and must not be reintroduced as prerequisites.

## Current-iPhone EVENT_EPHEMERAL bridge — merged 2026-09-16

Site PR `#1363` repaired the source continuation gap after authentic `INGRESS_ADMITTED` by invoking the already-existing SV002-derived `StegVerseStegBrowserManifestRuntime.materialize(...)` component. It retained the same deterministic write-once Node outbox entry, exact Node/Interlock/Receipt #1 binding, and returned only `RUNTIME_READY_FOR_WORKERCOORDINATOR` while keeping WorkerCoordinator claim/fence, A4, completion, and Round Trip 1 pending.

PR `#1363` exact validated head: `1e5350aa149ba707e756cd055f7132dadd95735c`.

```text
Validate StegOS Persistent Card UX = 35133005728 SUCCESS
Site Handoff Orchestrator = 35133005730 SUCCESS
Ecosystem Heartbeat Orchestration = 35133005818 SUCCESS
Site Bootstrap Validate - No Non-TV/TVC Credential Authority = 35133005757 SUCCESS
Node IndexedDB Schema Migration = 35133005896 SUCCESS
```

PR `#1363` merged as `8b032472d2861458daf2a1278fa3301d9a81a736` with expected-head protection.

This established source capability only, not runtime evidence.

## Explicit reconciliation with the proven StegVerse-002 route — 2026-09-17

Direct comparison against the proven Site SV002 browser lane confirms coincidence through:

```text
registered StegVerse Node
-> Interlock / Universal InTr materialization
-> bounded invocation lease
-> EVENT_EPHEMERAL browser Web Worker
-> execution-time runtime identity
```

The first StegBrowser-specific divergence was not execution. It was evidence retention after runtime readiness.

The proven SV002 lane retains post-materialization runtime evidence through the established `StegVerseNodeContinuity.recordStep(...)` Node continuity journal. Before Site PR `#1370`, StegBrowser produced a hashed `RUNTIME_READY_FOR_WORKERCOORDINATOR` readiness receipt but retained it only in page/local browser state.

This is classified as an `EVIDENCE_RETENTION_BINDING_DEFECT`, not an execution-path defect.

## SV002-style Node-journal retention repair — merged 2026-09-17

Site PR `#1370` reuses the existing SV002 Node continuity mechanism without changing any execution component. After and only after an authentic `RUNTIME_READY_FOR_WORKERCOORDINATOR` result, the current-iPhone page now appends one existing Node continuity journal step:

```text
capability = stegbrowser-manifest-runtime
step = runtime-ready
resulting_state = OBSERVED
evidence_ref schema = stegbrowser-runtime-readiness/v1
```

The evidence reference binds exactly:

```text
readiness receipt sha256
immutable invocation nonce
Node ID
Interlock ID
Receipt #1 sha256
lease ID
runtime ID
```

The retention operation fails closed if those exact correlations are absent. The retained page-side projection marks:

```text
state = RETAINED_BEFORE_A3
authority_effect = NONE_EVIDENCE_RETENTION_ONLY
workercoordinator_claim_pending = true
workercoordinator_fence_pending = true
```

No new Worker, service worker, scheduler, dispatcher, materializer, WorkerCoordinator, runtime path, credential path, request, or device dependency was introduced.

Site PR `#1370` exact validated head: `d2cf9656ed25d7e4642092c40a5f150b08805e9b`.

Exact-head validation:

```text
Validate StegOS Persistent Card UX = 35231083246 SUCCESS
Node IndexedDB Schema Migration = 35231083295 SUCCESS
Ecosystem Heartbeat Orchestration = 35231083218 SUCCESS
Site Handoff Orchestrator = 35231083625 SUCCESS
Site Bootstrap Validate - No Non-TV/TVC Credential Authority = 35231083363 SUCCESS
```

PR `#1370` merged with expected-head protection as `8bb773d230b33bdeac9a7cec3ff5d9fdb07812be`.

README was reviewed in Site. No byte change was required because this repair changes no public/runtime authority topology and reuses the already-existing Node continuity journal.

## Authentic evidence state

Source, CI, merge, page publication, and journal capability do not promote runtime predicates. The expected canonical retained A1-A4 receipt remains absent from repository-accessible custody after the Site merge.

Current authentic state therefore remains:

```text
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = false
STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INTR_MATERIALIZATION_ADMITTED = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
INTR_ADMISSION_OBSERVED = false
ROUND_TRIP_1_STARTED = false
```

Expected retained child observation remains:

`receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json`

Expected canonical invocation boundary remains:

`receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json`

No runtime predicate may be promoted from the Site merge or from the mere existence of the Node-journal retention code.

## Authority invariants

- Task Registry: coordination only.
- Native resident dispatcher: discovery/dispatch only; no authority and not a prerequisite for the current same-iPhone path.
- A1 resolver: observation/selection only.
- Existing browser materializer: bounded EVENT_EPHEMERAL runtime materialization only; no claim/fence authority.
- Existing Node continuity journal: evidence retention only; no execution or claim/fence authority.
- WorkerCoordinator: A3 claim/fence authority.
- Interlock/InTr: A1 transition-state and A4 transition/ingress authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- Heartbeat: timing/reference/validation only.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.

## Current first unresolved authentic predicate

The first unresolved authentic state remains the same-invocation retained observation proving the Node/Interlock/ingress/runtime chain. The source-side retention defect that previously prevented durable parity with SV002 is repaired, but no retained execution result has yet been observed through canonical evidence custody.

## Immediate continuation

Do not emit another request and do not require a standing or manually checked device. Re-observe only through the existing authorized same-invocation evidence surfaces. If an exact retained `stegbrowser-runtime-readiness/v1` Node-journal entry becomes observable for immutable nonce `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z`, bind only the exact correlated Node/Interlock/Receipt #1/lease/runtime evidence it proves. Continue to A3 only through the existing WorkerCoordinator claim/fence authority and to A4 only through the existing exact governed StegBrowser ingress. Do not enter Round Trip 1 until the full A1-A4 chain is authentically retained and correlated.

## README review

README reviewed. No byte change is required because the runtime/authority topology remains the already-documented single same-device Universal InTr/event-ephemeral architecture; the new Site repair only reuses the existing SV002-proven Node continuity journal for evidence retention.

## Manual work

None.
