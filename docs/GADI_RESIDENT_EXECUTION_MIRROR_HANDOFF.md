# GADI Resident Execution Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `SOURCE_CONTRACTS_RECONCILED / ACTUATOR_OBSERVATION_ADAPTER_MERGED / STEGOS_CONTROLLED_OUTPUT_RECEIPT_SEAM_MERGED / WORKERCOORDINATOR_REGISTRATION_REPAIR_IN_REVALIDATION / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and is not superseded.

Merged trajectory:

- runtime-evidence materialization: `2a86ea27ce222eda7f248e448e17d084004b7ede`;
- local-only source resolution PR #1341: `5b5d795d89b75829c4101719dc8c9f75c227c2d7`;
- handoff reconciliation PR #1351: `04150ebcfc58c275afefb069792461176960b7c8`;
- native StegOS command-contract repair PR #1362: `aad9915f6bfbe48bb75ce78d23e101ed0c3f7ff0`;
- canonical InTr admission-contract repair PR #1366: `0f857232707c7e3c9fa26c320e98f5031b75d76e`;
- WorkerCoordinator claim/fence-contract repair PR #1368: `26b3a8fda10f66946d2467e64e2e29b367c34d5f`;
- governed actuator-observation adapter PR #1369: exact repaired head `7be42c4e779d9b1a59dec7698a5e1f1bf3e2723c` passed organization-control, Heartbeat, and deterministic repository-suite validation and squash-merged as `260c12ea0b3877ffc0829c840dd9f8b9ef7b330a`;
- StegOS controlled-output receipt seam PR #331: exact repaired head `c016858cadae8a159cd7667034c2063b9dab5aca` passed all six observed exact-head validations and squash-merged as `84302fc96502eceb074ce2920b8816eb491b9d83`;
- parent source-chain reconciliation PR #1376: exact head `8c4a4d8c2f209242cf3869f84207c358e054c05e` passed organization-control, deterministic repository-suite, and Heartbeat validation and squash-merged as `9088069ab33f344dd199f9926f65629e95f36293`.

The canonical execution chain remains:

```text
SOURCE RESOLUTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
```

## Authentic source ownership

The four runtime source classes have explicit non-overlapping ownership:

- **StegOS command:** native command state, `intr_decision_ref`, `runtime_binding_ref`, `control_surface`, `target_class`.
- **InTr admission:** canonical admission state and matching `intr_decision_ref`; no runtime-binding ownership.
- **WorkerCoordinator:** authentic `claim_id`, `fencing_token`, worker identity/instance and assignment state; no GADI target/runtime ownership.
- **Actuator observation:** already-executed, controlled pre-authorized governed output, execution subject, observed state/effect, and exact command/runtime bindings.

Canonical staging paths remain:

```text
state/gadi-resident-execution/source/stegos-command.json
state/gadi-resident-execution/source/intr-admission.json
state/gadi-resident-execution/source/worker-claim.json
state/gadi-resident-execution/source/actuator-observation.json
```

## Governed actuator observation adapter — merged

PR #1369 installed `scripts/materialize_gadi_actuator_observation.py` as a non-authorizing adapter for the fourth source class. It accepts only an already-receipted, pre-authorized controlled governed-output observation and preserves exact source SHA-256, runtime/InTr/subject/control/target bindings, while explicitly recording that the adapter executes no actuator and mints no authority.

## StegOS controlled-output receipt seam — merged

StegOS PR #331 added `stegos/gadi_controlled_actuator.py` without creating a second runtime or actuator. `record_controlled_actuator_output()` reuses the caller-supplied existing `StegOSKernel`, receipts only an effect already observed by the runtime caller, and binds the resulting packet to the existing hash-linked runtime receipt chain. Source/CI still do not prove an authentic effect.

## WorkerCoordinator runtime-registration audit — repair in revalidation

Runtime assembly inspection found that the GADI child was source-compatible but not actually claimable through the existing targeted WorkerCoordinator path. Five stale/missing registration projections were identified.

### 1. Missing independent-task-control admission

