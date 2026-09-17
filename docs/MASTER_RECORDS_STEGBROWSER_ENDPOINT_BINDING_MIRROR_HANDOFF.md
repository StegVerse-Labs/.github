# Master Records StegBrowser Endpoint Binding Mirror Handoff

Updated: 2026-09-17
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001`
- Parent Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
- Decomposed from: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001` at Goal Prompt Count `20/20`
- Issue: `StegVerse-Labs/.github#2078`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / PROVIDER-NEUTRAL BROWSER+GATEWAY SOURCE BINDING MERGED+VALIDATED / AUTHENTIC RECORDED+PASS PENDING`

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


## Goal prompt 1: provider-neutral binding repaired in source

Session Prompt Count: 7. Goal Prompt Count: 1/20.

### Binding resolution

Current canonical authority source was re-read before mutation. `master-records/orchestration:services/canonical_state_transition_custody.py` already owns the sole state-transition custody implementation and authoritative bearer-authenticated API. No Master Records authority code or durable store was added or replaced.

The applicable browser binding had two independently reproduced source defects:

1. Site treated `/api/master-records/state-transitions` as a same-origin browser endpoint and sent only an informational TV/TVC header/cookie context rather than an authentic server-side credential path.
2. The immutable StegBrowser page recorded top-level `transition_outcome=INGRESS_ADMITTED`, while the authoritative state-transition custody contract permits only its canonical outcome set, including `OBSERVED` but not `INGRESS_ADMITTED`.

Both defects are repaired without changing the immutable invocation.

### Merged Site binding

Site PR `#1380` merged with expected-head protection as `c46b5631e3ee4c2be92497879947c3539fc04277`. Exact head `fbb168a437dca9036f23b8d861ade9621d2407bb` passed all 12 PR-triggered workflows, including MIR SV002 Browser Event Conformance, Site Bootstrap, Site Handoff Orchestrator, Ecosystem Heartbeat Orchestration, Node IndexedDB Schema Migration, and No Required Third-Party Runtime.

Current source blobs:

```text
stegos-bootstrap/canonical-work-runtime-consumption.html
  cf381a3c3001eb61447381789376ef52ce85ca20

assets/canonical-master-records-transition-custody-browser.js
  769fa04bf01bc1258ea905a4ba553b33f18f893d
```

The browser now resolves the fixed canonical path `/api/master-records/state-transitions` only through a hash-verified and health-verified `stegverse.node.endpoint-advertisement.v1`. Candidate discovery reuses existing provider-neutral mechanisms:

```text
query:master_records_gateway
query:gateway
runtime injection
persisted local configuration
same origin
loopback fallback
```

A candidate is admissible only when the advertisement preserves Master Records owner `master-records/orchestration`, TV/TVC credential authority, browser credential requirement `false`, gateway authority `NONE`, advertisement digest equality, and a healthy node response.

The browser sends no Master Records bearer token, cookie credential, or credential-authority placeholder. Browser IndexedDB remains subordinate continuity/cache only.

The exact custody receipt now uses:

```text
transition_outcome = OBSERVED
transition_evidence.intr_ingress_state = INGRESS_ADMITTED
transition_evidence.intr_governance_decision = ALLOW
```

The immutable nonce remains `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z`; requested invocation count remains `1`; no second request was emitted.

The temporary Site implementation claim was released after validation through Site PR `#1381`, merged as `8380564aacd16c687a2affa401453d0a8bfad554`.

### Merged credential-nonexporting gateway transport

StegVerse-org/LLM-adapter PR `#344` merged with expected-head protection as `608147cafa8506dfc11359223bb8de7c34c2b2b9`. Exact head `1266a9758d214182744889996204f80e54d35d6b` passed all 10 PR-triggered workflows, including the full `validate` workflow and Work Mutation Safety.

Current relay blob:

```text
llm_adapter/stegbrowser_master_records_state_transition_relay.py
  417200990b6029665407c93c790201a15d2e2437
```

The existing Service Gateway now advertises the bounded relay only when its existing server-side Master Records configuration is available. The browser supplies only the non-secret canonical state-transition submission. The gateway keeps Master Records bearer material server-side under the existing TV/TVC `service_gateway_master_records` credential role and relays the unchanged submission to the sole canonical Master Records API.

The relay accepts only the immutable nonce, transition `STEGBROWSER_RUNTIME_READINESS_MASTER_RECORDS_CUSTODY`, sequence `1`, COSV `40000100100000`, canonical predecessor task, `OBSERVED` outcome, exact InTr `ALLOW / INGRESS_ADMITTED` evidence, and complete Node/Interlock/Receipt-1/lease/runtime/exported-bundle tuple. It independently recomputes the canonical receipt digest and accepts success only when Master Records returns `RECORDED + reconstruction_status=PASS` with identical receipt/reconstruction digests and no authority escalation.

This gateway route is transport only. It is not a second custody API, store, transition authority, credential authority, scheduler, dispatcher, runtime, or governance plane.

### Authentic evidence boundary

Source implementation and exact-head validation are complete for the applicable binding, but authentic runtime completion is not claimed.

No authentic current `stegverse.node.endpoint-advertisement.v1` carrying the new state-transition endpoint has yet been observed for this immutable invocation from an authority-owned runtime context. Therefore no authentic Master Records `RECORDED + reconstruction_status=PASS` response or exact tuple digest equality has been observed in this continuation.

The task remains `ACTIVE / CHECKED_OUT`. These completion predicates remain false:

```text
AUTHORITATIVE_BROWSER_CUSTODY_ENDPOINT_BOUND = false
AUTHENTIC_MASTER_RECORDS_RECORDED = false
AUTHENTIC_MASTER_RECORDS_RECONSTRUCTION_PASS = false
EXACT_STEGBROWSER_TUPLE_DIGEST_EQUALITY = false
```

Source/CI/merge state does not promote them. A3, A4 and Round Trip 1 remain unentered.

### Next authentic transition

Observe an existing verified StegVerse gateway advertisement for the merged relay without assuming a fixed provider or host. If the advertisement is authentic and healthy, submit only the existing exact custody receipt for the unchanged nonce through that transport and require the sole Master Records authority to return `RECORDED + PASS` with exact digest equality. Only then hand the same invocation back to the existing A1-A4 execution owner.

Render remains excluded. No hosting provider, platform, OS, browser engine, device class, standing remote host, or second user-operated device is canonical or required.

## Manual work

None.
