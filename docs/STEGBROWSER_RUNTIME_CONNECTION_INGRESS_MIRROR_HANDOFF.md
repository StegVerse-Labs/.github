# StegBrowser Runtime Connection Ingress Mirror Handoff

Updated: 2026-09-16

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Root lineage: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SINGLE A1-A4 INVOCATION COMPOSITION SOURCE RECONCILED / CURRENT-IPHONE INGRESS+EVENT-RUNTIME BRIDGE MERGED+VALIDATED / NATIVE NO-MANUAL OBSERVATION ROUTE RECONCILED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- External/second user-operated device required: `false`
- Manual user-device observation required: `false`

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

## Immutable invocation

The existing current-device page remains one admissible same-device execution surface:

```text
https://stegverse.org/stegos-bootstrap/canonical-work-runtime-consumption.html?autostart=1
```

It is not a user-operated evidence prerequisite. The immutable request remains exactly:

```text
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
invocation_request_nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested_invocation_count = 1
second_request_allowed = false
destination = StegBrowser:ManifestInvocation
```

Site PR `#1360` merged as `76af62f2befdfa7034d3dd00891bfe60a0990abb` and handoff reconciliation PR `#1361` merged as `7c483335f259d5eacf9a55dde923c0c4fefd660e`. They rebound the existing Node IndexedDB, write-once `intr_outbox`, root `/intr-service-worker.js`, and `CURRENT_USER_IPHONE_SERVICE_WORKER` to the immutable StegBrowser invocation without creating another request or runtime path.

The abandoned resident-dispatch transport branches remain non-gating and must not be reintroduced as prerequisites.

## EVENT_EPHEMERAL bridge — merged 2026-09-16

Site PR `#1363` repaired the source continuation gap where a successful same-invocation `INGRESS_ADMITTED` result previously stopped before the already-validated EVENT_EPHEMERAL materializer. After authentic admission, the launcher now reuses the exact same deterministic write-once Node outbox entry, loads the existing canonical `stegbrowser-manifest-runtime-binding.v1.json`, invokes only the existing `StegVerseStegBrowserManifestRuntime.materialize(...)`, binds admitted Node/Interlock/Receipt #1 identity, and returns only `RUNTIME_READY_FOR_WORKERCOORDINATOR` after the existing materializer proves bounded runtime readiness and execution-time runtime identity.

WorkerCoordinator claim/fence remains pending, A4 remains pending, completion remains false, and Round Trip 1 remains false. No second request, listener, service worker, scheduler, dispatcher, materializer, WorkerCoordinator, device, credential path, or GitHub runtime authority was introduced.

PR `#1363` exact validated head: `1e5350aa149ba707e756cd055f7132dadd95735c`.

```text
Validate StegOS Persistent Card UX = 35133005728 SUCCESS
Site Handoff Orchestrator = 35133005730 SUCCESS
Ecosystem Heartbeat Orchestration = 35133005818 SUCCESS
Site Bootstrap Validate - No Non-TV/TVC Credential Authority = 35133005757 SUCCESS
Node IndexedDB Schema Migration = 35133005896 SUCCESS
```

PR `#1363` merged as `8b032472d2861458daf2a1278fa3301d9a81a736` with expected-head protection. `.github` handoff reconciliation PR `#2017` merged as `369c6ba4bc78a64a330c89af9b66d4e233e1fd09` after exact-head Deterministic, Organization Control, and Heartbeat validation.

Source capability does not establish runtime execution.

## Native observation/custody reconciliation — 2026-09-16

A newer canonical descendant, `STEG-BROWSER-CURRENT-IPHONE-A1-A4-EXECUTION-001`, explicitly removes manual device observation as a prerequisite. Its canonical handoff states that the user is not required to open Safari, inspect IndexedDB/service-worker state, copy page JSON, or use a second device. The task must re-observe the existing registered Node/InTr runtime and canonical receipt paths directly.

The shared runtime evidence owner is `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`. The StegBrowser-native receipt reachability owner is `STEG-BROWSER-RESIDENT-RECEIPT-TRANSPORT-001`, whose selected substrate is `STEG-BROWSER-RETAINED-RESIDENT-NODE` with alternate eligible StegOS substrates and no external connector/device gate.

The existing production evidence path is:

