# Repository Hygiene Mirror Handoff

Updated: 2026-08-15T19:52:00-05:00

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

Canonical order is causal roots -> shared authority/runtime producers -> low-complexity leaves -> medium consumers -> high-complexity sinks. Site and StegCore remain terminal Wave-4 sinks; destructive sink cleanup is deferred until upstream debt generation is measured and remediated.

## Hygiene invariants

Healthy repositories converge toward canonical handoffs with explicit supersession, bounded expiring claims, no session/observer branch proliferation when durable task state suffices, evidence-cleared branch retirement, no stale PR/issue disagreement with canonical state, GitHub Actions limited to validation/coordination, 0/1/2 stable repo-authored workflow surfaces where sufficient, StegVerse-owned recurring production execution, and TV/TVC-only credential authority.

## Durable control surfaces

```text
docs/REPOSITORY_HYGIENE_MIRROR_HANDOFF.md
control/repository-hygiene-wave0-baseline.json
control/repository-hygiene-wave0-classification.json
control/workflow-surface-registry.json
scripts/validate_workflow_surface_hygiene.py
.github/workflows/org-control-plane-validate.yml
StegVerse-Labs/.github#165
StegVerse-Labs/.github#167
StegVerse-Labs/.github#168
```

## Wave-0 state

### StegVerse-Labs/.github

- branches: 73 at baseline;
- open PRs: 0 at baseline;
- open issues observed: 17;
- original repo-authored workflow files: 20;
- first hygiene batch removed 3 redundant standalone organization validators;
- subsequent direct file reconciliation found additional workflows removed by other canonical workstreams and two fresh concurrent workflow additions;
- current registered repo-authored workflow files: 15;
- state: `ROOT_DEBT_PRESENT_ACTIVE_CLEANUP`.

The root repository itself is therefore a proven debt generator/sink and requires a prevention mechanism, not only deletion.

### StegVerse-Labs/repo-standards

- branches: 16;
- open PRs: 2;
- open issues: 4;
- repository-authored YAML workflows: 4 -> 2 (`bootstrap.yml`, `declared-tasks.yml`);
- GitHub additionally reports one platform-managed dynamic security workflow;
- inactive ST-018 template workflows were removed because their own headers assigned execution/validation to `declared-tasks.yml`;
- state: `WORKFLOW_TARGET_MET_BRANCH_PR_ISSUE_RECONCILIATION_PENDING`.

### StegVerse-Labs/Continuity

- branches: 5;
- open PRs: 0;
- open issues: 1;
- workflows: 9 -> 2;
- retained: `continuity.yml` compatibility marker + consolidated `validate-continuity.yml`;
- removed legacy PAT/token dispatch and GitHub-hosted self-mutation workflows;
- consolidated readiness, recreation/recovery, release verification and StegGate decision-state validation;
- validation run `31917953856`: SUCCESS at source commit `e830429e24ed757075bd9fd172515c00d180697b`;
- current canonical handoff validation run `31918052502`: SUCCESS at `a1aab928cd1ea967b40109af59460e64e4184d6d`;
- state: `WORKFLOW_TARGET_MET_VALIDATED_BRANCH_EVIDENCE_RECONCILIATION_PENDING`.

## Root workflow debt-regeneration guard

During the hygiene window, direct state showed that workflow counts are not static: `mcp-activation-binding-test.yml` and `stegfin-early-adopter-contribution-validator-source.yml` appeared as fresh concurrent surfaces, while four other specialized workflow files disappeared under separate canonical workstreams. This proves that one-time count reduction cannot make the root healthy.

Installed prevention controls:

```text
control/workflow-surface-registry.json
scripts/validate_workflow_surface_hygiene.py
.github/workflows/org-control-plane-validate.yml -> Fail closed on unregistered workflow proliferation
```

The registry requires every current repository-authored workflow to have a path, owner, reason and hygiene classification. New unregistered workflow files fail closed. Registration is classification evidence only and does not authorize permanent retention.

Commits:

```text
9ac5c05ca4875171f5612e6354a81cd8107cf638  initial registry
b96756cec4400954ab8c169c027b3a0b734e38ea  fail-closed validator
b44e40f79ac9bdb4e50b23493626b96bfb83cc69  bind guard into stable org validator and all workflow path changes
0b0df75ff6434d62c6b51a1f51bffd2528e9e750  reconcile registry to exact live files
```

