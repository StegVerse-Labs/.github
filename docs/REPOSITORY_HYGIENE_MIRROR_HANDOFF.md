# Repository Hygiene Mirror Handoff

Updated: 2026-08-15T19:30:00-05:00

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
claim_release_condition: causal-root baseline and first-wave root repository classifications are committed, issue #165 is updated to the new ordering, and all remaining cleanup is assigned to durable repo-native owners
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
render_production_runtime: prohibited
```

## Governing strategy

The cleanup order is changed from "worst repositories first" to **causal roots -> shared infrastructure -> low-complexity leaves -> medium-complexity consumers -> high-complexity sinks (Site and StegCore)**.

The purpose is not cosmetic count reduction. The purpose is to prove that upstream repositories and control surfaces do not continually create branch, PR, issue, workflow, claim, and session-state debt in downstream repositories.

A downstream cleanup is not considered durable until its upstream dependency producers satisfy the hygiene invariants below.

## Hygiene invariants

A healthy repository should converge toward all of the following unless an explicit exception is recorded:

1. one canonical mirror handoff per active capability/workstream, with supersession links rather than parallel competing handoffs;
2. bounded, expiring task/implementation claims with terminal release evidence;
3. no branch-per-session or branch-per-observer pattern when repository-native task/worker state can carry continuation;
4. no duplicate branch families pointing to the same terminal commit without an evidence-retention reason;
5. completed/merged/superseded branches are deletion candidates after evidence and ownership references are verified;
6. no stale open PR whose work is already merged, superseded, abandoned, or transferred;
7. no stale issue whose completion state disagrees with current task receipts/handoffs;
8. GitHub workflows are repository validation/coordination only, not production continuity;
9. stable workflow entry surfaces are preferred over one-workflow-per-capability; >2 requires a documented technical exception;
10. recurring operational work belongs to StegVerse-controlled resident workers when technically appropriate;
11. TV/TVC remains the only credential/secret/token authority; repository hygiene must introduce no NON-TV/TVC runtime credential path;
12. Site and StegCore are treated as downstream sinks until upstream debt generators are proven clean.

## Causal cleanup order

### Wave 0 — organization/control roots

- `StegVerse-Labs/.github`
- `StegVerse-Labs/repo-standards`
- `StegVerse-Labs/Continuity` ownership/handoff standards and registries

Purpose: prove that organization policy, worker/task coordination, handoff conventions, and automation patterns do not generate hygiene debt downstream.

### Wave 1 — shared infrastructure / authority producers

- `StegVerse-Labs/TV`
- `StegVerse-Labs/TVC`
- `StegVerse-Labs/StegID`
- `StegVerse-002/micro-node-runtime`
- `StegVerse-org/LLM-adapter`
- `master-records/orchestration`
- other shared SDK/runtime repositories discovered from live dependency contracts

### Wave 2 — low-complexity leaves

Repositories with low branch/PR/issue/workflow counts are audited and brought to the invariants first. These become reference examples for healthy StegVerse repository lifecycle behavior.

### Wave 3 — medium-complexity consumers

Repositories that consume the shared infrastructure but are not ecosystem-wide sinks.

### Wave 4 — high-complexity sinks

- `StegVerse-Labs/Site`
- `StegVerse-Labs/StegCore`

Only after Waves 0-3 are measured and remediated should the largest sink cleanup be considered causally complete.

## First live baseline — StegVerse-Labs/.github

Direct GitHub observations at claim creation:

```text
branch_count: 73
open_pr_count: 0
open_issue_count_observed: 17
active_workflow_count: 20
main_branch_present: true
```

Notable branch-family debt visible in the root control repository includes repeated variants such as:

- `feat/fail-closed-resolution-task-escalation` + `-v2`;
- `feat/master-records-same-carrier-reconstruction-20260810` + `-v2-20260810`;
- `feat/sovereign-heartbeat-host` + `-v2`;
- `feat/sovereign-runtime-self-bootstrap-001` + `-002`;
- `feat/sovereign-stegfin-post-bootstrap-001`, `-v2`, `-v3`;
- `fix/stegfin-post-bootstrap-provenance-172` + `-v2`;
- `reconcile/ae-retrospective-127` + `-v2`;
- `reconcile/heartbeat-carrier-contract-120-v2`.

These are **candidates**, not deletion authorization. Each must be reconciled against merge history, open/closed PRs, current handoffs, task registries, worker ownership, and evidence references before removal.

The root repo itself therefore already violates the desired low-debt posture. This validates the causal-root-first strategy: Site/StegCore are not the only repositories accumulating branch/workstream residue.

## Required execution inventory

For every repository audited, persist:

```text
repository
wave
branch_count
open_pr_count
open_issue_count
workflow_count
canonical_handoff(s)
active_claims
machine_owned_branches
protected_or_release_branches
merged_branch_candidates
superseded_branch_candidates
duplicate_branch_families
stale_pr_candidates
stale_issue_candidates
workflow_consolidation_candidates
upstream_debt_generated
upstream_debt_received
cleanup_actions_applied
validation_evidence
remaining_blockers
next_owner
```

## Completion states

- `COMPLETE_CLEAN`: invariants satisfied and evidence retained.
- `COMPLETE_WITH_EXCEPTIONS`: remaining debt has explicit technical/evidence justification.
- `CLEANUP_READY`: candidates classified and safe mutations identified.
- `BLOCKED_ACTIVE_OWNERSHIP`: cleanup would collide with active worker/task ownership.
- `BLOCKED_EVIDENCE_REFERENCE`: branch/PR/issue still referenced by canonical evidence.
- `REVIEW_REQUIRED`: ambiguity remains after repository-state inspection.
- `FAILED`: hygiene mutation broke validation or authority boundaries.

## Current next executable actions

1. Update `.github#165` to make causal-root-first ordering canonical.
2. Build a machine-readable Wave-0 baseline for `.github`, `repo-standards`, and `Continuity`.
3. Classify `.github` branch families against merge/PR/task/handoff state before deleting anything.
4. Inspect the 20 `.github` workflows against #167's 0/1/2 stable-surface policy.
5. Close or supersede stale `.github` issues only when current handoffs/task records prove terminality.
6. Proceed to `repo-standards` and `Continuity` before touching Site/StegCore cleanup again.

## Blockers

None for audit/classification. Destructive cleanup remains fail-closed until each candidate is proven unowned or terminal and no evidence/reference requirement depends on it.

## Session-consolidation state

```text
strategy_transfer: COMPLETE
root_handoff_created: COMPLETE
wave0_baseline: PARTIAL (1/3 repositories)
root_branch_classification: NOT_STARTED
root_workflow_classification: NOT_STARTED
root_pr_classification: COMPLETE (0 open)
root_issue_classification: NOT_STARTED
wave1: NOT_STARTED
wave2: NOT_STARTED
wave3: NOT_STARTED
wave4 Site/StegCore: DEFERRED_UNTIL_UPSTREAM_CAUSAL_AUDIT
```

## Completion accounting

```text
developed control surfaces: 1/2
validation: 1/5
integration: 1/5
goal activation: 10%
```

Archive condition for this hygiene session: the causal-order strategy and all unique cleanup requirements are durably transferred to repository-native owners with no active session-only claim. This handoff does not claim organization-wide hygiene is complete.
