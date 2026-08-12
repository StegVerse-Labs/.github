# Repository Heartbeat Federation Mirror Handoff

## Goal

```text
goal_id: REPO-HEARTBEAT-FEDERATION-001
repository: StegVerse-Labs/.github
branch: main
state: DESCRIPTOR_ENROLLMENT_COMPLETE_LIVE_COVERAGE_PENDING
canonical_issue: StegVerse-Labs/.github#81
canonical_task_owner: SHWP-REPO-HEARTBEAT-FEDERATION-001 / single StegVerse heartbeat
credential_authority: TV/TVC
github_token_required: false
```

This layer extends the existing organization-level federation task with repository-level identity, commit/ref/runtime state, freshness, dependency-loss propagation, and fail-closed coverage. It does not create a second heartbeat or per-repository schedulers.

## Authoritative central files

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

## Critical denominator — descriptor enrollment complete

All eleven required participants now carry `.stegverse/repo-heartbeat.json` under their own repository authority:

```text
StegVerse-Labs/StegCore
  b7cbd49f2cede01ec81fd5e397eaa4f9912b2257
StegVerse-Labs/Continuity
  656d773f3c4503e2ee9753811f30d6aaf549626f
StegVerse-Labs/TV
  ce8ea561742ae1b2a09352f9b6ac0e5fe8e0932b
StegVerse-Labs/TVC
  65009af6ab57ded6d091f1e33283499066fe9461
StegVerse-Labs/StegID
  440ffd575d036a63a9236539534706dcabac5224
StegVerse-Labs/StegAgents
  56be9ef2c0fe4a1fb2994264abf712431041ade1
StegVerse-Labs/Site
  e74cb5532f997a72710f1fa0e281d1c0175c7d19
StegVerse-Labs/ara-admissibility-interop
  c963a3016b015c63680f8cc23064575183f3b66d
StegVerse-002/micro-node-runtime
  7674486444c830995d8f664d19b7ef4ae23f83bd
StegVerse-org/LLM-adapter
  04146f97115e5d47eeb674454ccb1ebe40ce5d94
master-records/orchestration
  af99f09b6c6dd2d991d3d228f1ee637122099e1a
```

`StegVerse-Labs/StegDB` remains an adjacent denominator candidate. It must not be silently added before the critical live topology semantics are proven and its applicable handoff is read.

## Contract and authority

Each participant exposes repository/org identity, participant class, runtime identity for active classes, capabilities, required dependencies, handoff location, freshness policy, and explicit non-authority metadata. The dynamic manifest emitted on a locally materialized repository adds commit/ref/tag, sequence, emitted/fresh-until timestamps, status, evidence references, optional handoff hash, and last-success evidence.

```text
credential_authority: TV/TVC
heartbeat_grants_execution_authority: false
github_token_required: false
```

A descriptor or manifest is evidence. It never grants execution, credential, route, release, deployment, custody, or publication authority.

## Fail-closed topology

The central worker constructs an inspectable topology and deterministic SHA-256 topology hash. Required coverage fails if a participant is missing, stale, identity-invalid, FAILED, BLOCKED, RETIRED, or loses a required dependency. Required dependency loss propagates to dependent topology state. The worker writes only `receipts/repo-heartbeat-federation/**`.

Descriptor enrollment does not count as live health. Live health begins only when the resident single heartbeat emits and evaluates fresh manifests from the locally materialized participants under an admitted claim/fence.

## Central source validation

```text
Heartbeat Worker Project run 31610774741: SUCCESS
  anonymous/no-GitHub-credential checkout
  canonical JSON parse PASS
  executable handoff validation PASS
  runtime/workers/scripts compile PASS
  112 deterministic tests PASS, including repository federation tests

Heartbeat Worker Project run 31611065409: SUCCESS
  reusable manifest emitter + emitter tests included
```

Those hosted cycles were nonpersistent validation. They do not substitute for resident heartbeat activation or live coverage.

## Participant validation observations