Hosted run `31918210805` proves the new hygiene guard itself PASSes against the exact live root workflow files. The subsequent pre-existing `validate_org_control_plane.py` step still fails on separate wallet/trade `TASK-2026-0004` descriptive flags; that task belongs to another session and is not modified here. Therefore the hygiene guard is validated, while the entire aggregate organization workflow is not reported as passed.

## Root workflow classifications

Current registry has 15 exact live repo-authored surfaces:
- `org-control-plane-validate.yml`: `KEEP_STABLE_DISPATCHER`;
- fresh MCP and StegFin early-adopter surfaces: `BLOCKED_ACTIVE_OWNERSHIP`, retained pending their separate active owners;
- remaining heartbeat/runtime/archive/handoff/StegGate validation surfaces: `REVIEW_REQUIRED` pending exact owner/contract reconciliation.

Removed by this hygiene lane:

```text
org-allocator.yml
org-continuation-check.yml
org-aggregation-check.yml
```

Observed removed by other workstreams during the same window:

```text
sovereign-stegfin-post-bootstrap.yml
stegfin-continuity-machine-executor.yml
tvc-github-broker-crossrepo-validation.yml
validate-ae-handoff-worker-conformance.yml
```

This concurrent movement is now machine-observable rather than silently changing the denominator.

## Branch classification

`.github` batch 1:
- `feat/sovereign-runtime-self-bootstrap-002`: `MERGED_DELETE_CANDIDATE`, ahead=0; deletion still needs evidence-reference clearance;
- `feat/sovereign-runtime-self-bootstrap-001`: `REVIEW_REQUIRED`;
- `feat/sovereign-heartbeat-host`: `REVIEW_REQUIRED`;
- `feat/sovereign-heartbeat-host-v2`: `REVIEW_REQUIRED`.

Continuity:
- `feat/handoff-execution-ownership-v1`: `MERGED_DELETE_CANDIDATE`, ahead=0;
- build/release/verify 109%-continuity branches: retained/review-required until release-evidence lineage is reconciled.

No branch is deleted by naming inference.

## Current claims and collision boundaries

The hygiene claim owns repository lifecycle classification, safe workflow consolidation, stale PR/issue reconciliation, evidence-preserving cleanup and debt-prevention controls. It does not own wallet/trade implementation, heartbeat product activation, TV/TVC authority, Site/StegCore product work, or fresh worker-owned MCP/StegFin workflows.

## Exact next tasks

1. Reconcile the 14 non-dispatcher `.github` workflow files against their active handoffs/owners and classify each terminally as standalone exception, consolidate, worker-transfer or eliminate.
2. Classify remaining `.github` branches and 17 open issues against current task/worker/evidence state.
3. Reconcile repo-standards PR #36/#40, 15 non-main branches and four issues without colliding with #37/#39 owners.
4. Reconcile Continuity release/evidence branches; its workflow-surface hygiene is complete.
5. Advance to Wave 1 only after Wave-0 control generators are either clean or explicitly exception-bound.
6. Keep Site/StegCore cleanup deferred until upstream causal lanes no longer silently regenerate debt.

## Blockers

- `.github` aggregate validation beyond the new hygiene guard remains blocked by unrelated wallet/trade `TASK-2026-0004` flag/schema mismatch; this hygiene lane will not mutate that separate product task.
- Branch ref removal remains fail-closed pending evidence/owner clearance; current connector authority also does not expose a branch-delete operation, so safe delete candidates must remain classified until a canonical repository-native deletion lane performs ref retirement.

## Session-consolidation state

```text
strategy_transfer: COMPLETE
root_handoff: COMPLETE
wave0_baseline: COMPLETE
root_debt_regeneration_guard: COMPLETE_VALIDATED
.github workflow terminal classification: PARTIAL (1 stable dispatcher; 14 unresolved/active-owner)
.github branch classification: PARTIAL
.github issue classification: NOT_STARTED
repo-standards workflow target: COMPLETE
repo-standards lifecycle classification: PARTIAL
Continuity workflow target: COMPLETE_VALIDATED
Continuity branch/evidence classification: PARTIAL
wave1: NOT_STARTED
wave2: NOT_STARTED
wave3: NOT_STARTED
wave4 Site/StegCore: DEFERRED
```

## Completion accounting

```text
task completion: 5/10 = 50%
developed hygiene control surfaces: 4/4 = 100%
validation: 3/5 = 60%
integration: 3/5 = 60%
propagation: 2/5 = 40%
goal activation: 50%
session consolidation: 1/1 = 100%
```

Archive condition: do not archive while this session retains the active Wave-0 root classification/cleanup claim. Release only after unique cleanup work is completed or durably transferred with exact owners, evidence and machine-observable release conditions.
