# SV-DN-1 Repository Persistence Dispatch Mirror Handoff

Updated: 2026-08-31
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001`
Task: `SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001`
Canonical product owner: `StegVerse-org/stegverse-demo-suite`
Upstream task: `SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001`
TVC successor: `StegVerse-Labs/TVC#264`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE_REQUEST_STAGING_ONLY`

## Goal

Eliminate manual construction of the repository-persistence transport after the authentic
SV-DN-1 five-file package exists.

The dispatcher remains credential-free and never performs a GitHub mutation itself:

```text
exact persistence package
-> TVC repository inspection request
-> sanitized inspection receipt
-> exact APPLY_BOUNDED_FILE_SET warrant staged
-> require explicit TVC SV-DN-1 mutation admission
-> submit exact apply warrant to TVC spool
-> sanitized branch-commit receipt
-> exact OPEN_PULL_REQUEST warrant
-> sanitized PR receipt
-> SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED
```

No credential value enters this task.

## Source-of-truth order

1. `docs/SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001.json`
3. `workers/sv_dn1_repository_persistence_dispatch_worker.py`
4. `docs/SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_MIRROR_HANDOFF.md`
5. `StegVerse-Labs/TVC#264`
6. `StegVerse-Labs/TVC:docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md`
7. authentic local TVC spool receipts

Newer authentic runtime evidence overrides this handoff.

## Required package

```text
schema: stegverse.sv-dn1.repository-persistence-package/v1
state: READY_FOR_ADMITTED_REPOSITORY_MUTATION
target_repository: StegVerse-org/stegverse-demo-suite
target_ref: main
target_root: public/sv-dn1
files: exactly five canonical public artifacts
```

The dispatcher independently verifies package SHA-256, embedded content SHA-256, file
sizes, UTF-8 decodability and exact path set before it constructs any request.

## Phase 1 — inspection

The dispatcher emits only the already-supported TVC read-only request:

`stegverse.tvc-github-repository-inspection-request/v0.1`

for the exact five target paths on `main`.

The sanitized receipt must bind:
- request SHA-256;
- exact repository/ref;
- exact current base SHA;
- exact five path states;
- current SHA-256 or ABSENT for each path;
- TV/TVC credential authority;
- no credential disclosure.

## Phase 2 — staged mutation warrant

From the exact package + inspection receipt, the dispatcher constructs:

`APPLY_BOUNDED_FILE_SET`

with:
- exact inspected base SHA;
- deterministic fresh-branch name derived from the package SHA;
- exactly five file entries;
- exact UTF-8 package bytes;
- each `expected_source_sha256` taken from the inspection receipt;
- exact file and total-byte ceilings;
- TV/TVC authority reference;
- no secret values.

Before issue #264 is admitted, this warrant remains under local `staged/`; it MUST NOT
enter the TVC outbox.

## TVC mutation admission gate

Submission requires a local admission receipt:

```text
schema: stegverse.tvc.sv-dn1-repository-persistence-admission/v1
state: ADMITTED
issue: 264
repository: StegVerse-org/stegverse-demo-suite
credential_authority: TV/TVC
consumer_credential_allowed: false
allowed_operation_classes:
  - APPLY_BOUNDED_FILE_SET
  - OPEN_PULL_REQUEST
```

This receipt is produced only by the TVC successor after the current broker is
authentically governed-validated, current-base compatible and admitted. Source/CI state
cannot substitute.

## Phase 3 — PR warrant

A valid TVC branch-commit receipt must prove:
- `operation_class=APPLY_BOUNDED_FILE_SET`;
- exact warrant SHA;
- result status `BRANCH_COMMIT_CREATED`;
- exact repository/base/branch;
- file_count=5;
- 40-character commit SHA;
- no credential disclosure;
- `merge_performed=false`.

The dispatcher then emits one exact `OPEN_PULL_REQUEST` warrant bound to that branch/head.
The returned receipt must prove `PULL_REQUEST_CREATED` and the exact head/base identities.

Terminal transition:

`SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED`

PR creation is not merge, Pages deployment, public observation, release or certification.

## Authority boundary

This task MAY:
- read the exact local persistence package;
- create non-secret inspection/apply/PR request JSON;
- write its bounded state/outbox/staged files;
- consume sanitized TVC receipts.

This task MUST NOT:
- read or receive `TVC_EPHEMERAL_GITHUB_TOKEN`;
- call GitHub directly;
- mutate a repository;
- merge a PR;
- deploy Pages;
- change package bytes or publication semantics;
- execute SDK/governance/custody;
- grant release/certification authority.

## Runtime truth at implementation

```text
persistence package producer: MERGED / RUNTIME PACKAGE NOT YET OBSERVED
TVC broker APPLY/OPEN_PR source: IMPLEMENTED ON CURRENT BROKER VALIDATION BRANCH
TVC resident spool mutation admission: NOT YET ADMITTED / TVC#264
dispatcher source: IMPLEMENTING
authentic repository branch/PR: NOT YET OBSERVED
merge: NOT YET OBSERVED
Pages authentic-result deployment: NOT YET OBSERVED
public exact-byte observation: MACHINE WORKER MERGED / RUNTIME PENDING
```
