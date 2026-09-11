# GADI Resident Execution Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / NONCLAIM_READINESS_MERGED / GOVERNANCE_INTR_ADMISSION_PRODUCER_MERGED / RUNTIME_SUBJECT_BINDING_MERGED / NATIVE_COMMAND_ARTIFACT_BRIDGE_MERGED / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE / CLAIMED_INTEGRATION and is not superseded.

The source/contract chain now contains all of the following without introducing parallel authority planes:

- canonical runtime evidence source resolution/materialization/preflight/consumption;
- native StegOS defensive planning and command validation;
- Governance-owned GADI connector profile;
- StegCore governance-decision -> GADI Admission projection;
- current subject-bound GADI runtime-binding observation;
- exact native-command artifact bridge from plan + admitted request + current runtime binding;
- controlled StegOS actuator-output receipt seam;
- WorkerCoordinator claim/fence normalization and targeted worker bridge;
- non-claim readiness gating and stale-consumption replay protection.

Authentic current runtime execution is still unobserved. Source, CI, merged code, profile declarations, and simulation evidence do not satisfy runtime predicates.

## Relevant merged trajectory

- `.github` PR #1388 -> `261b1636db05baa3d34072236557618e9607b5e7`: targeted WorkerCoordinator registration repair.
- `.github` PR #1395 -> `b1b613452406b26d8fe17a9fbb98b57054a4f046`: post-claim ProcessWorkerAdapter/GADI dispatcher bridge.
- `.github` PR #1396 -> `b4b6e467d057b476e1e12fae75097d2b39b3c7e0`: canonical handoff reconciliation.
- `.github` PR #1405 -> `1fe63d76ffd2d499daaeab9a942af5dfef50b4d9`: non-claim readiness convergence and stale-consumption replay protection.
- `StegVerse-Labs/Governance` PR #40 -> `2765854132872078bcd15a4432a65095831b432e`: authoritative `gadi.defensive-intervention.v1` profile reusing `governance-external-action`; no execution authority.
- `StegVerse-Labs/StegCore` PR #202 -> `282f30e9e46efc3a8d0d867f48e08c3aa6534e22`: exact governance-decision -> GADI Admission projection; no runtime binding or execution authority minted.
- `.github` PR #1413 -> `71338d71c7122e7be9d4a1015e2bde353a3ff0e6`: current runtime-root/node subject binding from canonical runtime-presence evidence and exact readiness enforcement.
- `StegVerse-Labs/StegOS` PR #337 -> `0409aadbc894c9d0976e41a946b588ef93c34b8d`: native command artifact bridge. Exact head `c597ff3f7791040e0d3f247072821bd81f59d86d` passed all six observed StegOS validation lanes before merge.

## Canonical execution chain

```text
CURRENT RESIDENT-PRESENCE SUBJECT BINDING
-> CURRENT PRE-ADMISSION NATIVE DEFENSE PLAN
-> CURRENT GOVERNANCE / INTR ADMISSION
-> NATIVE STEGOS COMMAND BOUND TO EXACT RUNTIME SUBJECT
-> CONTROLLED PREAUTHORIZED OUTPUT OBSERVATION
-> NON-CLAIM READINESS
-> TARGETED WORKERCOORDINATOR CLAIM/FENCE
-> SOURCE RESOLUTION WITH CLAIM DEFERRED
-> FRESH CLAIM PROJECTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
-> REASSESSMENT / TERMINATION
-> CONTINUITY / MASTER RECORDS RECONSTRUCTION
```

WorkerCoordinator remains sole claim/fence authority. HB/runtime-presence remains observation only. TV/TVC remains credential authority. Governance/InTr remains transition/admission authority. GitHub validation does not become runtime authority.

## Runtime subject binding — merged

`scripts/materialize_gadi_runtime_binding.py`, merged by PR #1413, consumes only canonical runtime-presence and referenced supervision evidence. It emits `state/gadi-resident-execution/runtime-binding.json` only when the exact runtime root, resident node ID, canonical carrier runtime, canonical WorkerCoordinator identity, process separation, worker-cycle freshness, and non-authority boundaries are observed.

The binding is deterministic as `runtime://gadi/<sha256>` and explicitly grants no claim/fence, lease, execution authority, heartbeat authority, GitHub-token authority, or credentials.

