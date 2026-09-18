# Repository Hygiene Mirror Handoff

Updated: 2026-09-17T22:52:45Z

## Active goal

```text
goal_id: HYGIENE-CAUSAL-ROOTS-001
originating_goal: clean the StegVerse ecosystem from causal roots outward so downstream repositories are not repeatedly re-contaminated by upstream branch/workflow/issue/task-generation patterns
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#165
workflow_minimization_issues: StegVerse-Labs/.github#167 and #168
canonical_owner: StegVerse-Labs organization hygiene control plane
session_claim_state: RELEASED_TO_CANONICAL_CONTROL_PLANE
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
render_production_runtime: prohibited
```

The prior chat-scoped Wave-0 claim is released. Remaining hygiene work is durably owned by the canonical issues and fail-closed workflow registry; this session must not remain open merely to preserve that work.

## Governing strategy

Causal order remains: organization/control roots -> shared authority/runtime producers -> low-complexity leaves -> medium consumers -> Site/StegCore terminal sinks. Sink cleanup must not be treated as causal completion while upstream generators remain unresolved.

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

## Completed hygiene work

- `.github` organization validation surfaces were consolidated and redundant `org-allocator.yml`, `org-continuation-check.yml`, and `org-aggregation-check.yml` were removed.
- `repo-standards` repository-authored workflow surface was reduced to `bootstrap.yml` plus `declared-tasks.yml`; GitHub's dynamic security workflow is a platform-managed exception.
- Continuity workflow surface was reduced 9 -> 2: compatibility marker plus consolidated validator.
- Continuity consolidated validation has direct SUCCESS evidence, including run `31918052502` after canonical handoff reconciliation.
- The root workflow debt-regeneration guard is installed: every repo-authored `.github/workflows/*` file must be registered in `control/workflow-surface-registry.json`; unregistered additions fail closed.
- Hosted run `31918210805` proved the workflow-surface guard itself passes against exact live root files.
- Organization task files `TASK-2026-0004` and `TASK-2026-0005` were subsequently normalized to the v0.2 task state/flag vocabulary, removing the earlier task-schema blocker from `validate_org_control_plane.py`.

## Remaining hygiene inventory

Exact continuation is carried by issues #165/#167/#168 and the registry. Remaining work includes:

1. Terminally classify the 14 non-dispatcher root workflow surfaces as standalone exception, consolidation target, worker-transfer, eliminate, or active-owner blocked.
2. Reconcile remaining `.github` branches and open issues against canonical worker/task/evidence state.
3. Reconcile `repo-standards` PR #36/#40, non-main branches and open issues without competing with #37/#39 ownership.
4. Reconcile Continuity build/release/verify branches against release-evidence lineage; workflow hygiene there is already complete.
5. Advance to Wave 1 only after Wave-0 generators are clean or explicitly exception-bound.
6. Keep Site/StegCore destructive sink cleanup deferred until upstream causal ownership is reconciled.

