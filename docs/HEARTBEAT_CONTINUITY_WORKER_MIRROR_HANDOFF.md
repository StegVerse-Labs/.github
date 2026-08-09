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
session_continuation_workers_active: true
```

Two facts must remain separate:

1. **Heartbeat-owned worker execution has occurred and now owns the remaining session-specific activation work.** Real workers are claimed, bound, fenced, heartbeat-timed, cycle-leased, invoked, checkpointed and rechecked through the canonical registry.
2. **Durable continuously running production heartbeat and real sovereign LLM execution on a StegVerse-owned/federated node are not yet directly observed.** Those are remaining product/runtime proofs. GitHub Actions, Render, Cloudflare, Vercel, hosted inference, or other third-party runtime state cannot satisfy or block these proofs.

## Active worker continuation evidence

The canonical registry/status projection at heartbeat epoch 17 records `activation_required_count=0` because all currently admitted session-specific continuation tasks have active executor bindings.

### Sovereign heartbeat/runtime activation worker

```text
task_id: SHWP-DURABLE-RUNTIME-ACTIVATION
worker_id: sovereign-runtime-activation-worker
worker_instance_id: sovereign-runtime-activation-worker-HB15-G18
claim_id: SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18
fencing_token: 18
state: BLOCKED
current_transition: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
expected_next_transition: SOVEREIGN_RUNTIME_RECHECK
heartbeat_epoch: 17
heartbeat_timing_established: true
executor_binding: BOUND
executor_resolved: true
expiry_epoch: 4111
checkpoint: checkpoints/workers/SHWP-DURABLE-RUNTIME-ACTIVATION/HB17-G18.json
receipt: receipts/sovereign-runtime-activation/SHWP-DURABLE-RUNTIME-ACTIVATION.json
issue: StegVerse-Labs/.github#59
```

This worker rechecks node-local sovereign activation evidence on admitted heartbeat cycles and completes only when the nine direct runtime/restart predicates are true. Its BLOCKED state is expected and fail-closed; it is not an inactive or merely documented task.

### Ecosystem Chat sovereign inference activation worker

```text
task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
worker_id: ecosystem-chat-sovereign-inference-worker
worker_instance_id: ecosystem-chat-sovereign-inference-worker-HB17-G20
claim_id: SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20
fencing_token: 20
state: BLOCKED
current_transition: SOVEREIGN_LLM_INFERENCE_RUNTIME_NOT_YET_OBSERVED
expected_next_transition: SOVEREIGN_INFERENCE_RECHECK
heartbeat_epoch: 17
heartbeat_timing_established: true
executor_binding: BOUND
executor_resolved: true
expiry_epoch: 4113
checkpoint: checkpoints/workers/SHWP-ECOSYSTEM-CHAT-INFERENCE-001/HB17-G20.json
receipt: receipts/ecosystem-chat-sovereign-inference/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json
issue: StegVerse-Labs/.github#60
consumer: StegVerse-org/LLM-adapter#18
```

This worker is active independently of the runtime worker so it can observe/recheck inference readiness while the sovereign node carrier remains blocked. It completes only after a real StegVerse-local/private model execution, sovereign E1→worker→E2 response transport, measured usage, and same-execution Master Records provider-usage plus transition reconstruction all pass.

### Existing organization-federation worker

```text
task_id: SHWP-ALL-ORG-FEDERATION-001
worker_id: organization-federation-readiness-worker
worker_instance_id: organization-federation-readiness-worker-HB11-G17
claim_id: SHWP-SHWP-ALL-ORG-FEDERATION-001-G17
fencing_token: 17
state: BLOCKED
expected_next_transition: FEDERATION_RECHECK
heartbeat_timing_established: true
executor_binding: BOUND
```

This worker remains the all-organization readiness observer; blocked organization rows stay machine-owned rather than becoming silent success.

Historical and current worker evidence is inspectable under `receipts/`, `checkpoints/`, `events/`, `control/worker-registry.json`, `control/worker-status.json`, `control/heartbeat-state.json`, and `control/heartbeat-subsignals.json`.

## StegVerse-only production host

Canonical production surfaces:

```text
heartbeat_runtime/engine_v9.py
scripts/run_heartbeat_runtime.py
scripts/install_sovereign_heartbeat_service.py
workers/sovereign_runtime_activation_worker.py
workers/ecosystem_chat_sovereign_inference_worker.py
tests/test_sovereign_heartbeat_service.py
docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json
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

The native OS provides process liveness only. Runtime v9 owns heartbeat cadence, worker-control evaluation, claims, fences, cycle leases, checkpoints and carriage of the worker-coordination subsignal.

## Third-party platform classification

