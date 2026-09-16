# StegBrowser Runtime Connection Ingress Mirror Handoff

Updated: 2026-09-16

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Root lineage: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SINGLE A1-A4 INVOCATION COMPOSITION SOURCE RECONCILED / CURRENT-IPHONE INGRESS+EVENT-RUNTIME BRIDGE MERGED+VALIDATED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Scope and terminal boundary

This child owns the A1 observation/projection surface and composes A2 through A4 through the existing canonical StegBrowser reusable invocation. It does not implement a second lease, runtime materializer, WorkerCoordinator path, or A4 ingress worker and stops before Round Trip 1 payload processing.

```text
A1 authentic invocation-bound connection-state observation
-> resolve canonical registered StegVerse Node Receipt #1 input
-> A2 bind validated Node/Interlock to exact manifest invocation
-> A2.1 establish existing bounded invocation lease/state binding
-> A2.2 materialize existing EVENT_EPHEMERAL StegOS runtime
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

Source review found that the merged current-iPhone page stopped after authentic `INGRESS_ADMITTED` even though the already-validated StegBrowser EVENT_EPHEMERAL browser materializer from the SV002 adaptation was present. Therefore a successful page run could not reach the existing bounded runtime identity needed before WorkerCoordinator.

Site PR `#1363` repaired only that continuation gap. It does not add another runtime component. After authentic same-invocation `INGRESS_ADMITTED`, the launcher now:

1. reads the exact same deterministic write-once Node outbox entry;
2. loads the existing canonical `stegbrowser-manifest-runtime-binding.v1.json` route binding;
3. invokes the existing `StegVerseStegBrowserManifestRuntime.materialize(...)` component;
4. binds the runtime to the admitted Node ID, Interlock ID, and Receipt #1 hash;
5. returns only `RUNTIME_READY_FOR_WORKERCOORDINATOR` after the existing materializer proves `EVENT_EPHEMERAL` runtime readiness and execution-time runtime identity;
6. leaves WorkerCoordinator claim/fence pending, A4 pending, completion false, and Round Trip 1 false.

No second request, listener, service worker, scheduler, dispatcher, materializer, WorkerCoordinator, device, credential path, or GitHub runtime authority was introduced.

PR `#1363` exact validated head: `1e5350aa149ba707e756cd055f7132dadd95735c`.

Exact-head source-validation evidence:

```text
Validate StegOS Persistent Card UX = 35133005728 SUCCESS
Site Handoff Orchestrator = 35133005730 SUCCESS
Ecosystem Heartbeat Orchestration = 35133005818 SUCCESS
Site Bootstrap Validate - No Non-TV/TVC Credential Authority = 35133005757 SUCCESS
Node IndexedDB Schema Migration = 35133005896 SUCCESS
```

PR `#1363` merged as `8b032472d2861458daf2a1278fa3301d9a81a736` with expected-head protection.

This merge establishes source capability only. It does not establish that the current iPhone executed the Node binding, ingress, lease, EVENT_EPHEMERAL runtime, WorkerCoordinator, or A4 transitions.

## Authentic evidence state

No authority-owned same-invocation page/runtime evidence has yet been retained in canonical custody. Therefore current authentic state remains:

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

The merged page is now capable of returning authentic same-device evidence through `RUNTIME_READY_FOR_WORKERCOORDINATOR`. If such a result is returned, predicates through execution-time runtime identity may be promoted only from that exact result. WorkerCoordinator and A4 remain separately authority-owned transitions and may not be inferred.

Expected retained child observation remains `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json`. Expected canonical invocation boundary remains `receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json`.

## Authority invariants

- Task Registry: coordination only.
- Native resident dispatcher: discovery/dispatch only; no authority and not a prerequisite for the current same-iPhone path.
- A1 resolver: observation/selection only.
- Existing browser materializer: bounded EVENT_EPHEMERAL runtime materialization only; no claim/fence authority.
- WorkerCoordinator: A3 claim/fence authority.
- Interlock/InTr: A1 transition-state and A4 transition/ingress authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- Heartbeat: timing/reference/validation only.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.

## Current first unresolved predicate

`RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED` / `REGISTERED_STEGVERSE_NODE_BOUND_TO_INVOCATION` remains unresolved authentically until the current iPhone returns exact same-invocation JSON.

## Immediate continuation

Do not emit another request. On the same iPhone/Safari site-data context that owns registered StegVerse Node Receipt #1, open the existing current-device page with `autostart=1`. Preserve the complete displayed JSON or exact `FAIL_CLOSED` reason unchanged. A successful updated page is expected to stop at `RUNTIME_READY_FOR_WORKERCOORDINATOR`; promote only predicates directly evidenced by that same invocation and then continue only through the existing WorkerCoordinator/A4 authority path. Do not enter Round Trip 1 unless A1-A4 is fully authentic.

## README review

README reviewed. No byte change is required because the runtime/authority topology remains the already-documented single same-device Universal InTr/event-ephemeral architecture; PR #1363 only joins two existing validated pieces of that path.

## Manual work

On the same iPhone and Safari site-data context that owns the registered StegVerse Node, open `https://stegverse.org/stegos-bootstrap/canonical-work-runtime-consumption.html?autostart=1`. Do not use Private Browsing and do not clear site data. Return the complete page JSON or exact `FAIL_CLOSED` reason unchanged.
