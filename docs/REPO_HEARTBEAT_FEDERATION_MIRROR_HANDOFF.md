# Repository Heartbeat Federation Mirror Handoff

## Goal

```text
goal_id: REPO-HEARTBEAT-FEDERATION-001
repository: StegVerse-Labs/.github
branch: main
state: ACTIVE_ENROLLMENT_AND_LIVE_COVERAGE
canonical_issue: StegVerse-Labs/.github#81
canonical_task_owner: SHWP-REPO-HEARTBEAT-FEDERATION-001 / single StegVerse heartbeat
credential_authority: TV/TVC
github_token_required: false
```

This layer extends the existing organization-level federation task with repository-level identity, commit/ref/runtime state, freshness, dependency-loss propagation, and fail-closed coverage. It does not create a second heartbeat or per-repository schedulers.

## Authoritative files

- `schemas/repo-heartbeat-manifest.schema.json`
- `control/repo-heartbeat-federation.json`
- `scripts/emit_repo_heartbeat_manifest.py`
- `workers/repo_heartbeat_federation_worker.py`
- `authorizations/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`
- `handoffs/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`
- `control/worker-registry.d/repo-heartbeat-federation-001.json`
- `control/worker-capability-profiles.json#repository-maintenance-v1`
- `control/process-worker-adapters.json#process:repo-heartbeat-federation-v1`
- `cost-basis/worker-runtime/repo-heartbeat-federation.json`
- `tests/test_repo_heartbeat_federation_worker.py`
- `tests/test_emit_repo_heartbeat_manifest.py`
- `control/session-goal-inventory-2026-08-12-ecosystem-chat-federation-delta.json`

## Critical denominator

```text
StegVerse-Labs/StegCore
StegVerse-Labs/Continuity
StegVerse-Labs/TV
StegVerse-Labs/TVC
StegVerse-Labs/StegID
StegVerse-Labs/StegAgents
StegVerse-Labs/Site
StegVerse-Labs/ara-admissibility-interop
StegVerse-002/micro-node-runtime
StegVerse-org/LLM-adapter
master-records/orchestration
```

`StegVerse-Labs/StegDB` remains an adjacent denominator candidate and must be classified only after its applicable `*_MIRROR_HANDOFF.md` is read.

## Contract and authority

Every participant manifest carries repository/org identity, participant class, sequence, emitted/fresh-until timestamps, status, capabilities, dependencies, evidence refs, and authority metadata. CONTROL/RUNTIME/SERVICE participants also require `commit_sha` and `runtime_id`; optional fields include `ref`, `release_tag`, `handoff_hash`, and `last_success`.

```text
credential_authority: TV/TVC
heartbeat_grants_execution_authority: false
github_token_required: false
```

The reusable emitter derives commit/ref/tag from a locally materialized repository and can hash an explicitly selected handoff. It does not schedule itself, fetch source, contact GitHub, or grant authority.

## Fail-closed topology

The central worker builds an inspectable topology and SHA-256 topology hash. Required coverage fails when a manifest is missing, stale, invalid, FAILED, BLOCKED, RETIRED, or has lost a required dependency. Required dependency loss propagates to dependent topology state. The worker writes only `receipts/repo-heartbeat-federation/**` and grants no cross-repository mutation, execution, credential, deployment, or policy authority.

## Central implementation evidence

```text
schema: 0a02c9a3dc32b83c8fce4887390258b0a0921e2f
registry: 49d3bbfebd9f9629addc8220d83a75727b425747
coverage worker: 4a14a416ffc0ed80d4bfa5ad861f35da42de367e
authorization: cc16bcad63ef1b32c9206a6d99afac2118fd6661
handoff: 9bc7d42c7c4ff8d64ba803f1ccbdec42725c0808
cost basis: 410f41df3a97e6707b7e7fabe77c41c3127656cf
capability profile: 66fbb858efd84c3655ef3a3b2cc2b3671a78a733
registry fragment: 19163e09a94c11f5b81ffa5b231b2ee79f98079d
coverage tests: d4c89eb660c6f90801dc9d6f9cb6d3558ad475a5
process adapter: 84a423ec1eca178503fd1110dc63eaa5f62de817
manifest emitter: c8f7c03fa3f47fd6d9cf164e29a3f232d4a920df
emitter tests: fbea12d575c2745d9a2e4d1923ac5fa5a418fa77
canonical issue: #81
session delta inventory: 5f08556d527c1537dd619acb5c6ebefc4d6ce1f2
```

Heartbeat Worker Project run `31610774741` completed SUCCESS with anonymous/no-GitHub-credential checkout, executable-handoff validation, canonical JSON parsing, compilation, and 112 deterministic tests PASS including repository-federation tests. Heartbeat Worker Project run `31611065409` also completed SUCCESS after the reusable emitter and emitter tests were added. These runs validate source only; their heartbeat cycles were nonpersistent and are not live coverage activation.

## Participant enrollment state

### 1. StegCore — descriptor installed

