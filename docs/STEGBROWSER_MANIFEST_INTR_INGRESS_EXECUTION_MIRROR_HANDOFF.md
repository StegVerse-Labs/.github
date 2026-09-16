# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-16
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SINGLE CANONICAL UNIVERSAL-INTR BINDING MERGED+VALIDATED / SV002 SITE BASELINE AND STEGBROWSER ADAPTATION MERGED+VALIDATED / RESIDENT NODE-BINDING TRANSPORT REPAIR PR #1998 IN VALIDATION / AUTHENTIC A1-A4 EXECUTION PENDING`
- Current exact condition: `AUTHENTIC_STEGBROWSER_UNIVERSAL_INTR_A1_A4_EXECUTION_NOT_YET_OBSERVED`

## Canonical source history

The retained StegBrowser-specific route remains the single PR #1955 `StegBrowser:ManifestInvocation` representation. PR #1960's overlapping alternate representation was retired by corrective convergence PR #1964 and must not be reintroduced.

Reusable execution-baseline reconciliation is complete:

- `.github` PR #1966 exact validated head `6edba060692e275361f9d8be8d17b5ad21158711`.
- #1966 validation: Organization Control `35092566189`, Deterministic Suite `35092566222`, Heartbeat `35092566216` — all SUCCESS.
- #1966 merged as `94b8804687baed9251b4e6ecbb640f14c7259dc6`.
- Site SV002 baseline retest PR #1354 exact validated head `0ae6bbd252741599c7cab06746f274b901d2e455`; focused validation `34993797222`, Site Bootstrap `34993797221`, Site Handoff Orchestrator `34993797281`, and Ecosystem Heartbeat `34993797195` all SUCCESS.
- Site PR #1354 merged as `a8846026bc80b9890c07ad72dda1350ce7f3c0d4`.

The bounded StegBrowser Site adaptation is now also merged:

- Site PR #1358 copied the already-validated SV002 browser-runtime mechanics and changed only the current StegBrowser Goal/COSV/manifest/payload/owned-mirror bindings.
- Final exact head: `d3ec3416f95d84df723bd70f904ebb2e29bef8cb`.
- Exact-head validations: StegBrowser SV002 Lane Adaptation `35093634436` SUCCESS; StegBrowser SV002 Validated Lane Retest `35093634409` SUCCESS; Site Bootstrap `35093634412` SUCCESS; Site Handoff Orchestrator `35093634346` SUCCESS; Ecosystem Heartbeat `35093634408` SUCCESS.
- Site PR #1358 merged as `64dcbb8803dae67d96d33849d92f45fb1206d57e`.
- The earlier PR #1354 validation claim was terminalized with its actual PR/merge evidence before #1358 final validation, eliminating the task/dependency-surface collision without changing runtime code.

## Canonical architecture

Preserve this single execution path:

```text
valid registered StegVerse Node
-> exact immutable one-shot invocation payload
-> stegverse.universal-intr-transport/v1
-> stegverse.universal-intr-materialization-request/v1
-> Node-bound write-once InTr outbox trigger
-> existing shared /intr/materialization ingress
-> write-once INGRESS_ADMITTED receipt
-> bounded invocation lease/state binding
-> self-contained EVENT_EPHEMERAL browser Web Worker runtime
-> execution-time runtime identity
-> existing WorkerCoordinator claim/fence
-> exact governed StegBrowser A4 ingress
-> Round Trip 1 only after authentic A1-A4 evidence
```

No control-plane source-package relay, resident-request sweep, external runtime/device/host discovery, second listener, second scheduler, second dispatcher, second materializer, second WorkerCoordinator, or second user-operated device is a prerequisite.

## Site adaptation bindings

Merged Site artifacts from PR #1358:

- `assets/stegbrowser-manifest-runtime-materializer.js`
- `data/stegbrowser-manifest-runtime-binding.v1.json`
- `tests/test_stegbrowser_sv002_lane_adaptation.py`
- `.github/workflows/stegbrowser-sv002-lane-adaptation.yml`
- `docs/STEGBROWSER_SV002_LANE_ADAPTATION.md`

Exact binding envelope:

```text
Goal Task ID = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001
COSV = 40000100100000
manifest task = STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001
destination = StegBrowser:ManifestInvocation
payload schema = stegverse.stegbrowser-universal-intr-invocation-binding/v1
route owner = STEGVERSE
outbound endpoint = STEGVERSE_OWNED_INTR_EGRESS_ENDPOINT
far-end receiver = STEGVERSE_OWNED_MIRROR_REFLECTOR
expected action = REFLECT_DECLARED_RECORDS_PACKET
runtime substrate = BROWSER_WEB_WORKER_ON_VALID_STEGVERSE_NODE
runtime class = EVENT_EPHEMERAL
GitHub runtime authority = NONE
credential authority = TV/TVC
```

The Site browser materializer is non-authorizing. It validates the already-admitted Node/Interlock/InTr invocation and may produce bounded runtime-readiness evidence only. It does not mint a WorkerCoordinator claim/fence, grant execution authority, replace TV/TVC credential authority, or convert CI/source evidence into runtime evidence.

## Immutable one-shot request

```text
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
invocation_request_nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested_test_scope = A0_A4_SINGLE_INVOCATION
requested_invocation_count = 1
```