```text
Continuity descriptor commit 656d773f3c4503e2ee9753811f30d6aaf549626f
  Test Readiness run 31619109440: SUCCESS
  Guardian run 31619109410: FAILED at existing configuration gate (TV_AUDIENCE empty)
  descriptor defect inferred: false

TV descriptor commit ce8ea561742ae1b2a09352f9b6ac0e5fe8e0932b
  Test Readiness run 31619283434: failure with zero executed job steps observed
  Architecture Guard run 31619283435: failure with zero executed job steps observed
  semantic descriptor validation: not established

TVC descriptor commit 65009af6ab57ded6d091f1e33283499066fe9461
  Architecture Guard run 31619373013: failure with zero executed job steps observed
  Test Readiness run 31619373011: queued at direct observation
  semantic descriptor validation: not established
```

Zero-step hosted runs are retained as infrastructure evidence and are neither semantic PASS nor semantic descriptor failure.

## No-GitHub-token integration correction discovered during enrollment

The sovereign local-model/runtime path already satisfies the no-GitHub-token rule. A separate legacy conflict remains in the Healer scheduler/control plane: `HEALER_GH_TOKEN` and GitHub Actions credential-bearing dispatch/write behavior are still represented in current Healer/Continuity runtime surfaces.

Canonical task:

```text
HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001
StegVerse-Labs/StegVerse-Healer/data/session_consolidation/tv-tvc-no-github-token-dispatch-migration.json
commit: eedbfac58fb2f02e326de024fede89ec83a04901
owner: StegVerse-Healer + TV + TVC
state: CLAIMED_FOR_INTEGRATION
```

Release requires the production scheduler, quiet-enforcer and publication-remediation paths to stop depending on `HEALER_GH_TOKEN`, `GITHUB_TOKEN`, `GH_TOKEN`, PAT, or equivalent GitHub credential authority, and to use a TV/TVC-governed admitted mechanism with inspectable no-secret receipts. This is a distinct integration task and must not reopen the completed local-model implementation.

## Claims

```text
central implementation: COMPLETE / released
central deterministic source validation: COMPLETE / released
critical descriptor enrollment: COMPLETE / released
live topology coverage: MACHINE_OWNED / resident heartbeat pending
Healer no-token migration: CLAIMED_FOR_INTEGRATION / separate durable owner
collision boundary: one heartbeat; one worker registry; no per-repo schedulers; no GitHub-token production authority; no duplicate local-model implementation
```

## Exact next tasks

1. Resident single heartbeat admits `SHWP-REPO-HEARTBEAT-FEDERATION-001`, discovers locally materialized enrolled repositories, emits fresh normalized manifests, and writes the first fail-closed coverage receipt at `receipts/repo-heartbeat-federation/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`.
2. Coverage remains incomplete until every required participant is fresh, identity-valid, dependency-satisfied and nonfailed in that receipt.
3. `HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001` replaces legacy GitHub-token dispatch authority with TV/TVC-governed admission/execution evidence.
4. Only after critical live topology proof may an admitted denominator transition evaluate StegDB and additional active runtime/provider/control repositories.
5. Coverage publication/propagation is evaluated only after a real resident receipt exists; source completion alone does not authorize Site, Publisher, admissibility-wiki, or stegguardian-wiki publication.

## Archive conditions

This federation implementation no longer requires chat history to reconstruct source or participant enrollment: central source and all eleven descriptor installations are repository-resident. The broader session remains non-archivable while it still owns distinct no-token integration work and while the organization archive gate requires measurable resident sovereign-carrier progress.

## Completeness

```text
central developed files: 12/12
required participant descriptors: 11/11
scaffolding_or_stubs: 0
missing required descriptor files: 0
central deterministic validation: 2/2 source suites PASS
live resident coverage validation: 0/1
central integration + participant enrollment: 13/13
critical live coverage: 0/11 until first resident topology receipt
session delta requirements transferred: 2/2
federation source/descriptor task completion: 100%
federation goal activation: 82%
archive_ready_for_broader_session: false
```
