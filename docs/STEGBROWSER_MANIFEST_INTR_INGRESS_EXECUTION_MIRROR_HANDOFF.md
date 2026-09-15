# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / PR #1914 MERGED / NODE+INTERLOCK LEASE+A4 SOURCE REPAIR IMPLEMENTED / EXACT-HEAD VALIDATION PENDING / AUTHENTIC A1-A4 PENDING`
- Prior source merge: PR `#1914`, merge commit `7337271028d1226e76af88b33765f38334159b23`
- Current source-repair PR: `#1923`
- Current branch: `fix/stegbrowser-node-interlock-lease-binding`

## Goal

Execute the manifest-defined StegBrowser path through the existing invocation-owned architecture:

```text
manifest
-> applicable registered/profile-derived StegVerse Node Receipt #1
-> Node-bound Interlock
-> governed InTr materialization
-> bounded invocation lease/state binding
-> EVENT_EPHEMERAL StegOS runtime
-> execution-time runtime identity binding
-> WorkerCoordinator claim/fence
-> exact A4 Interlock/InTr ingress
-> Round Trip 1
-> Master Records/mirror processing
-> Round Trip 2
-> ecosystem re-entry
```

No external runtime/device/host discovery stage exists.

## Current source implementation

PR #1923 now implements the bounded Node/Interlock repair on its branch:

1. the runner requires an applicable registered StegVerse Node Receipt #1 through `node_genesis_receipt` / `STEGVERSE_NODE_GENESIS_RECEIPT`;
2. Receipt #1 is validated with `StegOS/stegos/network_manifold.py::validate_node_genesis_receipt`;
3. exact `node_id`, `interlock_id`, and `registration_receipt_sha256` are consumed from the validated receipt;
4. `manifest_sha256 + node_id + interlock_id + registration_receipt_sha256 + Goal + COSV` are bound into the invocation lease/state identity;
5. the resulting `lease_id + runtime_id + state_root_binding` are bound back to the same invocation identity;
6. a durable `stegverse.stegbrowser-node-interlock-runtime-binding/v1` receipt is retained in both the EVENT_EPHEMERAL runtime and resident evidence roots;
7. A4 loads that exact binding receipt and carries `manifest_sha256 + node_id + interlock_id + registration_receipt_sha256 + lease_id + runtime_id + state_root_binding` in the organization-local packet;
8. the existing organization-local receipt must still verify exact payload hash + full packet hash and authentic WorkerCoordinator `claim_id + fencing_token` before A4 is accepted;
9. the runner fails closed on a missing/invalid Receipt #1, manifest mismatch, incomplete Node/Interlock binding, lease/runtime mismatch, or incomplete A4 correlation.

This source repair does not promote runtime predicates. It is pending exact-head validation and merge.

## Existing reusable implementations reused

No duplicate Node or Interlock implementation was created.

- `StegOS/stegos/network_manifold.py::validate_node_genesis_receipt` is the canonical Receipt #1 validator reused by the runner.
- `StegOS/stegos/sovereign_local_event_runtime.py::SovereignLocalEventRuntimeAdapter` remains the EVENT_EPHEMERAL compute/materializer/identity adapter.
- `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` remains the bounded local A3/A4 execution boundary.
- `workers/stegbrowser_manifest_intr_ingress.py` remains the StegBrowser A4 adapter and now requires exact Node/Interlock/lease/runtime correlation.

Historical SV002/Site evidence remains architectural precedent only and does not promote current StegBrowser predicates.

## Reusable-task synchronization

Canonical reusable owner:

`source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json`

Current reusable source conformance:

`NODE_INTERLOCK_BINDING_SOURCE_IMPLEMENTED_VALIDATION_PENDING`

The same branch synchronizes:

- reusable task definition;
- resident execution request;
- legacy materialization runner;
- active wrapper/A3-A4 projection;
- A4 ingress worker;
- canonical continuation task record;
- affected regression tests;
- this handoff.

Standing rule: every reusable architecture confirmation/correction must update the reusable task and affected request/test/profile consumers in the same change. No deferred cleanup pass.

## Current Goal Chart

### A0 — Manifest

Bind exact Goal/COSV and manifest-defined route. No endpoint or receiver discovery.

### A1 — Registered Node binding

Consume and validate applicable registered/profile-derived StegVerse Node Receipt #1.

