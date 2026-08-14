# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-14T18:13:00-05:00

## Authority and active goal

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
originating_goal: implement the AE-bound responsibility split so heartbeat remains the regulatory carrier/reference frame, StegBrain owns contract observation/signal formation, domain subsystems act only under independently admitted authority, and Master Records remains passive custody
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#122
parent_contract: StegVerse-Labs/.github#120 / PR #140 MERGED 2026-08-14T21:47:30Z
canonical_owner: StegVerse-Labs/.github
source_implementation_claim: COMPLETE_RELEASED
source_validation_claim: COMPLETE_RELEASED
live_runtime_migration_claim: CANONICAL_RUNTIME_OWNER_ONLY
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This scoped handoff is authoritative for issue #122 source/schema separation. `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` remains authoritative for carrier semantics. Live runtime claims, fences, leases, worker process state, route state, and production carrier operation are not granted to this source lane.

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

PR #140 is merged at `34a1744a4cf314ea4f3b80925d4cbd5a7910dd97`; therefore the #122 source/schema separation prerequisite is satisfied. Issue #120 is closed completed. The carrier handoff remains authoritative for the carrier contract; its older pre-merge completion accounting is superseded by the verified merge/closure evidence.

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

## Validation evidence

Source validation is complete and released.

```text
workflow: Validate organization control plane - No GitHub Token Authority
run: 31849518737
job: 94922516176
head: ca0f4c6859bbb997d2db2e339106ac5fd444b687
conclusion: SUCCESS
handoff ownership: PASS
AE control-plane conformance: PASS
heartbeat carrier contract: PASS
heartbeat runtime separation validator: PASS
runtime separation unit tests: PASS 4/4
cross-repository dependency collision tests: PASS 7/7
JSON/JSONL syntax: PASS
validation no-authority check: PASS
```

The hosted runner exposed platform metadata permission only; the workflow subprocess explicitly ran without `GITHUB_TOKEN`/`GH_TOKEN`, used anonymous checkout, `permissions: {}`, and remained validation evidence rather than StegVerse runtime authority.

Implementation claim release record:

```text
control/session-implementation-claim-2026-08-14-heartbeat-runtime-separation-122.json
state: COMPLETE_RELEASED
release commit: 6509a38a3752ff3295233f6018a356bb9acf13df
```

## Cross-repository dependencies

```text
StegVerse-Labs/StegBrain#860 / docs/STEGBRAIN_MIRROR_HANDOFF.md
  source evaluator complete; repository-native validation remains separately owned
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
  execution_owner: NONE
  manual_execution_allowed: false
  worker_registry_ref: NONE
  collision_scope: released source/schema implementation only
  release_condition: COMPLETE_RELEASED_AFTER_RUN_31849518737
  next_executable_action: NONE; source work is complete
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
  execution_owner: StegVerse-Labs/.github#122 canonical runtime owner
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.json + issue #122
  collision_scope: live heartbeat producer/consumer switch, control/heartbeat-state.json, active claims/fences/leases, resident worker processes, production carrier operation
  release_condition: live runtime migrates to separated contracts under a fresh authorized runtime claim and produces runtime evidence
  next_executable_action: adopt the released carrier/control-plane contracts and pure projection into the live producer/consumer path without rewriting historical provenance
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
  release_condition: COMPLETE_MERGED_PR_140_AND_ISSUE_120_CLOSED
  next_executable_action: NONE; #122 consumes the merged contract
```

## Current state

```text
parent carrier contract: COMPLETE_MERGED_RELEASED
bounded source/schema separation: COMPLETE_VALIDATED_RELEASED
live runtime migration: MACHINE_OWNED / PENDING RUNTIME EVIDENCE
StegBrain source enforcement: COMPLETE_SOURCE / repository-native validation separately owned
Master Records passive-custody integration: CLAIMED_BY master-records/orchestration#33
trade source readiness: 7/8; WALLET_HANDOFF_READY pending machine execution
local model/runtime source: COMPLETE_RELEASED
```

## Canonical continuation

```text
PRIMARY LIVE MIGRATION: StegVerse-Labs/.github#122
NERVOUS SYSTEM: StegVerse-Labs/StegBrain#860
PASSIVE CUSTODY: master-records/orchestration#33
TRADE: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md -> canonical machine worker
LOCAL MODEL LIVE ACTIVATION: StegVerse-Labs/.github#60 -> TVC -> LLM-adapter
```

## Completion accounting

```text
developed_files: 8/8
scaffolding_or_stubs: 0
missing_required_files: 0
validation: 2/2 PASS
integration: 2/3 source+validation integrated; live runtime producer/consumer migration pending canonical #122 owner
session_consolidation: 11/11 prior session goals durable; new source-separation implementation transferred to live runtime owner
archive_ready: false while this reactivated session retains distinct integration/observation responsibility for activation goals
```
