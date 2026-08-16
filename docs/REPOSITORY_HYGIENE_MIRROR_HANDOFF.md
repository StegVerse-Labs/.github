# Repository Hygiene Mirror Handoff

Updated: 2026-08-15T19:45:00-05:00

## Active goal

```text
goal_id: HYGIENE-CAUSAL-ROOTS-001
originating_goal: clean the StegVerse ecosystem from causal roots outward so downstream high-complexity repositories are not repeatedly re-contaminated by upstream branch/workflow/issue/task-generation patterns
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#165
related_cost_issue: StegVerse-Labs/.github#164
related_workflow_minimization: StegVerse-Labs/.github#167 and #168
canonical_owner: StegVerse-Labs organization hygiene control plane
active_implementation_claim: HYGIENE-CAUSAL-ROOTS-001-20260815
claimant: current repository-hygiene session
role: IMPLEMENTATION_AND_VALIDATION
claim_created_at: 2026-08-15T19:30:00-05:00
claim_expires_at: 2026-08-15T22:30:00-05:00
claim_release_condition: Wave-0 roots are classified, safe cleanup batches are applied/assigned, and all remaining work is carried by durable repository-native owners
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
render_production_runtime: prohibited
```

## Governing strategy

Canonical cleanup order:

1. Wave 0 — organization/control roots: `.github`, `repo-standards`, `Continuity`.
2. Wave 1 — shared authority/runtime producers: TV, TVC, StegID, micro-node-runtime, LLM-adapter, Master Records and live-contract peers.
3. Wave 2 — low-complexity leaves used as healthy reference repos.
4. Wave 3 — medium-complexity consumers.
5. Wave 4 — Site and StegCore as high-complexity sinks.

Site/StegCore destructive cleanup remains deferred until upstream debt generation is measured and remediated.

## Hygiene invariants

A healthy repository converges toward: canonical handoffs with explicit supersession; bounded expiring claims; no branch-per-session lifecycle when durable worker/task state suffices; no duplicate terminal branch families without evidence-retention need; no stale PR/issue state contradicting current task evidence; GitHub Actions used only for validation/coordination; 0/1/2 stable workflow entry surfaces where technically sufficient; recurring production work on StegVerse-controlled workers; and TV/TVC-only credential authority.

## Durable evidence surfaces

```text
docs/REPOSITORY_HYGIENE_MIRROR_HANDOFF.md
control/repository-hygiene-wave0-baseline.json
control/repository-hygiene-wave0-classification.json
StegVerse-Labs/.github#165
StegVerse-Labs/.github#167
StegVerse-Labs/.github#168
```

## Wave-0 live baseline

| repository | branches | open PRs | open issues observed | workflows | state |
|---|---:|---:|---:|---:|---|
| StegVerse-Labs/.github | 73 | 0 | 17 | 17 after batch-1 | ACTIVE_CLEANUP |
| StegVerse-Labs/repo-standards | 16 | 2 | 4 | 5 | CLASSIFICATION_PENDING |
| StegVerse-Labs/Continuity | 5 | 0 | 1 | 9 | CLASSIFICATION_PENDING |

The control root itself therefore generates material lifecycle/automation debt; Site and StegCore cannot be treated as isolated causes.

## Completed cleanup batch 1 — organization validation surfaces

The organization workflow surface was reduced from 20 to 17 active workflows.

Retained stable entrypoint:

```text
.github/workflows/org-control-plane-validate.yml
```

It now includes the non-authorizing organization control-plane, allocator, continuation, session-assistance, aggregation, observer, repository-inventory, dashboard, handoff-term and aggregation-manifest validation paths.

Eliminated as redundant standalone entrypoints:

```text
.github/workflows/org-allocator.yml
.github/workflows/org-continuation-check.yml
.github/workflows/org-aggregation-check.yml
```

Commits:

```text
6703611f3181694667996b5a7ac5a25646887531  consolidate checks into org-control-plane-validate
b14dfa8f3fa92c7460e1f9e4afa7bd2e2f175eab  remove org-allocator workflow
9cee37ec5eb1a21245525004b37113d25b17c13b  remove org-continuation workflow
f00f8cb42bd9aad40ad650ec9d7e65e13b49239a  remove org-aggregation workflow
c13e63e91f9752b970516325cdf2612636099c4c  persist first classification record
```

No GitHub/provider/wallet/NON-TV/TVC secret or token path was introduced.

## Validation