```text
existing resident cycle
-> standing Healer carrier
-> neutral reusable scheduler
-> RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
-> admitted ephemeral StegOS / Canonical Work
-> authentic resident receipts retained under resident custody
-> merged non-authorizing receipt verifier
-> exact SHA/path/outcome binding
-> Master Records reconstruction where required
```

The already-merged verifier classifies authentic resident receipts only as `MISSING`, `INVALID`, or `VALID_BINDABLE`; it does not mint evidence.

Exact resident receipt targets remain:

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
receipts/sovereign-host/stegbrowser-runtime-consumption-evidence-custody.latest.json
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json
receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json
```

Current re-observation of accessible canonical custody/source surfaces has not exposed an authentic authority-owned receipt for the immutable nonce. The expected `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json` is not present in canonical repository custody, and source/CI absence or presence may not be converted into runtime proof.

Therefore the first unresolved authentic predicate remains the native receipt-surface/runtime observation itself:

```text
AUTHENTIC_STEGVERSE_NATIVE_RESIDENT_RECEIPT_SURFACE_OBSERVED = false
REGISTERED_STEGVERSE_NODE_BOUND_TO_INVOCATION = false
```

The authorized continuation is to inspect the existing StegVerse-native resident custody surface, classify any exact retained receipts with the already-merged verifier, bind `VALID_BINDABLE` evidence by exact SHA/path/outcome, or remediate the first concrete producer/retention/custody defect if classified `MISSING` or `INVALID`. Do not create another scheduler, dispatcher, runtime, credential route, evidence owner, physical-device dependency, or external connector path.

## Existing A3/A4 authority path

The newer execution child has collision-checked the existing continuation and found no competing StegBrowser WorkerCoordinator implementation:

```text
validated StegBrowser Node/Interlock/lease/runtime binding
-> workers/stegbrowser_manifest_intr_ingress.py
-> exact organization-local packet
-> scripts/refresh_and_execute_resident_task.py
-> ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001
-> fresh WorkerCoordinator fenced atomic checkout
-> ACCEPTED_LOCAL_BOUNDARY receipt
-> exact StegBrowser A4 correlation verification
```

WorkerCoordinator remains the sole A3 claim/fence authority. `workers/stegbrowser_manifest_intr_ingress.py` remains the A4 exact-correlation boundary. The generic SV001 portable WorkerCoordinator adapter is not an authority path for this invocation.

A3/A4 must not be invoked or promoted until authentic `RUNTIME_READY_FOR_WORKERCOORDINATOR` or equivalent exact same-invocation runtime evidence is retained.

## Authentic evidence state

No authority-owned same-invocation runtime evidence has been retained in canonical custody during this reconciliation. Therefore:

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

The merged page/source path can return authentic evidence through `RUNTIME_READY_FOR_WORKERCOORDINATOR`, but no predicate may be promoted without exact authority-owned retained evidence. WorkerCoordinator and A4 remain separately authority-owned transitions and may not be inferred.

## Authority invariants

- Task Registry: coordination only.
- Native resident dispatcher: discovery/dispatch only; no authority.
- A1 resolver: observation/selection only.
- Existing browser materializer: bounded EVENT_EPHEMERAL runtime materialization only; no claim/fence authority.
- WorkerCoordinator: A3 claim/fence authority.
- Interlock/InTr: A1 transition-state and A4 transition/ingress authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- Heartbeat: timing/reference/validation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- External connectors: not applicable to this evidence lane.
- Second user-operated device: prohibited as a prerequisite.

## Immediate continuation

Do not emit another request and do not require a user-operated device check. Continue through `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001` and `STEG-BROWSER-RESIDENT-RECEIPT-TRANSPORT-001` by re-observing only the existing StegVerse-native resident custody targets for the immutable nonce. If exact authentic receipts are `VALID_BINDABLE`, retain their SHA-256/path/outcome and promote only the predicates they directly prove. If the exact native receipt surface is `MISSING` or `INVALID`, identify and remediate only the first concrete existing producer/retention/custody defect. Only after authentic runtime readiness is retained may the existing WorkerCoordinator/A4 path run. Round Trip 1 remains prohibited until full A1-A4 completion is authentically proven.

## README review

README reviewed. No byte change is required because the runtime/authority topology remains the already-documented single StegVerse-native Universal InTr/event-ephemeral architecture; this reconciliation removes a stale manual-observation instruction and binds the child to already-canonical evidence owners.

## Manual work

None.
