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

Examples of subject binding include request id, node id, target task, execution instance, receiver, or other canonical identity needed to prove that two consumers are asking about the same underlying fact.

Therefore `resident_request_consumed` for request A MUST NOT satisfy `resident_request_consumed` for request B. Evidence whose bound subject differs is rejected with `SUBJECT_BINDING_MISMATCH`.

## Required autonomous-augmentation invariant

No task declaring `autonomous_augmentation: true` may pass WorkerCoordinator pre-initiation review unless a fresh coordination preflight reports:

- all required predicates satisfied or explicitly consumable under the task's own authority;
- no conflicting active mutation scope;
- no duplicate production claim for the same evidence-producing activity;
- authoritative evidence reuse resolved before a new check is proposed;
- any remaining gap expressed as an exact producer/output/schema/field/freshness delta;
- expected blast radius declared.

The preflight itself has `authority_effect: NONE`.

## Canonical implementation locations

```text
schemas/cross-task-coordination.schema.json
heartbeat_runtime/coordination_graph.py
control/cross-task-coordination.json
tests/test_coordination_graph.py
heartbeat_runtime/worker_task_admission.py
heartbeat_runtime/admitted_worker_runtime.py
scripts/render_cross_task_coordination_handoff.py
tests/test_cross_task_coordination_handoff_projection.py
.github/workflows/cross-task-coordination-validation.yml
```

StegIndex read-only consumer:

```text
StegVerse-Labs/StegIndex/scripts/resolve_cross_task_coordination.py
StegVerse-Labs/StegIndex/tests/test_cross_task_coordination.py
StegVerse-Labs/StegIndex/docs/CROSS_TASK_COORDINATION_INDEX_MIRROR_HANDOFF.md
```

## Handoff projection rule

`*_MIRROR_HANDOFF.md` files are portable projections, not the master coordination database. Repository-local handoffs remain authoritative for repository-local implementation evidence. The canonical coordination ledger references those records and may be regenerated without replacing their authority.

The deterministic renderer emits task predicate state, active claims, exact evidence gaps, and the mandatory adjacency-before-blocker instruction from the canonical ledger.

## Collision rules

Claims are scope-specific rather than task-wide. Collision resolution compares:

- repository/path/module mutation scopes;
- runtime surfaces;
- evidence-production responsibility;
- declared expected blast radius.

Read-only validation may coexist with a mutation claim when it does not mutate, claim, fence, lease, route, receive, publish, or alter the same evidence-production responsibility.

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

## Evidence-gap contract

When existing evidence is insufficient, produce a gap containing:

```text
predicate_id
semantic_predicate_id
subject_binding
existing_evidence_refs
rejected_because
missing_observation
required_producer
required_output_ref
required_schema
required_fields
required_freshness
collision_refs
action_without_collision
```

A generic `runtime evidence required` response is insufficient when the missing delta can be expressed more precisely.

## Adjacency rule

Before declaring a task blocked, the resolver MUST inspect whether another task:

1. already satisfied the same bound predicate;
2. is actively producing the required evidence;
3. produced adjacent evidence containing reusable underlying data; or
4. owns a scope that would collide with the proposed check.

Newly satisfied predicates MUST also resolve downstream consumers that have become unblocked.

## Validated source evidence

```text
core + WorkerCoordinator integration:
  run: 33923391425
  result: SUCCESS

StegIndex read-only projection:
  commit: 758316ea043a56fe523c222a923f726d2a0805c2
  run: 33943933317
  result: SUCCESS

handoff projection + dedicated non-authorizing validator:
  exact-head validation source: e6d4fb406c860b496542e5a6112128b1295d31ab
  run: 33944001324
  result: SUCCESS

subject-bound predicate equivalence guard:
  source commits: 23c65ae1ce853f8c0239a1b9604abbecd9b277b8 / 0b282337f38139f5753595c9c69165504ddd922e / cf86d4697a26eac0307389ebaaaf0ccdc2110803
  dedicated coordination validation run: 33998265474
  result: SUCCESS
```

These are source/validation facts only and are not runtime-event or product-activation evidence.

## First migrated bound runtime predicate

The canonical coordination ledger now registers the concrete Ecosystem Chat resident-consumption predicate:

```text
predicate_id: PRED-RESIDENT-REQUEST-CONSUMED-ECOSYSTEM-CHAT-PARENT-002
semantic_predicate_id: resident_request_consumed
subject_binding.request_id: RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002
subject_binding.consumer_task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
state: UNKNOWN
expected evidence: receipts/sovereign-host/resident-execution-request-consumption.latest.json
```

Canonical sources:

- `docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md`
- `control/runtime-observability-consumers/ecosystem-chat-sovereign-inference-001.json`

The gap explicitly instructs consumers to wait for/consume the existing resident bridge result and not create a parallel resident transport or replay terminal orphan recovery.

## Current coordination state

Canonical machine ledger: `control/cross-task-coordination.json`.

The core source implementation is validated. Ecosystem adoption is NOT complete. Shared-predicate migration across convergent lanes remains active work.

Existing runtime activation, WorkerCoordinator execution, sovereign inference, HIL, credential/route, and other already-owned workstreams remain outside the coordination source claim and must not be restarted merely because they consume coordination predicates.

## Remaining machine work

1. inspect canonical handoffs for G18, HIL, SV001, SV002, SV-011, and other convergent lanes;
2. identify only predicates whose semantic subject identity can be proven equivalent;
3. register those bound predicates, producers, evidence locations, consumers, and active claims in the canonical ledger;
4. connect StegIndex/session-build handoff consumers to these migrated records;
5. validate each migration deterministically;
6. when the capability reaches an actual release/tag boundary, perform the release and then verify governed propagation requirements for:
   - `StegVerse-Labs/Site`
   - `GCAT-BCAT-Engine/Publisher`
   - `admissibility-wiki`
   - `stegguardian-wiki`.

## Completion and archive rule

A thread MUST NOT be described as ready for archiving merely because its current state has been written into a handoff.

Archive-ready may be stated only when one of these conditions is true:

1. the session goal is complete; or
2. every remaining task needed for that goal is durably assigned to an actually operating autonomous executor whose continuation does not depend on this session, with that ownership and executable continuation evidenced canonically.

A handoff by itself is continuity evidence, not task completion and not proof that remaining work will execute automatically.

Current goal completion: FALSE.
Current ecosystem-adoption work remaining: TRUE.
Thread archive-ready: FALSE.
