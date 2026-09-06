# Cross-Task Coordination / Evidence Resolution Mirror Handoff

Updated: 2026-09-05
Repository: `StegVerse-Labs/.github`
Status: SOURCE_VALIDATED / ECOSYSTEM_ADOPTION_ACTIVE

## Authority boundary

This is the canonical scoped handoff for cross-session and autonomous-entity task coordination.

Coordination truth is NOT runtime truth. This layer may describe goals, tasks, predicates, evidence locators, claims, mutation scopes, gaps, dependencies, adjacency, and collision state. It grants NO execution, InTr transition, TV/TVC credential, route, claim, fence, lease, custody, publication, receiving, or runtime-event authority.

Runtime predicates are satisfied only by evidence from the declared authoritative producer that matches the required predicate, semantic subject binding, scope, schema, execution instance, and freshness contract.

## Goal

Prevent independent sessions and autonomous entities from duplicating checks, colliding with adjacent work, or declaring blockers before resolving reusable evidence and active work claims.

Canonical preflight sequence:

```text
goal
-> task
-> required predicates
-> qualifying existing evidence
-> active scope-specific claims
-> adjacency discovery
-> mutation-scope collision check
-> precise evidence-gap derivation
-> README impact completeness when functional mutation is declared
-> ADMIT_COORDINATION | BLOCK_COORDINATION | UPDATE_COORDINATION
```

## First-class records

- Goal
- Task
- Predicate
- Evidence
- Claim
- MutationScope
- Gap
- Dependency

Predicate states:

- SATISFIED
- UNSATISFIED
- IN_PROGRESS
- UNKNOWN
- CONFLICTED

## Shared-predicate identity invariant

A similar predicate name is not sufficient to establish shared truth.

Predicate equivalence requires:

```text
semantic_predicate_id
+
subject_binding
```

Examples of subject binding include request id, node id, target task, execution instance, receiver, claim/fence identity, or another canonical identity needed to prove that two consumers are asking about the same underlying fact.

Therefore `resident_request_consumed` for request A MUST NOT satisfy `resident_request_consumed` for request B. Evidence whose bound subject differs is rejected with `SUBJECT_BINDING_MISMATCH`.

## Canonical ledger composition

The canonical logical coordination ledger is now composed deterministically from:

```text
control/cross-task-coordination.json
+
lexicographically sorted control/cross-task-coordination.d/*.json
```

Implementation:

```text
heartbeat_runtime/coordination_ledger.py
heartbeat_runtime/admitted_worker_runtime.py
scripts/render_cross_task_coordination_handoff.py
tests/test_coordination_ledger.py
.github/workflows/cross-task-coordination-validation.yml
```

Rules:

1. base ledger remains the stable coordination root;
2. canonical extension fragments are append-only coordination records;
3. duplicate fragment ids or duplicate stable record ids fail closed;
4. fragment authority effect must remain `NONE` / `NONE_COORDINATION_ONLY`;
5. WorkerCoordinator autonomous preflight consumes the composed ledger;
6. portable handoff projection consumes the same composed ledger;
7. fragments do not alter runtime truth authority.

This replaces repeated whole-ledger rewrites as the normal migration path and reduces cross-session write collision risk.

## Required autonomous-augmentation invariant

No task declaring `autonomous_augmentation: true` may pass WorkerCoordinator pre-initiation review unless a fresh coordination preflight reports:

- all required predicates satisfied or explicitly consumable under the task's own authority;
- no conflicting active mutation scope;
- no duplicate production claim for the same evidence-producing activity;
- authoritative evidence reuse resolved before a new check is proposed;
- any remaining gap expressed as an exact producer/output/schema/field/freshness delta;
- expected blast radius declared.

The preflight itself has `authority_effect: NONE`.

## Functional-change README completeness invariant

The organization README defines a standing rule: any change that materially changes repository function must update that repository's README in the same functional change.

Machine enforcement is bound into the existing worker-task admission review rather than a parallel scheduler or authority path. New functional mutations entering through the StegVerse session-entry contract must set:

```text
readme_impact_required = true
```

The task or handoff must then provide a structured `readme_impact` determination.

For `material_function_change = true`, admission requires:

```text
readme_updated_in_change_set = true
readme_path = <affected repository README>
evidence_refs = <README + functional-change evidence>
```

For `material_function_change = false`, a no-update determination is admissible only when it carries:

```text
no_readme_update_reason = <explicit rationale>
evidence_refs = <supporting evidence>
```

Missing materiality, missing required evidence, or a material functional change without a README update makes `readme_impact_complete = false` and causes the existing worker-task admission review to fail closed.

Legacy/nonfunctional tasks that predate this contract are not retroactively blocked solely because they lack the field. The session-entry/preflight contract is responsible for marking new functional mutations as README-impact-required.

Implementation locations:

```text
heartbeat_runtime/worker_task_admission.py
tests/test_worker_task_admission.py
README.md
```

Authority effect remains `NONE`. README completeness does not grant execution, admission authority, claim, fence, lease, credential, routing, transition, publication, custody, or runtime truth.

## Evidence qualification

Evidence is reusable only when all declared requirements match:

- predicate id;
- semantic predicate id and subject binding when declared;
- authoritative producer;
- schema;
- scope;
- execution instance when required;
- freshness requirement when required;
- authority effect constraints.

Existence of a nearby file, merge, deployment, heartbeat, CI result, issue, handoff, or similarly named receipt does not satisfy a runtime predicate by inference.