No branch is deleted by age or naming inference. No active product/runtime work is claimed by the hygiene lane.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HYGIENE-CAUSAL-ROOTS-VALIDATION
  execution_owner: bounded future hygiene validation session only when explicitly claimed through issue #165
  claim_state: UNCLAIMED
  worker_registry_ref: StegVerse-Labs/.github#165
  manual_execution_allowed: true
  collision_scope: repository lifecycle classification and evidence reconciliation only; excludes product implementation, heartbeat activation, TV/TVC authority, wallet/trade, Site product and StegCore product scopes
  release_condition: validation mutation is durably recorded in issue #165 and this handoff, then claim released
  next_executable_action: claim one nonconflicting classification batch from issue #165 when execution capacity exists
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HYGIENE-WORKFLOW-PROLIFERATION-GUARD
  execution_owner: StegVerse-Labs organization control plane validator
  claim_state: MACHINE_OWNED_ACTIVE
  worker_registry_ref: control/workflow-surface-registry.json + scripts/validate_workflow_surface_hygiene.py + .github/workflows/org-control-plane-validate.yml
  manual_execution_allowed: false
  collision_scope: detect unregistered root workflow files and fail closed; registration does not authorize retention
  release_condition: every live workflow remains registered and unresolved classifications reach terminal owner-approved states
  next_executable_action: automatically validate every root workflow file change through the stable organization validator
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: HYGIENE-BRANCH-REF-RETIREMENT
  execution_owner: repository administration / canonical repository-native ref-retirement authority
  claim_state: AUTHORITY_OWNED_FAIL_CLOSED
  worker_registry_ref: StegVerse-Labs/.github#165
  manual_execution_allowed: false
  collision_scope: actual branch ref deletion after evidence/ownership clearance
  release_condition: candidate is terminal, unowned, evidence-safe and deletion authority is available
  next_executable_action: retire only evidence-cleared refs; otherwise retain classification
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: HYGIENE-CONTINUITY-WORKFLOW-REDUCTION
  execution_owner: StegVerse-Labs/Continuity
  claim_state: COMPLETE_VALIDATED
  worker_registry_ref: NONE_COMPLETE
  manual_execution_allowed: false
  collision_scope: Continuity workflow surface 9 -> 2
  release_condition: SATISFIED
  next_executable_action: NONE_WORKFLOW_SURFACE
- task_id: HYGIENE-REPO-STANDARDS-WORKFLOW-REDUCTION
  execution_owner: StegVerse-Labs/repo-standards
  claim_state: COMPLETE
  worker_registry_ref: NONE_COMPLETE
  manual_execution_allowed: false
  collision_scope: repository-authored workflow surface reduced to bootstrap + declared-tasks
  release_condition: SATISFIED
  next_executable_action: lifecycle reconciliation remains separate under canonical issues
