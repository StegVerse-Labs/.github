# Heartbeat Control-Plane Separation Mirror Handoff

Updated: 2026-08-14T18:09:00-05:00

## Authority and claim

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-SCHEMA
originating_goal: separate heartbeat carrier semantics from worker/control-plane runtime semantics while preserving Admissible-Existence and TV/TVC-only credential authority
repository: StegVerse-Labs/.github
branch: feat/heartbeat-control-plane-schema-separation-122
canonical_issue: StegVerse-Labs/.github#122
canonical_pr: StegVerse-Labs/.github#158
parent_handoff: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
canonical_owner: StegVerse-Labs/.github
implementation_claim: current-session / bounded source-schema separation
active_validation_claim: current-session
claim_created_at: 2026-08-14T16:58:30-05:00
claim_release_condition: schema/control separation installed, deterministic validation PASS, PR merged, issue #122 records source/schema release evidence
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This scoped handoff is subordinate to the merged heartbeat carrier contract and grants no authority to mutate live worker claims, fences, leases, runtime state, provider/model operations, credentials, wallet state, or Master Records custody.

## Canonical separation

Heartbeat is the carrier/synchronization continuity reference only. Worker/task coordination, claims, fences, leases, federation control state, route decisions and runtime execution belong to a separate worker/control-plane contract. Subsystem communications retain `manifest packet + expiration wrapper + data packet` semantics and terminalize independently to Master Records.

Installed source/schema separation:

```text
schemas/heartbeat-carrier-signal.schema.json
schemas/worker-control-plane.schema.json
schemas/expired-worker-history.schema.json
control/heartbeat-documentation-semantics-audit.json v3
scripts/validate_heartbeat_control_plane_separation.py
tests/test_heartbeat_control_plane_separation.py
.github/workflows/org-control-plane-validate.yml integration
```

The legacy `schemas/heartbeat-subsignal.schema.json` and `control/heartbeat-subsignals.json` remain compatibility/live projection surfaces pending machine-owned migration. This source/schema lane does not rewrite historical receipts or mutate the live projection.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-SCHEMA
  execution_owner: current bounded source/schema implementation session
  manual_execution_allowed: true
  worker_registry_ref: NONE
  collision_scope: carrier/control schemas, semantics audit, deterministic validator/tests, workflow validation integration and PR #158 only; no live worker/runtime mutation
  release_condition: execution-capable validation passes, PR #158 merges, and issue #122 records source/schema release evidence
  next_executable_action: execute current-head no-token validation, inspect the exact separation validator and focused tests, merge PR #158 if all required gates pass, then release this source/schema claim
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE
  execution_owner: current resident heartbeat/runtime machine owners
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.json and applicable live handoff fragments
  collision_scope: live claim/fence/lease/runtime state, heartbeat engine adoption and legacy projection migration
  release_condition: canonical runtime owner explicitly admits source/schema contract and performs live migration with inspectable evidence
  next_executable_action: consume merged schemas after source release; do not allow this session to mutate live state
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: HEARTBEAT-CONTROL-PLANE-AUTHORITY-COLLISION
  execution_owner: StegCore/StegGate + TV/TVC + canonical resident runtime owners as applicable
  manual_execution_allowed: false
  worker_registry_ref: applicable canonical owner record
  collision_scope: authority conflicts involving admissibility, credentials, live runtime control, or Master Records custody
  release_condition: canonical authority owner resolves the exact conflict
  next_executable_action: fail closed and preserve carrier/control-plane separation rather than widening authority
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: HEARTBEAT-AS-WORKER-CONTROL-PLANE
  execution_owner: NONE
  manual_execution_allowed: false
  worker_registry_ref: NONE
  collision_scope: legacy architecture/terminology only
  release_condition: superseded by merged heartbeat carrier contract #120 and this explicit source/schema separation
  next_executable_action: NONE
```

## Validation evidence

PR #158 run `31844972170` first exposed two HANDOFF ownership defects before the new schema validator. This handoff defect was repaired. The separately owned `SESSION_ASSISTANCE_SCOPE_MIRROR_HANDOFF.md` defect was then repaired and released by #146; issue #146 records successful post-fix organization-control-plane validation. This commit intentionally advances PR #158 so GitHub synthesizes and validates against the current `main` rather than the stale pre-#146 merge base.

Required validation:

```text
python scripts/validate_heartbeat_control_plane_separation.py
python -m unittest tests.test_heartbeat_control_plane_separation -v
```

Mandatory hosted gate: `.github/workflows/org-control-plane-validate.yml`. Hosted validation is evidence only and grants no StegVerse runtime authority.

## Cross-repository dependencies

```text
StegVerse-Labs/.github#120 COMPLETE_RELEASED
StegVerse-Labs/.github#146 COMPLETE_RELEASED shared validation blocker cleared
StegVerse-Labs/StegCore#105 COMPLETE_RELEASED
StegVerse-Labs/repo-standards#39 / PR #40 standards integration separately owned
master-records/orchestration#33 / PR #34 terminal custody separately owned
```

## Completion accounting

```text
source/schema files: 7/7 implemented on branch
scaffolding/stubs: 0
missing required files: 0
focused deterministic validation: current-head hosted execution pending
organization control-plane integration validation: current-head hosted execution pending
live runtime migration: machine-owned, excluded from source/schema completion denominator
```

## Archive condition

This scoped role is archive-safe when source/schema separation is validated and merged, or when the exact remaining role is durably transferred to another claimant with a machine-observable release condition. Live runtime adoption is not a reason to retain this session once its source/schema role is complete.
