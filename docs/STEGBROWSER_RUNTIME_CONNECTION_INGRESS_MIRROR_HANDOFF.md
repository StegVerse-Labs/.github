# StegBrowser Runtime Connection Ingress Mirror Handoff

Updated: 2026-09-15

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Root lineage: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / A1-A4 RESIDENT SOURCE COMPOSED + NATIVE DISPATCH MERGED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Scope and terminal boundary

This child owns only GC A1 through A4 and stops before Round Trip 1 payload processing.

```text
A1 authentic invocation-bound connection-state observation
-> select only matching existing reusable capabilities
-> A2 invocation-bound admitted execution materialization
-> A3 existing organization-local boundary executor obtains WorkerCoordinator claim/fence
-> A4 exact manifest-defined Interlock/InTr ingress
-> STOP CHILD
```

`RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` remains the later two-round-trip transport capability after authentic A4.

## Canonical resident request and native discoverability

Request:

`control/resident-execution-request.d/stegbrowser-runtime-connection-ingress-001.json`

Consumer:

`scripts/consume_stegbrowser_runtime_connection_ingress_request.py`

Native resident selector:

`stegbrowser_runtime_connection_ingress`

The selector is registered in:

`scripts/dispatch_resident_execution_requests.py`

Local resident source refresh materializes:

- `scripts/consume_stegbrowser_runtime_connection_ingress_request.py`
- `scripts/resolve_stegbrowser_runtime_connection_transition.py`
- `scripts/refresh_sovereign_worker_runtime_source_reusable.py`
- the existing `workers/` directory, including `workers/stegbrowser_manifest_intr_ingress.py`
- `control/resident-execution-request.d`, including this child's request.

This makes the child discoverable by the existing native resident request sweep after the ordinary already-local source refresh. Registration and materialization grant no execution authority and do not prove resident consumption.

The request is non-authorizing and explicitly forbids Round Trip 1 payload processing, network source fetch, GitHub runtime authority, and second-machine dependency.

## Merged source evidence

PR `#1917` exact head `a19994be30060b467855c95387f463790b21c26e` passed the deterministic repository suite, organization-control validation, heartbeat validation, and adjacent resident-validation lanes, then squash-merged as `70f4fefc8183de63c6542bd3efac08f8a8f6b987`.

That merge proves only source composition and native-dispatch discoverability. It does not satisfy A1, A2, A3, or A4 runtime predicates.

## A1 authentic observation

The resident consumer installs/checks the existing CanonicalWork route in the existing shared Universal InTr listener, starts one bounded loopback request surface from that existing implementation, and reads its live `/intr/profile` response.

A1 observation schema:

`stegverse.intr-runtime-connection-transition-observation/v1`

Required owner/effect:

```text
authority_owner = Interlock/InTr
authority_effect = OBSERVATION_ONLY
```

The observation binds:

- `callable`
- `refreshable`
- `applicable_protocol_resolved`

`callable` and `refreshable` remain invocation-bound state-transition variables, never persistent runtime/source assumptions.

`applicable_protocol_resolved` requires both a live resident InTr profile and the already-local exact manifest ingress adapter `workers/stegbrowser_manifest_intr_ingress.py`. Adapter presence does not itself prove A4 admission.

Resolver:

`scripts/resolve_stegbrowser_runtime_connection_transition.py`

## Existing reusable-task selection

No new reusable task is required.

```text
callable=false
-> do not materialize execution
-> do not select refresh

callable=true AND refreshable=true
-> RT-SOVEREIGN-SOURCE-REFRESH-001

callable=true AND refreshable=false
-> no refresh task

callable=true AND applicable_protocol_resolved=false
-> RT-INTR-PROTOCOL-ESTABLISH-001

callable=true AND applicable_protocol_resolved=true
-> reuse existing protocol path
```

## A2

When source refresh is selected, the consumer invokes the existing `RT-SOVEREIGN-SOURCE-REFRESH-001` runner with exact invocation-bound `callable=true`, `refreshable=true`, and the A1 transition receipt reference.

