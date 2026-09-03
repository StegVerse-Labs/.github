# Ecosystem Worker Blocker Fallback Invariant

## Status

```text
goal_id: WORKER-BLOCKER-FALLBACK-ECOSYSTEM-001
owner: StegVerse-Labs/.github#242
source_runtime_policy: docs/BLOCKER_RESOLUTION_MIRROR_HANDOFF.md / issue #65
state: ADOPTION_IN_PROGRESS
credential_authority: TV/TVC_ONLY
github_token_runtime_authority: NONE
```

## Purpose

A blocker constrains a surface; it does not terminate a worker's broader assignment.

Every StegVerse or Admissible-Existence worker that can encounter more than one admissible in-scope surface MUST preserve the blocked surface as durable work state and continue to the next admissible, non-colliding surface.

This contract extends the existing blocker-resolution rule that a blocker requires solution/workaround/escalation. It does not replace the runtime blocker policy, widen worker authority, or transfer repository-local ownership.

## Normative invariant

For each assigned scope, a worker MUST:

1. inspect the current canonical `*_MIRROR_HANDOFF.md`, active claim, task registry, or equivalent owner record before mutation;
2. attempt the highest-priority admissible non-duplicate work;
3. when a surface cannot proceed, classify the constraint and preserve the exact evidence;
4. persist a blocker record in the repository-local handoff/task/receipt when authorized;
5. if repository-local persistence is unavailable, persist the blocker in the coordinating worker/task registry or central adoption owner;
6. record at minimum:
   - repository or system;
   - task/surface identity;
   - failure or constraint class;
   - observed evidence;
   - authority/collision boundary;
   - `solution_required=true` unless the surface is explicitly not applicable;
   - release condition;
   - expected completion evidence;
   - next executable action;
   - durable owner;
7. enumerate all remaining in-scope surfaces immediately after persisting the blocker;
8. execute the next highest-priority admissible, non-colliding surface;
9. avoid unchanged retry loops; repeated observation without state change is not progress;
10. revisit blocked surfaces when their release conditions change or new evidence appears;
11. stop only when every in-scope surface is COMPLETE, SUPERSEDED/NOT_APPLICABLE with evidence, or durably constrained and no other admissible work remains.

## Required state semantics

`BLOCKED` means the specific surface cannot currently progress through the attempted path. It MUST NOT mean:

- worker stopped;
- task abandoned;
- assignment complete;
- authority silently transferred;
- retry forever;
- wait without a durable owner;
- skip later in-scope work.

Workers SHOULD expose a machine-readable fallback state equivalent to:

```text
fallback_mode: PERSIST_BLOCKER_AND_CONTINUE
```

## Constraint classes

### Internal solvable constraint

The worker SHOULD derive or execute another admitted implementation path within its existing authority.

### Third-party constraint

Third-party failure is never a terminal StegVerse blocker. Preserve the unavailable path and select an admitted StegVerse-owned, federated, or explicitly governed fallback consistent with `docs/BLOCKER_RESOLUTION_MIRROR_HANDOFF.md`.

### Authority constraint

If the worker lacks authority, it MUST create or refresh the correct TV/TVC, machine-owned, or authority-owner continuation and continue unrelated admissible in-scope work. Authority escalation does not imply completion.

### Collision constraint

If another live claim owns the exact surface, the worker MUST not compete. It records the collision/owner/release condition and continues elsewhere in scope.

### Evidence constraint

Missing proof, artifact, receipt, hosted result, runtime observation, or physical evidence remains open. The worker records the evidence requirement and continues any other work whose prerequisites remain satisfied.

## Failure isolation requirement

A repository-local or item-local exception MUST NOT abort a multi-item worker sweep unless continuing would violate authority, integrity, or safety for every remaining item.

Controllers SHOULD isolate each independent repository/task item so that an exception is converted into a durable blocker record and later items continue.

Tests for multi-item workers MUST include at least one case proving:

1. item A encounters a blocker;
2. item A blocker is persisted with owner, release condition, and next action;
3. item B is still executed;
4. final aggregate status remains fail-closed while item A is unresolved.

## Handoff/task propagation

When a blocker is found, the worker MUST prefer the following durable destination order:

1. repository-local canonical handoff/task/receipt owned by the affected scope;
2. existing repository-native worker issue/task registry;
3. coordinating worker registry/control-plane blocker queue;
4. authority-owner escalation task.

A blocker reported only in transient logs or chat is non-conformant.

## Adoption boundary

Issue `StegVerse-Labs/.github#242` owns ecosystem adoption inventory and bounded follow-up task creation.

Issue `StegVerse-Labs/.github#65` and canonical heartbeat workers retain machine-owned runtime blocker classification, workaround selection, successor task derivation, runtime transitions, and remediation receipts for already-bound worker scopes.

Adoption MUST NOT mass-edit worker repositories without reading their current handoffs and claims.

## Credential and authority invariants

