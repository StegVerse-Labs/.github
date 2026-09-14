# Actions Cost + Public Exposure Mirror Handoff

Status: ACTIVE / PUBLIC-READINESS-SCRUB-PRS-OPEN / CONSERVATION-PATCH-PR-OPEN  
Goal Task ID: `SV-ACTIONS-COST-PUBLIC-EXPOSURE-001`  
COSV task.v1: `21111100110000`  
Repository: `StegVerse-Labs/.github`  
Canonical task record: `data/canonical-task-records/SV-ACTIONS-COST-PUBLIC-EXPOSURE-001.json`

## Goal

Reduce GitHub Actions minute burn across the StegVerse ecosystem, stop duplicate or blind validation runs, and classify/prepare repositories that can safely become public without exposing StegVerse data that should remain private.

## Authority boundary

GitHub Actions remains validation/evidence transport only. Hosted CI must not claim runtime execution, credential authority, wallet authority, TV/TVC authority, Interlock/InTr admission, WorkerCoordinator claim/fence, or Master Records custody. This task may patch workflow conservation controls, create review artifacts, and open non-destructive PRs. It must not change repository visibility; visibility changes are `OWNER_EXPLICIT_CONSENT` / `USER_ONLY`.

## Current inventory basis

The connected GitHub repository inventory exposed administrative/write access to repositories across `Admissible-Existence`, `AdmittedCode`, `Data-Continuation`, `GCAT-BCAT-Engine`, `master-records`, `StegGhost`, `StegVerse-002`, and `StegVerse-Labs` during the 2026-09-14 sweep.

The immediate operational incident is month-to-date Actions use at 42,938 of 50,000 included minutes as seen by the owner screenshot, combined with repeated failure notifications for `.github`, `Site`, `TV`, `TVC`, `StegOS`, `Governance`, Admissible-Existence repositories, and GCAT-BCAT-Engine repositories.

## Applied Actions conservation patch set

PR: `StegVerse-Labs/.github#1820`  
Branch: `actions-conservation-sweep-20260914`

Applied conservation controls in `StegVerse-Labs/.github`:

```text
.github/workflows/cross-framework-current-basis-v04-resident.yml
  + concurrency group cross-framework-current-basis-v04-${{ github.ref }}
  + cancel-in-progress true

.github/workflows/cross-task-coordination-validation.yml
  + concurrency group cross-task-coordination-validation-${{ github.ref }}
  + cancel-in-progress true

.github/workflows/validate-kv-ai-memory-resident.yml
  + concurrency group validate-kv-ai-memory-resident-${{ github.ref }}
  + cancel-in-progress true
```

These are low-risk because they only cancel older duplicate in-progress validations for the same workflow/ref and do not weaken test commands or authority boundaries.

## Public-readiness scrub performed

The six make-public candidates were searched with bounded GitHub code search for:

```text
password token secret private_key api_key credential wallet seed mnemonic sk- OPENAI_API_KEY GITHUB_TOKEN
Rigel Randolph Chelsie Rensley Ryori address phone ssn va claim veteran disability medical bank coinbase icloud personal-kv skap
PRIVATE PERSONAL CONFIDENTIAL INTERNAL TODO FIXME HACK secret credential
```

Result: no matching search results returned for these six candidate repositories in the bounded scan.

## Active public-readiness PRs

```text
StegVerse-Labs/Governance#43
  branch: public-readiness-20260914
  adds: docs/PUBLIC_READINESS.md
  state: OPEN

StegVerse-Labs/hybrid-collab-bridge#28
  branch: public-readiness-20260914
  adds: docs/PUBLIC_READINESS.md
  state: OPEN
  note: legacy bridge-openai.yml is already manual-only and fail-closed

StegVerse-Labs/SCW#89
  branch: public-readiness-20260914
  adds: docs/PUBLIC_READINESS.md
  state: OPEN

StegVerse-Labs/StegVerse-SCW#46
  branch: public-readiness-20260914
  adds: docs/PUBLIC_READINESS.md
  state: OPEN

Admissible-Existence/standing-proof-formalism#4
  branch: public-readiness-20260914
  adds: docs/PUBLIC_READINESS.md
  state: OPEN

Data-Continuation/formalisms#2
  branch: public-readiness-20260914
  adds: docs/PUBLIC_READINESS.md
  state: OPEN
```

## Make-public candidates under active readiness work

```text
StegVerse-Labs/Governance
StegVerse-Labs/hybrid-collab-bridge
StegVerse-Labs/SCW
StegVerse-Labs/StegVerse-SCW
Admissible-Existence/standing-proof-formalism
Data-Continuation/formalisms
```

## Repositories still not public-ready

Do not make these public in the current state without targeted review: `TVC`, `TV`, `Continuity`, `StegOS`, `micro-node-runtime`, `StegProfile`, `StegGuardian`, `entity-sandbox-runner`, telemetry/orchestration repos, private GCAT/BCAT core-full/core-addons/core-master/Marketplace/Gemstone_IV, and any repo that carries KV, SKAP, resident runtime, credential, receipt, custody, personal-state, patent-private, or unpublished implementation details.

## Best fixes by workflow class

1. Add root-level workflow `concurrency` with `${{ github.repository }}-${{ github.workflow }}-${{ github.ref }}` or tighter workflow-specific group and `cancel-in-progress: true` for every push/PR validation workflow.
2. Keep `workflow_dispatch` available for diagnostics, but stop broad automatic triggers while failures are unresolved.
3. Convert recurring non-authoritative observation/audit/dispatch workflows to manual-only or move them to the existing Healer scheduler when they are not release gates.
4. Add path filters to push and pull_request triggers; avoid `on: push` across entire repos unless it is a real release gate.
5. Collapse matrix validation where the matrix is not proving distinct compatibility requirements.
6. Set default permissions to `{}` or `contents: read`; use write permissions only in the exact job that mutates repository state.
7. Never rerun failed workflows blindly. Reruns require a named failure class, expected fix, and narrow validation target.

## Current truth

```text
canonical task: IN_PROGRESS
workflow conservation patch branch: CREATED
.github low-risk workflow concurrency patches: APPLIED
public-readiness candidate PRs: OPEN_IN_6_REPOS
repository visibility mutations: NOT PERFORMED
full ecosystem workflow scan: STARTED_NOT_COMPLETE
public-safe classification: INITIAL_CONSERVATIVE
Actions cost reduction: NOT VALIDATED UNTIL PR_MERGED_AND_NEXT_RUN_OBSERVED
```
