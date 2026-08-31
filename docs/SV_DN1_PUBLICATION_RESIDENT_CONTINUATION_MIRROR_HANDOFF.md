# SV-DN-1 Publication Resident Continuation Mirror Handoff

Updated: 2026-08-31
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-PUBLICATION-RESIDENT-CONTINUATION-001`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Heartbeat authority: `REFERENCE_ONLY`
Authority effect: `NONE_ORCHESTRATION_ONLY`

## Goal

Provide a distinct resident continuation after the already-bounded first-round request is
terminal, without widening or reusing that request's semantics.

The continuation is:

```text
SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY
-> SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001
-> SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED
-> SV-DN1-REPOSITORY-MERGE-DISPATCH-001
-> SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED
-> repository-owned Pages deployment
-> SV-DN1-PUBLICATION-OBSERVER-001
-> SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED
```

The continuation may be invoked repeatedly. A pending TVC admission, unmerged PR, or stale
Pages deployment remains `HANDOFF_READY` and is not converted into failure or authority.

## Source-of-truth order

1. `docs/SV_DN1_PUBLICATION_RESIDENT_CONTINUATION_MIRROR_HANDOFF.md`
2. `scripts/run_sv_dn1_publication_continuation.py`
3. `scripts/consume_sv_dn1_publication_resident_request.py`
4. `control/resident-execution-request.d/sv-dn1-publication-001.json`
5. `docs/SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_MIRROR_HANDOFF.md`
6. `docs/SV_DN1_PUBLICATION_OBSERVER_TASK_MIRROR_HANDOFF.md`

Newer authentic runtime evidence overrides this handoff.

## Request boundary

The publication request is intent only:

```text
request_granted_authority: false
heartbeat_grants_execution_authority: false
github_token_required: false
credential_authority: TV/TVC
second_machine_required: false
```

It does not replace `RESIDENT-EXEC-SV-DN1-FIRST-ROUND-006` and does not reopen a completed
first-round request.

## Resident execution model

The continuation uses targeted WorkerCoordinator cycles only:

```text
python scripts/run_worker_runtime.py --task-id SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001
python scripts/run_worker_runtime.py --task-id SV-DN1-REPOSITORY-MERGE-DISPATCH-001
python scripts/run_worker_runtime.py --task-id SV-DN1-PUBLICATION-OBSERVER-001
```

The merge-dispatch task is naturally dependency-gated until persistence dispatch is
`COMPLETED` at `SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED`.

The observer is dependency-gated until merge dispatch is `COMPLETED` at
`SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED`, and may still return `HANDOFF_READY`
while repository-owned Pages deployment remains pending.

## Completion

Terminal continuation transition:

`SV_DN1_PUBLICATION_CONTINUATION_COMPLETE`

Required terminal child receipt:

```text
SV-DN1-PUBLICATION-OBSERVER-001
transition_id = SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED
all_public_artifacts_observed = true
exact_bytes_preserved = true
credential_used = false
repository_writeback_performed = false
deployment_performed = false
```

## Authority boundary

This continuation MUST NOT:
- use GitHub/provider credentials;
- execute TVC repository operations itself;
- merge a PR;
- deploy Pages;
- decide publication semantics;
- execute SDK/InTr/governance/custody again;
- grant release/certification authority.

It only revisits already-registered downstream machine tasks.

## Current state

```text
first-round request: distinct existing request / unchanged
persistence-dispatch worker: MERGED
TVC issue-264 admission evaluator: MERGED
publication observer: MERGED
publication observer dependency refinement: MERGED
publication resident continuation: MERGED BASE / MERGE-DISPATCH EXTENSION SOURCE COMPLETE / VALIDATION PENDING
authentic persistence PR: NOT YET OBSERVED
authentic public exact-byte observation: NOT YET OBSERVED
```


## 2026-08-31 integration completion

The resident dispatcher now has an exact `sv_dn1_publication` selector bound only to:

`scripts/consume_sv_dn1_publication_resident_request.py`

The portable refresh+dispatch bridge accepts the same exact selector and forwards only
the non-secret persistence-package and TVC admission locators required by this
continuation.

The continuation intentionally does not forward the generic
`STEGVERSE_BOUND_STATE_ROOT`, because both downstream tasks use that generic variable
for different canonical task-specific bound-state roots. Each worker therefore retains
its own canonical default bound state, preventing cross-task receipt/state collision.

Deterministic tests cover selector isolation, non-secret locator propagation, retry-until-
terminal request semantics, generic bound-state isolation, and hosted/credential-bearing
fail-closed behavior.


## Validation evidence

Validated branch head before merge-state recording:

`d7b5e1896ffe87eb3f2ee2699c8838613a7ed8b3`

```text
Heartbeat Worker Project validation
  run: 33405521577
  result: SUCCESS

Organization control-plane validation
  run: 33405521281
  result: SUCCESS

Cross-Framework Current-Basis Resident Request validation
  run: 33405521369
  result: SUCCESS
```

These workflow results are source/contract validation only and do not prove resident
execution, TVC admission, repository persistence, PR merge, Pages deployment, or public
observation.


## 2026-08-31 merge-dispatch extension

The continuation now contains three targeted WorkerCoordinator tasks:

```text
persistence dispatch -> merge dispatch -> publication observer
```

The merge-dispatch worker never receives TVC_EPHEMERAL_GITHUB_TOKEN and does not call
GitHub. It stages one exact non-secret merge request into the bounded TVC merge spool and
consumes only the sanitized merge receipt. Publication observation no longer releases on
PR creation.


The TVC merge-gate resident dispatcher binding is merged at
`StegVerse-Labs/TVC@bec6f0de3d52022c8ddc542c4deca353671a463f`.