```

## Session-consolidation state

```text
strategy_transfer: COMPLETE
root_handoff: COMPLETE
wave0_baseline: COMPLETE
root_debt_regeneration_guard: COMPLETE_VALIDATED
workflow terminal classification: PARTIAL / TRANSFERRED
branch classification: PARTIAL / TRANSFERRED
issue reconciliation: PENDING / TRANSFERRED
repo-standards workflow target: COMPLETE
Continuity workflow target: COMPLETE_VALIDATED
current chat hygiene claim: RELEASED
canonical continuation: .github#165/#167/#168 + registry
```

## Completion accounting

```text
hygiene task completion: 5/10 = 50%
developed hygiene control surfaces: 4/4 = 100%
validation: 3/5 = 60%
integration: 3/5 = 60%
propagation: 2/5 = 40%
goal activation: 50%
session-specific hygiene transfer: 100%
```

The hygiene goal itself is not complete, but this session no longer owns its continuation. Deleting the chat does not remove the inventory, prevention guard, owner, release conditions or next executable actions.


## 2026-08-28 bounded Wave-0 G18 branch classification

Issue #165 claim comment: 5459755905.

StegHealth issue #38 supplied deterministic per-branch evidence under the merged branch-health classifier. The following root branches are now classified as evidence-cleared ref-retirement candidates while actual deletion remains owned by HYGIENE-BRANCH-REF-RETIREMENT:

- `fix/g18-resolution-bootstrap-missing-resident-20260827`
- `chore/g18-handoff-postmerge-reconcile`
- `chore/g18-v13-postmerge-reconcile`
- `chore/g18-resolution-postmerge-reconcile`

Evidence source:
- StegVerse-Labs/StegHealth PR #45 merge `be448d5ea9f47b98576de39c4f5b159fad887cb4`
- exact-head signal validation `33228554588 SUCCESS`
- `evidence/operations/2026-08-28-g18-safe-delete-observation.json`
- `evidence/operations/2026-08-28-g18-safe-delete-classification.json`

Each candidate has completed merge/open-work/source-reference/protection checks. The first candidate is squash-merge divergent by ancestry but all compare-reported changed files are byte-identical to current main; the other three are ahead 0. None is protected. No branch ref deletion has been performed.

This advances Wave-0 classification only. It does not alter G18 runtime authority, active fence18 state, HeartBeat, or any product/runtime claim.

## 2026-08-28 bounded Wave-0 G18 branch classification — batch 3

Issue #165 claim comment: 5460279974.

StegHealth issue #38 and merged PR #46 supplied deterministic evidence for five additional behind-only G18 branches. Current `.github/main` was refreshed after the StegHealth observation; all five remain ahead 0, unprotected, and have zero current exact branch-name source references.

The following refs are now classified as `EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE` while actual ref retirement remains owned by `HYGIENE-BRANCH-REF-RETIREMENT`:

- `fix/g18-resident-request-resolution-worker`
- `fix/g18-self-bootstrap-no-predeclared-node`
- `fix/g18-v13-runtime-execution`
- `fix/g18-v13-sovereign-node-resolution`
- `fix/hb29-g18-bootstrap-220`

Evidence source:
- StegVerse-Labs/StegHealth PR #46 merge `4f21a7fa4b0408769fb2bc2ee8f0164f82f64233`
- exact-head signal validation `33233331274 SUCCESS`
- `evidence/operations/2026-08-28-g18-safe-delete-observation-batch2.json`
- `evidence/operations/2026-08-28-g18-safe-delete-classification-batch2.json`

Current `.github/main` recheck shows the five refs behind by 79, 1410, 127, 142, and 951 commits respectively, with `ahead_by=0`. No branch ref mutation has been performed. This advances Wave-0 classification only and does not alter G18 runtime authority, HeartBeat, or sovereign activation state.

### Wave-0 G18 batch 3 merge/validation — 2026-08-28

PR #394 merged the five-ref batch as `05599436d7f24833297229d400ae58533fcb9b90`.

Validated exact PR head:
`2758cf124ed039fea89c8cd28443de5063239dc2`

Validation:
- Heartbeat Worker Project run `33233465931 SUCCESS`
- organization control plane run `33233466004 SUCCESS`

Nine G18 refs are now durably evidence-cleared across Wave-0 batches 2 and 3. `HYGIENE-BRANCH-REF-RETIREMENT` remains authority-owned/fail-closed; this merge does not perform or authorize repository-ref changes. G18 resident consumption and sovereign runtime activation remain separately unobserved.

## 2026-08-28 bounded Wave-0 G18 review classification batch

Issue #165 claim comment: 5460310556.

Merged StegHealth PR #47 supplies deterministic content-equivalence evidence for the three remaining branches in the original G18 sample. Each retains content different from current `.github/main`, so Wave-0 records all three as `REVIEW_REQUIRED`:

- `chore/g18-v13-control-plane-reconcile-20260827` — ahead 3 / behind 129.
- `chore/g18-v13-control-plane-reconcile-v2-20260827` — ahead 3 / behind 125.
- `feat/g18-resident-execution-request-20260827` — ahead 6 / behind 102.

Evidence source:
- StegVerse-Labs/StegHealth PR #47 merge `c545fd5c7a6da2e994d6689beb940210a6f4ea13`
- exact-head signal validation `33233611462 SUCCESS`
- `evidence/operations/2026-08-28-g18-authority-risk-classification-batch3.json`

The original 12-branch G18 hygiene sample is now explicit: nine evidence-cleared candidates and three review-required branches. G18 resident execution and activation remain separate and unobserved.



## 2026-08-30 Wave-0 repo-standards and Continuity reconciliation

### repo-standards lifecycle classification

Current `StegVerse-Labs/repo-standards/REPO_STANDARDS_MIRROR_HANDOFF.md` was read before classification.

```text
PR #36 / issue #35: ACTIVE_OWNER_RETAIN / DRAFT_INTEGRATION_TRANSFER
PR #40 / issue #39: ACTIVE_OWNER_RETAIN / PRODUCT_STANDARD_ISSUE_39
issue #37: CLOSED_COMPLETE / no longer owns active PR scope
```

Neither open PR is a hygiene close/merge target. PR #36 preserves unresolved ST-020 canonical adoption/numbering work; PR #40 remains an active standards change owned by issue #39. Hygiene must not steal those scopes.

### Continuity branch classification

Current `StegVerse-Labs/Continuity/docs/CONTINUITY_MIRROR_HANDOFF.md` and release-verification issue #3 were read before branch classification.

```text
feat/handoff-execution-ownership-v1:
  compare: ahead 0 / behind 30 / no file diff
  classification: EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE

