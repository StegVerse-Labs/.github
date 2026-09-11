# GADI Resident Execution Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / NONCLAIM_READINESS_MERGED / GOVERNANCE_INTR_ADMISSION_PRODUCER_MERGED / RUNTIME_SUBJECT_BINDING_REPAIR_IN_VALIDATION / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE / CLAIMED_INTEGRATION and is not superseded.

The resident trajectory now has merged source/contract support for:

- native StegOS defensive command validation;
- canonical GADI InTr admission shape;
- WorkerCoordinator claim/fence normalization;
- governed actuator observation projection;
- controlled StegOS output receipt materialization;
- resident source resolution/materialization/preflight/consumption;
- targeted WorkerCoordinator registration and post-claim dispatcher bridging;
- claimless readiness gating and stale-consumption replay protection;
- Governance-owned GADI defensive-intervention profile;
- StegCore governance-decision -> GADI Admission projection.

Authentic current runtime execution is still unobserved. No current claim/fence, concrete runtime binding, current admitted intervention traversal, controlled actuator effect, or new resident-consumption receipt is claimed.

## Relevant merged trajectory

- `.github` PR #1388 -> `261b1636db05baa3d34072236557618e9607b5e7`: targeted WorkerCoordinator registration repair.
- `.github` PR #1395 -> `b1b613452406b26d8fe17a9fbb98b57054a4f046`: post-claim ProcessWorkerAdapter/GADI dispatcher protocol repair.
- `.github` PR #1396 -> `b4b6e467d057b476e1e12fae75097d2b39b3c7e0`: canonical handoff reconciliation.
- `.github` PR #1405 -> `1fe63d76ffd2d499daaeab9a942af5dfef50b4d9`: non-claim readiness convergence repair. This made claimless dispatch resolve only current non-claim evidence first, then visit the existing targeted WorkerCoordinator only when ready; unchanged historical consumption receipts cannot satisfy a new visit.
- `StegVerse-Labs/Governance` PR #40 -> `2765854132872078bcd15a4432a65095831b432e`: authoritative `gadi.defensive-intervention.v1` Universal Governance Connector profile. It reuses `governance-external-action`, full canonical governance/admissibility, separate consequence authority, TV/TVC credential authority, and no execution authority.
- `StegVerse-Labs/StegCore` PR #202 -> `282f30e9e46efc3a8d0d867f48e08c3aa6534e22`: hash-bound governance-decision -> GADI `Admission` projector. `ALLOW` projects `ADMITTED`; `DENY/FAIL-CLOSED` project `DENIED`; runtime binding and execution authority are not minted. The StegCore cross-repo snapshot remains pinned to the authoritative Governance merge.

These merges close the source-level GADI admission producer gap. They do not prove a current runtime admission.

## Canonical execution chain

```text
CURRENT RESIDENT-PRESENCE SUBJECT BINDING
-> CURRENT GOVERNANCE/INTR ADMISSION
-> NATIVE STEGOS COMMAND BOUND TO THAT EXACT RUNTIME SUBJECT
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

WorkerCoordinator remains sole claim/fence authority. HB/runtime-presence remains observation only. TV/TVC remains credential authority. InTr/Governance remains transition/admission authority. GitHub validation does not become runtime authority.

## Runtime subject-binding gap identified

Inspection of the shared runtime-presence architecture established that `control/runtime-node-profiles.json#runtime-node:gadi-resident-execution-001` is only a retained runtime profile declaration. Profile presence must not be treated as a concrete runtime binding.

The canonical shared contract is:

- `management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json`
- `heartbeat_runtime/runtime_presence_projection.py`
- `receipts/sovereign-host/runtime-presence.latest.json`

The existing cross-task correction explicitly requires concrete `runtime_root`, `resident.node_id`, and canonical worker-runtime identity before resident-presence evidence may satisfy a consumer. This GADI repair reuses that exact rule rather than creating another runtime probe or heartbeat plane.

## Current runtime-binding repair — in validation

Branch: `gadi-runtime-binding-observation-001`

### `scripts/materialize_gadi_runtime_binding.py`

This projector reads only local canonical runtime-presence evidence and emits:

`state/gadi-resident-execution/runtime-binding.json`

A binding is emitted only when all of the following are observed:

