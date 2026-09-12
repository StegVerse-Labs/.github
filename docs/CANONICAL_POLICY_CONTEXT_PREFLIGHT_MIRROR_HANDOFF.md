# Canonical Policy Context Preflight Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Canonical owner goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Parent: `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`
Status: `SOURCE_IMPLEMENTED / VALIDATION_PENDING`
Authority effect: `NONE_PREWORK_INTERPRETATION_ONLY`

## Problem

StegVerse already has canonical architecture, lifecycle, authority, custody, and task-continuity policy, but the session/build preflight previously consulted StegIndex and cross-task coordination without requiring those policy semantics to be loaded before the session interpreted task state.

That allowed repeated cross-session semantic drift: a session could correctly discover an existing task/evidence relationship and still misinterpret canonical terms such as worker expiry, ephemeral-node lifetime, absence, staleness, device/node role, HeartBeat role, authority, verifier/custody, or remediation ownership. The human then had to restate already-canonical policy.

## Repair

The existing `scripts/session_build_preflight.py` now resolves canonical policy context before state interpretation, blocker derivation, remediation proposal, or new work creation.

Canonical registry:

```text
control/canonical-policy-context-registry.json
```

Required global sources currently include:

```text
data/task-coordination-policy.json
docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md
```

When a canonical task record contains:

```json
"canonical_policy_refs": ["..."]
```

the preflight automatically resolves those refs as well. Cross-repository refs use the existing `STEGVERSE_REPO_ROOTS_JSON` materialized-repository map and use the form:

```text
StegVerse-Labs/StegHealth:STEGHEALTH_MIRROR_HANDOFF.md
StegVerse-Labs/StegDB:STEGDB_MIRROR_HANDOFF.md
```

No network fetch is introduced.

## Fail-closed behavior

If a required canonical policy ref cannot be resolved, preflight returns:

```text
STOP_AT_CANONICAL_POLICY_DEPENDENCY
```

The missing policy is an exact machine dependency. It is not permission to infer replacement semantics and it does not require the human to re-explain the policy in chat.

## Canonical invariants already reused

The global task-coordination policy already carries relevant standing invariants including:

```text
CANONICALLY_RESOLVABLE_TASK_DOCUMENTATION_IS_NOT_REPEATED_IN_PROMPTS
RUNNERS_EXPIRE_BEFORE_RECORDING_CONTINUITY
EPHEMERAL_CAPABILITY_DOES_NOT_MEAN_EPHEMERAL_ACCOUNTABILITY
TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY
WORKERCOORDINATOR_OWNS_EXECUTION_CLAIM_AND_FENCE
MASTER_RECORDS_OWNS_OBSERVED_REALITY_AND_RECONSTRUCTION
MISSING_EVIDENCE_IS_NOT_PROOF_OF_NON_OCCURRENCE
```

The new gate does not redefine those policies; it makes session/build pre-work consume them.

## Authority boundary

Policy-context resolution:

- does not prove runtime truth;
- does not create or renew a worker/WorkerCoordinator;
- does not create claim/fence authority;
- does not grant Interlock/InTr transition authority;
- does not grant TV/TVC credential authority;
- does not grant route, publication, custody, receiving, or release authority;
- does not create a second coordinator or governance layer.

It only constrains interpretation and task creation to already-canonical semantics.

## Validation

Regression coverage:

```text
tests/test_canonical_policy_context_preflight.py
```

The tests require:

1. global canonical policy sources resolve automatically;
2. known ephemeral/accountability invariants are surfaced without human restatement;
3. a missing required policy ref fails closed;
4. task-declared `canonical_policy_refs` are auto-loaded;
5. cross-repository canonical refs resolve through `STEGVERSE_REPO_ROOTS_JSON`.

Exact-head CI evidence is pending.

## Adoption

Existing tasks without `canonical_policy_refs` still receive the global policy context. Task/domain owners should add task-specific refs only where additional canonical domain semantics are required. Once declared, those refs become mandatory preflight dependencies and cannot be silently ignored.

The intended steady state is that a new session needs only the task/COSV continuation pointer; canonical policy, handoff, evidence, and lifecycle semantics are resolved by the system rather than re-entered by the human.

## README impact

Material. This changes session/build pre-work behavior by adding a new fail-closed interpretation gate. Root `README.md` must document the policy-context requirement in the same change set before merge.

## Manual work

None.
