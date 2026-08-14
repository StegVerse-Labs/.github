# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-14T18:12:00-05:00

## Authority and active goal

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
originating_goal: implement the AE-bound responsibility split so heartbeat remains the regulatory carrier/reference frame, StegBrain owns contract observation/signal formation, domain subsystems act only under independently admitted authority, and Master Records remains passive custody
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#122
parent_contract: StegVerse-Labs/.github#120 / PR #140 MERGED 2026-08-14T21:47:30Z
canonical_owner: StegVerse-Labs/.github
implementation_claim: CURRENT_SESSION_BOUNDED_SOURCE_SCHEMA_SEPARATION
validation_claim: CURRENT_SESSION_BOUNDED_SOURCE_VALIDATION
claim_created_at: 2026-08-14T18:10:00-05:00
claim_release_condition: versioned carrier-observation and control-plane contracts, deterministic separation validator/tests, and compatibility handoff are committed and validated; live runtime-state migration remains with the canonical runtime owner
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This scoped handoff is authoritative for issue #122 source/schema separation. `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` remains authoritative for carrier semantics. Live runtime claims, fences, leases, worker process state, route state, and production carrier operation are out of scope for this bounded source claim.

## Canonical responsibility split

```text
heartbeat = regulatory carrier/reference frame only
StegBrain = nervous-system contract observer/evaluator + typed subsystem-signal originator
domain subsystem = actor only under independently admitted authority
Master Records = passive event/lifecycle custody and queryable evidence only
TV/TVC = sole credential/secret/token authority
```

Observation does not grant action authority. Signal formation does not grant execution authority. Master Records custody does not grant remediation authority.

## Parent integration state

PR #140 is merged at `34a1744a4cf314ea4f3b80925d4cbd5a7910dd97`; therefore the #122 source/schema separation prerequisite is satisfied. The carrier handoff remains authoritative for the carrier contract; its older pre-merge completion accounting is superseded only by the verified PR #140 merge evidence.

## Installed bounded source implementation

```text
docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md
schemas/heartbeat-carrier-observation.schema.json
schemas/worker-control-plane-coordination.schema.json
control/runtime-separation-contract.json
heartbeat_runtime/runtime_separation.py
scripts/validate_heartbeat_runtime_separation.py
tests/test_heartbeat_runtime_separation.py
.github/workflows/org-control-plane-validate.yml
```

The executable `heartbeat_runtime/runtime_separation.py` is a pure compatibility projection over the historical combined registry. It emits two distinct objects without mutating live state: a carrier-observation object containing only reference/presence observations and a worker-control-plane object retaining task/worker/claim/fence/lease coordination. Historical `schemas/heartbeat-subsignal.schema.json` and historical receipts remain immutable provenance until a separately claimed live runtime migration switches producers/consumers.

## Required semantics

- carrier-observation contract contains continuity/reference-frame observations only and no task dispatch, claims, fences, leases, routes, credentials, custody decisions, or execution authority;
- worker/control-plane coordination contract owns task/worker/claim/fence/lease coordination semantics and explicitly treats heartbeat references as observations rather than authority;
- StegBrain typed enforcement signals are external inputs to the control plane and retain `authority_effect: NONE` / `execution_authority: false`;
- Master Records is referenced only as passive custody/evidence; no remediation or worker-management authority is represented;
- DEMO, TEST, StegVerse-org, StegGhost, and StegVerse-Labs transition domains remain structurally eligible for the same worker lifecycle opening/closure obligations;
- TV/TVC remains sole credential authority; no non-TV/TVC secret/token is introduced; GitHub token runtime authority is NONE.

## Validation state

The first organization-control-plane workflow after the new handoff obtained a hosted runner, but failed before the new separation validator because `docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md` lacked the repository-mandated execution-ownership section. Evidence: run `31849433963`, job `94922274950`; the failure was `missing required ownership section`. This handoff update corrects that defect. No runtime authority was exercised by the workflow.

