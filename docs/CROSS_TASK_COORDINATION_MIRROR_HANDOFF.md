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

### WorkerCoordinator claim-coverage parity

The composed ledger has a fail-closed source gate against `control/worker-registry.json` whenever that sibling registry is present.

`control/worker-registry.json` remains authoritative for WorkerCoordinator claim/fence ownership. Coordination claims remain projections only.

For every unreleased task with `executor_binding=BOUND` and a non-empty claim id, composed coordination must contain an `ACTIVE` claim row with matching:

```text
claim_id
task_id
fencing_token
worker_id
worker_instance_id
```

The inverse is also checked for worker-bound coordination rows: an `ACTIVE` coordination claim carrying WorkerCoordinator identity cannot survive after the matching registry claim is terminal/released. Duplicate bound claim ids, missing mirrors, stale mirrors, identity drift, or an incompatible worker-registry schema fail closed before consumers receive the composed ledger.

This check grants no claim/fence/execution authority and infers no current runtime execution. It exists solely to prevent coordination consumers from silently operating on stale or incomplete machine-ownership projections.

Validated implementation:

```text
PR: 1048
validated head: 67e968486dd642237963c30030ae747031c2cefb
merge: b693d9029197de61f1aee66d2211647eb42ff32d
cross-task coordination run: 34004857922 SUCCESS
heartbeat worker run: 34004857932 SUCCESS
organization control-plane run: 34004857950 SUCCESS
```

The Heartbeat validation includes the repository-real composed-ledger/worker-registry parity test; current G13/G17/G18 mirrors passed that exact check. These are source/validation facts only and do not prove current runtime execution.

README impact for PR #1048: MATERIAL; `README.md` was updated in the same change set.

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

Machine enforcement exists at two canonical boundaries, without creating a parallel scheduler or authority path:

1. **session/build pre-work** — `scripts/session_build_preflight.py` can require README-impact completeness before new functional work/task creation may be considered;
2. **WorkerCoordinator admission** — `heartbeat_runtime/worker_task_admission.py` requires README-impact completeness before an admitted worker can proceed toward existing assignment/claim/fence mechanics.

For a material functional change, both gates require an affected README path, an in-change-set README update, and evidence tying that update to the functional change. For an explicit non-material determination, both require rationale plus supporting evidence. Missing materiality or incomplete evidence fails closed.

The session/build gate emits `STOP_AT_README_IMPACT_DEPENDENCY` and prohibits task creation when its README-impact declaration is incomplete. Worker admission exposes the corresponding `readme_impact_complete` predicate and blocks admission when false.

Legacy/nonfunctional invocations that do not enter the new gate are not retroactively stranded solely because the field did not exist previously. New StegVerse functional mutations are expected to enter through the session-entry/preflight contract with README impact declared.

Implementation locations:

```text
scripts/session_build_preflight.py
management/session-build-preflight-contract.json
tests/test_session_build_preflight.py
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

README impact worker-admission preflight:
  PR: 1023
  validated head: e9eb525621e545588b704a5db06223c61662e31d
  merge: f62bf7094ef8028e425394397bd52522a17934cb
  organization control-plane run: 34001225776 SUCCESS
  cross-task coordination run: 34001225834 SUCCESS
  heartbeat worker run: 34001225851 SUCCESS

README impact session/build pre-work preflight:
  PR: 1027
  validated head: 45631a2c718fa8d982a771cdb55b301db595a81a
  merge: 5626bfc8d1cb76bb1d1eda6ef3d0c0be7429e17a
  organization control-plane run: 34001532346 SUCCESS
  cross-task coordination run: 34001532400 SUCCESS
  heartbeat worker run: 34001532342 SUCCESS

StegGate stable-rendezvous active claim projection:
  fragment commit: 1a4f61beaebf2d08d34a39c24117bb3b138403d2
  README completion commit: 01b3b0196ef25f934754f89730054742f4b893c9
  cross-task coordination run: 34004652942 SUCCESS

WorkerCoordinator claim-coverage parity:
  PR: 1048
  validated head: 67e968486dd642237963c30030ae747031c2cefb
  merge: b693d9029197de61f1aee66d2211647eb42ff32d
  cross-task coordination run: 34004857922 SUCCESS
  heartbeat worker run: 34004857932 SUCCESS
  organization control-plane run: 34004857950 SUCCESS
```

These are source/validation facts only and are not runtime-event or product-activation evidence.

## Migrated bound `resident_request_consumed` instances

