# HIL Same-Device Runtime Supersession — 2026-09-06

Parent canonical handoff: `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`  
Task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`  
Resident request: `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`  
Cross-task predicate: `PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`  
Machine preflight: `receipts/preflight/HIL-CANONICAL-SAME-DEVICE-RECONCILIATION-20260906.json`

## Purpose

This scoped record supersedes only historical HIL continuation prose that described a remote/public shared Gateway as a required causal prerequisite to routine ESRL `LEASE_OPEN`, or that classified the HIL source/control path as incomplete solely because same-device public rendezvous had not been implemented.

It does not replace historical provenance and does not create a new HIL task, runtime, heartbeat, oscillator, scheduler, dispatcher, WorkerCoordinator, claim/fence plane, credential route, transition authority, receiver, or execution surface.

## Current canonical same-device semantics

Current executable and Site state establish:

```text
same_device_execution_required = true
requires_other_machine = false
public_gateway_required_for_lease_open = false
local_identity_readiness_required_for_lease_open = true
public_observation = downstream / optional for routine local LEASE_OPEN
public_observation_authority_effect = NONE
```

Canonical implementation/evidence references:

- `handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json`
- `control/worker-registry.d/hil-sovereign-receiver-001.json`
- `control/cross-task-coordination.json#PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`
- `StegVerse-Labs/Site/docs/HIL_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS@95cb63a823ca86d6a04c44ef5140961ba9161d6a`
- `StegVerse-Labs/.github@2d7d7851a2144dacb2874268a8e16545f9f20d38`
- `StegVerse-Labs/.github@c2ceb4c92909ae5a0ff3a094467aebdce42599bf`
- `StegVerse-Labs/.github#246`

The historical September 3 diagnosis that `OTHER_MACHINE_REQUIRED` was a source/control blocker was valid for the source state observed at that time. It is now superseded by the later same-device `LEASE_OPEN` implementation and `.github` ports above.

## Current machine state

```text
task_id = SHWP-HIL-SOVEREIGN-RECEIVER-001
worker_registry_state = HANDOFF_READY
executor_binding = AUTHORIZED
claim_id = null
fresh_fence_required = true
resident_request = RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
resident_consumption_predicate = PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002
resident_consumption_predicate_state = UNKNOWN
authentic_runtime_execution_observed = false
receiver_ready_observed = false
tvc_lifecycle_receipt_observed = false
master_record_release_ready = false
release_tag_authority = false
```

Source/control completion must not be promoted into runtime execution evidence. The next required evidence remains component-produced evidence from the already-existing same-device runtime path.

## Highest-priority continuation

The existing machine path must continue in this order without creating a duplicate implementation:

1. authentic consumption of `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` or an admitted HIL Universal InTr event;
2. same-device ESRL materialization, local identity/readiness verification, and authentic `LEASE_OPEN`;
3. real WorkerCoordinator claim and fresh fence for `SHWP-HIL-SOVEREIGN-RECEIVER-001`;
4. sovereign HIL receiver canonical ready/active observation;
5. exact receiver/custody evidence and `HIL-RECEIVER-RECEIPT-v2` from one controlled real participant submission/retry when the public participant path is actually observable;
6. post-restart exact-byte reconstruction to the same SHA-256;
7. automatic TVC HIL lifecycle receiving/admission evidence;
8. separately governed private review, authenticated publication, Site projection, and Master Records release predicates.

The acceptance harness `scripts/run_hil_resident_activation_test.py` may report `PASS` only from the exact component-produced evidence denominator already documented in `README.md`. It may not infer request consumption from downstream receiver state, process presence, CI, source merge, heartbeat progression, or materialization alone.

## Master Records boundary

Master Records remains independently owned by `master-records/orchestration` task `HIL-MASTER-RECORD-001`. This reconciliation grants no custody, reconstruction, publication, release, or final Master Record authority and does not satisfy any Master Records upstream evidence dependency.

## README impact

README impact is **non-material** for this reconciliation. The behavior being recorded is already merged and already documented in the repository README's resident HIL activation acceptance-evidence section. This file only prevents historical superseded topology prose from being treated as current source/control truth.

No README update is required for this change.

## Authority

```text
HB / oscillator authority effect = NONE for execution/admission/claim/fence/transition
WorkerCoordinator = claim/fence execution ownership
Interlock/InTr = transition admissibility
TV/TVC = credential authority
GitHub token runtime authority = NONE
this document authority effect = NONE_DOCUMENTATION_RECONCILIATION_ONLY
```
