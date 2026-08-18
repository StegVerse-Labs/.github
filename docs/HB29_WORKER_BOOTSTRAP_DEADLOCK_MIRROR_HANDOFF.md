# HB29 Worker Bootstrap Deadlock Mirror Handoff

This is the bounded subordinate handoff for the repaired HB29→HB30 startup defect. It does not replace `docs/ORG_MIRROR_HANDOFF.md` or `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`.

```text
goal_id: SHWP-HB29-WORKER-BOOTSTRAP-DEADLOCK-003
originating_goal: Fix the implementation defect preventing machine-owned HB29→HB30 transition execution.
repository: StegVerse-Labs/.github
canonical_issue: #220
pull_request: #221
merge_commit: 3e7d67b3940ca0ce325b6fbf0b43a87fb83e65a8
parent_runtime_handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
organization_handoff: docs/ORG_MIRROR_HANDOFF.md
claim: control/session-implementation-claim-2026-08-18-hb29-worker-bootstrap-deadlock.json
state: SOURCE_FIX_MERGED_PENDING_REAL_HB30_OBSERVATION
implementation_claim: RELEASED_FROM_CHAT
observation_owner: SHWP-DURABLE-RUNTIME-ACTIVATION / G18 + normal StegVerse-native WorkerCoordinator execution
chat_session_required: false
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
render_production_authority: NONE
```

## Defect and root cause

`WorkerCoordinator.cycle()` requires `control/heartbeat-carrier-runtime-state.json` before worker coordination begins. The first separated-v12 carrier state is HB30, and the canonical producer is `scripts/advance_heartbeat_transition.py`. Before PR #221, the normal worker-runtime entrypoint constructed `WorkerCoordinator` before ensuring that HB30 existed. Fresh cutover at immutable HB29 could therefore fail before any coordination path capable of reaching the already-installed transition machinery.

This was a startup/integration circularity, not a missing transition producer.

## Released source repair

Merged `scripts/run_worker_runtime.py` now performs a narrow initial-carrier bootstrap before WorkerCoordinator construction when and only when the separated carrier state is absent. It requires immutable `control/heartbeat-state.json` at epoch 29 and delegates transition semantics to the existing canonical `scripts/advance_heartbeat_transition.py` producer.

The wrapper forwards only a minimal non-secret environment allowlist. GitHub credentials, TVC credential values, provider credentials, Render credentials, wallet credentials, and other secret-bearing environment values are not forwarded.

WorkerCoordinator is constructed only after a `CARRIER_TRANSITION_COMPLETE` receipt exists and an HB30+ separated carrier state is present. If transition execution fails, startup fails closed. Existing HB30+ state is reused without rerunning the initial transition.

The repair does not mutate legacy HB29 directly, create another heartbeat/scheduler/WorkerCoordinator/claim/fence, make a hosted runtime production authority, grant route/provider/wallet/trade/custody authority, bypass TV/TVC, or make a third-party dependency primary.

The previously released iPhone capsule remains optional supporting initiation evidence; it is no longer a coding prerequisite for the normal StegVerse-native worker-runtime path to materialize the first separated carrier state.

## Validation evidence

Exact PR head validated before merge:

```text
head: 9b0563bde31e766c78ac85e6ec375b480ce51c18
Heartbeat Worker Project: 32160758517
new HB29 bootstrap regressions: 4/4 PASS
existing HB29 transition contract tests: PASS
compile runtime/workers/scripts: PASS
canonical JSON parsing: PASS
executable handoff validation: PASS
Organization Control Plane: 32160758629
this handoff ownership partition: PASS after repair
```

The repository-wide suite was not globally green because concurrent/unrelated COSV work on main contained `test_cosv.COSVTests.test_aggregate_rollup` / `scripts/cosv.py` factor-encoding failure. Organization Control Plane likewise remained blocked only by ownership-section omissions in three separate COSV handoffs. Those failures are not evidence against this repair and were not modified by this lane.

## Current runtime observation

Immediately after merge, direct repository observation still found neither:

```text
control/heartbeat-carrier-runtime-state.json
receipts/heartbeat-transition-continuity/latest.json
```

Therefore **live HB30 is not claimed**. Source merge removes the startup deadlock; actual activation still requires a normal non-hosted StegVerse-native worker-runtime execution to run the merged entrypoint and persist the carrier/continuity evidence.

## Machine-observable completion condition

The existing machine owner completes this continuation when:

1. normal `scripts/run_worker_runtime.py` starts on the retained HB29 state;
2. the merged initial-carrier bootstrap invokes the canonical transition producer because no carrier exists;
3. `control/heartbeat-carrier-runtime-state.json` is persisted at HB30 or later while legacy `control/heartbeat-state.json` remains HB29;
4. `receipts/heartbeat-transition-continuity/latest.json` reports `CARRIER_TRANSITION_COMPLETE`;
5. independent WorkerCoordinator state observes that carrier epoch;
6. no duplicate claim/fence appears and reconstruction passes.

Hosted validation is never activation evidence.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
manual_execution_allowed: false
worker_registry_ref: control/session-implementation-claim-2026-08-18-hb29-worker-bootstrap-deadlock.json
collision_scope: source repair is merged and the chat implementation claim is released; no live runtime-state mutation belongs to a session
release_condition: SATISFIED by PR #221 merge 3e7d67b3940ca0ce325b6fbf0b43a87fb83e65a8 and durable transfer to G18/WorkerCoordinator observation
next_executable_action: none for a chat implementation lane; observe only if asked
```

### WORKER-OWNED / DO NOT COMPETE

```text
manual_execution_allowed: false
worker_registry_ref: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json + control/worker-registry.json
collision_scope: actual sovereign worker-runtime startup, HB30+ persistence, WorkerCoordinator observation, G18 claim/fence, reconstruction, and downstream activation
release_condition: HB30+ carrier and continuity receipt exist, WorkerCoordinator observes the successor, no duplicate claim/fence exists, and reconstruction passes
next_executable_action: existing StegVerse-native worker-runtime owner starts the merged entrypoint; its built-in initial-carrier bootstrap executes automatically if HB30 is still absent
```

### ESCALATED / AUTHORITY-OWNED

```text
manual_execution_allowed: false
worker_registry_ref: StegVerse-Labs/TV + StegVerse-Labs/TVC
collision_scope: credential and route authority only; heartbeat initial-carrier bootstrap requires no credential
release_condition: unchanged TV/TVC authority boundary remains satisfied with credential requirement NONE
next_executable_action: none for this repair
```

### COMPLETED / SUPERSEDED

```text
manual_execution_allowed: false
worker_registry_ref: control/session-integration-claim-2026-08-17-hb29-state-transition-carrier.json + StegVerse-Labs/.github#220/#221
collision_scope: prior PR #206 transition producer remains retained; the assumption that producer presence alone made HB29→HB30 reachable is superseded
release_condition: source startup deadlock repair merged in PR #221
next_executable_action: use the retained producer through the merged normal worker-runtime startup path
```

## Completion accounting

```text
developed_files: 4/4
scaffolding_or_stubs: 0
missing_required_files: 0
source_implementation: COMPLETE_MERGED
focused_validation: 4/4 PASS
integration: 1/1 MERGED
activation: 0/1 pending real HB30 observation
session_consolidation: COMPLETE_TRANSFERRED
```
