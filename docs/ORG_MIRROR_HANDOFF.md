# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the canonical StegVerse-Labs organization continuation/exit record. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local work. Machine-readable state under `control/`, `handoffs/`, `boundaries/`, `management/`, `events/`, `checkpoints/`, `receipts/`, `authorizations/`, and `schemas/` is authoritative over chat history.

## Active goal and ownership

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
originating_session_goal: make unfinished StegVerse work survive conversation retirement under one internal heartbeat without user/manual restart
repository: StegVerse-Labs/.github
canonical_task_owner: StegVerse-Labs/.github#12
protocol_implementation: COMPLETE
protocol_validation: COMPLETE
runtime_activation_task: SHWP-DURABLE-RUNTIME-ACTIVATION
runtime_activation_state: IMPLEMENTED_PENDING_LIVE_SOVEREIGN_NODE_OBSERVATION
canonical_runtime: heartbeat_runtime/engine_v8.py
canonical_host_installer: scripts/install_sovereign_heartbeat_service.py
third_party_deployment_dependency: NONE
third_party_scheduler_dependency: NONE
legacy_render_host_path: SUPERSEDED_FOR_PRODUCTION
live_worker_runtime: NOT_ACTIVE_YET
```

## Canonical architecture

StegVerse has one heartbeat. `heartbeat_runtime/engine_v8.py`, selected by `heartbeat_runtime/__init__.py`, is the canonical runtime. The same heartbeat is the scheduling, reconciliation, worker-relative timing, transition-measurement and general coordination carrier. There is no second worker heartbeat, GitHub scheduler heartbeat, Render scheduler heartbeat, cron heartbeat or conversation-owned timing plane.

Heartbeat carriage does not grant execution authority. Worker availability/capability/profile match does not grant authority. Policy drift, resource expansion, successor authority expansion, deployment and boundary resolution require separate admitted authority.

## Completed protocol capabilities

The core SHWP implementation is complete: atomic fenced checkout, same-HB worker timing, bounded native process execution, activation-request/authority separation, executor ambiguity refusal, blocked-state rechecks, expiry/renewal/orphan recovery, successor reconstruction, duplicate-lineage quarantine, policy rebind, mutation path/fence enforcement, persistent resource budgets, canonical checkpoints, capability profiles, fail-closed convergence, deterministic status/query surfaces and heartbeat-owned worker self-attestation support.

Canonical promoted-runtime validation remains:

```text
Heartbeat Worker Project 31242636078 / 93066031288 SUCCESS
Heartbeat Worker Project 31242995304 SUCCESS
Org Continuation Check 31260010793 SUCCESS
```

## Sovereign production-host correction

Third-party infrastructure is no longer an allowed production activation dependency for SHWP. The previous Render service/KV/bootstrap path is historical evidence only and is superseded for production execution.

PR #54 installs the StegVerse-native host path:

```text
scripts/install_sovereign_heartbeat_service.py
tests/test_sovereign_heartbeat_service.py
docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
```

The installer materializes all runtime/control/HANDOFF/authorization/worker/state surfaces from an already-present canonical source tree onto durable local StegVerse node storage. It performs no GitHub/network source fetch. It registers the materialized `scripts/run_heartbeat_runtime.py --continuous` directly with the host OS service manager:

```text
Linux: systemd user service
macOS: LaunchAgent
Windows: logon scheduled task
```

The service manager supplies process liveness only. HeartbeatRuntime owns cadence and worker-control decisions. After materialization, GitHub, Render, cloud queues and cloud schedulers are not required for the heartbeat to run.

This is the same sovereign deployment principle already adopted by `StegVerse-002/micro-node-runtime#16` and the portable-node autostart pattern proven by `StegVerse-org/LLM-adapter#17`; neither repository becomes heartbeat authority.

## Legacy provider path

The following resources are retained as historical/diagnostic evidence but are not production prerequisites:

```text
Render service srv-d9s197vavr4c73a8rjjg
Render KV red-d9s17pnavr4c73a8p2ng
master-records/monitoring#2 bootstrap workflow
```

`PROVIDER_BUILD_PIPELINE_CAPACITY` is therefore no longer the canonical SHWP production blocker. `master-records/monitoring#2` should be marked `SUPERSEDED_BY_SOVEREIGN_HOST` for process hosting. Master Records remains custody/reconstruction authority.

## First heartbeat-owned production worker proof

The existing worker proof remains canonical:

```text
task: SHWP-HOST-SELF-ATTEST-001
executor_binding: AUTHORIZED
worker: master-records-host-self-attest-worker / AVAILABLE
adapter: process:host-runtime-self-attest-v1
authorization: authorizations/SHWP-HOST-SELF-ATTEST-001.json
handoff: handoffs/SHWP-HOST-SELF-ATTEST-001.json
worker code: workers/host_runtime_self_attest.py
receipt path: receipts/host-self-attest/SHWP-HOST-SELF-ATTEST-001.json
```

Its name reflects its historical creation location only. It executes through canonical SHWP heartbeat authority and may not gain network/deployment/general-repository authority.

## Current activation release conditions

`SHWP-DURABLE-RUNTIME-ACTIVATION` reaches COMPLETE only when a StegVerse-owned/federated node directly proves:

1. sovereign materialization completed without third-party fetch/deployment;
2. native service registration is active;
3. `run_heartbeat_runtime.py --continuous` is live from the local runtime root;
4. heartbeat epoch advances above preactivation state;
5. `SHWP-HOST-SELF-ATTEST-001` is claimed/executed/completed by heartbeat and receipt is durable;
6. controlled native-service restart occurs;
7. prior durable state is restored and epoch/registry generation do not regress;
8. no duplicate heartbeat/claim/fence/split-brain appears;
9. registry/event/cost/receipt/checkpoint state survives restart.

Current blocker:

```text
class: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
owner: StegVerse-Labs/.github#12
release_condition: one StegVerse-owned/federated node executes the installed sovereign service and passes all nine criteria
GitHub required after materialization: false
Render required: false
human authority required: false
```

## Cross-repository dependencies

- `StegVerse-002/micro-node-runtime#16`: canonical sovereign platform migration owner; candidate StegVerse execution environment, not heartbeat authority.
- `StegVerse-org/LLM-adapter#17`: existing zero-touch native autostart implementation pattern; not heartbeat authority.
- `master-records/orchestration`: evidence/custody/reconstruction authority.
- `master-records/monitoring#2`: legacy provider-host bootstrap to be superseded for production hosting.
- Site / Publisher / admissibility-wiki / stegguardian-wiki: no publication obligation arises solely from heartbeat runtime activation.

## Validation and claims

```text
protocol implementation: 100%
protocol validation: 100%
production goal activation before live sovereign node proof: 96%
sovereign host implementation: PR #54
live worker-runtime execution: NOT_ACTIVE_YET
third-party deployment blocker: REMOVED
current blocker: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
```

## Session consolidation

Canonical continuation remains:

```text
StegVerse-Labs/.github#12
docs/ORG_MIRROR_HANDOFF.md
docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
management/SHWP_SESSION_EXECUTION_INVENTORY.json
control/worker-registry.json
control/worker-status.json
```

Do not report production activation as 100% until direct live sovereign-node worker/restart evidence exists. Do not reactivate GitHub/Render deployment as a substitute.