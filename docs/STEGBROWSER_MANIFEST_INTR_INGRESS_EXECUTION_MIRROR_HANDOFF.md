# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / NODE+INTERLOCK LEASE+A4 SOURCE MERGED+VALIDATED / DUPLICATE A1-A4 REPRESENTATION RECONCILED / AUTHENTIC A1-A4 EXECUTION PENDING`
- Node/Interlock source repair: PR `#1923`, validated head `f7b6cb86b9fff9fbeb1817e45920acc2effc200f`, merge `0098bc793865fd1db835c400b502dad5f8a5e32d`
- Issue `#1918`: `CLOSED / SOURCE DEFECT COMPLETE`; authentic runtime evidence remains separate.

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

There is no external runtime/device/host discovery stage, no waiting online runtime, no generic chat-session process host, and no second user-operated device prerequisite.

## Single Node-binding representation

The only concrete registered Node Receipt #1 path input is:

```text
parameter = node_genesis_receipt
environment = STEGVERSE_NODE_GENESIS_RECEIPT
schema = stegos.node_handoff_receipt.v1
receipt_number = 1
```

`CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING` is retained only as the A1-A4 child selector label. It resolves to the concrete `node_genesis_receipt` / `STEGVERSE_NODE_GENESIS_RECEIPT` input and is not a second receipt schema, path, identity, or authority source.

A plain `stegverse.sovereign-node-declaration/v0.4` declaration cannot be inferred into Receipt #1.

## A1-A4 composition

`STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001` is the bounded A1-A4 observation/composition child. It no longer calls `workers/stegbrowser_manifest_intr_ingress.py` directly.

A1 observes invocation-bound `callable`, `refreshable`, and `applicable_protocol_resolved`. If source refresh is selected, it uses existing `RT-SOVEREIGN-SOURCE-REFRESH-001`. When callable and protocol-resolved, it composes A2-A4 through the one existing execution path:

`RT-STEGBROWSER-RUNTIME-CONSUMPTION-001 -> scripts/run_stegbrowser_manifest_bound_runtime.py -> scripts/run_stegbrowser_runtime_consumption_reusable.py`

The reusable runner validates Receipt #1 with `StegOS/stegos/network_manifold.py::validate_node_genesis_receipt`, constructs the existing Node/Interlock-bound `LeaseRequest`, materializes the existing `SovereignLocalEventRuntimeAdapter` with `RuntimeClass.EVENT_EPHEMERAL`, obtains A3 through the existing organization-local WorkerCoordinator boundary, and reaches A4 through the existing exact manifest ingress worker. It stops before Round Trip 1.

No duplicate lease implementation, runtime materializer, A4 worker, scheduler, WorkerCoordinator, credential path, host path, or device path is created.

## Goal Chart evidence predicates

### A1

```text
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED
CALLABLE_STATE_BOUND_TO_INVOCATION
REFRESHABLE_STATE_BOUND_TO_INVOCATION
```

### A2

```text
STEGVERSE_NODE_BOUND_TO_INVOCATION
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
INTR_MATERIALIZATION_ADMITTED
```

### A2.1

```text
INVOCATION_SCOPED_LEASE_ESTABLISHED
```

Lease/state identity binds manifest SHA-256, Node, Interlock, registration receipt, Goal/COSV, and canonical task/registry state.

### A2.2

```text
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
```

### A3

`CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED`

### A4

```text
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
AUTHENTIC_INTR_INGRESS_OBSERVED
```

A4 exact correlation includes manifest, Node, Interlock, registration receipt, lease, runtime, state-root binding, claim, and fencing token.

## Current authentic predicates

```text
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = false / not authentically observed
STEGVERSE_NODE_BOUND_TO_INVOCATION = false / not authentically observed
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false / not authentically observed
INTR_MATERIALIZATION_ADMITTED = false / not authentically observed
INVOCATION_SCOPED_LEASE_ESTABLISHED = false / not authentically observed
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false / not authentically observed
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false / not authentically observed
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false / not authentically observed
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false / not authentically observed
AUTHENTIC_INTR_INGRESS_OBSERVED = false / not authentically observed
```

Current exact defect:

`AUTHENTIC_NODE_INTERLOCK_LEASE_RUNTIME_A3_A4_EVIDENCE_NOT_YET_OBSERVED`

Source/CI state does not promote any runtime predicate.

## #1918 disposition

Issue `#1918` is already closed as completed after PR `#1923` fixed and validated the bounded Node/Interlock/lease/runtime/A4 source defect. The reconciliation of the A1-A4 child preserves that source-complete implementation and removes the remaining duplicate representation; therefore #1918 remains closed. Authentic A1-A4 evidence is an active runtime-evidence condition, not a source defect requiring #1918 reopening.

## Round Trip continuation

Only after authentic A1-A4 evidence:

Round Trip 1 requires governed returned records, recording delivery, durable recording, final allowed InTr exit, and `SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED`.

Master Records/mirror processing occurs between trips.

Round Trip 2 requires mirror-boundary InTr re-entry, declared endpoint call/allow, final ecosystem re-entry, and `SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED`.

Overall terminal remains `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED`.

## Authority boundaries

- Manifest: route declaration/binding only.
- StegVerse Node: continuity/admission anchor; no transition authority.
- Interlock/InTr: transition and governed packet-movement authority.
- Lease: bounded invocation scope only.
- EVENT_EPHEMERAL StegOS runtime: compute/materialization only.
- WorkerCoordinator: claim/fence authority.
- TV/TVC: credential authority.
- Master Records: observed-reality custody/reconstruction authority.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.
- Healer: triggered remediation only.

## Immediate continuation

Validate the reconciliation exact head. Then inspect only StegVerse-native retained evidence for the A1-A4 child and canonical invocation boundary. If no authentic Receipt #1 path or A1-A4 receipt is retained, leave runtime predicates false and continue through the existing native resident request path when that evidence becomes available; do not introduce external runtime/device/host discovery.

## Manual work

None.
