# Master Records StegBrowser Endpoint Binding Mirror Handoff

Updated: 2026-09-17
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001`
- Parent Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
- Decomposed from: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001` at Goal Prompt Count `20/20`
- Issue: `StegVerse-Labs/.github#2078`
- COSV: `40000100100000`
- Status: `PROPOSED / HANDOFF_READY / BROWSER CUSTODY ENDPOINT BINDING UNRESOLVED`

## Scope

Resolve only the custody binding actually used by the immutable StegBrowser invocation. The execution page at `StegVerse-Labs/Site:stegos-bootstrap/canonical-work-runtime-consumption.html` loads `assets/canonical-master-records-transition-custody-browser.js` and constructs the canonical custody client with:

```text
endpoint = /api/master-records/state-transitions
subject = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
transition = STEGBROWSER_RUNTIME_READINESS_MASTER_RECORDS_CUSTODY
```

The generic Python local adapter in `workers/canonical_state_transition_custody.py` is not the immutable invocation's browser custody binding and must not be repaired as if it resolves this task.

## Proven defect

A read-only observation of `https://stegverse.org/api/master-records/state-transitions` returned HTTP 404 from the static public Site route. Current Site source has no root Universal InTr fetch handler that converts that path into the authoritative Master Records API. This proves the current same-origin browser endpoint binding is not visibly served at the probed public origin; it does not prove the durable Master Records store is empty and does not prove the immutable invocation never executed.

The canonical authority implementation remains `master-records/orchestration:services/canonical_state_transition_custody.py` installed by `services/canonical_master_records_api.py`. The authoritative contract remains:

```text
submission schema = stegverse.master-records.state-transition-submission/v1
receipt schema = stegverse.canonical-state-transition-receipt/v1
POST /api/master-records/state-transitions
GET /api/master-records/state-transitions/{receipt_sha256}/reconstruction
required = RECORDED + reconstruction_status=PASS
receipt_sha256 = reconstructed_receipt_sha256 = locally recomputed canonical digest
Master Records transition authority = false
Master Records execution authority = false
```

## Required solution path

1. Re-read the current canonical Master Records custody owner and the current Site browser custody client before mutation.
2. Bind the browser client to the existing authoritative Master Records custody surface through a provider-neutral, platform-neutral, OS-neutral, device-neutral configuration or routing contract already owned by StegVerse. Do not hard-code Render or any replacement hosting provider.
3. Preserve TV/TVC credential authority. A header naming TV/TVC is not authentication evidence; do not invent or expose credentials in browser source.
4. Do not create a second API, custody store, transport plane, runtime, scheduler, dispatcher, service worker authority, credential path, request nonce, or user-operated device dependency.
5. Preserve the immutable invocation nonce `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z` and requested invocation count `1`.
6. Require one authentic Master Records reconstruction of the exact StegBrowser tuple before returning control to A3.

## Exact tuple required

```text
runtime readiness receipt sha256
Node continuity readiness receipt sha256
immutable invocation nonce
Node ID
Interlock ID
Receipt #1 sha256
lease ID
runtime ID
exported evidence bundle sha256
StegBrowser custody transition/admission identity
```

## Completion predicates

```text
AUTHORITATIVE_BROWSER_CUSTODY_ENDPOINT_BOUND = true
TV_TVC_CREDENTIAL_AUTHORITY_PRESERVED = true
NO_PROVIDER_PLATFORM_OS_DEVICE_PREREQUISITE = true
NO_SECOND_CUSTODY_OR_TRANSPORT_PLANE = true
IMMUTABLE_NONCE_PRESERVED = true
AUTHENTIC_MASTER_RECORDS_RECORDED = true
AUTHENTIC_MASTER_RECORDS_RECONSTRUCTION_PASS = true
EXACT_STEGBROWSER_TUPLE_DIGEST_EQUALITY = true
```

Source, CI, merge, routing declarations, browser-local IndexedDB, or an ingress admission receipt cannot satisfy the authentic reconstruction predicates.

## Downstream handoff

After and only after authentic reconstruction succeeds, return the same invocation to the already-existing `STEG-BROWSER-CURRENT-IPHONE-A1-A4-EXECUTION-001` lineage for fresh WorkerCoordinator A3 claim/fence and exact A4 ingress. Round Trip 1 remains unentered until A1-A4 are authentically complete.

## Manual work

None.