st019/universal-pr-validation-8:
  compare: identical to current main
  classification: ISSUE_8_ACTIVE / NOT RETIREMENT-CLOSED BY IDENTITY ALONE

build/109-percent-recreatable-continuity:
  ahead 26 / behind 56
  classification: ACTIVE_RELEASE_EVIDENCE_LINEAGE_REVIEW

release/109-percent-verification:
  ahead 5 / behind 55
  classification: ACTIVE_RELEASE_EVIDENCE_LINEAGE_REVIEW

verify/109-percent-successor-block-receipt:
  ahead 2 / behind 54
  classification: ACTIVE_RELEASE_EVIDENCE_LINEAGE_REVIEW
```

Continuity issue #3 remains open and explicitly owns the 109-percent destination/release verification chain, so the three ahead/diverged release branches are retained pending lineage reconciliation.

### ST-019 universal-check blocker discovered

A fresh issue-#8 implementation attempt removed the `pull_request.paths` filter and caused the universal check to run, but exact hosted validation failed before source checkout:

```text
Continuity PR: #9 CLOSED_UNMERGED
run: 33296567452 FAILURE
job: 99217144193 FAILURE
failure: anonymous fetch of private Continuity repository requires authentication
GitHub credential workaround introduced: false
```

Because the repository is private and the canonical workflow intentionally forbids GitHub credentials, simply removing the path filter would make `validate` universally fail. The PR was therefore closed unmerged. Repo-standards issue #50 was notified that Continuity's earlier `validate + repo-smoke` required-check warrant must fail closed or be refreshed after a sovereign/TV-TVC-governed universal status-publication path exists.

No branch ref deletion, product implementation merge, protection mutation, credential mutation, runtime activation, or release decision was performed by this hygiene batch.


## 2026-08-30 Continuity release-lineage branch closure classification

Continuity release-verification issue #3 is now `CLOSED_COMPLETE`; successor BLOCK receipt v2 merged as `687e7c3b123a6761fb8bec8373a2536e60048a07`. The release itself remains `BLOCK`.

Content-equivalence/replacement checks support the following branch-ref classifications:

```text
build/109-percent-recreatable-continuity
  canonical protocol blob: byte-identical to main
  recreate_state.py blob: byte-identical to main
  recreation-receipt schema blob: byte-identical to main
  historical standalone validation workflow: superseded by consolidated current workflow surface
  classification: EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE

release/109-percent-verification
  release-verification schema: byte-identical to main
  semantic validator: byte-identical to main
  intake receipt: byte-identical to main
  handoff: older than current main
  historical standalone validation workflow: superseded by consolidated current workflow surface
  classification: EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE

verify/109-percent-successor-block-receipt
  prior BLOCK receipt/handoff: superseded by successor BLOCK v2 on main
  classification: EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE

feat/handoff-execution-ownership-v1
  ahead 0 / no file diff
  classification: EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE

st019/universal-pr-validation-8
  ref has no unique current content
  issue #8 remains active because the private-repo/no-token hosted source checkout blocker is unresolved
  classification: EVIDENCE_CLEARED_REF_RETIREMENT_CANDIDATE_FOR_REF_ONLY