```text
credential_authority: TV/TVC_ONLY
non_tv_tvc_secrets_allowed: false
github_token_runtime_authority: NONE
model_output_execution_authority: NONE
blocker_persistence_creates_authority: false
worker_continuation_creates_authority: false
```

## Completion condition

Ecosystem adoption is complete only when:

- shared runtime/control-plane contracts reference equivalent semantics;
- worker-family adoption inventory is complete;
- each applicable worker family is `ADOPTED`, `ALREADY_CONFORMANT`, or has a durable `FOLLOWUP_TASK_CREATED` owner;
- representative controller/runtime tests prove blocker isolation and continuation;
- hosted validation evidence is inspected where applicable;
- no unresolved adoption surface is left only in chat or transient logs.

## StegIndex validation/reconciliation adoption — 2026-09-03

The `validation_reconciliation` worker family is now adopted through the canonical StegIndex pre-work path rather than a new worker implementation.

Evidence:
- StegVerse-Labs/StegIndex PR #3 -> `637b33c99adf08505b485c504512b4b1ba708141`
- StegVerse-Labs/.github PR #881 -> `376d48b2ac9aa672920ab169ad6b6d2e62349d43`
- StegVerse-Labs/.github PR #885 -> `9ac197a019f695f3a5344b6b7498d4e2c1683836`
- organization control-plane validation `33713433913` SUCCESS
- Heartbeat Worker Project validation `33713434257` SUCCESS

Behavior:
- stale/contradictory indexed truth is persisted as the exact reconciliation dependency rather than a generic blocker;
- usable existing capability truth prevents duplicate implementation;
- machine-executable predicates are surfaced for continuation through their canonical owner;
- only `NO_EXISTING_CAPABILITY_MATCH` allows new work to be considered at the session/build pre-work boundary.

This adoption grants no execution, admission, credential, routing, transition, claim/fence, publication, custody, or consequence authority and does not modify the machine-owned #65 runtime blocker scope.

## Site / Publisher propagation conformance — 2026-09-03

The `site_publisher_propagation` worker family is already conformant and requires no duplicate worker implementation.

Canonical evidence:
- `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md`
- `GCAT-BCAT-Engine/Publisher/docs/PUBLISHER_MIRROR_HANDOFF.md`

Publisher persists `PENDING_SITE_ACTIVATION` with the exact blocker, release condition, next executable task, durable workflow owner, and trigger while retaining separate active/scheduled work. Site independently preserves explicit blocker ownership, parallel-safe workload continuation, and lifecycle distinctions such as deployment != activation.

This conformance does not grant publication, release, execution, custody, admissibility, Guardian, credential, routing, or transition authority.

## TV / TVC authority-bound invocation conformance — 2026-09-03

The `tv_tvc_authority_bound_invocation` family is already conformant.

Canonical evidence:
- `StegVerse-Labs/TV/docs/TV_MIRROR_HANDOFF.md`
- `StegVerse-Labs/TVC/TVC_MIRROR_HANDOFF.md`

TV/TVC preserves credential authority as TV/TVC-only, rejects generic GitHub/provider credential substitution, classifies missing resident credential or explicit authorization as bounded blocked-dependency states rather than FAILED, and explicitly allows unrelated validated execution to continue while credential-model semantic expansion is frozen.

The current iPhone-bound credential evidence also records `another_physical_machine_required=false`; no second-machine fallback is introduced by this conformance finding.

This adoption changes no credential, release, publication, execution, routing, transition, custody, or wallet authority.

## Healer mailbox/failure-remediation conformance — 2026-09-03

The `mailbox_failure_remediation` family is already conformant.

Canonical evidence:
- `StegVerse-Labs/StegVerse-Healer/failure_mailbox/FAILURE_MAILBOX_MIRROR_HANDOFF.md`
- `failure_mailbox/backfill.py`
- `failure_mailbox/incident_engine.py`

The historical backfill isolates malformed/unsupported messages per row, records them in quarantine with durable row identity/reason, and continues processing later rows. Valid observations enter independent incident state machines, so one unresolved incident does not terminate ingestion or erase later admissible work.

This conformance is credential-neutral and grants no mailbox mutation, repair, repository mutation, deployment, release, heartbeat, publication, or general runtime authority.

## Publication / release observer conformance — 2026-09-03

The `publication_release_observers` family is already conformant.

Canonical evidence:
- `GCAT-BCAT-Engine/Publisher/docs/STEGCLAW_RELEASE_AWARENESS_MIRROR_HANDOFF.md`
- `GCAT-BCAT-Engine/Publisher/PUBLISHER_MIRROR_HANDOFF.md`

Publisher release-awareness lanes are explicitly `PARALLEL_SAFE_NON_AUTHORIZING_RELEASE_AWARENESS`. Dedicated awareness success is retained independently while unrelated RTG-001 / stegdb-sync failures remain separate and are not converted into success or used to terminate other bounded observer work.

Publication, release, custody, execution, Guardian, admissibility, runtime, and cross-repository mutation authority remain false.