The existing WorkerCoordinator requires an independently targeted `HANDOFF_READY` task to project `INDEPENDENT_TASK_CONTROL`, `AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM`, `fresh_fence_required=true`, and a non-authorizing heartbeat posture. The executable GADI handoff already authorizes `TARGETED_INDEPENDENT_TASK_CONTROL_ONE_SHOT`, but the GADI registry fragment did not project that existing authority into the task row.

The repair adds the missing non-authorizing admission projection with the current portable fresh-fence floor:

```text
minimum_fencing_token_exclusive = 24
```

This does not mint a claim or fence. It only allows the existing WorkerCoordinator to create a future fresh claim/fence if every other admission predicate passes.

### 2. Missing finite WorkerCoordinator expiry basis

The GADI task had `cost_basis_ref = null`, so the existing WorkerCoordinator would fail closed with `EXPIRY_BASIS_UNAVAILABLE`.

The repair installs `cost-basis/worker-runtime/gadi-resident-execution.json` with an explicitly non-empirical conservative source-bounded estimate:

```text
sample_count = 0
confidence = LOW
expiry_candidate_beats = 16
estimate_basis = CONSERVATIVE_SOURCE_BOUNDED_ONE_SHOT_NOT_EMPIRICAL_RUNTIME_MEASUREMENT
```

No authentic execution timing is claimed.

### 3. Non-terminal relationships incorrectly modeled as terminal worker dependencies

The executable handoff previously placed `GADI-001`, `STEGVERSE-CANONICAL-WORK-COORDINATION-001`, and `TVC-CAPABILITY-RUNTIME-002` inside `task.dependencies`. The generic WorkerCoordinator interprets every such entry as a predecessor worker task that must be `COMPLETED`; because `GADI-001` is intentionally ACTIVE, that made the child permanently unclaimable.

The repair sets `task.dependencies=[]` and preserves those identifiers under `task.coordination_refs`. Actual InTr, TV/TVC, parent-goal, and runtime-evidence requirements remain enforced by the GADI authority/source/preflight chain.

### 4. Stale worker adapter identity

The registered GADI worker pointed to `process:gadi-resident-execution-v1`, while the enabled adapter is `process:gadi-resident-execution-v2-preflight-gated`. The repair aligns the worker row to the already-enabled preflight-gated v2 adapter.

### 5. Incompatible generic worker capability profile

Exact-head validation of PR #1388 exposed another real registration defect: the GADI worker used `control/worker-capability-profiles.json#repository-maintenance-v1`, but current WorkerCoordinator `_worker_for()` validates that every required capability is explicitly allowed by the selected profile. `repository-maintenance-v1` does not allow `gadi_resident_defensive_execution`, so the GADI worker remained correctly unselectable even after its adapter identity was repaired.

The repair adds a dedicated narrow profile:

`control/gadi-worker-capability-profiles.json#gadi-resident-defensive-execution-v1`

It allows exactly:

```text
gadi_resident_defensive_execution
```

with `executor_type=repository_worker`, bounded local mutation, no deployment authority, and explicit statements that profile availability/capability matching grants no authority. The GADI worker now references that narrow profile rather than broadening the shared repository-maintenance profile.

## Exact-head validation failure and regression repair

PR #1388 initial exact head `b94cde8b7c7efbbbebf38998c7289c3622ba05f4` produced:

- organization-control validation: PASS;
- deterministic repository suite: FAIL;
- Heartbeat validation: FAIL at the shared complete deterministic repository-suite step.

The failure was isolated to the new WorkerCoordinator registration regression path rather than an organization-control or authority-plane failure. Inspection of the current admitted runtime showed that normal imports resolve `heartbeat_runtime.worker_runtime.WorkerCoordinator` to the admitted WorkerCoordinator wrapper, whose inherited `_worker_for()` path enforces canonical worker capability profiles. The initial regression incorrectly treated adapter presence as sufficient worker eligibility and therefore failed to model the real profile gate.

The repaired test now loads adapters through the canonical `scripts.run_worker_runtime.load_adapters()` path and asks the admitted WorkerCoordinator to resolve the GADI worker using its actual registry/profile contract. The dedicated GADI capability profile was added because the resulting profile mismatch was a real production registration defect, not bypassed in the test.

### Regression coverage

