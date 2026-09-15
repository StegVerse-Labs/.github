# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / NODE+INTERLOCK SOURCE BINDING MERGED+VALIDATED / AUTHENTIC INVOCATION EXECUTION PENDING`
- Prior source merge: PR `#1914`, merge commit `7337271028d1226e76af88b33765f38334159b23`
- Node/Interlock binding repair: PR `#1925`, merge commit `0f27c6594c4a55b7ee77e0407523eaa4c9fb8ea7`

## Purpose

Execute the manifest-defined StegBrowser path using the existing StegVerse invocation-owned runtime architecture:

```text
manifest
-> StegVerse Node
-> Interlock
-> InTr
-> bounded lease/execution binding
-> EVENT_EPHEMERAL StegOS runtime
-> WorkerCoordinator claim/fence
-> authentic governed ingress
-> two governed round trips
```

No external runtime/device/host discovery stage exists.

## Goal Chart

### A0 — MANIFEST / PATH CONTRACT

Bind exact Goal, COSV, outbound Interlock/InTr endpoint, owned mirror receiver, Round Trip 1 recording destination, mirror-processing boundary, Round Trip 2 return endpoint, and ecosystem destination.

Predicate: `MANIFEST_BOUND_TO_INVOCATION`.

No route discovery. No endpoint discovery. No receiver discovery.

### A1 — STEGVERSE NODE BINDING

Resolve/reuse the applicable registered/profile-derived StegVerse Node for this manifest invocation.

Node is a continuity/admission anchor; it is NOT a waiting external machine and NOT a standing process prerequisite.

Retain `node_id`, node/profile binding, genesis/continuity commitment, and manifest/Goal/COSV correlation.

Current source implementation: `scripts/run_stegbrowser_runtime_consumption_reusable.py` accepts `node_binding_ref`, validates canonical `stegos.node_handoff_receipt.v1` Receipt #1 with the existing StegOS `validate_node_genesis_receipt`, and fails closed on missing or mismatched Node identity. This source capability does not itself satisfy A1.

### A2 — INTERLOCK / INTR ENTRY

Bind invocation to applicable/declared Interlock and submit the governed InTr materialization transition.

Interlock/InTr decides whether transition/materialization is allowed.

`REQUEST_AUTHORITY = NONE`.

The source repair binds the `interlock_id` from the same validated Receipt #1; source state does not prove an admitted A2 transition.

### A2.1 — BOUNDED LEASE / EXECUTION BINDING

If admitted, establish the invocation-scoped lease/binding and bind Node, Interlock, manifest, Goal, COSV, and requested execution class.

Lease is ephemeral. No standing host relationship is created.

The merged runner binds `manifest_sha256 + node_id + interlock_id + registration_receipt_sha256 + Goal + COSV` into the existing `LeaseRequest` state identity. It reuses the existing materializer and does not create a second runtime path.

### A2.2 — EVENT_EPHEMERAL STEGOS MATERIALIZATION

Materialize the admitted `EVENT_EPHEMERAL` StegOS runtime and bind exact execution-time `runtime_id`.

Required correlation: Node, Interlock, InTr transition, lease/binding, runtime_id, manifest, Goal, COSV.

No pre-existing runtime is required. No generic process host must be exposed to ChatGPT first.

On an authentic invocation, the merged source retains:

`receipts/sovereign-host/stegbrowser-node-interlock-lease-runtime-binding.latest.json`

with exact Node/Interlock/manifest/lease/runtime correlation. Absence of that authentic runtime receipt leaves A2.2 unsatisfied.

### A3 — WORKERCOORDINATOR CLAIM / FENCE

Obtain authentic current `claim_id` and `fencing_token` for this exact invocation.

`CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true`.

Only authentic runtime evidence may satisfy A3.

### A4 — AUTHENTIC INTERLOCK / INTR INGRESS

Enter the declared governed path and retain the exact durable ingress receipt.

Verify as applicable: packet identity, profile, payload hash, packet hash, manifest hash, node_id, interlock_id, lease/runtime binding, Goal, COSV, claim_id, fencing_token.

```text
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = true
AUTHENTIC_INTR_INGRESS_OBSERVED = true
```

The merged A4 worker now carries `manifest_sha256 + node_id + interlock_id + registration_receipt_sha256 + lease_id + runtime_id + Goal + COSV` inside the packet payload. The organization-local receipt binds that payload via exact `payload_hash` and `ingress_packet_sha256` verification.

Only then advance transport.

### A5 — ROUND TRIP 1 OUTBOUND

Follow manifest-declared governed transitions:

```text
ecosystem
-> Interlock/InTr
-> owned mirror reflector
```

No alternate receiver substitution.

### A6 — ROUND TRIP 1 RETURN

Owned mirror reflects the declared records packet.

Return path reaches:

```text
first final allowed Interlock/InTr exit
-> MASTER_RECORDS_RECORDING_SURFACE
```

### A7 — ROUND TRIP 1 VERIFICATION

Require:

```text
GOVERNED_RETURN_PACKET_RECEIVED = true
RECORDS_PACKET_DELIVERED_FOR_RECORDING = true
RETURN_RECORD_DURABLY_RECORDED = true
FIRST_FINAL_ALLOWED_INTR_EXIT_TRANSITION_OBSERVED = true
```

