# Actions Cost + Public Exposure Mirror Handoff

Status: ACTIVE / ECOSYSTEM-INVENTORY-STARTED / CONSERVATION-PATCH-PR-OPEN / PUBLIC-EXPOSURE-REVIEW-INITIAL  
Goal Task ID: `SV-ACTIONS-COST-PUBLIC-EXPOSURE-001`  
COSV task.v1: `21111100110000`  
Repository: `StegVerse-Labs/.github`  
Canonical task record: `data/canonical-task-records/SV-ACTIONS-COST-PUBLIC-EXPOSURE-001.json`

## Goal

Reduce GitHub Actions minute burn across the StegVerse ecosystem, stop duplicate or blind validation runs, and classify which repositories can safely be public without exposing StegVerse data that should remain private.

## Authority boundary

GitHub Actions remains validation and evidence transport only. Hosted CI must not claim runtime execution, credential authority, wallet authority, TV/TVC authority, Interlock/InTr admission, WorkerCoordinator claim/fence, or Master Records custody. This task may patch workflow conservation controls, create review artifacts, and open non-destructive PRs. It must not change repository visibility; visibility changes are `OWNER_EXPLICIT_CONSENT` / `USER_ONLY`.

## Current inventory basis

The connected GitHub repository inventory exposed administrative/write access to repositories across `Admissible-Existence`, `AdmittedCode`, `Data-Continuation`, `GCAT-BCAT-Engine`, `master-records`, `StegGhost`, `StegVerse-002`, and `StegVerse-Labs` during the 2026-09-14 sweep.

The immediate operational incident is month-to-date Actions use at 42,938 of 50,000 included minutes as seen by the owner screenshot, combined with repeated failure notifications for `.github`, `Site`, `TV`, `TVC`, `StegOS`, `Governance`, Admissible-Existence repositories, and GCAT-BCAT-Engine repositories.

## Applied patch set in PR branch

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

## Existing conservation evidence found

`StegVerse-Labs/StegVerse-Healer` already contains `app/actions_cost_reducer.py`, a deterministic analyzer for workflow schedule pressure, missing concurrency, unfiltered push/pull_request triggers, matrix fanout, artifact custody, and enforcement thresholds. The next repair should reuse this analyzer rather than inventing another cost model.

Some `.github` workflows already have appropriate `permissions: {}` and `concurrency: cancel-in-progress: true`, including `heartbeat-worker-project.yml` and `org-control-plane-validate.yml`.

## Best fixes by workflow class

1. Add root-level workflow `concurrency` with `${{ github.repository }}-${{ github.workflow }}-${{ github.ref }}` or tighter workflow-specific group and `cancel-in-progress: true` for every push/PR validation workflow.
2. Keep `workflow_dispatch` available for diagnostics, but stop broad automatic triggers while failures are unresolved.
3. Convert recurring non-authoritative observation/audit/dispatch workflows to manual-only or move them to the existing Healer scheduler when they are not release gates.
4. Add path filters to push and pull_request triggers; avoid `on: push` across entire repos unless it is a real release gate.
5. Collapse matrix validation where the matrix is not proving distinct compatibility requirements.
6. Set default permissions to `{}` or `contents: read`; use write permissions only in the exact job that mutates repository state.
7. Never rerun failed workflows blindly. Reruns require a named failure class, expected fix, and narrow validation target.

## Initial public-safety classification

Safe to keep public based on current visibility and role, subject to owner confirmation that public disclosure is intended:

```text
Admissible-Existence/.github
Admissible-Existence/ECAT-ICAT
Admissible-Existence/STCM
Admissible-Existence/learning-transition-governance
AdmittedCode/.github
AdmittedCode/admissibility-receipt
AdmittedCode/code-admit-gate
AdmittedCode/coherency-scanner
AdmittedCode/fleet-status
AdmittedCode/provider-harness
Data-Continuation/core-lite
Data-Continuation/formalism-tests
Data-Continuation/RTG-Tests
GCAT-BCAT-Engine/Documentation
GCAT-BCAT-Engine/Publisher
GCAT-BCAT-Engine/StegSim
GCAT-BCAT-Engine/Triage
GCAT-BCAT-Engine/core-lite
GCAT-BCAT-Engine/core-lite-prod
GCAT-BCAT-Engine/workflows
master-records/monitoring
StegVerse-002/core-lite
StegVerse-002/stegguardian-wiki
StegVerse-Labs/3I-Atlas
StegVerse-Labs/Epsteinality
StegVerse-Labs/FREE-DOM
StegVerse-Labs/Giuffre-ality
StegVerse-Labs/Maxwellality
StegVerse-Labs/Patents
StegVerse-Labs/Site
StegVerse-Labs/StegBiography
StegVerse-Labs/StegVerse-Healer
StegVerse-Labs/Trumpality
```

