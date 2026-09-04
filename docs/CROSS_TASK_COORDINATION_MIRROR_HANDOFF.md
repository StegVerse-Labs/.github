# Cross-Task Coordination / Evidence Resolution Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Status: IMPLEMENTATION_ACTIVE

## Authority boundary

This is the canonical scoped handoff for cross-session and autonomous-entity task coordination.

Coordination truth is NOT runtime truth. This layer may describe goals, tasks, predicates, evidence locators, claims, mutation scopes, gaps, dependencies, adjacency, and collision state. It grants NO execution, InTr transition, TV/TVC credential, route, claim, fence, lease, custody, publication, receiving, or runtime-event authority.

Runtime predicates are satisfied only by evidence from the declared authoritative producer that matches the required predicate, scope, schema, execution instance, and freshness contract.

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
```

## Handoff projection rule

`*_MIRROR_HANDOFF.md` files are portable projections, not the master coordination database. Repository-local handoffs remain authoritative for repository-local implementation evidence. The canonical coordination ledger references those records and may be regenerated without replacing their authority.

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

1. already satisfied the predicate;
2. is actively producing the required evidence;
3. produced adjacent evidence containing reusable underlying data; or
4. owns a scope that would collide with the proposed check.

Newly satisfied predicates MUST also resolve downstream consumers that have become unblocked.

## Existing work that must not be duplicated

The organization handoff currently assigns runtime activation, WorkerCoordinator execution, sovereign inference, and credential/route work to existing canonical workers/authorities. This coordination implementation does not restart or compete with those tasks.

## Remaining implementation

- canonical JSON schema;
- resolver and fail-closed preflight;
- initial ledger;
- WorkerCoordinator admission binding for autonomous augmentation;
- deterministic unit tests;
- later propagation adapters for StegIndex and repository-local handoff generators.

## Release candidate propagation

When this capability reaches a tagged/released state, verify whether its coordination/evidence semantics require updates in:

- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `admissibility-wiki`
- `stegguardian-wiki`

Do not claim propagation before each consumer's own release gate is satisfied.