- canonical runtime-presence schema;
- exact `runtime_root` match to the runtime being evaluated;
- concrete non-empty `resident.node_id`;
- `runtime_alive_observed=true`;
- `present_worker_runtime_observed=true`;
- fresh worker cycle;
- HB explicitly non-authorizing;
- runtime-presence projection explicitly non-authorizing;
- TV/TVC credential boundary intact;
- GitHub token runtime authority `NONE`;
- referenced supervision evidence remains inside the same runtime root;
- supervision evidence explicitly identifies `heartbeat_runtime.engine_v13.HeartbeatRuntime`;
- supervision evidence explicitly identifies `heartbeat_runtime.worker_runtime.WorkerCoordinator`;
- carrier and worker processes are active/separate;
- no third-party process host is required.

When valid, the projector produces a deterministic:

`runtime://gadi/<sha256>`

bound to the exact task/profile, `runtime_root`, `resident.node_id`, canonical carrier/worker identity, exact runtime-presence receipt hash, and exact supervision-receipt hash.

The artifact explicitly records:

```text
claim_or_fence_granted = false
runtime_lease_granted = false
execution_authority_granted = false
heartbeat_grants_execution_authority = false
credential_authority = TV/TVC
github_token_runtime_authority = NONE
authority_effect = NONE_OBSERVATION_ONLY
```

### Runtime observability consumer

`control/runtime-observability-consumers/gadi-resident-execution-001.json` registers GADI as a consumer of the existing shared runtime-presence contract. It does not create a new observer/runtime. Its current predicates remain unobserved until authentic local receipts exist.

### Readiness strengthening

`scripts/run_gadi_targeted_runtime_if_ready.py` now refreshes the GADI runtime-binding observation before source readiness evaluation.

A native GADI command may no longer pass readiness merely because `runtime_binding_ref` is non-empty. Its `runtime_binding_ref` must exactly equal the current subject-bound observation produced from the runtime-presence receipt. A stale/different runtime or node therefore fails closed before WorkerCoordinator is visited.

This closes a previous semantic hole in which a syntactically valid but stale/arbitrary runtime binding could survive the pre-claim readiness gate.

## Regression coverage

`tests/test_gadi_runtime_binding_observation.py` covers:

- current exact runtime subject -> observational binding;
- runtime-root mismatch -> fail closed;
- missing node identity -> fail closed;
- noncanonical WorkerCoordinator identity -> fail closed;
- binding changes when exact presence subject changes;
- no authority/lease/claim minting.

`tests/test_gadi_targeted_runtime_readiness.py` now additionally covers:

- command binding must match current subject-bound runtime binding;
- missing current runtime subject binding prevents WorkerCoordinator visitation;
- missing non-claim inputs still do not trigger targeted execution;
- unchanged old consumption receipt cannot satisfy a new visit;
- changed authentic consumption receipt may satisfy the visit.

## Current authentic evidence boundary

The following remain unobserved until produced on the actual resident runtime:

```text
CURRENT_GADI_RUNTIME_PRESENCE_SUBJECT_NOT_OBSERVED
CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED
CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED
CURRENT_GADI_NATIVE_COMMAND_NOT_OBSERVED
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED
CURRENT_GADI_RESIDENT_CONSUMPTION_NOT_OBSERVED
```

Source code, CI, profile declarations, governance tests, simulated commands, and historical receipts must not satisfy these predicates.

## Immediate continuation after this repair

1. Validate this runtime-binding repair on its exact branch head and merge only if all applicable canonical validation lanes pass.
2. On the actual runtime root, allow the existing canonical runtime-presence projector to emit a current subject-bound receipt; do not create a parallel probe.
3. Materialize the GADI runtime-binding observation from that exact receipt.
4. Use the merged StegCore/Governance path to produce a current hash-bound GADI admission artifact.
5. Materialize a native StegOS command whose `runtime_binding_ref` equals the current GADI binding observation and whose `intr_decision_ref` equals the current admission.
6. Produce the controlled pre-authorized software test-surface output observation through the merged StegOS actuator seam.
7. Only then allow `run_gadi_targeted_runtime_if_ready.py` to visit the canonical targeted WorkerCoordinator and obtain a fresh claim/fence.
8. Require zero-blocker materialization/preflight and a newly changed resident-consumption receipt.
9. Continue closed-loop reassessment/termination and exact Continuity/Master Records reconstruction.

## Collision boundary

No second heartbeat, runtime-presence projector, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, governance evaluator, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

No root README mutation is required for this bounded repair. The repository already documents the shared runtime-presence subject-binding rule, WorkerCoordinator authority separation, runtime convergence, and non-authorizing HB semantics. This change applies those existing rules to GADI.

## Release rule

None of the work above is GADI activation or release evidence. Release/tag propagation remains deferred until authentic current resident execution, adaptive reassessment/termination, complete receipt chain, exact reconstruction, and canonical activation predicates are observed.