Private/internal repositories that should stay private until a secret/credential/private-state/personal-data/IP scrub passes:

```text
Admissible-Existence/AE
Admissible-Existence/BC
Admissible-Existence/CHF
Admissible-Existence/CTA
Admissible-Existence/DC
Admissible-Existence/DaCo
Admissible-Existence/Existence
Admissible-Existence/FI
Admissible-Existence/Fundamental-Invariants-of-Reality
Admissible-Existence/GCAT-BCAT
Admissible-Existence/GTG
Admissible-Existence/HPS
Admissible-Existence/IICT
Admissible-Existence/IW
Admissible-Existence/RE
Admissible-Existence/RE-Reduction
Admissible-Existence/RTG
Admissible-Existence/SOL
Admissible-Existence/TT
Admissible-Existence/Triad
Admissible-Existence/ae-validation-factory
Admissible-Existence/ae-validation-research
Admissible-Existence/core-lite
Admissible-Existence/standing-proof-formalism
Admissible-Existence/telemetry
Admissible-Existence/tracker
Admissible-Existence/validation-profile-registry
Admissible-Existence/validator
Data-Continuation/.github
Data-Continuation/StegClaw
Data-Continuation/formalisms
Data-Continuation/products
GCAT-BCAT-Engine/.github
GCAT-BCAT-Engine/Gemstone_IV
GCAT-BCAT-Engine/Marketplace
GCAT-BCAT-Engine/WZ
GCAT-BCAT-Engine/core-addons
GCAT-BCAT-Engine/core-full
GCAT-BCAT-Engine/core-master
GCAT-BCAT-Engine/telemetry
master-records/.github
master-records/core-lite
master-records/orchestration
master-records/telemetry
StegGhost/.github
StegGhost/StegCGE
StegGhost/automated_buildout
StegGhost/entity-sandbox-runner
StegGhost/ghost-pat-lab
StegGhost/stegverse-sandbox
StegGhost/telemetry
StegVerse-002/.github
StegVerse-002/StegGuardian
StegVerse-002/StegProfile
StegVerse-002/admissibility-gateway
StegVerse-002/capability-registry
StegVerse-002/legacy_core_lite
StegVerse-002/micro-node-runtime
StegVerse-Labs/Continuity
StegVerse-Labs/Governance
StegVerse-Labs/SCW
StegVerse-Labs/StegVerse-SCW
StegVerse-Labs/TVC
StegVerse-Labs/TV
StegVerse-Labs/hybrid-collab-bridge
```

Potentially public after scrub/review, not before:

```text
StegVerse-Labs/Governance
StegVerse-Labs/hybrid-collab-bridge
StegVerse-Labs/SCW
StegVerse-Labs/StegVerse-SCW
Admissible-Existence/standing-proof-formalism
Data-Continuation/formalisms
```

Do not make these public in the current state without targeted review: `TVC`, `TV`, `Continuity`, `StegOS`, `micro-node-runtime`, `StegProfile`, `StegGuardian`, `entity-sandbox-runner`, telemetry/orchestration repos, private GCAT/BCAT core-full/core-addons/core-master/Marketplace/Gemstone_IV, and any repo that carries KV, SKAP, resident runtime, credential, receipt, custody, personal-state, patent-private, or unpublished implementation details.

## Next bounded work

1. Open PR for the `.github` conservation patch.
2. Continue scanning `Site`, `TVC`, `TV`, `StegOS`, `Governance`, Admissible-Existence, and GCAT-BCAT-Engine workflow directories for missing concurrency, unfiltered triggers, high-frequency schedules, and duplicate validators.
3. Use `StegVerse-Healer/app/actions_cost_reducer.py` as the canonical analyzer and add repo inventory input rather than running every validator.
4. Patch only low-risk workflow controls automatically; leave visibility changes for owner action.

## Current truth

```text
canonical task: IN_PROGRESS
workflow conservation patch branch: CREATED
.github low-risk workflow concurrency patches: APPLIED
repository visibility mutations: NOT PERFORMED
full ecosystem workflow scan: STARTED_NOT_COMPLETE
public-safe classification: INITIAL_CONSERVATIVE
Actions cost reduction: NOT VALIDATED UNTIL PR MERGED_AND_NEXT_RUN_OBSERVED
```
