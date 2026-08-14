# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-14T18:10:00-05:00

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

PR #140 is merged at `34a1744a4cf314ea4f3b80925d4cbd5a7910dd97`; therefore the #122 source/schema separation prerequisite is satisfied. The older carrier handoff still contains pre-merge integration accounting and is historical/stale for that one field only; it remains authoritative for the carrier contract itself.

## Bounded source implementation scope

This session may implement only non-live source/schema surfaces that make the separation executable and testable without mutating current live claims/fences/leases:

```text
schemas/heartbeat-carrier-observation.schema.json
schemas/worker-control-plane-coordination.schema.json
control/runtime-separation-contract.json
scripts/validate_heartbeat_runtime_separation.py
tests/test_heartbeat_runtime_separation.py
.github/workflows/org-control-plane-validate.yml integration if non-authorizing and compatible
```

Historical `schemas/heartbeat-subsignal.schema.json` and historical receipts remain immutable provenance unless a separately validated migration explicitly supersedes them. Existing live control/heartbeat state is not rewritten by this claim.

## Required semantics

- carrier-observation contract contains continuity/reference-frame observations only and no task dispatch, claims, fences, leases, routes, credentials, custody decisions, or execution authority;
- worker/control-plane coordination contract owns task/worker/claim/fence/lease coordination semantics and explicitly treats heartbeat references as observations rather than authority;
- StegBrain typed enforcement signals are external inputs to the control plane and retain `authority_effect: NONE` / `execution_authority: false`;
- Master Records is referenced only as passive custody/evidence; no remediation or worker-management authority is represented;
- DEMO, TEST, StegVerse-org, StegGhost, and StegVerse-Labs transition domains remain structurally eligible for the same worker lifecycle opening/closure obligations;
- TV/TVC remains sole credential authority; no non-TV/TVC secret/token is introduced; GitHub token runtime authority is NONE.

## Cross-repository dependencies

```text
StegVerse-Labs/StegBrain#860 / docs/STEGBRAIN_MIRROR_HANDOFF.md
  source evaluator complete; repository-native validation pending/failed before runner steps at last observation
master-records/orchestration#33
  passive custody contract owner
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
  local model/runtime source COMPLETE_RELEASED; do not duplicate
StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md
  live trade path MACHINE_OWNED; do not mutate provider/wallet authority
```

## Collision boundaries

Do not mutate `control/heartbeat-state.json`, active worker claims/fences/leases, live worker processes, TV/TVC route/credential state, StegFin provider/wallet execution, or Master Records custody contents from this bounded source claim. Do not use GitHub-hosted validation as runtime authority.

## Validation requirements

Deterministic validation must prove the carrier schema rejects control-plane authority fields, the control-plane schema preserves claim/fence/lease semantics outside heartbeat, StegBrain signals carry no execution authority, passive Master Records references carry no action authority, and no non-TV/TVC credential/token semantics are introduced.

## Current state

```text
parent carrier contract: COMPLETE_MERGED
bounded source/schema separation: CLAIMED_FOR_IMPLEMENTATION
live runtime migration: MACHINE_OWNED / NOT CLAIMED HERE
StegBrain source enforcement: COMPLETE_SOURCE / HOSTED VALIDATION PENDING
Master Records passive-custody integration: CLAIMED_BY master-records/orchestration#33
trade source readiness: 7/8; WALLET_HANDOFF_READY pending machine execution
local model/runtime source: COMPLETE_RELEASED
```

## Next executable action

Inspect the current heartbeat subsignal schema and runtime references, then install the versioned carrier-observation and worker-control-plane contracts plus deterministic validation without rewriting live state. After validation, release this bounded source claim and transfer the runtime switch to the canonical #122 runtime owner.

## Completion accounting

```text
developed_files: 1/6
scaffolding_or_stubs: 0
missing_required_files: 5
validation: 0/2
integration: 1/3
session_consolidation: 11/11 prior session goals durable; this new source-separation goal active
archive_ready: false
```
