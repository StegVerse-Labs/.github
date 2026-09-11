# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
Status: `ACTIVE / CHECKED_OUT / REGISTRY-BOUNDARY DISPOSITION IMPLEMENTED / VALIDATION PENDING`

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
- `tests/test_task_registry_collision_checkin.py`

The evaluator reads all canonical task records at check-in time. It does not grant execution authority, replace WorkerCoordinator claims/fences, or treat GitHub as runtime authority.

## Known gap this task addresses

`STEGOS-NODE-MANIFOLD-001` was actively being worked in StegOS while absent from central `.github` canonical task records. Under the new boundary behavior, an unregistered task receives `STOP_NOT_REGISTERED`, preventing invisible work from proceeding without central coordination visibility.

## Next

1. validate the branch;
2. repair any false-positive/false-negative collision classifications;
3. merge only after canonical repository validation passes;
4. bind this evaluator into every canonical task checkout/check-in ingress so callers receive the disposition automatically rather than invoking it ad hoc;
5. add persistent checkout/check-in timestamps/session identity/branch-PR target metadata so recent-returned task collision windows can be evaluated deterministically.

## Manual work

None.
