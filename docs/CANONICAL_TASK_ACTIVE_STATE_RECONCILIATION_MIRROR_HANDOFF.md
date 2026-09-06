# Canonical Task Active-State Reconciliation Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: #1062
State: ATTEMPTING_CANONICAL_ACTIVE_STATE_RECONCILIATION
Authority effect: NONE
Activation effect: NONE

## Purpose

Reconcile the canonical Task Registry state contract with the already-established active-worker invariant in `control/active-worker-state-policy.json` / issue #83.

StegVerse does not treat `BLOCKED` as an operational task status. An unresolved task remains active/machine-owned while its current problem or constraint is represented separately and a solution is attempted within the current authority ceiling or transferred/escalated through the canonical mechanism.

## Canonical authorities retained

- work intent / coordination: `data/canonical-task-registry.json`;
- execution claim / fence: existing WorkerCoordinator only;
- observed reality / reconstruction: Master Records;
- governed ingress / egress: Interlock/InTr;
- credential authority: TV/TVC;
- HB/oscillator: non-authorizing carrier/reference only.

This reconciliation creates no WorkerCoordinator, claim, fence, scheduler, heartbeat, runtime, credential path, ingress authority, or evidence authority.

## Problem confirmed in source

`schemas/canonical-task-record.schema.json` still exposed `BLOCKED` in `coordination_state`, and canonical transition producers still emitted or allowed `BLOCKED` as a next task-state transition.

This conflicts with the existing active-worker policy, which states:

- `forbidden_unresolved_state = BLOCKED`;
- constraint metadata is separate from operational state;
- a next executable action is required;
- a constraint may not suspend unresolved work.

The current checked-in `data/canonical-task-registry.json` contains no task whose `coordination_state` or `allowed_next_transitions` uses `BLOCKED`, so no live source task history needs rewriting.

## Source reconciliation

The #1062 change set:

1. removes `BLOCKED` from the canonical task `coordination_state` enum;
2. removes `BLOCKED` from the canonical ingress and WorkerCoordinator-projection next-transition sets;
3. keeps claimed work `IN_PROGRESS` while a solution is being attempted;
4. retains dependency/problem information in existing dependency, blocker/problem, incident, and evidence metadata rather than encoding a stopping task state;
5. aligns task-selection policy to `SELECT_HIGHEST_PRIORITY_ADMISSIBLE_NON_DUPLICATE_NON_COLLIDING_TASK`;
6. adds deterministic regression tests;
7. updates the repository README in the same change set.

Historical receipts and unrelated schemas that retain `BLOCKED` as immutable provenance or a different domain-specific value are not rewritten by this task.

## README completeness preflight

README update required: **YES**.

Reason: removing an operational state from the canonical coordination schema changes task-state interface/evidence semantics and continuation meaning. The README must state that problems/constraints are metadata rather than an operational stopping state and that machine-owned progression selects the next highest-priority admissible nonduplicate task.

## Evidence boundary

Source/CI/merge proves only the source contract and deterministic validation that actually ran. It does not prove:

- an authentic WorkerCoordinator claim/fence;
- a task execution attempt;
- a problem was solved at runtime;
- Master Records custody/reconstruction;
- Interlock/InTr egress;
- product/runtime activation.

## Next transition

Validate the exact PR head with the existing `.github` test/organization-control surfaces. Merge only the exact validated head. After merge, issue #1062 may be closed as the canonical task-state source reconciliation; historical domain-specific status migrations, if any are desired, remain separate tasks and must not be rewritten as part of this source contract correction.