Direct workflow inventory after cleanup reports `17` active workflows, down from `20`.

Hosted run `31917615187` executed the retained workflow at commit `6703611f...` but failed before the new consolidated checks ran. Exact failure:

```text
TASK-2026-0004: unknown flags: ['fail-closed-claim-gate', 'no-render', 'phone-sovereign', 'trade-readiness', 'tv-tvc-only']
```

The failing source is `tasks/TASK-2026-0004.json`; `scripts/validate_org_control_plane.py` admits only the control flags `blocked`, `suspended`, `superseded`, and `reconciliation_required`.

That task belongs to the separate wallet/trade workstream. This hygiene session will not repair or reinterpret its product semantics. The mismatch is recorded as a hosted-validation blocker; it is not counted as evidence that the new consolidated checks passed or failed.

## Branch classification batch 1

Persisted in `control/repository-hygiene-wave0-classification.json`.

- `feat/sovereign-runtime-self-bootstrap-002`: `MERGED_DELETE_CANDIDATE`; compare to main is `behind`, `ahead_by=0`, `behind_by=164`. No unique commit remains off main. Final deletion still requires evidence-reference/ownership clearance.
- `feat/sovereign-runtime-self-bootstrap-001`: `REVIEW_REQUIRED`; diverged, `ahead_by=5`, `behind_by=174`.
- `feat/sovereign-heartbeat-host`: `REVIEW_REQUIRED`; diverged, `ahead_by=6`, `behind_by=894`.
- `feat/sovereign-heartbeat-host-v2`: `REVIEW_REQUIRED`; diverged, `ahead_by=3`, `behind_by=880`.

No branch is deleted from naming alone.

## Current claims and collision boundaries

The hygiene claim owns only repository lifecycle classification, safe workflow consolidation, stale issue/PR reconciliation, and evidence-preserving cleanup. It does not own product implementation, wallet/trade tasks, heartbeat runtime activation, TV/TVC authority, Site product work, StegCore product work, or active worker claims.

## Current next executable actions

1. Classify the remaining 69 `.github` branches against main, PR history, current handoffs/task registries, worker ownership, and evidence references.
2. Classify the remaining 16 `.github` workflows into `KEEP_STANDALONE_EXCEPTION`, `CONSOLIDATE_INTO_STABLE_DISPATCHER`, `TRANSFER_TO_STEGVERSE_WORKER`, or `ELIMINATE`.
3. Continue Wave-0 classification in `repo-standards` and `Continuity`, respecting their canonical handoffs before mutation.
4. Close/supersede stale `.github` issues only when live state proves terminality.
5. Do not resume Site/StegCore sink cleanup until Waves 0-3 establish causal cleanliness.

## Blockers

- Hosted validation of batch 1 is blocked by the unrelated `TASK-2026-0004` flag/schema mismatch before consolidated checks execute.
- Destructive branch cleanup remains fail-closed until each candidate is proven terminal/unowned and no canonical evidence reference requires the ref.

## Machine-owned / authority-owned work

Existing product/runtime workers remain authoritative for their scopes. Hygiene may observe those records to determine retention but must not mutate their execution authority. TV/TVC remains sole credential authority.

## Session-consolidation state

```text
strategy_transfer: COMPLETE
root_handoff_created: COMPLETE
wave0_baseline: COMPLETE (3/3 repositories)
root_workflow_cleanup_batch_1: COMPLETE (20 -> 17)
root_branch_classification: PARTIAL (4/73)
root_workflow_classification: PARTIAL (4/20 original surfaces; 3 eliminated, 1 retained)
root_pr_classification: COMPLETE (0 open)
root_issue_classification: NOT_STARTED
repo-standards classification: BASELINED_NOT_CLEANED
Continuity classification: BASELINED_NOT_CLEANED
wave1: NOT_STARTED
wave2: NOT_STARTED
wave3: NOT_STARTED
wave4 Site/StegCore: DEFERRED_UNTIL_UPSTREAM_CAUSAL_AUDIT
```

## Completion accounting

```text
task completion: 3/10 = 30%
developed control surfaces: 2/2 = 100%
validation: 2/5 = 40%
integration: 2/5 = 40%
propagation: 1/5 = 20%
goal activation: 30%
session consolidation: 1/1 = 100%
```

Archive condition: do not archive while this session still owns the active Wave-0 classification/cleanup claim. Release only after current unique cleanup work is completed or durably transferred to repository-native owners with exact next actions and evidence.