Canonical composition carries distinct subject-bound records for resident request consumers including Ecosystem Chat, StegIndex one-shot activation, HIL sovereign receiver, G18 existing-claim resume, SV002 organization/public runtime boundaries, SV-011 phase5 boundaries, and StegVerse-001 bounded autonomy. Each remains subject-bound; similarly named predicates are not globally interchangeable.

The StegVerse-001 bounded-autonomy predicate records its dependency on the already-existing one-shot resident-stack activation predicate; it does not create a second activation mechanism or bypass TVC lease issuance.

## Active claim projection state

The composed ledger mirrors the currently resolved control-plane active claims for collision detection:

1. `SHWP-SHWP-ALL-ORG-FEDERATION-001-G17` / fence 17;
2. `SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18` / fence 18;
3. `SHWP-STEGGATE-STABLE-RENDEZVOUS-WORKER-001-G13` / fence 13.

These projections preserve existing ownership only. They do not mint, renew, transfer, or prove execution authority. A `BLOCKED` or otherwise nonterminal task state does not release the underlying claim.

Claim-coverage parity now makes this set fail closed against current WorkerCoordinator registry truth rather than relying on static-fragment completeness by convention.

## Resident-presence migration boundary

`control/cross-task-coordination-candidates/resident-process-alive-supervised.json` remains intentionally `DEFERRED_SUBJECT_BINDING_REQUIRED`.

The shared runtime-presence projector proves a concrete runtime root/node instance. Static consumer files do not yet prove that all consumers refer to the same runtime-root/node subject. Therefore a global resident-presence Boolean MUST NOT be registered until authentic runtime evidence supplies stable subject identity. No second presence projector should be created to bypass that requirement.

## StegIndex consistency

`StegVerse-Labs/StegIndex/scripts/resolve_cross_task_coordination.py` composes the same base + fragment model in read-only form and fails closed on duplicate/drifted fragments. WorkerCoordinator, handoff projection, StegIndex, and session/build pre-work therefore consume the same logical coordination composition model rather than independently interpreting partial state.

## Current coordination state

Core source implementation: VALIDATED.
Composed canonical ledger: VALIDATED.
WorkerCoordinator claim-coverage parity: MERGED / VALIDATED.
Subject-bound resident-request migration: PARTIAL / ACTIVE.
Active control-plane claim projection: CURRENTLY RESOLVED G13/G17/G18 REPRESENTED AND PARITY-VALIDATED.
StegIndex composed discovery: VALIDATED.
README impact WorkerCoordinator enforcement: MERGED / VALIDATED.
README impact session/build pre-work enforcement: MERGED / VALIDATED.
Resident-presence shared predicate: DEFERRED / AUTHENTIC SUBJECT BINDING REQUIRED.
Ecosystem adoption: NOT COMPLETE.
Runtime activation claims created by this coordination work: NONE.

Existing runtime activation, WorkerCoordinator execution, sovereign inference, HIL, credential/route, and other already-owned workstreams remain outside the coordination source claim and must not be restarted merely because they consume coordination predicates.

## Remaining machine work

1. inspect remaining canonical handoffs for genuinely shared predicates beyond `resident_request_consumed`;
2. establish exact subject identity before any shared registration, especially runtime-presence predicates;
3. register only genuinely reusable producer/evidence relationships and exact gaps;
4. bind any additional session/build consumers that still read an incomplete coordination slice;
5. re-resolve the active control-plane claim set before each new claim migration; claim-coverage parity must fail closed if projections drift;
6. validate each migration deterministically;
7. evaluate tag/release only after ecosystem-adoption criteria are actually satisfied;
8. after actual release/tag, verify governed propagation requirements for `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Completion and archive rule

A thread MUST NOT be described as ready for archiving merely because its current state has been written into a handoff.

Archive-ready may be stated only when one of these conditions is true:

1. the session goal is complete; or
2. every remaining task needed for that goal is durably assigned to an actually operating autonomous executor whose continuation does not depend on this session, with that ownership and executable continuation evidenced canonically.

A handoff by itself is continuity evidence, not task completion and not proof that remaining work will execute automatically.

Current goal completion: FALSE.
Current ecosystem-adoption work remaining: TRUE.
Thread archive-ready: FALSE.

README impact for this reconciliation commit: NON-MATERIAL. Reason: documentation-only reconciliation of already-merged, already-validated PR #1048 behavior and exact run evidence; repository function is unchanged. Evidence: PR #1048, merge `b693d9029197de61f1aee66d2211647eb42ff32d`, runs `34004857922`, `34004857932`, and `34004857950`.
