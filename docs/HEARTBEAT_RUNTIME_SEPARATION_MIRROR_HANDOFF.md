# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-15T14:23:00-05:00

## Authority and active goal

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
originating_goal: implement the AE-bound responsibility split so heartbeat remains the regulatory carrier/reference frame, StegBrain owns contract observation/signal formation, domain subsystems act only under independently admitted authority, and Master Records remains passive custody
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#122
parent_contract: StegVerse-Labs/.github#120 / PR #140 MERGED
canonical_owner: StegVerse-Labs/.github
source_implementation_claim: COMPLETE_RELEASED
source_validation_claim: COMPLETE_RELEASED
live_runtime_migration_claim: CANONICAL_RUNTIME_OWNER_ONLY
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This handoff is authoritative for issue #122 source/schema separation. `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` remains authoritative for carrier semantics. Live runtime claims, fences, leases, worker processes, route state, protected values, and production carrier operation are not granted to this source lane.

## Canonical responsibility split

```text
heartbeat = regulatory carrier/reference frame only
StegBrain = nervous-system contract observer/evaluator + typed subsystem-signal originator
domain subsystem = actor only under independently admitted authority
Master Records = passive event/lifecycle custody and queryable evidence only
TV/TVC = sole credential/secret/token authority
```

Observation does not grant action authority. Signal formation does not grant execution authority. Master Records custody does not grant remediation authority.

## Installed bounded source implementation

```text
docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md
schemas/heartbeat-carrier-observation.schema.json
schemas/worker-control-plane-coordination.schema.json
schemas/expired-worker-history.schema.json
control/runtime-separation-contract.json
heartbeat_runtime/runtime_separation.py
scripts/validate_heartbeat_runtime_separation.py
tests/test_heartbeat_runtime_separation.py
.github/workflows/org-control-plane-validate.yml
```

`heartbeat_runtime/runtime_separation.py` is a pure compatibility projection over the historical combined registry. It emits a carrier-observation object containing reference/presence observations and a separate worker/control-plane object retaining task/worker/claim/fence/lease coordination. Historical heartbeat-named schemas and receipts remain provenance until the separately claimed live migration switches producers/consumers.

## Expired-worker convergence contract

The nonduplicative `schemas/expired-worker-history.schema.json` artifact from superseded PR #158 was selectively integrated without merging the competing branch. The terminal history packet is evidence only and preserves the opening/closure obligation:

```text
worker expiration at R_expire
-> active worker/claim/lease authority ends
-> immutable expired-worker history packet is finalized
-> closure must be observable by NEXT_ADMISSIBLE_CARRIER_OR_EQUIVALENT_RETURN_REFERENCE
-> Master Records passively records/custodies the terminal evidence
```

Required zero-authority predicates include:

```text
authority_effect=NONE
execution_authority=false
claim_active=false
lease_active=false
heartbeat_grants_authority=false
reactivates_expired_worker=false
master_records_action_authority=false
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_required=false
```

StegBrain, not heartbeat or Master Records, derives present/due/missing/mismatch contract signals from observable evidence. The same lifecycle structure applies to StegVerse-Labs, DEMO, TEST, StegVerse-org, and StegGhost where worker capability is admitted.

## Validation evidence

Initial separation validation:

```text
workflow: Validate organization control plane - No GitHub Token Authority
run: 31849518737
job: 94922516176
head: ca0f4c6859bbb997d2db2e339106ac5fd444b687
conclusion: SUCCESS
runtime separation validator: PASS
runtime separation unit tests: PASS 4/4
cross-repository collision tests: PASS 7/7
```

Expired-worker convergence validation:

