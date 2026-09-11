# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
PR: `StegVerse-Labs/.github#1344`
Status: `ACTIVE / CHECKED_OUT / REGISTRY-BOUNDARY DISPOSITION IMPLEMENTED / INITIAL VALIDATION PASS / CANONICAL WORK INGRESS PREFLIGHT BOUND / FRESH EXACT-HEAD VALIDATION PENDING`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition derived from current canonical task records.

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
- `tests/test_task_registry_collision_checkin.py`

The evaluator reads all canonical task records at check-in time. It does not grant execution authority, replace WorkerCoordinator claims/fences, or treat GitHub as runtime authority.

Canonical Work event bootstrap now executes the registry collision preflight before route installation or bounded work bootstrap. Only `CONTINUE` proceeds automatically. `COORDINATE_CONVERGENCE` and every `STOP_*` result fail closed before mutation and surface the complete `TASK_REGISTRY_CHECKIN` JSON to the caller/session. A missing evaluator, malformed response, identity mismatch, or non-NONE authority effect also fails closed before route mutation.

## Validation evidence

Initial PR #1344 head `7b12ca062b463270c7b4564aad502e9a397ea3e8` passed:

- Deterministic Repository Suite - Diagnostic Evidence Only run `34544805866`;
- Validate organization control plane - No GitHub Token Authority run `34544805762`;
- Heartbeat Worker Project - Validation Only / No GitHub Token Authority run `34544805873`.

The branch has advanced with Canonical Work ingress integration and focused source-order tests. Fresh exact-head validation is required before merge.

## Known gap this task addresses

`STEGOS-NODE-MANIFOLD-001` was actively being worked in StegOS while absent from central `.github` canonical task records. Under the new boundary behavior, an unregistered task receives `STOP_NOT_REGISTERED`, preventing invisible work from proceeding without central coordination visibility.

## Remaining integration

1. obtain fresh exact-head validation and repair any regression;
2. bind the same registry disposition requirement to portable current-iPhone WorkerCoordinator checkout without creating a second collision-policy implementation;
3. expose the check-in disposition as retained coordination evidence with check-in timestamp/session identity/branch-PR target metadata;
4. make task registration/check-in persist enough target information to compute recent-returned collision windows deterministically;
5. reconcile currently invisible active task identities such as `STEGOS-NODE-MANIFOLD-001` into central registry custody;
6. merge only when required validation remains green.

## Authority invariants

Task Registry check-in is coordination evidence only. It grants no claim/fence, execution, credential, transition, custody, publication, release, or completion authority. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## README impact

The existing root README already defines Canonical Work task ingress and cross-task collision resolution as Task Registry coordination responsibilities. The implementation adds a fail-closed pre-mutation enforcement step to that documented behavior; a direct README reference to the evaluator should be added before merge if the branch can update the complete README without truncation risk.

## Manual work

None.