If refresh is not selected, no refresh prerequisite is invented.

A2 is satisfied only when the callable invocation has the required already-local materialization state.

## A3/A4 exact existing authority path

The child does not create a new WorkerCoordinator task or new A4 adapter.

It reuses:

`workers/stegbrowser_manifest_intr_ingress.py`

That existing exact manifest-bound ingress worker:

1. validates/binds the canonical StegBrowser transport manifest;
2. stages the organization-local InTr ingress packet;
3. invokes the existing `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` through the canonical targeted resident task path;
4. requires the existing WorkerCoordinator to produce the authentic claim/fence;
5. verifies the organization-local boundary receipt and exact payload hash;
6. returns `AUTHENTIC_INTR_INGRESS_OBSERVED` only when the accepted local-boundary receipt and claim/fence are authentic.

The child records that claim/fence as A3 evidence and the verified manifest ingress as A4 evidence.

This existing worker stops at ingress. It does not execute A5 or Round Trip 1 payload processing.

## Post-merge native evidence inspection

After PR `#1917` merged, repository-visible StegVerse-native evidence surfaces were searched for:

- `receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json`
- `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a2.latest.json`
- `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json`
- `receipts/sovereign-host/stegbrowser-manifest-intr-ingress.latest.json`
- `receipts/organization-local-boundary/stegbrowser-manifest-intr-ingress.json`
- global retained references to `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- global retained references to packet id `stegbrowser-manifest-intr-ingress`

Result: source definitions, tests, handoff/task metadata, and expected receipt paths were found; no retained authentic resident A1/A2/A3/A4 receipt or Master Records copy was found.

This negative evidence inspection does not mean the resident path failed. It means authentic execution remains unobserved from retained evidence and therefore no runtime predicate is promoted.

## Child completion predicates

```text
MANIFEST_BOUND_TO_INVOCATION = true
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = true
CALLABLE_STATE_BOUND_TO_INVOCATION = true
REFRESHABLE_STATE_BOUND_TO_INVOCATION = true
MATCHING_REUSABLE_CAPABILITIES_SELECTED = true
ADMITTED_EXECUTION_SURFACE_MATERIALIZED = true
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true
INTR_ADMISSION_OBSERVED = true
NO_ROUND_TRIP_1_PAYLOAD_PROCESSING_EXECUTED_BY_CHILD = true
NO_SECOND_USER_OPERATED_DEVICE_REQUIRED = true
```

Only authentic resident/authority-owned evidence may satisfy them. GitHub/CI validation cannot.

## Current authentic state

```text
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
INTR_ADMISSION_OBSERVED = false
```

No authentic resident invocation receipt for the A1-A4 consumer is presently retained in repository-visible evidence.

## Validation surfaces

- `tests/test_stegbrowser_runtime_connection_transition.py`
- `tests/test_stegbrowser_runtime_connection_ingress_consumer.py`
- `tests/test_stegbrowser_runtime_connection_resident_dispatch_registration.py`
- `docs/STEGBROWSER_RUNTIME_CONNECTION_INGRESS_IMPLEMENTATION_STATUS.md`

## Out-of-scope defect rule

The canonical out-of-scope remediation contract applies unchanged. An observed foreign defect is evidence-retained and sent to StegVerse-Healer for independent trigger evaluation; the current Goal does not silently repair the foreign subsystem. A pending predicate is not a Healer trigger.

## Authority invariants

- Task Registry: coordination only.
- Native resident dispatcher: discovery/dispatch only; no authority.
- Resolver: selection only.
- `RT-SOVEREIGN-SOURCE-REFRESH-001`: local source materialization only.
- `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` / WorkerCoordinator: A3 claim/fence authority.
- Interlock/InTr: A1 connection-state and A4 transition/ingress authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.

## Current first unresolved predicate

`RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED`

## Manual work

None.
