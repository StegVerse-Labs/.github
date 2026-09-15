# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / NODE+INTERLOCK LEASE+A4 SOURCE MERGED+VALIDATED / SINGLE A1-A4 PATH RECONCILED+MERGED+VALIDATED / NATIVE SOURCE-PACKAGE REPAIR VALIDATION PENDING / AUTHENTIC A1-A4 EXECUTION PENDING`
- Node/Interlock source repair: PR `#1923`, validated head `f7b6cb86b9fff9fbeb1817e45920acc2effc200f`, merge `0098bc793865fd1db835c400b502dad5f8a5e32d`.
- Single-path A1-A4 reconciliation: PR `#1929`, validated head `60e7246e326d32d17525d83783c38c5e21528ff0`, merge `a4c2d173aad04219795e44d2051703accd404c9c`.
- PR #1929 validation: organization control `34976675513`, deterministic repository suite `34976675506`, Heartbeat validation `34976675536` — all SUCCESS on the same exact head.
- Issue `#1918`: `CLOSED / SOURCE DEFECT COMPLETE / CLOSURE CONFIRMED AFTER #1929`.

## Canonical path

```text
manifest
-> A1 Interlock/InTr invocation-state observation
-> canonical registered StegVerse Node Receipt #1
-> A2 Node-bound Interlock/manifest binding
-> A2.1 bounded invocation lease/state binding
-> A2.2 EVENT_EPHEMERAL StegOS materialization
-> A3 WorkerCoordinator claim/fence
-> A4 exact Interlock/InTr ingress
-> STOP A1-A4 child
-> Round Trip 1
-> Master Records / mirror processing
-> Round Trip 2
-> ecosystem re-entry
```

There is no external runtime/device/host discovery stage and no second user-operated device prerequisite.

## Single Node-binding representation

The only concrete registered Node Receipt #1 path input is:

```text
parameter = node_genesis_receipt
environment = STEGVERSE_NODE_GENESIS_RECEIPT
schema = stegos.node_handoff_receipt.v1
receipt_number = 1
```

`CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING` is selector metadata only. It is not a second receipt schema, identity, path, or authority source. A plain `stegverse.sovereign-node-declaration/v0.4` declaration cannot be inferred into Receipt #1.

## A1-A4 composition

`STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001` owns bounded A1 observation/composition. A1 observes invocation-bound `callable`, `refreshable`, and applicable-protocol state. `callable` and `refreshable` are transition variables governed by Interlock/InTr, not persistent runtime properties.

When the admitted transition resolves `callable=true` and `refreshable=true`, existing `RT-SOVEREIGN-SOURCE-REFRESH-001` may be selected. When `callable=true` and `refreshable=false`, no refresh prerequisite is invented. When callable and protocol-resolved, A2-A4 continue through the one existing path:

`RT-STEGBROWSER-RUNTIME-CONSUMPTION-001 -> scripts/run_stegbrowser_manifest_bound_runtime.py -> scripts/run_stegbrowser_runtime_consumption_reusable.py`

That path validates Receipt #1, binds manifest + Node + Interlock + registration receipt + Goal/COSV into the existing lease/state identity, materializes the existing `SovereignLocalEventRuntimeAdapter` as `RuntimeClass.EVENT_EPHEMERAL`, obtains A3 through the existing WorkerCoordinator boundary, and reaches A4 through the existing exact manifest ingress worker. It stops before Round Trip 1.

No duplicate lease, runtime materializer, A4 worker, scheduler, WorkerCoordinator, credential path, host path, or device path is introduced.

## One-shot native invocation request

The already-issued request remains immutable for this test:

```text
commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
invocation_request_nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested_test_scope = A0_A4_SINGLE_INVOCATION
requested_invocation_count = 1
```

No second resident request may be emitted for this continuation and the existing request bytes must remain unchanged.

## Native canonical-source localization repair

The resident `refresh_sovereign_worker_runtime_source.py` is intentionally transport-free. It copies `control/resident-execution-request.d` and other allowlisted static control-plane state only from an already-local canonical source and records `source_git_head`; it does not fetch or pull GitHub.

The existing reusable localization mechanism is `RT-CONTROL-PLANE-SOURCE-PACKAGE-001`, whose exact content-addressed output is carried only by the existing governed `RTC-INTERLOCK-INTR-TRANSPORT-008 / TVC` relay path. Inspection found that the package default allowlist did not contain the StegBrowser one-shot request and manifest-bound invocation chain, so the existing package could not carry the unchanged request introduced at commit `19935454...` into the resident already-local source.

The bounded repair on branch `fix/stegbrowser-native-source-package-001` changes only the existing control-plane package allowlist. It adds the already-existing StegBrowser request, canonical-work consumer, route manifest, reusable task definition, manifest-bound runner, reusable runner/legacy implementation, A4 worker, and active remediation task record. It does not modify the one-shot request, create a new source transport, add network-fetch authority to resident refresh, or alter Interlock/InTr, TV/TVC, WorkerCoordinator, credential, runtime, device, host, scheduler, dispatcher, receiver, endpoint, or authority semantics.

Validation/merge of this source-package repair is pending. Source/CI validation does not prove package relay, resident source materialization, request consumption, or A0-A4 runtime execution.

## Current authentic predicates

StegVerse-native retained evidence was checked after PR #1929 merge. Expected retained A1-A4 paths were absent from canonical retained evidence, including:

```text
receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json
receipts/sovereign-host/stegbrowser-runtime-connection-a1-a2.latest.json
receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json
receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json
receipts/sovereign-host/stegbrowser-manifest-intr-ingress.latest.json
```

The one-shot continuation also has not yet retained:

```text
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

Repository source references to these locations are contracts, not authentic runtime receipts. Therefore:

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
AUTHENTIC_INTR_INGRESS_OBSERVED = false
ROUND_TRIP_1_STARTED = false
```

Current exact condition: `UNCHANGED_ONE_SHOT_REQUEST_NOT_YET_OBSERVED_IN_RESIDENT_ALREADY_LOCAL_SOURCE_OR_A0_A4_RUNTIME`.

Source/CI/GitHub state does not promote runtime predicates. External connector/device/host reachability is not part of this Goal's evidence path and is not a prerequisite, failure predicate, or substrate-disqualification signal.

## Authority boundaries

- StegVerse Node: continuity/admission anchor only.
- Interlock/InTr: transition and governed packet-movement authority.
- Lease: bounded invocation scope only.
- EVENT_EPHEMERAL StegOS runtime: compute/materialization only.
- WorkerCoordinator: claim/fence authority.
- TV/TVC: credential authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality custody/reconstruction authority.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.
- Healer: triggered remediation only.

## Immediate continuation

Validate and merge only the bounded existing control-plane source-package allowlist repair. Then use the existing governed control-plane source-package transport/localization path with the unchanged nonce request. Require the next authentic resident source-refresh receipt to identify commit `19935454cd8c68000b3a0fd70478b0d89d5cd622` or an exact descendant containing the unchanged request. Only then follow the same resident cycle through dispatch, canonical-work consumption, and A0-A4. Do not issue a second request or create another runtime, transport, scheduler, dispatcher, device, host, receiver, endpoint, credential path, or authority surface.

## Manual work

None.