GitHub repositories and GitHub Actions may remain source mirrors, review surfaces, validation surfaces, bootstrap evidence, or migration evidence. They are not permitted to own production deployment, scheduling, liveness, recovery, heartbeat timing, worker leasing, model execution, or worker execution authority.

Render/Cloudflare/Vercel resources may remain historical/interoperability evidence. Their availability or credentials are not release conditions for sovereign heartbeat or Ecosystem Chat activation.

The only current session-specific production block classes are:

```text
SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
SOVEREIGN_LLM_INFERENCE_RUNTIME_NOT_YET_OBSERVED
```

Both have active heartbeat workers, explicit machine-observable release conditions and next heartbeat transitions.

## Remaining production activation proof

Heartbeat production activation reaches 100% only after one StegVerse-owned or StegVerse-federated node directly proves:

1. sovereign runtime materialization completed from already-present local source/capsule;
2. native service registration is active;
3. `run_heartbeat_runtime.py --continuous --interval-ms 10.0` is live from durable local storage;
4. heartbeat epochs advance under runtime-v9 timing ownership;
5. the worker-coordination subsignal is carried on consecutive cycles and a heartbeat-owned worker response/checkpoint is produced from that carrier;
6. controlled native-service restart occurs;
7. heartbeat epoch and registry generation do not regress after restart;
8. no duplicate heartbeat, claim, fence, or split-brain state appears;
9. registry/event/cost/receipt/checkpoint/worker-coordination state survives restart/reconstruction.

Ecosystem Chat product activation reaches 100% only after the inference worker additionally observes:

1. a real model process on a StegVerse-owned/federated node;
2. a loopback/private/StegVerse-local inference endpoint only;
3. the sovereign ephemeral E1→worker→E2 execution path;
4. measured provider/model usage persisted;
5. provider-usage reconstruction PASS in Master Records;
6. transition reconstruction PASS for the same execution;
7. `third_party_inference_required=false`.

No manual receipt construction is an archive or release condition.

## Cross-repository continuation

```text
heartbeat/runtime worker owner: StegVerse-Labs/.github#59
inference worker owner: StegVerse-Labs/.github#60
archive worker gate: StegVerse-Labs/.github#61
sovereign migration owner: StegVerse-002/micro-node-runtime#16
inference consumer owner: StegVerse-org/LLM-adapter#18
custody/reconstruction: master-records/orchestration
all-org readiness: SHWP-ALL-ORG-FEDERATION-001
```

`StegVerse-002/micro-node-runtime#16` owns sovereign execution-environment migration and external-platform retirement. It does not become heartbeat timing or worker-execution authority.

Master Records remains custody/reconstruction only through `master-records/orchestration/WORKER_LIFECYCLE_CUSTODY_MIRROR_HANDOFF.md` and must ingest real sovereign runtime/model evidence when produced.

## Session consolidation and archive condition

The originating session's unique requirements are now durable in implementation, worker code, process adapters, capability profiles, cost bases, executable handoffs, registry claims, fences, heartbeat-cycle leases, receipts, checkpoints and cross-repository issues.

The session-specific archive rule is stricter than durable ownership alone:

```text
archive allowed when:
  product activation is complete
  OR
  every unfinished session-specific goal is carried by an ACTIVE canonical heartbeat worker registry claim with executor binding, fence, heartbeat timing, checkpoint, machine-observable release condition and next transition
```

That worker-management condition is now satisfied for the unfinished sovereign runtime and Ecosystem Chat inference goals. Product activation remains below 100%; archival does not mean product activation is complete. It means execution responsibility no longer resides uniquely in the conversation.

## Completion assessment

```text
heartbeat protocol implementation: 100%
worker-coordination cycle-lease implementation: 100%
sovereign host implementation: 100%
ephemeral E1→worker→E2 carrier implementation: 100%
third-party production blocker: REMOVED
sovereign runtime continuation worker: ACTIVE / BLOCKED / RECHECKING
Ecosystem Chat inference continuation worker: ACTIVE / BLOCKED / RECHECKING
all-org federation readiness worker: ACTIVE / BLOCKED / RECHECKING
heartbeat-owned worker execution proof: OBSERVED
durable continuous sovereign runtime: NOT YET OBSERVED
real sovereign LLM execution: NOT YET OBSERVED
heartbeat production activation: 96%
Ecosystem Chat product activation: NOT COMPLETE
session-specific worker continuation activation: 100%
scaffolding_or_stubs_in_required_worker_path: 0
```

Do not report product/runtime activation as 100% until its direct predicates pass. Do not reactivate this conversation merely to poll those predicates; canonical heartbeat workers own the rechecks.
