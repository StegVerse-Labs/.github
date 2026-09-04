# Canonical Work Coordination System Mirror Handoff

Updated: 2026-09-04
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `SOURCE_IMPLEMENTATION_IN_PROGRESS`

## Source of truth

This file is the bounded continuation record for the StegVerse Canonical Work Coordination System. It inherits and does not replace:

- `docs/UNIVERSAL_WORK_INTERLOCK_MIRROR_HANDOFF.md`
- `ORG_RESIDENT_RUNTIME_INTR_BOUNDARY_MIRROR_HANDOFF.md`
- `org-runtime/interlock-intr.json`
- `control/worker-registry.json` as the existing WorkerCoordinator task/claim runtime registry
- existing Master Records reconstruction invariants and custody records

The purpose of this workstream is to provide one canonical coordination substrate for multiple StegVerse AI entities, sessions, workers, repository tasks, failure-email incidents, and human-action dependencies.

## Core invariant

There is one canonical work truth and many projections.

The canonical work system is authoritative for work intent, obligation, dependency, ownership references, adjacency, blocking state, and admissible next work. Master Records remains authoritative for observed events, evidence, state-transition history, custody, and reconstructable reality. Neither silently substitutes for the other.

WorkerCoordinator remains authoritative for executable claim/fence ownership. The canonical task registry references WorkerCoordinator claim/fence state rather than independently minting execution ownership.

Interlock/InTr governs ingress and egress state transitions for task admission, transfer, closure, and other governed work-state transitions. Source files and GitHub state do not prove those runtime transitions occurred.

## Coordination topology

```text
source stimulus / proposal / session / GitHub failure / runtime event
  -> Interlock ingress
  -> InTr materialization
  -> canonical task identity
  -> registry + dependency/incident graph
  -> Task Registry <-> Master Records reconciliation
  -> duplicate / convergence / blocker / evidence resolution
  -> WorkerCoordinator claim/fence when executable
  -> governed execution
  -> evidence / receipts / Master Records custody
  -> reconciliation
  -> completion claim validation or unresolved state
  -> Interlock egress / transfer / closure
  -> dependent-work reevaluation
```

## Canonical task identity

A task receives one stable `task_id` and `correlation_id` from admission through closure. Session changes, repository changes, worker changes, handoffs, retries, and transfers MUST NOT create a new identity merely because execution context changed.

Derived subtasks may have their own task IDs but MUST retain explicit parent/root correlation lineage.

## Task Registry responsibility

The Task Registry records factual work coordination state, including:

- stable task/correlation identity
- normalized goal
- source/proposal references
- current coordination state
- target organization/repository/component
- dependencies
- blockers
- parent systemic incident, when any
- adjacent tasks and evidence
- WorkerCoordinator claim/fence reference
- expected evidence predicates
- completion claim state
- human-action dependency reference, when any
- allowed/admissible next transitions
- handoff/projection references

The registry MUST NOT infer that work occurred from source, merge, CI, deployment, heartbeat progression, handoff prose, or issue state.

## WorkerCoordinator responsibility

WorkerCoordinator owns executable work assignment and claim/fence authority. The Task Registry MUST NOT create a competing ownership truth.

Before new execution is admitted, coordination must determine whether:

1. equivalent work is already complete by admissible evidence;
2. equivalent work is actively claimed;
3. adjacent work is producing the required evidence;
4. the task is blocked by a shared dependency or systemic incident;
5. a narrower non-colliding task remains admissible.

## Handoff model

Handoffs become projections of canonical coordination state, not independent truth stores.

A handoff projection must expose enough state for a new session/entity to determine:

- what work exists;
- what is complete and evidenced;
- what is unresolved;
- what is blocked and by what;
- what is actively claimed and where;
- what adjacent checks/evidence already exist or are in progress;
- what exact evidence gap remains;
- what non-colliding next work is admissible.

A session may be safely terminated once all unique task state has been materialized into canonical work records/projections and the session is no longer the sole continuity carrier.