```text
schema commit: e6ff6f9a0135c4e815ac0df9f859eabc7e1e66f4
validator contract commit: 166806cf8ad0c0c121f746f1f0b7723852b5d795
unit-test binding commit: cb692de072eac0e5114a0d9a135d86e3fbff87b3
workflow: Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run: 31849685349
job: 94922986048
head: cb692de072eac0e5114a0d9a135d86e3fbff87b3
conclusion: SUCCESS
compile runtime/workers/scripts: PASS
canonical JSON parsing: PASS
executable handoffs: PASS
complete deterministic repository suite including expired-worker contract: PASS
heartbeat dry-run non-persistence: PASS
ephemeral projection rebuild: PASS
workflow non-authorizing proof: PASS
```

The later organization-control-plane run `31849685358` was cancelled and is not used as positive evidence. The successful Heartbeat Worker Project run above is the exact-head release evidence for the convergence artifact.

Implementation/convergence claim:

```text
control/session-implementation-claim-2026-08-14-heartbeat-runtime-separation-122.json
state: COMPLETE_RELEASED
release commit: 057a0e0b51ff2a95effaa6d6afeb2650fdc711c9
```

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
manual_execution_allowed: false
worker_registry_ref: NONE_SOURCE_RELEASED
collision_scope: released source/schema separation only
release_condition: COMPLETE_RELEASED
next_executable_action: NONE
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
execution_owner: StegVerse-Labs/.github#122 canonical runtime owner
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.json
collision_scope: live heartbeat producer/consumer switch, control/heartbeat-state.json, active claims/fences/leases, resident worker processes, production carrier operation
release_condition: live runtime migrates under a fresh authorized claim and produces immutable runtime evidence
next_executable_action: consume the released carrier/control-plane/expired-worker contracts without rewriting historical provenance
```

### ESCALATED / AUTHORITY-OWNED

```yaml
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.json
collision_scope: TV/TVC credential/route authority, StegCore/StegGate admissibility, Master Records custody
release_condition: each canonical authority owner resolves its own bounded dependency
next_executable_action: escalate only through the named canonical authority owner when a live migration dependency cannot be satisfied within #122 scope
```

### COMPLETED / SUPERSEDED

```yaml
task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-SOURCE
execution_owner: NONE
manual_execution_allowed: false
worker_registry_ref: NONE_TERMINAL
collision_scope: bounded source/schema separation and expired-worker convergence artifacts
release_condition: COMPLETE_RELEASED_AFTER_EXACT_HEAD_VALIDATION_31849685349
next_executable_action: NONE
```

### CROSS-REPOSITORY OWNERS

```text
NERVOUS SYSTEM: StegVerse-Labs/StegBrain#860 / docs/STEGBRAIN_MIRROR_HANDOFF.md
PASSIVE CUSTODY: master-records/orchestration#33
TRADE: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md -> STEGFIN-CONTINUITY-CARRIER-007
LOCAL MODEL LIVE ACTIVATION: StegVerse-Labs/.github#60 -> TVC -> LLM-adapter -> Master Records
```

No source lane may mutate TV/TVC credential authority, live StegFin provider/wallet state, Master Records custody, or active runtime claims/fences/leases.

## Current state and completion accounting

```text
parent carrier contract: COMPLETE_MERGED_RELEASED
bounded source/schema separation: COMPLETE_VALIDATED_RELEASED
expired-worker convergence artifact: COMPLETE_VALIDATED_RELEASED
live runtime migration: MACHINE_OWNED / PENDING RUNTIME EVIDENCE
StegBrain source enforcement: COMPLETE_SOURCE / validation separately owned
Master Records passive-custody integration: CLAIMED_BY master-records/orchestration#33
trade source readiness: 7/8; WALLET_HANDOFF_READY pending machine execution
local model/runtime source: COMPLETE_RELEASED

developed_files: 9/9
scaffolding_or_stubs: 0
missing_required_files: 0
validation: 3/3 PASS
integration: 2/3 (source + validation integrated; live producer/consumer migration pending #122 runtime owner)
session_consolidation: 12/12 current session requirements implemented or durably transferred
archive_dependency: none from this source lane; remaining runtime work is machine-owned
```
