# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
PR: `StegVerse-Labs/.github#1344`
Status: `ACTIVE / CHECKED_OUT / REGISTRY-BOUNDARY DISPOSITION IMPLEMENTED / CANONICAL WORK PREFLIGHT BOUND / PORTABLE WORKERCOORDINATOR PRECLAIM GATE BOUND / EXACT-HEAD VALIDATION PENDING`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition derived from current canonical task records, and no WorkerCoordinator claim may be minted from the portable current-iPhone path unless that exact task has a current `CONTINUE` disposition.

## Required dispositions

- `CONTINUE` — no current collision candidate discovered.
- `COORDINATE_CONVERGENCE` — overlapping active work exists; coordinate before mutation.
- `STOP_COLLISION` — a currently checked-out task overlaps the same component or task lineage strongly enough that this session should end and continue only through the returned collision owner/convergence path.
- `STOP_SUPERSEDED` — canonical task state is superseded/retired with a continuation task.
- `STOP_INACTIVE` — canonical task is inactive/retired without a continuation.
- `STOP_NOT_REGISTERED` — task is absent from canonical task records and must not mutate source until registered/reconciled.

## Response requirements

The evaluator returns task ID, canonical handoff when available, disposition, session action, collision candidates, overlapping repositories/components, lineage/adjacency evidence, hard-collision task IDs, continuation task/handoff when applicable, and `authority_effect=NONE`.

## Current implementation

- `data/canonical-task-records/TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001.json`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `workercoordinator/portable_checkout.js`
- `tests/test_task_registry_collision_checkin.py`
- `tests/test_portable_workercoordinator_registry_gate.py`

The evaluator reads all canonical task records at check-in time. It does not grant execution authority, replace WorkerCoordinator claims/fences, or treat GitHub as runtime authority.

Canonical Work event bootstrap executes the registry collision preflight before route installation or bounded work bootstrap. Only `CONTINUE` proceeds automatically. `COORDINATE_CONVERGENCE` and every `STOP_*` result fail closed before mutation and surface the complete `TASK_REGISTRY_CHECKIN` JSON to the caller/session. A missing evaluator, malformed response, identity mismatch, or non-NONE authority effect also fails closed before route mutation.

Portable current-iPhone WorkerCoordinator checkout now requires that same disposition as an explicit third input before it reads or mutates portable WorkerCoordinator state. The checkout validates schema, exact task identity, `authority_effect=NONE`, and `disposition=CONTINUE`; any other condition fails closed before claim/fence mutation. The emitted WorkerCoordinator checkout receipt includes `registry_checkin_disposition`, `registry_checkin_sha256`, and `registry_checkin_authority_effect`, and the portable state retains the latest registry-checkin hash. This binds claim issuance to the exact non-authorizing Task Registry decision that preceded it without converting the registry into claim authority.

## Validation evidence

PR #1344 head `7b12ca062b463270c7b4564aad502e9a397ea3e8` passed:

- Deterministic Repository Suite - Diagnostic Evidence Only run `34544805866`;
- Validate organization control plane - No GitHub Token Authority run `34544805762`;
- Heartbeat Worker Project - Validation Only / No GitHub Token Authority run `34544805873`.

Canonical Work ingress head `d7b36d6a6e850e2a423dac62ebf721ca871117fe` passed:

- Deterministic Repository Suite run `34549352435`;
- Validate organization control plane run `34549352440`;
- Heartbeat Worker Project validation run `34549352456`.

The branch has advanced again with portable WorkerCoordinator preclaim enforcement and focused tests. Fresh exact-head validation is required before merge.

## Known gap this task addresses

`STEGOS-NODE-MANIFOLD-001` was actively being worked in StegOS while absent from central `.github` canonical task records. Under the new boundary behavior, an unregistered task receives `STOP_NOT_REGISTERED`, preventing invisible work from proceeding without central coordination visibility.

## Remaining integration

1. obtain fresh exact-head validation for the portable preclaim gate and repair any regression;
2. identify any portable checkout caller that still invokes the old two-argument checkout contract and migrate it to supply the exact Task Registry disposition;
3. expose check-in timestamp/session identity/branch-PR target metadata as retained coordination evidence;
4. make task registration/check-in persist enough target information to compute recent-returned collision windows deterministically;
5. reconcile currently invisible active task identities such as `STEGOS-NODE-MANIFOLD-001` into central registry custody;
6. add a direct root README reference to the registry preflight and preclaim gate before merge if needed to make the functional change explicit;
7. merge only when required validation remains green.

## Authority invariants

Task Registry check-in is coordination evidence only. It grants no claim/fence, execution, credential, transition, custody, publication, release, or completion authority. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## README impact

The existing root README already defines Canonical Work task ingress and cross-task collision resolution as Task Registry coordination responsibilities. The implementation now materially adds fail-closed pre-mutation and preclaim enforcement. A direct root README reference to the evaluator/preclaim sequence remains required before merge unless current README semantics are formally judged sufficient and that disposition is recorded.

## Manual work

None.