```

Actual ref deletion remains `HYGIENE-BRANCH-REF-RETIREMENT` authority-owned and was not performed by this batch.


## 2026-09-01 Workspace DEVICE_KV workflow registry repair

The validation-only `.github/workflows/workspace-device-kv-validation.yml` surface is now explicitly registered in `control/workflow-surface-registry.json` as a `KEEP_STANDALONE_EXCEPTION`.

Reason:
- it validates only the bounded Workspace/Personal-KV DEVICE_KV source extension;
- authentic resident DEVICE_KV execution remains prohibited on GitHub Actions;
- registration grants no runtime, credential, KV, or heartbeat authority;
- credential authority remains TV/TVC and non-TV/TVC secret/token allowance remains false.

This repairs the fail-closed workflow-surface hygiene error observed during the SV002 pre-T0 review without weakening the proliferation guard.


## 2026-09-17 canonical Task Registry continuity repair

The hygiene goal predates the canonical Task Registry bootstrap on 2026-09-04. Direct history inspection found no removal event: `HYGIENE-CAUSAL-ROOTS-001` was never migrated into `data/canonical-task-registry.json`, even though this handoff and issue #165 continued to state that hygiene work was transferred to the organization control plane.

The bounded repair registers the existing goal as `PROPOSED` / `ECOSYSTEM_RECONCILIATION` source state, with WorkerCoordinator claim/fence authority still unminted and Interlock/InTr admission still required. It also emits the non-authorizing `task.v1` COSV pointer `10100000100000` and indexes it in `control/task-vector-index.json`.

This repair restores discoverability only. It does **not** authorize chat-driven Site/StegCore issue closure, branch deletion, runtime execution, provider action, or any bypass of the existing causal-root-first policy. Downstream repository mutation remains gated by canonical ownership, current evidence, WorkerCoordinator claim/fence, and applicable repository-native authority.

Current continuity state:

```text
canonical task registration: PROPOSED_SOURCE_STATE_RESTORED
work priority class: ECOSYSTEM_RECONCILIATION
COSV task.v1: 10100000100000
worker claim/fence: NOT OBSERVED / WORKERCOORDINATOR ONLY
Interlock/InTr admission: NOT CLAIMED
Master Records reconciliation: NOT CLAIMED
Site/StegCore direct chat cleanup authority: NONE
```


## 2026-09-17 autonomous root-Goal selection defect repair

After the Task Registry continuity repair, `HYGIENE-CAUSAL-ROOTS-001` was still not selectable by the existing resident Canonical Work cycle. The first concrete divergence was in `scripts/run_task_registry_canonical_work_cycle.py`: `progression_context()` treated the autonomous-progression controller's own `root_correlation_id` (`STEGVERSE-CANONICAL-WORK-COORDINATION-001`) as the current root Goal Task. The later `load_candidates(..., goal_task_id=...)` filter therefore discarded every valid task rooted elsewhere before repair-priority ordering or collision check-in could run.

PR `#2077` merged the bounded repair as `32ea0d8feade730604540a54ce322b78c6ab2872` from exact validated head `a3aaf67bcff91734e882fe1706e39affe3312136`. Automatic exact-head PR validation passed in `validate-deepseek-resident` run `35283976786` and `Validate KV AI Memory Resident Binding` run `35283976872`. Organization Control, Heartbeat Worker Project, and Deterministic Repository Suite were not dispatched for this PR and are not claimed as validation evidence. It separates controller lineage from current Goal context, adds `--goal-task-id` to the existing registry selector, threads that same context through the existing `canonical_work_coordination` resident consumer, and keeps all selection/delegation authority boundaries unchanged. This is not a hygiene-specific execution request and creates no second scheduler, dispatcher, WorkerCoordinator, heartbeat, credential path, runtime, or authority plane.

For this goal, the intended existing path is now:

```text
current Goal context = HYGIENE-CAUSAL-ROOTS-001
-> canonical Task Registry row
-> goal-scoped machine-ingress eligibility
-> ECOSYSTEM_RECONCILIATION priority
-> existing Task Registry collision check-in
-> existing Canonical Work bootstrap
-> WorkerCoordinator claim/fence
-> Interlock/InTr admission
-> repository-native bounded hygiene execution
-> Master Records reconciliation
```