`tests/test_gadi_workercoordinator_registration.py` now verifies:

- independent-task-control admission projects the existing handoff authority and remains heartbeat-non-authorizing;
- fresh-fence floor is 24;
- the registered worker matches the enabled preflight-gated adapter;
- the worker uses the dedicated narrow GADI capability profile and that profile does not grant authority by availability or capability match;
- runtime/authority relationships are coordination references rather than false terminal worker dependencies;
- `_expiry_budget()` resolves the finite 16-beat LOW-confidence source estimate;
- canonical adapter loading plus the admitted WorkerCoordinator can resolve exactly the GADI worker;
- authentic InTr/runtime/actuator blockers remain present.

This repair only makes the existing task registration structurally eligible for future WorkerCoordinator admission. It does not make current runtime evidence appear and does not itself execute the task.

## Current WorkerCoordinator evidence state

The canonical runtime evidence state remains unchanged while this repair revalidates:

```text
state = HANDOFF_READY
claim_id = null
worker_id = null
worker_instance_id = null
heartbeat_timing = null
lease = null
```

The registered `gadi-resident-execution-worker` remains `AVAILABLE`.

The authentic runtime conditions remain explicitly unobserved:

```text
CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED
CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED
```

No claim, fence, admission, runtime binding, or actuator result is inferred from this registration repair, source availability, or CI.

## Controlled simulation boundary

The historical Continuity controlled-simulation fixture remains semantic evidence only and cannot satisfy authentic runtime execution predicates because it explicitly records no production effect, resident runtime observation, or Master Records reconciliation.

## Remaining authentic completion predicates

1. Revalidate and merge the WorkerCoordinator registration repair without weakening runtime preflight.
2. Produce or locate an authentic current native StegOS GADI command for `GADI-001`.
3. Produce or locate the exact current canonical InTr admission carrying the matching `intr_decision_ref`.
4. Allow the existing WorkerCoordinator to acquire an authentic fresh claim/fence for `GADI-RESIDENT-EXECUTION-001` only after its real admission predicates pass.
5. Bind the actual controlled pre-authorized software test-surface node to the same runtime/control surface/target and observe an actual controlled effect.
6. Receipt that already-observed effect through the merged existing-kernel StegOS controlled-output seam.
7. Project that exact governed-output receipt through the merged `.github` actuator-observation adapter.
8. Run source resolution -> materialization -> preflight -> resident consumption against the exact four authentic source artifacts.
9. Emit and independently inspect the subject-bound resident consumption receipt.
10. Complete closed-loop reassessment/adaptation/termination evidence.
11. Pass the authentic receipt chain to Continuity/Master Records and prove exact reconstruction.
12. Reconcile parent `GADI-001` and the umbrella manifold only from those authentic observations.

## Immediate continuation

After this registration repair validates and merges, inspect the post-claim GADI source-projection order for circularity, then inspect the current Universal InTr/GADI ingress opportunity and runtime-local source state. Do not invoke targeted WorkerCoordinator execution merely because the task becomes structurally claimable. A legitimate claim must still be paired with current admitted GADI runtime evidence and the preflight-gated source chain.

Do not treat GitHub source, CI, historical simulation, a request record, an AVAILABLE worker registration, a capability profile, or the admission projection itself as authentic resident execution evidence.

## Collision boundary

No second heartbeat, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## Evidence boundary

Source implementation, CI validation, registration repair, capability-profile eligibility, compatibility adapters, source projection, test receipts, and historical simulation are not authentic resident execution evidence. Authentic execution remains pending until current runtime-local evidence exists and the resident consumer emits a qualifying subject-bound receipt.

## README impact

`README.md` was reviewed. Existing documentation already defines targeted independent WorkerCoordinator execution, local-only source refresh, resident-request dispatch, WorkerCoordinator authority separation, and non-authorizing HB transport semantics. This repair changes internal GADI task registration consistency and adds no new top-level operator interface; no README mutation is required.

## Release rule

This source/registration repair is not a GADI release or activation. Release/tag propagation remains deferred until authentic resident runtime execution, closed-loop evidence, exact reconstruction, and canonical activation predicates are satisfied.
