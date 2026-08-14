# Heartbeat Control-Plane Separation Mirror Handoff

Updated: 2026-08-14T16:59:30-05:00

## Authority and claim

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-SCHEMA
originating_goal: separate heartbeat carrier semantics from worker/control-plane runtime semantics while preserving Admissible-Existence and TV/TVC-only credential authority
repository: StegVerse-Labs/.github
branch: feat/heartbeat-control-plane-schema-separation-122
canonical_issue: StegVerse-Labs/.github#122
parent_handoff: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
canonical_owner: StegVerse-Labs/.github
implementation_claim: current-session / bounded source-schema separation
active_validation_claim: current-session after source implementation
claim_created_at: 2026-08-14T16:58:30-05:00
claim_release_condition: schema/control separation installed, deterministic validation PASS, PR merged, issue #122 records release evidence
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This scoped handoff is subordinate to the merged heartbeat carrier contract and does not grant authority to mutate live worker claims, fences, leases, runtime state, provider/model operations, credentials, or Master Records custody.

## Canonical separation

Heartbeat is the carrier/synchronization continuity reference only. Worker/task coordination, claims, fences, leases, federation control state, route decisions and runtime execution belong to a separate worker/control-plane contract. Subsystem communications retain `manifest packet + expiration wrapper + data packet` semantics and terminalize independently to Master Records.

The source/schema refactor must therefore:

1. reduce `schemas/heartbeat-subsignal.schema.json` to carrier-observation and subsystem-signal carriage metadata only;
2. move worker coordination, transport lease, federation/claim/fence semantics to an explicit control-plane schema;
3. preserve historical heartbeat-named receipts as provenance rather than rewriting them;
4. permit `expired_worker_history` as a subsystem signal whose payload has its own manifest/expiration/data identity and no execution authority;
5. keep carrier continuity separate from capability activation proof under StegCore Admissible-Existence;
6. retain TV/TVC credential authority and prohibit GitHub/non-TV/TVC token runtime authority.

## Collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-SCHEMA
  owner: current bounded source/schema implementation session
  files:
    - schemas/heartbeat-subsignal.schema.json
    - schemas/worker-control-plane.schema.json
    - control/heartbeat-subsignals.json (migration metadata only where safe)
    - focused validator/tests
    - docs/HEARTBEAT_CONTROL_PLANE_SEPARATION_MIRROR_HANDOFF.md
  release_condition: validated PR merged and issue #122 records source/schema release evidence
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE
  owner: current resident heartbeat/runtime machine owners
  files: live claim/fence/lease/runtime state and execution paths
  release_condition: canonical runtime owner explicitly admits source/schema contract and performs live migration
```

### AUTHORITY-OWNED

```yaml
- task_id: TV-TVC-CREDENTIAL-AUTHORITY
  owner: StegVerse-Labs/TV + StegVerse-Labs/TVC
  release_condition: none; ongoing authority invariant
```

## Validation commands

Deterministic validation must prove carrier-only heartbeat semantics, explicit control-plane ownership of claims/fences/leases, `expired_worker_history` non-authorizing packet structure, and TV/TVC-only credential authority. Hosted workflows are evidence only and do not grant runtime authority.

## Cross-repository dependencies

```text
StegVerse-Labs/.github#120 COMPLETE_RELEASED
StegVerse-Labs/StegCore#105 COMPLETE_RELEASED
StegVerse-Labs/repo-standards#39 / PR #40 standards integration pending
master-records/orchestration#33 / PR #34 terminal custody validation/integration pending
```

## Archive condition

This scoped role is archive-safe when source/schema separation is validated and merged, or when the exact remaining role is durably transferred to another claimant with a machine-observable release condition. Live runtime adoption is not a reason to retain this session once its source/schema role is complete.