## Adjacency / blocker rule

Before declaring a task blocked, the resolver MUST inspect whether another task:

1. already satisfied the same bound predicate;
2. is actively producing the required evidence;
3. produced adjacent evidence containing reusable underlying data; or
4. owns a scope that would collide with the proposed check.

Newly satisfied predicates MUST also resolve downstream consumers that have become unblocked.

A generic `runtime evidence required` response is insufficient when the missing producer/output/schema/field/freshness delta can be expressed precisely.

## Validated implementation evidence

```text
core + WorkerCoordinator integration:
  run: 33923391425
  result: SUCCESS

initial StegIndex read-only projection:
  run: 33943933317
  result: SUCCESS

handoff projection:
  run: 33944001324
  result: SUCCESS

subject-binding equivalence guard:
  run: 33998265474
  result: SUCCESS

HIL + G18 bound predicate migration:
  commit: 20f1b495a38961e40069f28fb4c55ca85c9fd9c2
  run: 34000603720
  result: SUCCESS

append-only composed-ledger integration + SV002/SV-011 canonical fragments:
  commit: 6a9907f8157d32396e23d38b5bf9a156d35dda7c
  run: 34000794804
  result: SUCCESS

StegVerse-001 bound predicate fragment:
  commit: fd881e81cf60bb10e8f29f3cb109c02a52cef72e
  run: 34000820166
  result: SUCCESS

StegIndex composed-fragment discovery:
  commit: 051bece05afda4fd0bef85af46ce7ab68c60d56c
  run: 34000847936
  result: SUCCESS
```

These are source/validation facts only and are not runtime-event or product-activation evidence.

## Migrated bound `resident_request_consumed` instances

Canonical composition now carries distinct subject-bound records for:

1. Ecosystem Chat parent — `RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002`;
2. StegIndex one-shot resident stack activation — `RESIDENT-EXEC-ONE-SHOT-STACK-ACTIVATION-001`;
3. HIL sovereign receiver — `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`;
4. G18 existing-claim resume — `RESIDENT-EXEC-G18-RESUME-FENCE18-001`, additionally bound to claim/fence18;
5. SV002 organization-runtime activation — `RESIDENT-EXEC-SV002-ORG-RUNTIME-ACTIVATION-001`;
6. SV002 public observation — `RESIDENT-EXEC-SV002-PUBLIC-OBSERVATION-RUNTIME-001`;
7. SV-011 phase5 boundary — `RESIDENT-EXEC-SV011-PHASE5-BOUNDARY-001`;
8. SV-011 phase5 source materialization — `RESIDENT-EXEC-SV011-PHASE5-SOURCE-MATERIALIZATION-001`;
9. StegVerse-001 bounded autonomy — `RESIDENT-EXEC-STEGVERSE001-BOUNDED-AUTONOMY-001`.

SV002 and SV-011 staging records are marked `ADMITTED_CANONICAL_FRAGMENT` and point to their canonical fragments so later sessions must not repeat migration.

The StegVerse-001 bounded-autonomy predicate records its dependency on the already-existing one-shot resident-stack activation predicate; it does not create a second activation mechanism or bypass TVC lease issuance.

## StegIndex consistency

`StegVerse-Labs/StegIndex/scripts/resolve_cross_task_coordination.py` now composes the same base + fragment model in read-only form and fails closed on duplicate/drifted fragments. Its complete validation suite passed run `34000847936`.

WorkerCoordinator, handoff projection, and StegIndex therefore now share one logical coordination composition model rather than reading different subsets of canonical state.

## Current coordination state

Core source implementation: VALIDATED.
Composed canonical ledger: VALIDATED.
Subject-bound resident-request migration: PARTIAL / ACTIVE.
StegIndex composed discovery: VALIDATED.
README impact machine-preflight enforcement: SOURCE IMPLEMENTED / VALIDATION PENDING.
Ecosystem adoption: NOT COMPLETE.
Runtime activation claims created by this coordination work: NONE.

Existing runtime activation, WorkerCoordinator execution, sovereign inference, HIL, credential/route, and other already-owned workstreams remain outside the coordination source claim and must not be restarted merely because they consume coordination predicates.

## Remaining machine work

1. validate and merge README impact machine-preflight enforcement, then replace `VALIDATION PENDING` above with exact evidence;
2. inspect remaining canonical handoffs for shared predicates beyond `resident_request_consumed`, beginning with resident-presence/runtime-observation and common claim/fence/evidence predicates;
3. establish subject identity before any shared registration;
4. register only genuinely reusable producer/evidence relationships and exact gaps;
5. bind additional session/build consumers that still read an incomplete coordination slice;
6. register active claims/producers where canonical ownership records exist;
7. validate each migration deterministically;
8. evaluate tag/release only after ecosystem-adoption criteria are actually satisfied;
9. after actual release/tag, verify governed propagation requirements for `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Completion and archive rule

A thread MUST NOT be described as ready for archiving merely because its current state has been written into a handoff.

Archive-ready may be stated only when one of these conditions is true:

1. the session goal is complete; or
2. every remaining task needed for that goal is durably assigned to an actually operating autonomous executor whose continuation does not depend on this session, with that ownership and executable continuation evidenced canonically.

A handoff by itself is continuity evidence, not task completion and not proof that remaining work will execute automatically.

Current goal completion: FALSE.
Current ecosystem-adoption work remaining: TRUE.
Thread archive-ready: FALSE.
