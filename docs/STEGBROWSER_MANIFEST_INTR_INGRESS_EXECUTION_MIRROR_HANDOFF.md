# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / NODE+INTERLOCK LEASE+A4 SOURCE MERGED+VALIDATED / AUTHENTIC A1-A4 EXECUTION PENDING`
- Prior source merge: PR `#1914`, merge `7337271028d1226e76af88b33765f38334159b23`
- Node/Interlock source repair: PR `#1923`, validated head `f7b6cb86b9fff9fbeb1817e45920acc2effc200f`, merge `0098bc793865fd1db835c400b502dad5f8a5e32d`
- Validation runs: organization control `34970252692`; deterministic suite `34970252614`; Heartbeat validation `34970252669`

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
-> Master Records / mirror processing
-> Round Trip 2
-> ecosystem re-entry
```

There is no external runtime/device/host discovery stage, no waiting online runtime, no generic chat-session process host, and no second user-operated device prerequisite.

## Source state

PR #1923 is merged and exact-head validated. Source now:

1. requires an applicable registered StegVerse Node Receipt #1 through `node_genesis_receipt` / `STEGVERSE_NODE_GENESIS_RECEIPT`;
2. validates Receipt #1 with `StegOS/stegos/network_manifold.py::validate_node_genesis_receipt`;
3. consumes exact `node_id`, `interlock_id`, and `registration_receipt_sha256`;
4. binds `manifest_sha256 + node_id + interlock_id + registration_receipt_sha256 + Goal + COSV` into the invocation lease/state identity;
5. binds resulting `lease_id + runtime_id + state_root_binding` back to the same invocation identity;
6. retains `stegverse.stegbrowser-node-interlock-runtime-binding/v1` as durable evidence;
7. carries exact manifest/Node/Interlock/registration/lease/runtime/state-root correlation into the A4 organization-local packet;
8. requires exact packet/payload-hash verification plus authentic WorkerCoordinator `claim_id + fencing_token` before A4 can be accepted;
9. fails closed on missing/mismatched Node, Interlock, manifest, lease, runtime, or A4 correlation.

No runtime predicate was promoted by PR #1923, CI, source reconciliation, or historical SV002 evidence.

## Reusable-task synchronization

Canonical reusable owner:

`source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json`

Current reusable source conformance:

`NODE_INTERLOCK_BINDING_SOURCE_MERGED_VALIDATED_RUNTIME_EVIDENCE_PENDING`

Standing rule: every reusable architecture confirmation or correction must update the reusable task and affected request/test/profile consumers in the same workstream. No deferred cleanup pass.

## Current Goal Chart

### A0 — Manifest/path contract

Bind exact Goal/COSV and declared outbound endpoint, owned mirror receiver, Round Trip 1 recording target, mirror-processing boundary, Round Trip 2 endpoint, and ecosystem destination. No endpoint or receiver discovery.

### A1 — Registered Node binding

Consume and validate the applicable registered/profile-derived StegVerse Node Receipt #1:

```text
schema = stegos.node_handoff_receipt.v1
receipt_number = 1
transition = NODE_REGISTERED
node_id = non-empty
interlock_id = non-empty
receipt_sha256 = valid
```

Runtime predicate:

`STEGVERSE_NODE_BOUND_TO_INVOCATION`

### A2 — Interlock/InTr + bounded lease

Bind the validated Node's Interlock to the exact manifest invocation. Lease/state identity binds:

```text
manifest_sha256
node_id
interlock_id
registration_receipt_sha256
Goal
COSV
canonical task/registry hashes
```

Runtime predicates:

```text
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
INTR_MATERIALIZATION_ADMITTED
INVOCATION_SCOPED_LEASE_ESTABLISHED
```

### A2.2 — EVENT_EPHEMERAL StegOS runtime identity

Use existing `SovereignLocalEventRuntimeAdapter` with:

```text
RuntimeClass.EVENT_EPHEMERAL
RendezvousRequirement.NOT_REQUIRED
persistent_host_required = false
participant_machine_required = false
developer_machine_required = false
```

Bind `lease_id + runtime_id + state_root_binding` back to the same manifest/Node/Interlock identity and retain the durable binding receipt.

Runtime predicates:

```text
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
```

### A3 — WorkerCoordinator

Require authentic exact `claim_id + fencing_token` from the existing organization-local boundary for this invocation.

Runtime predicate:

`CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED`

### A4 — Authentic Interlock/InTr ingress

Require durable receipt whose verified packet is correlated to:

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

Runtime predicates:

```text
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
AUTHENTIC_INTR_INGRESS_OBSERVED
```

Only after authentic A1-A4 evidence may transport advance.

### Round Trip 1

```text
StegVerse ecosystem
-> declared Interlock/InTr endpoint
-> owned mirror reflector
-> reflected records packet
-> first final allowed Interlock/InTr exit
-> Master Records recording
```

Require:

```text
GOVERNED_RETURN_PACKET_RECEIVED
RECORDS_PACKET_DELIVERED_FOR_RECORDING
RETURN_RECORD_DURABLY_RECORDED
FIRST_FINAL_ALLOWED_INTR_EXIT_TRANSITION_OBSERVED
SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED
```

### Between trips

Master Records records/preserves/reconstructs and applicable processing advances to the declared owned mirror boundary. This does not transfer transport authority and cannot retroactively erase a verified Round Trip 1.

### Round Trip 2

```text
owned mirror boundary
-> Interlock/InTr re-entry
-> declared endpoint Interlock/InTr
-> final allowed StegVerse ecosystem re-entry
```

Require:

```text
MIRROR_BOUNDARY_PROCESSING_COMPLETE
MIRROR_BOUNDARY_INTR_REENTRY_OBSERVED
ENDPOINT_INTERLOCK_INTR_CALLED
ENDPOINT_INTERLOCK_INTR_ALLOWED
ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION_OBSERVED
SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED
```

Then and only then:

`SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED`

## Current authentic predicates

```text
MANIFEST_BOUND_TO_INVOCATION = source implementation present; runtime confirmation pending
STEGBROWSER_ACTIVE_RESIDENT_REQUEST_DISPATCH_BINDING_VALID = true at source
STEGVERSE_NODE_BOUND_TO_INVOCATION = false / not authentically observed
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false / not authentically observed
INTR_MATERIALIZATION_ADMITTED = false / not authentically observed
INVOCATION_SCOPED_LEASE_ESTABLISHED = false / not authentically observed
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false / not authentically observed on corrected path
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false / not authentically observed
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false / not authentically observed
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false / not authentically observed
AUTHENTIC_INTR_INGRESS_OBSERVED = false / not authentically observed
```

Current exact defect:

`AUTHENTIC_NODE_INTERLOCK_LEASE_RUNTIME_A3_A4_EVIDENCE_NOT_YET_OBSERVED`

## Issue #1918 disposition

Issue #1918 represented the bounded source defect in Node/Interlock/lease/runtime/A4 correlation. PR #1923 fixes that source defect and is merged+validated. Issue #1918 may therefore close as source-complete; authentic runtime closure remains owned by this active Goal/handoff.

## Authority boundaries

- Manifest: route declaration/binding only.
- StegVerse Node: continuity/admission anchor; no independent transition authority.
- Interlock/InTr: transition and governed packet-movement authority.
- Lease: bounded invocation scope only.
- EVENT_EPHEMERAL StegOS runtime: compute/materialization surface only.
- WorkerCoordinator: claim/fence authority.
- TV/TVC: credential authority.
- Master Records: observed-reality custody/reconstruction authority; not transport-success authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Immediate continuation

Execute the corrected manifest-bound invocation using the applicable registered/profile-derived Node Receipt #1. Retain authentic A1-A4 durable evidence with exact manifest/Node/Interlock/registration/lease/runtime/claim/fence correlation. Advance to Round Trip 1 only if those predicates are authentically proven.

## Manual work

None.
