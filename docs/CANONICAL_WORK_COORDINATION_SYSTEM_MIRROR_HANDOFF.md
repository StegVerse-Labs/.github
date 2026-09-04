# Canonical Work Coordination System Mirror Handoff

Updated: 2026-09-04
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `SOURCE_IMPLEMENTED_RUNTIME_ENFORCEMENT_PENDING`

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

The Task Registry records factual work coordination state, including stable identity, normalized goal, source/proposal references, current coordination state, targets, dependencies, blockers, parent systemic incident, adjacent tasks/evidence, WorkerCoordinator claim/fence references, expected evidence predicates, completion claim state, human-action references, admissible next transitions, and projection references.

The registry MUST NOT infer that work occurred from source, merge, CI, deployment, heartbeat progression, handoff prose, or issue state.

## WorkerCoordinator responsibility

WorkerCoordinator owns executable work assignment and claim/fence authority. The Task Registry MUST NOT create a competing ownership truth.

Before new execution is admitted, coordination must determine whether equivalent work is already complete, equivalent work is actively claimed, adjacent work is producing the required evidence, a shared dependency/systemic incident blocks the transition, or a narrower non-colliding task remains admissible.

## Handoff model

Handoffs become projections of canonical coordination state, not independent truth stores.

A handoff projection exposes what work exists, what is complete and evidenced, what is unresolved, blockers/dependencies, active claim references, adjacent work/evidence, the exact evidence gap, and non-colliding next transition candidates.

A session may be safely terminated once all unique task state has been materialized into canonical work records/projections and the session is no longer the sole continuity carrier.

## Master Records reconciliation

Task Registry and Master Records are intentionally comparable but not interchangeable.

Task Registry answers: what should or may happen?
Master Records answers: what actually happened?

Every reconciliation produces one explicit state:

- `CONSISTENT`
- `TASK_AHEAD_OF_EVIDENCE`
- `REALITY_AHEAD_OF_TASK`
- `CONFLICT`
- `UNKNOWN`
- `ORPHANED_EVENT`

`COMPLETED` is not accepted merely because the Task Registry claims completion. A task first enters `COMPLETION_CLAIMED`; closure is admissible only when required evidence predicates validate the claim.

Absence of evidence MUST NOT be interpreted as proof that work did not occur. Missing/unavailable evidence remains explicit as `UNKNOWN` or `TASK_AHEAD_OF_EVIDENCE` depending on known state.

If Master Records contains a work-relevant event with no corresponding task identity, reconciliation may propose a new task/incident ingress, but the historical event itself does not gain task-execution authority.

## Dependency, blocker, and convergence model

A dependency is a prerequisite relationship. A blocker is a dependency currently preventing a task transition.

Repeated symptoms are normalized before systemic-defect promotion. Multiple sessions, GitHub failure emails, runtime failures, or human requests may bind to one systemic incident rather than becoming duplicate repair tasks.

When one shared dependency is resolved, every dependent task MUST be reevaluated before another duplicate implementation or human request is created.

## Human-action canonicalization

A human action is represented once as a canonical dependency object and may have many dependent tasks. Multiple tasks MUST NOT independently request the same human action when one unresolved canonical human-action dependency already exists.

## Closure and historical integrity

Task history is append-only in meaning. A closed task is not silently rewritten to appear never completed. If later evidence invalidates prior closure, a new governed transition such as `COMPLETION_REVOKED` or `REOPENED_DUE_TO_NEW_EVIDENCE` must be recorded.

## Projections

Session handoffs, GitHub issues, status dashboards, weekly accomplishment logs, developer views, repository-local task projections, and public progress surfaces may be generated from canonical coordination state and MUST NOT become competing sources of truth.

## Installed machine surfaces

Source implementation now exists in `StegVerse-Labs/.github`:

- `schemas/canonical-task-record.schema.json`
- `schemas/task-master-records-reconciliation.schema.json`
- `data/canonical-task-registry.json`
- `data/task-coordination-policy.json`
- `scripts/validate_canonical_work_coordination.py`
- `scripts/reconcile_task_registry_master_records.py`
- `scripts/query_canonical_tasks.py`
- `scripts/render_task_handoff_projection.py`

Existing surfaces consumed by reference:

- `control/worker-registry.json`
- Master Records custody/reconstruction records
- Universal Work Interlock/InTr records

The bootstrap registry contains `STEGVERSE-CANONICAL-WORK-COORDINATION-001` in `PROPOSED` source state only. It deliberately does not fabricate Interlock/InTr admission or WorkerCoordinator claim/fence authority.

## Source behavior now implemented

- fail-closed task schema with stable correlation identity;
- explicit separation of Task Registry, WorkerCoordinator, Master Records, and Interlock/InTr authority;
- completion-claim versus validated-closure distinction;
- explicit dependency/blocker/adjacency/evidence fields;
- explicit shared human-action and systemic-incident surfaces;
- deterministic Task Registry vs supplied Master Records projection reconciliation;
- query utility for topic-based task discovery in new sessions;
- handoff projection renderer so session continuity can be materialized outside the chat context;
- validator that checks authority separation, closure requirements, blocker/dependency integrity, reconciliation states, and existing WorkerCoordinator-registry presence.

## Completion predicates

1. A canonical task record schema exists with stable identity, dependency, blocker, adjacency, evidence, and claim-reference semantics. **SOURCE COMPLETE**
2. The registry does not duplicate WorkerCoordinator claim/fence authority. **SOURCE COMPLETE**
3. A reconciliation schema exists for Task Registry vs Master Records comparison. **SOURCE COMPLETE**
4. Completion claims require evidence validation before closure. **SOURCE COMPLETE**
5. Missing evidence is represented explicitly rather than inferred as non-occurrence. **SOURCE COMPLETE**
6. Handoffs are projections of canonical task state. **SOURCE COMPLETE**
7. Duplicate/adjacent work resolution occurs before execution admission. **POLICY/SOURCE COMPLETE; RUNTIME ENFORCEMENT PENDING**
8. Shared human actions can be represented once with multiple dependents. **SOURCE COMPLETE; RUNTIME POPULATION PENDING**
9. Systemic incidents can bind many symptoms/tasks without duplicating repair ownership. **SOURCE COMPLETE; RUNTIME POPULATION PENDING**
10. Source validators can fail closed on malformed or authority-conflicting records. **SOURCE IMPLEMENTED; EXECUTION PROOF PENDING**
11. An authentic task ingress, claim/fence, evidence, reconciliation, and egress/closure cycle is demonstrated through runtime Interlock/InTr and Master Records. **PENDING**

## Remaining machine work

- execute `scripts/validate_canonical_work_coordination.py` in an admitted validation environment;
- connect task ingress/egress to the Universal Work Interlock/InTr runtime;
- populate canonical task records from existing session/handoff/project state without duplicating WorkerCoordinator ownership;
- bind live WorkerCoordinator claim/fence projection into canonical task records;
- define/consume the Master Records projection/feed used for runtime reconciliation;
- canonicalize repeated GitHub failure emails and shared human-action dependencies into incidents/tasks;
- trigger dependent-task reevaluation when blockers resolve;
- prove one authentic end-to-end task lifecycle from ingress through closure.

## Runtime status

`SOURCE_IMPLEMENTED_RUNTIME_ENFORCEMENT_PENDING`

Source installation does not prove canonical runtime coordination, Interlock/InTr materialization, WorkerCoordinator execution, Master Records reconciliation, or task closure occurred.

## Archive readiness

The workstream is not runtime-complete until predicate 11 is proven. This conversation may be archived once no unique coordination state remains only in chat context; all current design/source state is preserved here.