The workflow now includes:

```text
python scripts/validate_heartbeat_runtime_separation.py
python -m unittest tests.test_heartbeat_runtime_separation -v
```

A subsequent successful run is required before source validation is released.

## Cross-repository dependencies

```text
StegVerse-Labs/StegBrain#860 / docs/STEGBRAIN_MIRROR_HANDOFF.md
  source evaluator complete; repository-native validation still pending/failing at last direct observation
master-records/orchestration#33
  passive custody contract owner
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
  local model/runtime source COMPLETE_RELEASED; do not duplicate
StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md
  live trade path MACHINE_OWNED; do not mutate provider/wallet authority
```

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-SOURCE
  execution_owner: current-session-bounded-source-schema-separation
  manual_execution_allowed: true
  worker_registry_ref: NONE
  collision_scope: versioned carrier/control-plane schemas, pure compatibility projection, deterministic validator/tests, validation workflow integration, and this scoped handoff only
  release_condition: deterministic validator/tests and organization control-plane workflow pass, then implementation claim is released
  next_executable_action: observe current workflow; fix only source/validation defects inside this bounded scope; on PASS release source claim to #122 runtime owner
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
  execution_owner: StegVerse-Labs/.github#122 canonical runtime owner
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.json + issue #122
  collision_scope: live heartbeat producer/consumer switch, control/heartbeat-state.json, active claims/fences/leases, resident worker processes, production carrier operation
  release_condition: live runtime migrates to separated contracts under a fresh authorized runtime claim and produces runtime evidence
  next_executable_action: after bounded source claim release, canonical runtime owner may adopt separated projection/contracts without rewriting historical provenance
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: HEARTBEAT-RUNTIME-SEPARATION-AUTHORITY-COLLISION
  execution_owner: StegCore/StegGate + TV/TVC + affected domain owner
  manual_execution_allowed: false
  worker_registry_ref: applicable canonical owner record
  collision_scope: admissibility, credential/route authority, protected values, custody authority conflicts
  release_condition: exact canonical authority resolves the conflict
  next_executable_action: fail closed; do not infer authority from heartbeat continuity or StegBrain signals
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120
  execution_owner: NONE
  manual_execution_allowed: false
  worker_registry_ref: NONE
  collision_scope: parent carrier contract source/integration only
  release_condition: COMPLETE_MERGED_PR_140
  next_executable_action: NONE; #122 consumes the merged contract
```

## Collision boundaries

Do not mutate `control/heartbeat-state.json`, active worker claims/fences/leases, live worker processes, TV/TVC route/credential state, StegFin provider/wallet execution, or Master Records custody contents from this bounded source claim. Do not use GitHub-hosted validation as runtime authority.

## Current state

```text
parent carrier contract: COMPLETE_MERGED
bounded source/schema separation: IMPLEMENTED_VALIDATION_ACTIVE
live runtime migration: MACHINE_OWNED / NOT CLAIMED HERE
StegBrain source enforcement: COMPLETE_SOURCE / HOSTED VALIDATION PENDING
Master Records passive-custody integration: CLAIMED_BY master-records/orchestration#33
trade source readiness: 7/8; WALLET_HANDOFF_READY pending machine execution
local model/runtime source: COMPLETE_RELEASED
```

## Next executable action

Observe the current organization control-plane workflow. If source validation fails, repair only the bounded separation source. If it passes, persist validation evidence, release `control/session-implementation-claim-2026-08-14-heartbeat-runtime-separation-122.json`, and transfer the live producer/consumer switch to the canonical #122 runtime owner.

## Completion accounting

```text
developed_files: 8/8
scaffolding_or_stubs: 0
missing_required_files: 0
validation: 0/2 pending validator+unit workflow execution after ownership repair
integration: 2/3 parent contract + validation workflow integrated; live runtime migration pending canonical owner
session_consolidation: 11/11 prior session goals durable; this new source-separation goal active
archive_ready: false
```