A second pre-consumption defect was also found in the stale-resident case. The resident consumer correctly preserves an existing monolithic Task Registry, while generic task-shard materialization does not make shard-only tasks discoverable because both the selector and collision evaluator remain registry-first. Since hygiene was restored to the source monolithic registry but has no canonical source shard, an older resident could still miss it. PR #2077 now reuses the already-existing bootstrap exact-shard projection refresh: for an explicit current Goal, the consumer materializes that exact source registry row as a runtime shard and appends only the missing identity to the preserved resident monolithic registry before selection. Existing resident rows are not replaced, and the projection has `authority_effect=NONE`.

The source repair is merged, but source staging and regression-test coverage do not by themselves prove resident consumption, WorkerCoordinator claim/fence, Interlock/InTr admission, Master Records reconciliation, or any downstream repository mutation. Site/StegCore issue or branch mutation remains explicitly out of scope. The next evidence predicate is an authentic existing resident Canonical Work cycle carrying `--goal-task-id HYGIENE-CAUSAL-ROOTS-001`, with the stale-registry projection receipt when needed, followed by the normal collision/claim/admission chain.


## 2026-09-17 current-Goal dispatcher propagation defect

Post-PR #2077 tracing found the next concrete existing-path divergence before authentic resident consumption. The Canonical Work consumer and registry selector accept `--goal-task-id`, but both existing invocation surfaces above them dropped that value: `scripts/refresh_and_dispatch_resident_requests.py` invoked the resident dispatcher with only the exact consumer selector, and `scripts/dispatch_resident_execution_requests.py` invoked `canonical_work_coordination` with only source/runtime roots. An on-demand portable invocation therefore could not carry `HYGIENE-CAUSAL-ROOTS-001` into the merged root-Goal selection repair.

PR #2081 merged the bounded propagation repair as `26a6ccd166a80f3991499f19c3b41d25ac2104a6` from exact head `291d2d01079405df609fa96bbb408e2be380b6d3`. Goal context is accepted only with exact `canonical_work_coordination` selection, is forwarded bridge -> dispatcher -> existing consumer -> registry-first selector, and is preserved in receipts. Any attempt to attach Goal context to another consumer or a multi-consumer dispatch fails closed before consumer execution. No new request identity, dispatcher, scheduler, runtime, heartbeat, WorkerCoordinator, credential path, transition authority, or Site/StegCore mutation is introduced.

All five automatically dispatched exact-head workflows completed successfully: `Validate KV AI Memory Resident Binding` run `35287938180`, `Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing)` run `35287938197`, `validate-deepseek-resident` run `35287938195`, `SDK WorkSpace External Collaboration Consent Listener Resident Validation` run `35287938217`, and `SDK WorkSpace External Collaboration Reseal Resident Validation` run `35287938203`. The KV validation run explicitly py-compiled both modified scripts. The newly added focused regression file `tests/test_canonical_work_goal_context_dispatch.py` was not among the tests executed by those automatic workflows, so its runtime execution is not claimed.

Source repair and CI do not establish resident consumption, WorkerCoordinator claim/fence, Interlock/InTr admission, Master Records reconciliation, or downstream cleanup. The current Task Registry row therefore remains `PROPOSED / ECOSYSTEM_RECONCILIATION`. No connector-visible resident invocation or retained hygiene runtime receipt was observed in this session. The next authentic predicate remains an on-demand portable `canonical_work_coordination` invocation carrying `--goal-task-id HYGIENE-CAUSAL-ROOTS-001`, followed by retained registry projection/collision/claim/admission evidence.


## 2026-09-17 execution-substrate preflight defect

After the current-Goal propagation repair, the next deterministic existing-path failure occurs inside the already-canonical general Task Registry collision evaluator. `HYGIENE-CAUSAL-ROOTS-001` has `runtime_requirements`, but its restored pre-registry-era row lacked `execution_substrate_resolution`. `scripts/evaluate_task_registry_collision_checkin.py` calls `validate_task_registration_substrate_resolution.validate_resolution()` before collision sorting, so the exact row necessarily returns `STOP_SUBSTRATE_REVIEW_REQUIRED` with `HYGIENE-CAUSAL-ROOTS-001: runtime-capable task registration requires execution_substrate_resolution`. This is before WorkerCoordinator claim/fence or Interlock/InTr admission and is therefore the next proven pre-transition defect.

