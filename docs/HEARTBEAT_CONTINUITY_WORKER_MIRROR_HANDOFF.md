# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/continuity implementation. `management/SHWP_SESSION_EXECUTION_INVENTORY.json` remains the machine-readable session inventory.

No conversation, GitHub Actions schedule, GitHub-hosted process, Render service, cloud queue, cron service, or other third-party deployment/scheduler is normative heartbeat authority.

## Goal and claim state

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
repository: StegVerse-Labs/.github
branch: feat/sovereign-heartbeat-host -> main
canonical_owner: issue #12
protocol_implementation: COMPLETE
protocol_validation: COMPLETE
runtime_activation_task: SHWP-DURABLE-RUNTIME-ACTIVATION
runtime_activation_state: IMPLEMENTED_PENDING_LIVE_SOVEREIGN_NODE_OBSERVATION
runtime_activation_claim: CLAIMED_FOR_INTEGRATION
runtime_activation_worker: NONE_LIVE_YET
third_party_deployment_dependency: REMOVED_FROM_CANONICAL_PATH
third_party_scheduler_dependency: NONE
human_authority_required: false
session_state: ACTIVE_DISTINCT_INTEGRATION_ROLE
production_activation_complete: false
```

## Canonical runtime

`heartbeat_runtime.engine_v8.HeartbeatRuntime` remains the single production runtime. One heartbeat owns epoch progression, worker-relative timing, HANDOFF/registry evaluation, transition/coherence observations, recovery, canonical checkpoints and successor state. Heartbeat never grants execution, renewal, policy-change, authority-expansion, deployment, procurement or human-decision authority.

The runtime cadence is internal to `scripts/run_heartbeat_runtime.py --continuous`. The process host supplies liveness only.

## StegVerse-native host path

The former Render-host activation path is superseded as the canonical production path because third-party deployment infrastructure may not be a StegVerse activation dependency.

Installed source:

```text
scripts/install_sovereign_heartbeat_service.py
tests/test_sovereign_heartbeat_service.py
```

The installer:

1. materializes the already-present canonical heartbeat implementation onto durable local StegVerse node storage;
2. performs no GitHub/network fetch at runtime materialization;
3. copies runtime, control, HANDOFF, authorization, worker, schema, checkpoint, event, receipt, heartbeat and cost-basis state locally;
4. registers `run_heartbeat_runtime.py --continuous` directly with the node host OS using a systemd user service, macOS LaunchAgent, or Windows logon task;
5. uses native restart supervision only for process liveness;
6. leaves cadence and worker-control decisions exclusively with runtime v8;
7. records materialization/activation receipts under the local runtime root;
8. grants no execution authority and requires no third-party deployment/scheduler after materialization.

This is compatible with StegVerse portable-node deployment: the physical execution environment may be any StegVerse-owned or StegVerse-federated node. GitHub may remain a source/evidence mirror, but its availability is not required for the installed runtime to continue executing.

## Superseded provider path

The prior `master-records-heartbeat-host` Render service, Render Key Value state, and bootstrap retry workflow are retained only as historical/diagnostic evidence. `PROVIDER_BUILD_PIPELINE_CAPACITY` is no longer an admissible canonical activation blocker. `master-records/monitoring#2` must be reconciled as SUPERSEDED_BY_SOVEREIGN_HOST for heartbeat process hosting; Master Records remains evidence/custody/reconstruction authority, not process hosting authority.

## Activation completion criteria

Production activation reaches 100% only after direct evidence from a StegVerse-owned/federated node proves all of:

1. the sovereign materialization receipt exists with `third_party_deployment_required=false` and `third_party_scheduler_required=false`;
2. the native service registration is active;
3. `scripts/run_heartbeat_runtime.py --continuous` is a live process from the materialized local runtime root;
4. heartbeat epoch advances above the preactivation epoch under runtime-v8 ownership;
5. `SHWP-HOST-SELF-ATTEST-001` is claimed/executed/completed by the heartbeat and its receipt is durable;
6. the native service is deliberately restarted;
7. heartbeat epoch and worker-registry generation are preserved or incremented after restart;
8. no duplicate heartbeat, claim, fence or split-brain state is observed;
9. registry/event/cost/receipt/checkpoint state survives restart from local durable StegVerse storage.

## Machine-observable blocker

```text
block_class: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
owner: StegVerse-Labs/.github#12
release_condition: a StegVerse-owned/federated node executes the installed sovereign service and satisfies all nine activation criteria
next_executable_action: bind the materialized runtime to the next available StegVerse portable/micro-node execution environment and run the restart/self-attestation proof
GitHub availability required: false
Render availability required: false
third-party hosting required: false
```

## Validation

Protocol implementation remains 100%/hosted-green from the prior canonical runtime validation. The sovereign-host implementation adds deterministic validation that materialization is network-independent, native service registration invokes the continuous runtime directly, third-party deployment/scheduler flags are false, and host activation grants no execution authority.

## Cross-repository integration

- `StegVerse-002/micro-node-runtime#16` already owns sovereign platform migration and is the canonical StegVerse-only migration workstream for external operational dependencies.
- `StegVerse-org/LLM-adapter` already proves zero-touch portable-node autostart across Linux/macOS/Windows; the heartbeat installer intentionally follows the same native-host pattern without making LLM-adapter heartbeat authority.
- `master-records/orchestration` remains custody/reconstruction authority.
- `master-records/monitoring#2` legacy Render-host bootstrap must be marked superseded for production activation.

## Completion assessment

```text
heartbeat protocol implementation: 100%
developed protocol files/surfaces: 50/50 = 100%
scaffolding/stubs: 0
protocol validation: 27/27 = 100%
production activation before sovereign-host integration: 27/28 = 96%
sovereign-host implementation: IMPLEMENTED_PENDING_MERGE_AND_LIVE_NODE_PROOF
live worker-runtime execution: NOT_ACTIVE_YET
third-party deployment blocker: REMOVED
remaining blocker: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
```

Do not report production activation as 100% until a StegVerse-owned/federated node proves live continuous execution and restart continuity. Do not reactivate Render/GitHub hosting as a substitute.