# COSV Task Pointer Runtime Enforcement Mirror Handoff

Status: SOURCE_RUNTIME_ENFORCEMENT_PATH_IMPLEMENTED / AUTHENTIC_RUNTIME_CONSUMPTION_PENDING
Repository: `StegVerse-Labs/.github`
Task ID: `COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001`
Root correlation / goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Parent task: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Canonical pointer policy: `data/task-coordination-policy.json`
Pointer contract handoff: `docs/COSV_TASK_POINTER_COORDINATION_MIRROR_HANDOFF.md`
Reusable construct handoff: `docs/REUSABLE_TASK_EPHEMERAL_CONSTRUCT_MIRROR_HANDOFF.md`
Reusable registry: `data/reusable-task-registry.json#generation-2`
Reusable construct contract: `data/reusable-task-ephemeral-construct-contract.json`
COSV profile: `management/COSV_PROFILE_V1.json#task.v1`
Machine preflight: `receipts/preflight/COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001.json`
Resident execution request: `control/resident-execution-request.d/cosv-task-pointer-runtime-enforcement-001.json`
Resident consumer: `scripts/consume_cosv_task_pointer_runtime_enforcement_request.py`
Resident dispatcher: `scripts/dispatch_resident_execution_requests.py#cosv_task_pointer_runtime_enforcement`
Resident execution bridge: `scripts/refresh_and_execute_resident_task.py`
Expected consumption receipt: `receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json`

## Purpose

Implement machine/runtime enforcement so a continuation payload containing only:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

can resolve complete canonical task context, applicable reusable identities, and the exact invocation-specific TT/RTG/GTG construct needed for the highest-priority admissible work without repeated prompt prose or permanent one-off runners.

## Implemented source behavior

The source path now includes:

1. canonical `task_id + task.v1 vector` continuation policy;
2. durable reusable-task identity registry generation 2;
3. invocation-specific parameter contract;
4. deterministic `scripts/materialize_reusable_task_construct.py` source constructor;
5. manifest schema binding reusable identity, parameters, optional task/COSV pointer, derived RTG/GTG/TT envelopes, runner plan, authority, recording, and entropy-recovery conditions;
6. shared identity model for maintenance, InTr protocol establishment, external adapters, AI adapters, endpoint monitoring, and social-platform interaction;
7. explicit ephemeral-runner lifecycle and residual non-executing recording semantics;
8. the existing resident targeted execution bridge extended with optional `--cosv-task-vector` validation;
9. exact pointer validation after already-local source refresh and before the existing WorkerCoordinator execution command;
10. fail-closed handling for malformed vectors, missing or duplicate task identities, missing source-vector provenance, and task/vector mismatch;
11. resident targeted-execution receipt schema v3 carrying the verified non-authorizing `cosv_task_pointer` projection;
12. the canonical resident request passing both `--task-id COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001` and `--cosv-task-vector 10100000100000`;
13. a dedicated request consumer that verifies the request and requires the execution bridge to report the exact verified pointer before recording `ATTEMPT_RECORDED`;
14. registration of that consumer in the existing independent resident dispatcher; and
15. propagation of the consumer through the existing local-only WorkerCoordinator source refresh.

No second task registry, COSV profile, scheduler, WorkerCoordinator, heartbeat, oscillator, credential authority, transition authority, dispatcher, or permanent runner plane was created.

## Exact resident path

```text
already-local canonical source
-> scripts/refresh_sovereign_worker_runtime_source.py
-> refreshed control/task-vector-index.json
-> refreshed resident request + COSV consumer + dispatcher + targeted execution bridge
-> scripts/dispatch_resident_execution_requests.py
-> selector cosv_task_pointer_runtime_enforcement
-> scripts/consume_cosv_task_pointer_runtime_enforcement_request.py
-> scripts/refresh_and_execute_resident_task.py
-> exact task_id + task.v1 vector validation
-> existing scripts/run_worker_runtime.py targeted WorkerCoordinator cycle
-> ordinary WorkerCoordinator claim/fence + Interlock/InTr governed transition path
-> runtime receipts / Master Records evidence
```

Pointer validation occurs before targeted execution and has `authority_effect=NONE`. WorkerCoordinator remains claim/fence authority, Interlock/InTr remains governed transition authority, TV/TVC remains credential authority, and Master Records remains observed-reality/reconstruction authority.

## Current request

The request at `control/resident-execution-request.d/cosv-task-pointer-runtime-enforcement-001.json` binds:

```text
task_id: COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001
profile: task.v1
vector: 10100000100000
mode: TARGETED_INDEPENDENT_TASK_CONTROL
entrypoint: scripts/refresh_and_execute_resident_task.py
argv: ... --task-id COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001 --cosv-task-vector 10100000100000
```

The request and consumer are coordination/execution-path materialization only. They mint no WorkerCoordinator claim/fence, Interlock/InTr admission, TV/TVC credential authority, or Master Records runtime truth.

## Remaining runtime work

Authentic runtime evidence must still demonstrate:

1. a resident local-source refresh carrying this source revision into the authentic resident runtime;
2. resident dispatcher visitation of `cosv_task_pointer_runtime_enforcement`;
3. component-produced consumption receipt with `pointer_binding_verified_before_execution=true`;
4. ordinary WorkerCoordinator admission and fresh claim/fence for the task when execution is admissible;
5. applicable Interlock/InTr governed transition admission;
6. reusable identity + invocation-parameter resolution for a real bounded invocation;
7. exact manifest-bound RTG -> GTG -> TT derivation under canonical definitions;
8. bounded runner materialization, execution, and expiry;
9. chained runtime receipts and residual recording-only behavior after runner expiry;
10. required recording projections;
11. Master Records custody and reconstruction;
12. observed entropy recovery after reconstruction; and
13. adjacent canonical task derivation when genuinely distinct same-goal work appears.

## Current COSV state

```text
profile: task.v1
vector: 10100000100000
symbol_order: LRUIVGOCMTBEAP
lifecycle: UNCLAIMED
archive_ready: false
unassigned_work: 1
chat_owned_implementation: 0
chat_owned_validation: 0
chat_owned_integration: 0
chat_owned_observation: 0
chat_owned_credentials: 0
canonical_owner_installed: true
thread_required: false
blocker_count: 0
evidence_complete: false
activated: false
propagated: false
```

The vector remains unchanged because source mutation, request registration, dispatcher registration, and propagation eligibility are not a WorkerCoordinator claim, authentic resident execution receipt, Master Records custody/reconstruction proof, or activation proof.

## Validation and evidence boundary

Source tests cover exact pointer resolution, fail-closed vector mismatch, duplicate task identity, and malformed vector. Source merge/commit presence and tests are not authentic resident runtime evidence.

The expected first authentic evidence is:

```text
receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json
```

with an actual resident execution attempt and `pointer_binding_verified_before_execution=true`. Broader completion remains false until the downstream claim/fence, InTr, invocation construct, receipt chain, Master Records reconstruction, and entropy-recovery predicates are observed.

## README completeness

`README.md` now documents the resident `--cosv-task-vector` interface, fail-closed refreshed-index verification, resident dispatcher consumer, local source propagation, receipt semantics, and the unchanged authority boundaries. This satisfies the task-specific machine preflight README-impact requirement for the implemented source change.