The bounded repair on `fix/hygiene-substrate-resolution-20260917` adds only the existing canonical six-substrate review to the existing registry identity and, after reconciling the concurrent Master Records update already on main, advances the registry source generation from 25 to 26. It does not select a runtime. The first five same-device/ephemeral candidates remain `PENDING_EVIDENCE / EVIDENCE_REACHABILITY`; `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` is `NOT_APPLICABLE`; `selected_substrate_id=null`; `external_device_required=false`; `second_user_operated_device_allowed=false`; and `authority_effect=NONE`. This preserves the no-second-user-operated-device invariant and does not convert missing connector/runtime reachability into substrate unsuitability.

PR #2085 merged the bounded substrate-registration repair as `6e74d9a419ad26c81be463ad29272c506a4408cd` from exact head `bdceb72ac86cbb5f42075f378fb9a640a41d8358`. The branch was reconciled against concurrent generation-25 Master Records changes before merge; current canonical registry generation is 26. No PR-triggered workflow covers this registry/test change because the broad organization-control and heartbeat suites are workflow-dispatch-only. Exact branch-source validation against the canonical validator contract passed, and regression coverage is retained in `tests/test_repository_hygiene_substrate_resolution.py`; CI execution of that focused test is not claimed.

A source-derived collision projection against the pre-repair generation-25 registry finds four current non-hard repository-overlap candidates:
- `SS-EVIDENCE-COMPARISON-001` — ACTIVE / CLAIMED_INTEGRATION, overlap only `StegVerse-Labs/.github`;
- `AI-GOVERNANCE-OPPORTUNITY-ENGINE-001` — ACTIVE / CLAIMED_INTEGRATION, overlap only `StegVerse-Labs/.github`;
- `STEGVERSE-002-EXPERIMENT-RERUN-001` — ACTIVE / UNCLAIMED, overlap only `StegVerse-Labs/.github`;
- `MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001` — ACTIVE / CHECKED_OUT, repository overlap `StegVerse-Labs/.github` and `StegVerse-Labs/Site`, with no component or lineage overlap.

Under the existing anti-collision evaluator these overlaps are not hard collisions because there is no checked-out component or lineage overlap, but current source semantics would yield `COORDINATE_CONVERGENCE` rather than `CONTINUE`. That is a source-derived preflight expectation only; no authentic resident check-in disposition is claimed. After this registration repair merges, the next authentic evidence remains the exact portable `canonical_work_coordination --goal-task-id HYGIENE-CAUSAL-ROOTS-001` invocation and retained check-in result. If it observes `COORDINATE_CONVERGENCE`, convergence must be reconciled through the returned canonical owners and rechecked; collision policy must not be weakened to force WorkerCoordinator claim/fence.

Post-merge re-observation found no new retained hygiene runtime evidence: the Task Registry remains `PROPOSED / ECOSYSTEM_RECONCILIATION`, `runtime_resolution=null`, and WorkerCoordinator `claim_ref` / `fence_ref` remain null. Searches for the hygiene Goal plus `INGRESS_ADMITTED`, claim/fence, and current-Goal runtime receipts returned only source/preflight/test references, not an authentic resident transition. Therefore WorkerCoordinator claim/fence, Interlock/InTr admission, Master Records reconciliation, and downstream Site/StegCore mutation remain unclaimed.


## 2026-09-17 repository-only convergence reconciliation

Generation 26 source reconciliation confirms the four projected hygiene convergence candidates are repository-only overlaps, not component, lineage, adjacency, or selected-substrate overlaps:

