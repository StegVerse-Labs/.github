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

The canonical historical descriptor commits remain retained by repository history. `StegVerse-Labs/StegDB` remains an adjacent denominator candidate and must not be silently added before critical live topology semantics are proven and its applicable handoff is read.

## Contract and authority

Each participant exposes repository/org identity, participant class, runtime identity for active classes, capabilities, required dependencies, handoff location, freshness policy, and explicit non-authority metadata. The dynamic manifest emitted on a locally materialized repository adds commit/ref/tag, sequence, emitted/fresh-until timestamps, status, evidence references, optional handoff hash, and last-success evidence.

```text
credential_authority: TV/TVC
heartbeat_grants_execution_authority: false
github_token_required: false
```

A descriptor or manifest is evidence. It never grants execution, credential, route, release, deployment, custody, or publication authority.

## Fail-closed topology

The central worker constructs an inspectable topology and deterministic SHA-256 topology hash. Required coverage fails if a participant is missing, stale, identity-invalid, FAILED, historically BLOCKED, RETIRED, or loses a required dependency. Required dependency loss propagates to dependent topology state. The worker writes only `receipts/repo-heartbeat-federation/**`.

Descriptor enrollment does not count as live health. Live health begins only when the resident single heartbeat emits and evaluates fresh manifests from the locally materialized participants under an admitted claim/fence.

## Central source validation

```text
Heartbeat Worker Project run 31610774741: SUCCESS
Heartbeat Worker Project run 31611065409: SUCCESS
```

Those hosted cycles were nonpersistent validation. They do not substitute for resident heartbeat activation or live coverage.

## Participant validation observations

Continuity, TV and TVC descriptor validation observations are retained as historical evidence. Zero-step hosted runs are infrastructure evidence and are neither semantic PASS nor semantic descriptor failure.

## No-GitHub-token integration correction discovered during enrollment

The sovereign local-model/runtime path already satisfies the no-GitHub-token rule. A separate legacy conflict remains in the Healer scheduler/control plane. Canonical task:

```text
HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001
StegVerse-Labs/StegVerse-Healer/data/session_consolidation/tv-tvc-no-github-token-dispatch-migration.json
owner: StegVerse-Healer + TV + TVC
state: CLAIMED_FOR_INTEGRATION
```

Release requires production scheduler, quiet-enforcer and publication-remediation paths to use a TV/TVC-governed admitted mechanism without GitHub credential authority. This task must not reopen the completed local-model implementation.

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

1. Resident single heartbeat executes `SHWP-REPO-HEARTBEAT-FEDERATION-001` and writes the first live coverage receipt.
2. Coverage remains incomplete until every required participant is fresh, identity-valid, dependency-satisfied and nonfailed.
3. `HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001` completes the separate no-token dispatch integration.
4. Only after critical live topology proof may an admitted denominator transition evaluate StegDB and additional repositories.
5. Coverage propagation is evaluated only after a real resident receipt exists.

## Execution ownership and collision partition

Standard: `StegVerse-Labs/Continuity/docs/REPOSITORY_HANDOFF_STANDARD.md` / `stegverse.handoff-execution-ownership/v1`.

### MANUAL / SESSION-STARTABLE

No federation implementation or denominator expansion is manually startable by default. A distinct validation-only lane may be claimed for evidence review after a resident receipt exists, without mutating federation registry/topology state.

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: SHWP-REPO-HEARTBEAT-FEDERATION-001
  execution_owner: resident sovereign heartbeat + repo-heartbeat-federation worker
  claim_state: MACHINE_OWNED
  worker_registry_ref: control/worker-registry.d/repo-heartbeat-federation-001.json + StegVerse-Labs/.github#81
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: repository manifest emission/evaluation, live topology, freshness/dependency projection, federation claim/fence/lease, and federation receipts
  release_condition: live topology task completes/supersedes/releases its registry scope
  next_executable_action: resident heartbeat emits/evaluates fresh manifests and persists the canonical topology receipt

- task_id: HEALER-TV-TVC-NO-GITHUB-TOKEN-DISPATCH-001
  execution_owner: StegVerse-Healer + TV + TVC
  claim_state: CLAIMED_FOR_INTEGRATION
  worker_registry_ref: StegVerse-Labs/StegVerse-Healer/data/session_consolidation/tv-tvc-no-github-token-dispatch-migration.json
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: Healer scheduler/quiet-enforcer/publication dispatch credential and admission integration
  release_condition: TV/TVC-governed no-GitHub-token dispatch is installed, validated, and canonical owner releases the integration claim
  next_executable_action: existing integration owner completes the admitted no-token dispatch migration
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: REPO-HEARTBEAT-FEDERATION-CONSTRAINT-RESOLUTION
  execution_owner: engine-v11 authority chain and applicable repository/component authority
  claim_state: ESCALATED
  worker_registry_ref: control/worker-registry.json + docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md
  manual_execution_allowed: false
  manual_allowed_role: NONE
  collision_scope: repository availability, identity, dependency, resource, or authority conditions the federation worker cannot lawfully resolve
  release_condition: next capable authority resolves the condition or explicitly assigns bounded human-authority work
  next_executable_action: derive/register a resolution/escalation task instead of treating constrained coverage as manual implementation work
```

### COMPLETED / SUPERSEDED

- Central federation source implementation: complete/released.
- Critical descriptor enrollment: 11/11 complete/released.
- Duplicate per-repository heartbeat/scheduler creation: superseded/prohibited.

A pending live receipt or incomplete coverage row is not permission for manual implementation. Current registry/claim/fence/lease records govern ownership.

## Archive conditions

Source and participant enrollment no longer require chat history. Broader activation remains machine/integration-owner work under the exact records above.

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
```