No second request may be emitted or substituted.

## Current source truth

```text
SV002_RUNTIME_ARCHITECTURE_SOURCE_IDENTIFIED = true
SV002_SITE_REUSABLE_BASELINE_RETEST_PASS = true
STEGBROWSER_UNIVERSAL_INTR_MATERIALIZATION_BINDING_COMPLETE = true
STEGBROWSER_SITE_SV002_ADAPTATION_MERGED_VALIDATED = true
SINGLE_CANONICAL_STEGBROWSER_MATERIALIZATION_PATH = true
CONTROL_PLANE_SOURCE_PACKAGE_IS_RUNTIME_PREREQUISITE = false
RESIDENT_REQUEST_SWEEP_IS_RUNTIME_PREREQUISITE = false
SECOND_RUNTIME_OR_LISTENER_INTRODUCED = false
WORKERCOORDINATOR_AUTHORITY_CHANGED = false
INTERLOCK_INTR_AUTHORITY_CHANGED = false
TV_TVC_CREDENTIAL_AUTHORITY_CHANGED = false
GITHUB_RUNTIME_AUTHORITY = NONE
```

## Current authentic predicates

Source validation and merge do not establish authentic execution. No same-invocation authority-owned A1-A4 receipt set was observed during this work, and no authorized sovereign execution surface became available through this chat. Therefore all runtime predicates remain false:

```text
MANIFEST_BOUND_TO_INVOCATION runtime confirmation = false
STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INTR_MATERIALIZATION_ADMITTED = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
AUTHENTIC_INTR_INGRESS_OBSERVED = false
ROUND_TRIP_1_STARTED = false
```

This remains an execution/evidence-access condition, not a source-architecture or Site adaptation defect. GitHub/CI remains validation/evidence transport only and must not be promoted into runtime authority to bypass the sovereign execution surface.

## 2026-09-16 resident transport investigation and repair

The existing non-authorizing `scripts/dispatch_resident_execution_requests.py` already registers selector `stegbrowser_runtime_connection_ingress` and calls the existing `scripts/consume_stegbrowser_runtime_connection_ingress_request.py` with local source/runtime roots. That consumer already owns the correct A1 observation and invokes the canonical manifest-bound runtime owner; no new request, listener, materializer, scheduler, WorkerCoordinator, or runtime authority is required.

The precise source defect was the dispatcher's sanitized environment allowlist: it did not preserve the consumer's concrete registered Node Receipt #1 path binding `STEGVERSE_NODE_GENESIS_RECEIPT`, nor the optional `STEGVERSE_STEGOS_SOURCE_ROOT` / `STEGVERSE_EPHEMERAL_RUNTIME_BASE` path bindings used by that same canonical runtime composition. PR #1998 repairs only those non-secret path transports and recognizes the consumer's current bounded observation result states. Hosted-environment markers and GitHub credential variables remain stripped, GitHub runtime authority remains `NONE`, TV/TVC remains credential authority, and the dispatcher remains non-authorizing.

PR #1998 is a clean rebase of the bounded repair after stale PR #1996 became non-mergeable as main advanced. The dispatcher source itself had not changed on main, so the dispatcher/test delta was transplanted unchanged onto current main while the handoff was reconciled against the newest canonical text.

This repair makes the already-existing sovereign resident dispatch surface callable when authentic local bindings are present. It does not prove that such a resident surface executed, does not promote any A1-A4 predicate, and does not enter Round Trip 1.

## Expected same-invocation evidence

Retain, as applicable, exact Goal/COSV/nonce/manifest/node/interlock/registration/materialization/lease/runtime/claim/fence-correlated evidence at the existing canonical paths, including:

```text
intr-payloads/stegbrowser-manifest-invocation/<binding-hash>.json
intr-outbox/stegbrowser-manifest-invocation/<materialization-id>.json
receipts/sovereign-network/stegbrowser-intr-ingress/<materialization-id>.json
receipts/sovereign-host/stegbrowser-intr-materialization-consumption.latest.json
receipts/sovereign-host/stegbrowser-manifest-binding.latest.json
receipts/sovereign-host/stegbrowser-node-interlock-runtime-binding.latest.json
receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json
receipts/sovereign-host/stegbrowser-manifest-intr-ingress.latest.json
```

## Immediate continuation

Do not emit another request and do not add another materialization profile. After exact-head validation and merge of PR #1998, invoke only the already-registered `stegbrowser_runtime_connection_ingress` selector from an authorized sovereign resident dispatcher carrying the authentic local Node Receipt #1 path binding. The unchanged nonce remains the only invocation. Retain authentic same-invocation Node binding, `INGRESS_ADMITTED`, bounded lease, EVENT_EPHEMERAL runtime identity, WorkerCoordinator claim/fence, and A4 ingress receipts; promote only predicates directly proven by those authority-owned receipts. Stop before Round Trip 1 unless authentic A1-A4 completion is established.

## README review

README reviewed for PR #1998. No byte change is required: the public runtime/authority topology remains the already-documented single shared Universal InTr/event-ephemeral architecture, including the canonical registered Node binding and existing resident-dispatch/WorkerCoordinator authority boundaries. This repair changes only non-secret local path transport through the existing non-authorizing dispatcher.

## Manual work

None.