- `SS-EVIDENCE-COMPARISON-001`: shared repository `StegVerse-Labs/.github`; hygiene components and the task's 24 declared components are disjoint.
- `AI-GOVERNANCE-OPPORTUNITY-ENGINE-001`: shared repository `StegVerse-Labs/.github`; hygiene components and the task's four declared components are disjoint.
- `STEGVERSE-002-EXPERIMENT-RERUN-001`: shared repository `StegVerse-Labs/.github`; hygiene components and the task's seven declared components are disjoint.
- `MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001`: shared repositories `StegVerse-Labs/.github` and `StegVerse-Labs/Site`; its three custody components are disjoint from hygiene. The hygiene continuation also already forbids direct Site/StegCore mutation, so the shared Site target is not current mutation authority.

The first newly proven existing-path defect is in the general Task Registry evaluator, not in any of those four task owners: current-record repository overlap was sufficient for `COORDINATE_CONVERGENCE` even when both canonical rows carried explicit, disjoint component scopes. Existing `checkin_context` is additive and therefore could not narrow the candidate's full repository set. This prevented the exact hygiene Canonical Work path from reaching `CONTINUE` despite stronger scope metadata proving separation.

The bounded repair remains inside the existing `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001` mechanism. Repository-only current-record overlap is now nonblocking only when both tasks declare non-empty disjoint component scopes and there is no lineage, adjacency, component, or shared-selected-substrate overlap. The repository overlap remains visible under `repository_only_scope_distinctions` rather than being discarded. Missing component metadata remains fail-closed/conservative, and recent returned/stopped event-history overlap semantics are unchanged.

This repair does not alter the authority or coordination state of any of the four overlapping tasks, does not create another collision engine, runtime, scheduler, dispatcher, WorkerCoordinator, or transition plane, and grants no Site/StegCore mutation authority. Source behavior after the repair predicts an isolated hygiene check-in disposition of `CONTINUE`; authentic resident check-in, WorkerCoordinator claim/fence, and Interlock/InTr admission remain required before any runtime or downstream mutation claim.


## 2026-09-17 on-demand reusable invocation binding defect

After the repository-only convergence repair merged, generation-29 reconciliation rechecked the same four candidates. `SS-EVIDENCE-COMPARISON-001`, `AI-GOVERNANCE-OPPORTUNITY-ENGINE-001`, `STEGVERSE-002-EXPERIMENT-RERUN-001`, and `MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001` still overlap hygiene only at repository scope; both sides retain explicit non-empty disjoint component scopes, with no lineage, adjacency, component, or shared-selected-substrate overlap. They therefore remain canonically distinguished under the existing anti-collision mechanism; none receives changed authority or coordination ownership.

The exact portable bridge itself is source-ready and accepts `--only-consumer canonical_work_coordination --goal-task-id HYGIENE-CAUSAL-ROOTS-001`, but the existing neutral reusable-task trigger had no registered reusable identity whose runner was that bridge. A session/task could reference reusable work generally, but there was no canonical one-trigger manifest binding from the reusable lifecycle into this exact portable Canonical Work path. That is the first newly proven invocation-path defect after collision convergence; lack of an idle connected device is not classified as the defect.

The bounded repair introduces no new executable implementation: reusable identity `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` points directly at existing `scripts/refresh_and_dispatch_resident_requests.py`. The bridge consumes manifest-bound reusable parameters only for that exact identity and requires exact `canonical_work_coordination` plus a non-empty Goal Task ID; unknown parameters, identity mismatch, selector mismatch, and CLI/manifest disagreement fail closed. Historical direct CLI behavior is preserved. The existing neutral scheduler already resolves reusable definitions from the already-local repository root and injects source/runtime roots into child parameters, so no scheduler, dispatcher, runtime, control-plane package, authority plane, Site/StegCore mutation, or second user-operated device is added.

This source repair does not itself satisfy the requested runtime predicate. An authentic resident invocation must still produce `CONTINUE` from the Task Registry preflight before any WorkerCoordinator claim/fence or Interlock/InTr admission can be claimed. If that invocation is unavailable through the current conversation tool surface, the state remains evidence-reachability only; GitHub/CI execution is not an admissible substitute because the portable bridge rejects hosted execution and GitHub has no runtime authority.