Source implementation now requires:

```text
schema = stegos.node_handoff_receipt.v1
receipt_number = 1
transition = NODE_REGISTERED
node_id = non-empty
interlock_id = non-empty
receipt_sha256 = valid
```

Runtime terminal for this stage remains:

`STEGVERSE_NODE_BOUND_TO_INVOCATION = true`

### A2 — Interlock/InTr + invocation lease

Bind the validated Node's `interlock_id` to the exact manifest invocation. The lease/state identity is derived from:

```text
manifest_sha256
node_id
interlock_id
registration_receipt_sha256
Goal
COSV
canonical task/registry hashes
```

Runtime predicates remain:

```text
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
INTR_MATERIALIZATION_ADMITTED
INVOCATION_SCOPED_LEASE_ESTABLISHED
```

### A2.2 — EVENT_EPHEMERAL runtime identity

Materialize through the existing `SovereignLocalEventRuntimeAdapter` with:

```text
RuntimeClass.EVENT_EPHEMERAL
RendezvousRequirement.NOT_REQUIRED
persistent_host_required = false
participant_machine_required = false
developer_machine_required = false
```

Bind `lease_id + runtime_id + state_root_binding` back to the same manifest/Node/Interlock identity and retain the durable binding receipt.

Runtime predicates remain:

```text
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
```

### A3 — WorkerCoordinator

Require authentic exact `claim_id + fencing_token` for this invocation from the existing organization-local boundary.

### A4 — Interlock/InTr ingress

Require exact durable ingress receipt whose verified packet is correlated to:

```text
manifest_sha256
node_id
interlock_id
registration_receipt_sha256
lease_id
runtime_id
state_root_binding
Goal
COSV
claim_id
fencing_token
```

Only then may transport proceed.

### Round Trip 1

```text
StegVerse ecosystem
-> declared Interlock/InTr endpoint
-> owned mirror reflector
-> reflected records packet
-> first final allowed Interlock/InTr exit
-> Master Records recording
```

Terminal predicate:

`SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED`

### Between trips

Master Records recording/custody/reconstruction and declared mirror-boundary processing. No transport authority transfer.

### Round Trip 2

```text
owned mirror boundary
-> Interlock/InTr re-entry
-> endpoint Interlock/InTr
-> final allowed ecosystem re-entry
```

Terminal predicate:

`SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED`

Composition terminal:

`SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED`

## Current predicates

```text
MANIFEST_BOUND_TO_INVOCATION = source implementation present; authentic invocation confirmation pending
STEGBROWSER_ACTIVE_RESIDENT_REQUEST_DISPATCH_BINDING_VALID = true at source
STEGVERSE_NODE_BOUND_TO_INVOCATION = false / source implementation pending validation+runtime evidence
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false / source implementation pending validation+runtime evidence
INTR_MATERIALIZATION_ADMITTED = false / not authentically observed
INVOCATION_SCOPED_LEASE_ESTABLISHED = false / source implementation pending validation+runtime evidence
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false / not authentically observed for corrected path
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false / source implementation pending validation+runtime evidence
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false / not authentically observed
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false / source implementation pending validation+runtime evidence
AUTHENTIC_INTR_INGRESS_OBSERVED = false / not authentically observed
```

No runtime predicate is promoted from source implementation, historical evidence, CI, or GitHub state.

## Issue #1918

Issue #1918 is the bounded Node/Interlock/lease/runtime/A4 source-binding defect. PR #1923 now contains the implementation repair; issue disposition remains open until exact-head validation and merge complete. Runtime closure is separate.

## Authority boundaries

- Manifest: route declaration/binding only.
- StegVerse Node: continuity/admission anchor; no independent transition authority.
- Interlock/InTr: transition and governed packet-movement authority.
- Lease: bounded invocation scope only.
- EVENT_EPHEMERAL StegOS runtime: compute/materialization surface only.
- WorkerCoordinator: claim/fence authority.
- TV/TVC: credential authority.
- Master Records: custody/reconstruction authority; not transport-success authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Immediate continuation

Run exact-head organization-control, deterministic repository suite, and Heartbeat validation for PR #1923. Repair only proven source-contract failures. Merge only a head where all required lanes pass. After merge, invoke the corrected path and promote A1/A2/A3/A4 only from authentic durable runtime evidence.

## Manual work

None.