```text
file: StegVerse-Labs/StegCore/.stegverse/repo-heartbeat.json
commit: b7cbd49f2cede01ec81fd5e397eaa4f9912b2257
handoff update: 31dcc7fe9ba9b1a7efe50103411bc4c4a95114df
state: DESCRIPTOR_INSTALLED / LIVE_COVERAGE_PENDING
```

### 2. Continuity — descriptor installed

```text
file: StegVerse-Labs/Continuity/.stegverse/repo-heartbeat.json
commit: 656d773f3c4503e2ee9753811f30d6aaf549626f
handoff update: 7282db4c636d5eea2df2dff175f8bb3e6d8705d6
Test Readiness run: 31619109440 SUCCESS
Guardian run: 31619109410 FAILED at pre-existing configuration gate because TV_AUDIENCE was empty
state: DESCRIPTOR_INSTALLED / STATIC_REPO_READINESS_PASS / LIVE_COVERAGE_PENDING
```

The Guardian failure is not attributed to the descriptor. Its logs also expose a separate ecosystem no-token migration gap: the hosted workflow currently receives GitHub Actions credential authority for checkout/write behavior. That correction is owned separately by `HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001`.

### 3. TV — descriptor installed

```text
file: StegVerse-Labs/TV/.stegverse/repo-heartbeat.json
commit: ce8ea561742ae1b2a09352f9b6ac0e5fe8e0932b
state: DESCRIPTOR_INSTALLED / HOSTED_SEMANTIC_VALIDATION_UNESTABLISHED / LIVE_COVERAGE_PENDING
```

TV Test Readiness run `31619283434` and Architecture Guard run `31619283435` concluded failure with zero executed job steps in the directly inspected job records. They are retained as hosted infrastructure evidence, not semantic descriptor failures and not validation PASS.

### 4. TVC — descriptor installed

```text
file: StegVerse-Labs/TVC/.stegverse/repo-heartbeat.json
commit: 65009af6ab57ded6d091f1e33283499066fe9461
state: DESCRIPTOR_INSTALLED / HOSTED_VALIDATION_PENDING_OR_ZERO_STEP / LIVE_COVERAGE_PENDING
```

TVC Architecture Guard run `31619373013` concluded failure with zero executed job steps in the inspected job record. Test Readiness run `31619373011` was queued at the last direct observation. Neither condition is counted as semantic validation.

## TV/TVC no-GitHub-token integration correction

A distinct post-inventory integration gap was discovered in `StegVerse-Labs/StegVerse-Healer` and Continuity: legacy `HEALER_GH_TOKEN`/GitHub Actions token-bearing cross-repository behavior still exists outside the already-corrected sovereign local-model runtime path.

Canonical durable owner:

```text
StegVerse-Labs/StegVerse-Healer/data/session_consolidation/tv-tvc-no-github-token-dispatch-migration.json
commit: eedbfac58fb2f02e326de024fede89ec83a04901
task: HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001
state: CLAIMED_FOR_INTEGRATION
owner: Healer + TV + TVC
```

This migration must replace PAT/GITHUB_TOKEN/GH_TOKEN/HEALER_GH_TOKEN production dispatch authority with TV/TVC-governed admission and no-secret evidence. It is not permission to invent another credential system, and it does not reopen the already-released local-model implementation.

## Claims

```text
central implementation: COMPLETE / released
central deterministic source validation: COMPLETE / released
central source integration: COMPLETE / released
participant enrollment: ACTIVE under #81
live coverage execution: MACHINE_OWNED / PENDING RESIDENT HEARTBEAT
Healer no-token migration: DISTINCT INTEGRATION CLAIM / ACTIVE
collision boundary: do not replace SHWP-ALL-ORG-FEDERATION-001; do not create per-repo schedulers; do not reopen completed local-model source implementation
```

## Exact next tasks

1. Resident single heartbeat admits `SHWP-REPO-HEARTBEAT-FEDERATION-001` and emits the first real fail-closed coverage receipt.
2. Read and enroll `StegVerse-Labs/StegID`, `StegVerse-Labs/StegAgents`, `StegVerse-Labs/Site`, `StegVerse-Labs/ara-admissibility-interop`, `StegVerse-002/micro-node-runtime`, `StegVerse-org/LLM-adapter`, and `master-records/orchestration` using their applicable handoffs.
3. Connect locally materialized descriptors to fresh manifest emission on the resident carrier without arbitrary repo commands or per-repo scheduling authority.
4. Inspect StegDB handoff and admit it only through an explicit denominator transition if classification requires participation.
5. Complete `HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001` without GitHub-token production authority.
6. Expand denominator and propagate coverage only after the critical live topology receipt proves the existing denominator.

## Archive conditions

This workstream is not archive-ready while required descriptors remain missing, the first resident coverage receipt does not exist, or this thread still owns unique enrollment/integration work. Repository source completion is not live coverage.

## Completeness

```text
developed_central_files: 12/12
central_scaffolding_or_stubs: 0
missing_required_central_files: 0
central_validation: 2/3 (deterministic source suites PASS; resident live coverage pending)
central_integration: 2/2
repo_descriptors_installed: 4/11
critical_repo_live_coverage: 0/11
session_delta_requirements_transferred: 2/2
current_goal_activation: 68%
archive_ready: false
```
