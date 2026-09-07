# Reusable Tasks Mirror Handoff

Status: ACTIVE_SOURCE_DEFINED
Repository: `StegVerse-Labs/.github`
Canonical reusable-task registry: `data/reusable-task-registry.json`
Canonical task registry: `data/canonical-task-registry.json`

## Purpose

`Reusable Tasks` are stable, reusable work definitions that may be referenced by many sessions or canonical work items without recreating the task specification each time.

They are coordination/discovery primitives only. A reusable task definition does **not** mint execution authority, a WorkerCoordinator claim/fence, Master Records truth, InTr admission, TV/TVC credential authority, or runtime activation.

## Canonical reusable tasks

- `RT-README-VALIDATION-001` — evaluate README impact for materially changed repositories; update in the same change set when required or record an evidence-supported `NO_README_CHANGE_REQUIRED` determination.
- `RT-MIRROR-HANDOFF-VALIDATION-001` — resolve and reconcile applicable `*_MIRROR_HANDOFF.md` files against current task/evidence state.
- `RT-STEGINDEX-VALIDATION-001` — verify materially affected StegIndex/index projections are accurate and not overclaimed.
- `RT-NATIVE-EMAIL-ACTION-MONITOR-001` — invoke the existing `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001` / `RESIDENT-EXEC-NATIVE-EMAIL-ACTION-MONITOR-001` path without creating another monitor, scheduler, polling loop, heartbeat, worker, or credential route.
- `RT-CANONICAL-STATE-RECONCILIATION-001` — reconcile Task Registry, WorkerCoordinator claim/fence projection, Master Records, receipts, handoffs, README completeness determination, and StegIndex/index state without collapsing authority boundaries.
- `RT-SESSION-CLOSEOUT-001` — bounded composition of the five reusable tasks above before successor session handoff.

## Invocation semantics

A session or canonical task may reference a reusable task by `reusable_task_id` and bind it to the current repository/task/material scope. Invocation does not clone the reusable definition into a new implementation unless a distinct implementation is actually required.

Reusable-task execution must remain bounded to materially affected scope. `RT-SESSION-CLOSEOUT-001` must not recursively audit the entire ecosystem and must not become a prerequisite that blocks an otherwise admissible primary runtime transition.

## Authority separation

```text
Reusable Task Registry = reusable task definition/discovery
Canonical Task Registry = work intent / coordination
WorkerCoordinator = execution claim / fence
Master Records = observed reality / reconstruction
Interlock/InTr = governed ingress / egress
TV/TVC = credential authority
StegIndex = read/discovery projection
HB32 oscillator = reference/timing only
GitHub token runtime authority = NONE
```

## README completeness determination for this change

`NO_README_CHANGE_REQUIRED` for `StegVerse-Labs/.github` in this change set.

Evidence basis: the repository README already documents Canonical Work as a reusable governed ingress mechanism for additional registered tasks and already states that the resident `data/canonical-task-registry.json` is mutable coordination state whose authority remains separated from downstream Canonical Work, WorkerCoordinator, Master Records, and Interlock/InTr checks. This change adds a dedicated reusable-definition catalog and handoff without changing runtime behavior, interfaces, credential authority, admission semantics, execution semantics, failure behavior, or capability authority.

## Next integration

StegIndex should index this reusable-task capability as discovery-only and point back to this handoff and `data/reusable-task-registry.json`. The index must not assert runtime completion merely because reusable definitions exist.
