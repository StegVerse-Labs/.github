# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Immutable one-shot nonce: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z`
- Status: `ACTIVE / CHECKED_OUT / SV002 UNIVERSAL-INTR BINDING IMPLEMENTED / EXACT-HEAD VALIDATION PENDING / AUTHENTIC A1-A4 EVIDENCE PENDING`

## Canonical architecture

The validated StegVerse-002 implementation remains the architecture source:

```text
manifest invocation
-> registered StegVerse Node Receipt #1
-> stegverse.universal-intr-transport/v1
-> stegverse.universal-intr-materialization-request/v1
-> node-bound write-once InTr trigger
-> existing shared /intr/materialization ingress
-> write-once INGRESS_ADMITTED
-> credential-scrubbed non-authorizing consumer
-> existing StegBrowser manifest-bound runner
-> existing bounded EVENT_EPHEMERAL StegOS lease/runtime
-> existing WorkerCoordinator claim/fence
-> existing workers/stegbrowser_manifest_intr_ingress.py A4 verification
```

No control-plane source-package relay or resident-request sweep is a runtime prerequisite. No external runtime/device/host discovery stage exists.

## Bounded implementation

Branch `fix/stegbrowser-sv002-intr-binding-001` adds only the StegBrowser composition into existing surfaces:

- `workers/stegbrowser_intr_ingress.py`
  - profile adapter only; creates no listener;
  - requires Node-origin `stegos.node_intr_materialization_trigger.v1`;
  - validates exact write-once node outbox/materialization bindings;
  - writes `stegverse.stegbrowser-intr-materialization-ingress/v1` with `state=INGRESS_ADMITTED`;
  - mints no claim/fence and grants no execution authority.
- `scripts/consume_stegbrowser_intr_materialization_request.py`
  - requires the exact admitted request/receipt tuple;
  - dispatches the already-existing `scripts/run_stegbrowser_manifest_bound_runtime.py` in explicit post-admission mode;
  - does not create a runtime, lease, WorkerCoordinator, transport, listener, or credential authority.
- `scripts/install_stegbrowser_universal_intr_route.py`
  - idempotent fail-closed source transformer that adds `StegBrowser:ManifestExecution` to the existing shared Universal InTr router;
  - preserves the existing `ThreadingHTTPServer` listener count.
- `scripts/run_stegbrowser_manifest_bound_runtime.py`
  - pre-admission mode validates the existing manifest and registered Node Receipt #1, constructs the canonical Universal InTr intent/materialization request and exact Node trigger, and submits it through the StegBrowser adapter bound into the shared route;
  - post-admission mode re-enters the same manifest runner and then invokes the unchanged reusable StegBrowser runtime-consumption runner;
  - the downstream runner remains the owner of the existing EVENT_EPHEMERAL lease/runtime and A3/A4 flow.
- `tests/test_stegbrowser_sv002_intr_binding.py`
  - verifies fail-closed non-authorizing request semantics, Node-trigger admission, write-once A2 receipt composition, post-admission same-runner dispatch, idempotent shared-route installation, and no second listener.

## Authority boundaries

```text
manifest                    route declaration/binding only
StegVerse Node              continuity/admission anchor only
materialization request     execution authority NONE
shared InTr ingress         transition/admission only; claim/fence minting false
StegBrowser consumer        dispatch only; execution authority NONE
EVENT_EPHEMERAL StegOS      existing compute/materialization surface
WorkerCoordinator           sole claim/fence authority
Interlock/InTr              transition + governed packet movement authority
TV/TVC                      credential authority
GitHub/CI                   source validation/evidence only; runtime authority NONE
```

No second listener, runtime, scheduler, dispatcher, materializer, WorkerCoordinator, host/device path, transport, endpoint, credential path, or authority surface is introduced.

## Runtime truth

Source implementation and CI do not promote runtime predicates. Until same-invocation receipts are authentically retained:

```text
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

## README review

README reviewed. No byte change required because public StegVerse authority/topology semantics do not change; this is a bounded composition into already-documented Universal InTr and EVENT_EPHEMERAL behavior.

## Immediate continuation

Run exact-head repository validation. If green, merge the bounded source binding. Then inspect only same-invocation authentic receipts produced from the unchanged nonce and promote A1/A2/A2.1/A2.2/A3/A4 only where exact Goal/COSV/manifest/node/interlock/lease/runtime/claim/fence correlation is proven.

## Manual work

None.