Then:

`SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED = true`.

### B1 — RECORD / RECONSTRUCT / PROCESS

Master Records records, preserves custody, and reconstructs observed state.

Applicable processing advances the result to `STEGVERSE_OWNED_MIRROR_BOUNDARY`.

Master Records does NOT become transport authority. A verified Round Trip 1 remains verified independently of later failure.

### C1 — ROUND TRIP 2 INITIATION

At owned mirror boundary, initiate the declared Interlock/InTr return.

`MIRROR_BOUNDARY_INTR_REENTRY_OBSERVED = true`.

### C2 — ENDPOINT INTERLOCK / INTR

Traverse the governed return and call the declared ecosystem-return endpoint Interlock/InTr.

```text
ENDPOINT_INTERLOCK_INTR_CALLED = true
ENDPOINT_INTERLOCK_INTR_ALLOWED = true
```

### C3 — ECOSYSTEM RE-ENTRY

Observe the final allowed transition into `STEGVERSE_ECOSYSTEM`.

`ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION_OBSERVED = true`.

### C4 — ROUND TRIP 2 VERIFICATION

Require:

```text
MIRROR_BOUNDARY_PROCESSING_COMPLETE = true
MIRROR_BOUNDARY_INTR_REENTRY_OBSERVED = true
ENDPOINT_INTERLOCK_INTR_CALLED = true
ENDPOINT_INTERLOCK_INTR_ALLOWED = true
ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION_OBSERVED = true
```

Then:

`SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED = true`.

## Composition success

```text
SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED
AND
SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED
=>
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED = true
```

## Current authentic state

```text
MANIFEST_BOUND_TO_INVOCATION
    source-bound / runtime confirmation pending

STEGBROWSER_ACTIVE_RESIDENT_REQUEST_DISPATCH_BINDING_VALID
    source-valid

NODE_INTERLOCK_INTR_LEASE_MATERIALIZATION_PATH_IDENTIFIED
    SOURCE IMPLEMENTATION VERIFIED + MERGED
    current invocation proof pending

INVOCATION_OWNED_EPHEMERAL_STEGOS_MATERIALIZED
    NOT OBSERVED

CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
    NOT OBSERVED

ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
    NOT OBSERVED

AUTHENTIC_INTR_INGRESS_OBSERVED
    NOT OBSERVED
```

GitHub source, CI, architectural precedent, and the merged #1925 repair do not promote authentic runtime predicates.

## Reusable-task synchronization

Affected reusable owner: `source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json`.

Required reusable sequence:

```text
MANIFEST_BOUND_TO_INVOCATION
-> validated existing StegVerse Node Receipt #1
-> STEGVERSE_NODE_BOUND_TO_INVOCATION
-> INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
-> INTR_MATERIALIZATION_ADMITTED
-> INVOCATION_SCOPED_LEASE_ESTABLISHED
-> EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
-> EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
-> NODE_INTERLOCK_LEASE_RUNTIME_BINDING_RECEIPT_RETAINED
-> CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
-> ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
-> AUTHENTIC_INTR_INGRESS_OBSERVED
-> Round Trip 1
-> mirror-boundary processing
-> Round Trip 2
```

Reusable-task synchronization grants no runtime authority and never replaces authentic execution evidence.

## Issue #1918

Final source classification: `BOUNDED SOURCE BINDING DEFECT — REMEDIATED`.

The original generic-process-execution-surface premise is retired. Trace proved that the existing Python lane already materialized:

```text
manifest validation
-> LeaseRequest
-> RuntimeClass.EVENT_EPHEMERAL
-> RendezvousRequirement.NOT_REQUIRED
-> SovereignLocalEventRuntimeAdapter.provision()
-> SovereignLocalEventRuntimeAdapter.materialize()
-> execution-time runtime_id
-> WorkerCoordinator / organization-local ingress
```

The exact defect was that the current runner did not first validate and bind the applicable registered StegVerse Node Receipt #1 and its `node_id`/`interlock_id` into the lease/runtime identity and A4 ingress correlation.

PR `#1925` repaired that exact defect and passed deterministic repository, organization-control, and heartbeat validation before merge `0f27c6594c4a55b7ee77e0407523eaa4c9fb8ea7`.

Issue #1918 may therefore close as a completed source-gap issue. Closing #1918 does NOT assert A1/A2/A2.1/A2.2/A3/A4 runtime completion.

## Authority

- Manifest: route declaration only.
- StegVerse Node: continuity/admission anchor.
- Lease: bounded invocation scope only.
- StegOS `EVENT_EPHEMERAL` runtime: compute/execution surface.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition + governed packet movement authority.
- TV/TVC: credential authority.
- Master Records: custody/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Healer invariant

Healer remains triggered remediation only for an observed broken condition. It is not a normal stage owner, scheduler, carrier, prerequisite, Node materializer, or transport authority.

## Immediate continuation

Invoke the canonical reusable path only from an invocation that already owns/resolves the applicable registered StegVerse Node Receipt #1 and supplies its reference as `node_binding_ref`. Observe and retain the new Node/Interlock/lease/runtime binding receipt, then require authentic WorkerCoordinator claim/fence and exact A4 ingress receipt before entering Round Trip 1. Do not add external runtime/device/host discovery.

## Manual work

None.