## Master Records reconciliation

Task Registry and Master Records are intentionally comparable but not interchangeable.

Task Registry answers: what should or may happen?
Master Records answers: what actually happened?

Every reconciliation produces an explicit state:

- `CONSISTENT`
- `TASK_AHEAD_OF_EVIDENCE`
- `REALITY_AHEAD_OF_TASK`
- `CONFLICT`
- `UNKNOWN`
- `ORPHANED_EVENT`

`COMPLETED` is not accepted merely because the Task Registry claims completion. A task first enters `COMPLETION_CLAIMED`; closure is admissible only when the required Master Records/evidence predicates validate the claim.

Absence of evidence MUST NOT be interpreted as proof that work did not occur. Missing or unavailable evidence is represented explicitly as `UNKNOWN` or `TASK_AHEAD_OF_EVIDENCE` depending on known state.

If Master Records contains a work-relevant event with no corresponding task identity, reconciliation may propose a new task/incident ingress, but the historical event itself does not gain task-execution authority.

## Dependency, blocker, and convergence model

A dependency is a prerequisite relationship. A blocker is a dependency currently preventing a task transition.

Repeated symptoms are normalized before systemic-defect promotion. Multiple sessions, GitHub failure emails, runtime failures, or human requests may bind to one systemic incident rather than becoming duplicate repair tasks.

When one shared dependency is resolved, every dependent task MUST be reevaluated before another duplicate implementation or human request is created.

## Human-action canonicalization

A human action is represented once as a canonical dependency object and may have many dependent tasks.

Multiple tasks MUST NOT independently request the same human action when one unresolved canonical human-action dependency already exists.

## Closure and historical integrity

Task history is append-only in meaning. A closed task is not silently rewritten to appear never completed. If new evidence invalidates a prior closure, a new governed transition such as `COMPLETION_REVOKED` or `REOPENED_DUE_TO_NEW_EVIDENCE` must be recorded.

## Projections

The following may be generated from canonical coordination state and MUST NOT become competing sources of truth:

- session handoffs
- GitHub issues
- status dashboards
- weekly accomplishment logs
- developer views
- repository-local task projections
- public progress surfaces

## Machine surfaces

Initial source implementation in `StegVerse-Labs/.github`:

- `schemas/canonical-task-record.schema.json`
- `schemas/task-master-records-reconciliation.schema.json`
- `data/canonical-task-registry.json`
- `data/task-coordination-policy.json`
- `scripts/validate_canonical_work_coordination.py`
- `scripts/reconcile_task_registry_master_records.py`

Existing surfaces consumed by reference:

- `control/worker-registry.json`
- Master Records custody/reconstruction records
- Universal Work Interlock/InTr records

## Completion predicates

1. A canonical task record schema exists with stable identity, dependency, blocker, adjacency, evidence, and claim-reference semantics.
2. The registry does not duplicate WorkerCoordinator claim/fence authority.
3. A reconciliation schema exists for Task Registry vs Master Records comparison.
4. Completion claims require evidence validation before closure.
5. Missing evidence is represented explicitly rather than inferred as non-occurrence.
6. Handoffs are projections of canonical task state.
7. Duplicate/adjacent work resolution occurs before execution admission.
8. Shared human actions can be represented once with multiple dependents.
9. Systemic incidents can bind many symptoms/tasks without duplicating repair ownership.
10. Source validators can fail closed on malformed or authority-conflicting records.
11. An authentic task ingress, claim/fence, evidence, reconciliation, and egress/closure cycle is demonstrated through runtime Interlock/InTr and Master Records.

## Runtime status

The source model can be implemented before the full runtime path is active. Source installation does not prove canonical runtime coordination, Interlock/InTr materialization, WorkerCoordinator execution, or Master Records reconciliation occurred.

## Archive readiness

This workstream is not runtime-complete until predicate 11 is proven. Conversation/session continuity may be archived once all unique design and implementation state is preserved in this handoff and the canonical source files.