`run_gadi_targeted_runtime_if_ready.py` requires the native command's `runtime_binding_ref` to equal this current binding exactly before WorkerCoordinator may be visited.

## Governance / InTr admission producer — merged

Governance PR #40 provides the authoritative GADI profile. StegCore PR #202 binds the exact PENDING intervention-request candidate hash to a canonical governance result and projects:

```text
ALLOW       -> ADMITTED + intr://governance-decision/<receipt_hash>
DENY        -> DENIED   + intr://governance-decision/<receipt_hash>
FAIL-CLOSED -> DENIED   + intr://governance-decision/<receipt_hash>
```

The projection mints no runtime binding, credential, continuity authority, or execution authority.

## Native command artifact bridge — merged

StegOS PR #337 adds `stegos/gadi_native_command_bridge.py` and uses the existing `materialize_native_defensive_command()` implementation rather than adding a second planner or command authority.

The bridge accepts exactly:

1. a serialized pre-admission StegOS `NativeDefensePlan` with one already-selected discoverable TV/TVC capability;
2. a canonical GADI intervention request whose admission is `ADMITTED` and whose `required_capability_id` exactly matches the plan;
3. the current `stegverse.gadi-runtime-binding-observation/v1` in state `CURRENT_RUNTIME_SUBJECT_BOUND`.

It rejects PENDING/DENIED requests, capability mismatch, stale or wrong runtime subject, claim/lease/execution-authority drift, heartbeat authority drift, GitHub-token authority, or selected-capability preclaim.

On success the existing native materializer receives the exact admitted `intr_decision_ref` and exact current `runtime_binding_ref`. Reconstruction bindings are retained for intervention request, receipt correlation, threat observation, runtime root, and resident node. StegOS still records `execution_authority_claimed_by_stegos=false`.

## Controlled output seam

StegOS PR #331 remains the merged controlled-output receipt seam. `stegos/gadi_controlled_actuator.py` can receipt an effect that the caller has already authentically observed through the existing StegOS kernel chain. The recorder does not execute the actuator and cannot substitute for an actual controlled effect observation.

## Current authentic evidence boundary

The following remain unobserved until produced on the actual resident runtime:

```text
CURRENT_GADI_RUNTIME_PRESENCE_SUBJECT_NOT_OBSERVED
CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED
CURRENT_GADI_PRE_ADMISSION_PLAN_NOT_OBSERVED
CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED
CURRENT_GADI_NATIVE_COMMAND_NOT_OBSERVED
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED
CURRENT_GADI_RESIDENT_CONSUMPTION_NOT_OBSERVED
```

A future WorkerCoordinator claim is valid only when created by the actual targeted runtime invocation after all non-claim evidence is coherent. It must not be fabricated or retained from source-only state.

## Immediate continuation

1. On the actual runtime root, obtain a current canonical runtime-presence receipt and materialize the subject-bound GADI runtime binding; do not create a parallel runtime probe.
2. Materialize a current pre-admission `NativeDefensePlan` from an actual boundary interaction plus current discoverable TV/TVC capability evidence.
3. Submit the exact intervention request through the merged Governance/StegCore path and obtain the matching current ADMITTED artifact.
4. Feed the exact plan + admitted request + current runtime binding through the merged StegOS native-command bridge.
5. Observe the controlled pre-authorized software test-surface effect and receipt it through the merged StegOS actuator seam.
6. Let `run_gadi_targeted_runtime_if_ready.py` verify those non-claim artifacts; only then visit the canonical targeted WorkerCoordinator for a fresh claim/fence.
7. Require zero-blocker materialization/preflight and a newly changed resident-consumption receipt.
8. Complete adaptive reassessment/termination, Continuity custody, Master Records reconciliation, and exact confrontation reconstruction.

## Collision boundary

No second heartbeat, runtime-presence projector, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, governance evaluator, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

No root README mutation is required. Existing documentation already defines runtime-presence subject binding, WorkerCoordinator authority separation, runtime convergence, and non-authorizing HB semantics.

## Release rule

None of the source/contract merges above is GADI activation or release evidence. Release/tag propagation remains deferred until authentic current resident execution, adaptive reassessment/termination, complete receipt chain, exact reconstruction, and canonical activation predicates are observed.
