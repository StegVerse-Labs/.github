# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/runtime activation goal.

## Active goal

```text
goal_id: SOVEREIGN-HEARTBEAT-PRODUCTION-ACTIVATION
repository: StegVerse-Labs/.github
branch: main
canonical_owner: StegVerse-Labs/.github#12
canonical_runtime: heartbeat_runtime.engine_v9.HeartbeatRuntime
activation_carrier: single_stegverse_heartbeat
heartbeat_default_interval_ms: 10.0
nominal_cycles_per_second: 100
worker_coordination_subsignal: control/heartbeat-subsignals.json#worker_coordination
worker_lease_clock: canonical_heartbeat_cycle
third_party_deployment_dependency: NONE
third_party_scheduler_dependency: NONE
third_party_process_host_dependency: NONE
heartbeat_owned_worker_execution_observed: true
durable_continuous_sovereign_runtime_observed: false
production_activation_percent: 96
```

Two facts must remain separate:

1. **Heartbeat-owned worker execution has occurred.** Real workers have been claimed, bound, fenced, heartbeat-timed, cycle-leased, invoked and receipted through the canonical registry.
2. **Durable continuously running production heartbeat on a StegVerse-owned/federated node is not yet directly observed.** That is the remaining production-activation proof. GitHub Actions, Render, Cloudflare, Vercel, or other third-party runtime state cannot satisfy or block this proof.

## Activated worker evidence

Worker coordination is now carried by runtime v9 as a heartbeat subsignal. Canonical organization evidence includes the federation worker lease:

```text
task_id: SHWP-ALL-ORG-FEDERATION-001
worker_id: organization-federation-readiness-worker
worker_instance_id: organization-federation-readiness-worker-HB11-G17
claim_id: SHWP-SHWP-ALL-ORG-FEDERATION-001-G17
fencing_token: 17
lease_start_cycle: 11
lease_end_cycle_exclusive: 267
assigned_cycles: 256
lease_clock: canonical_heartbeat_cycle
```

Historical worker evidence remains inspectable under `receipts/`, `checkpoints/`, `events/`, `control/worker-registry.json`, `control/worker-status.json`, and `control/heartbeat-state.json`.

## StegVerse-only production host

Canonical production surfaces:

```text
heartbeat_runtime/engine_v9.py
scripts/run_heartbeat_runtime.py
scripts/install_sovereign_heartbeat_service.py
tests/test_sovereign_heartbeat_service.py
docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
```

The installer materializes an already-present canonical source tree or locally delivered StegVerse runtime capsule onto durable node-local storage and registers `run_heartbeat_runtime.py --continuous --interval-ms 10.0` directly with the node OS service manager.

Supported native liveness supervisors:

```text
Linux: systemd user service
macOS: LaunchAgent
Windows: logon scheduled task
```

After materialization:

```text
network_fetch_required: false
third_party_process_host_required: false
third_party_deployment_required: false
third_party_scheduler_required: false
github_runtime_dependency: false
render_runtime_dependency: false
cloudflare_runtime_dependency: false
heartbeat_timing_authority: heartbeat_runtime.engine_v9.HeartbeatRuntime
worker_lease_clock: canonical_heartbeat_cycle
wall_clock_worker_expiry_authority: false
execution_authority_effect: NONE
```

The native OS provides process liveness only. Runtime v9 owns heartbeat cadence, worker-control evaluation, and carriage of the worker-coordination subsignal.

## Third-party platform classification

GitHub repositories and GitHub Actions may remain source mirrors, review surfaces, or validation/evidence sources. Render/Cloudflare/Vercel resources may remain historical or interoperability evidence. None is permitted to own or block production deployment, scheduling, liveness, recovery, heartbeat timing, worker leasing, or worker execution authority.

The stale provider-quota blocker was removed from `management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json`. The only remaining block class is:

```text
SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
```

## Remaining production activation proof

Production activation reaches 100% only after one StegVerse-owned or StegVerse-federated node directly proves:

1. sovereign runtime materialization completed from already-present local source/capsule;
2. native service registration is active;
3. `run_heartbeat_runtime.py --continuous --interval-ms 10.0` is live from durable local storage;
4. heartbeat epochs advance under runtime-v9 timing ownership;
5. the worker-coordination subsignal is carried on consecutive cycles and a heartbeat-owned worker response/checkpoint is produced from that carrier;
6. controlled native-service restart occurs;
7. heartbeat epoch and registry generation do not regress after restart;
8. no duplicate heartbeat, claim, fence, or split-brain state appears;
9. registry/event/cost/receipt/checkpoint/worker-coordination state survives restart/reconstruction.

```text
block_class: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
owner: StegVerse-002/micro-node-runtime#16
canonical_execution_handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
release_condition: one StegVerse-owned/federated node executes the sovereign host and passes all nine criteria
GitHub required after materialization: false
GitHub availability may block activation: false
Render required: false
Cloudflare required: false
Vercel required: false
human procurement/provider authority required: false
```

## Cross-repository continuation

`StegVerse-002/micro-node-runtime#16` owns sovereign execution-environment migration and external-platform retirement. It does not become heartbeat timing or worker-execution authority.

Master Records remains custody/reconstruction only through `master-records/orchestration/WORKER_LIFECYCLE_CUSTODY_MIRROR_HANDOFF.md` and must ingest real sovereign runtime evidence when produced.

`master-records/monitoring/MONITORING_MIRROR_HANDOFF.md` marks the former Render host path `SUPERSEDED_BY_SOVEREIGN_HOST`; it must not be revived as a production dependency.

## Session consolidation

Unique no-third-party deployment requirements from the originating session are durably transferred to:

```text
docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
StegVerse-Labs/.github#12
StegVerse-002/micro-node-runtime#16
```

## Completion assessment

```text
heartbeat protocol implementation: 100%
worker-coordination cycle-lease implementation: 100%
sovereign host implementation: 100%
third-party deployment blocker: REMOVED
third-party scheduler blocker: REMOVED
third-party process-host blocker: REMOVED
heartbeat-owned worker execution proof: OBSERVED
durable continuous sovereign runtime: NOT YET OBSERVED
production activation: 96%
scaffolding_or_stubs_in_required_host_path: 0
```

Do not report production activation as 100% until the nine direct sovereign-node activation predicates pass.
