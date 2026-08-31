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
-> separately governed merge + Pages deployment
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
python scripts/run_worker_runtime.py --task-id SV-DN1-PUBLICATION-OBSERVER-001
```

The second task is naturally dependency-gated until the persistence-dispatch task is
`COMPLETED` at `SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED`.

The observer may still return `HANDOFF_READY` after PR creation while merge or Pages
deployment remains pending.

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
publication resident continuation: SOURCE COMPLETE / VALIDATION PENDING
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
