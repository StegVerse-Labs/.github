# Sovereign Heartbeat Deployment Mirror Handoff

## Active goal

```text
goal_id: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
originating_session_goal: remove GitHub and all third-party deployment/scheduler platforms from heartbeat production activation; GitHub may remain source/evidence only and must never be a production blocker
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_owner: StegVerse-Labs/.github#12
implementation_claim: CLAIMED_FOR_IMPLEMENTATION
validation_claim: CLAIMED_FOR_VALIDATION
claim_creation_time: 2026-08-09T19:27:00Z
claim_release_condition: native installer/capsule path validates on runtime v9 at high-frequency cadence and all unique requirements are transferred to issue #12 plus the canonical organization handoff
```

## Authority and collision boundaries

This handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and narrows only the sovereign deployment path for `SHWP-DURABLE-RUNTIME-ACTIVATION`. It does not create a second heartbeat, worker registry, scheduler, deployment authority, or Master Records authority.

GitHub, GitHub Actions, Render, Cloudflare, Vercel, hosted inference providers, and other third-party platforms may be used as source mirrors or validation/evidence surfaces only. Their availability is never a production activation dependency or blocker.

Canonical runtime authority remains:

```text
heartbeat_runtime.engine_v9.HeartbeatRuntime
scripts/run_heartbeat_runtime.py
control/worker-registry.json
control/heartbeat-subsignals.json#worker_coordination
```

## Sovereign deployment contract

A production StegVerse node receives an already-present local runtime source/capsule and materializes it to durable node-local storage. Native OS process supervision provides liveness only. `HeartbeatRuntime` owns the heartbeat cycle and worker-coordination subsignal.

Required invariants:

```text
network_fetch_required: false
third_party_deployment_required: false
third_party_scheduler_required: false
third_party_process_host_required: false
canonical_runtime: engine_v9
heartbeat_default_interval_ms: 10.0
nominal_cycles_per_second: 100
worker_lease_clock: canonical_heartbeat_cycle
wall_clock_worker_expiry_authority: false
master_records_role: custody_and_reconstruction_only
```

## Completed work

The previous sovereign installer already materializes an already-present source tree and registers the continuous runner with systemd user service, macOS LaunchAgent, or Windows logon task. No provider network fetch is required after materialization.

## Incomplete work

1. Reconcile the installer from legacy `engine_v8`/250 ms assumptions to canonical runtime v9 and 10 ms default cadence.
2. Add deterministic node-local activation verification that proves the materialized runtime is provider-independent before service registration.
3. Update tests and issue #12/handoffs so GitHub-hosted validation is evidence only and cannot block activation.
4. Preserve `SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED` as the only production activation block until a StegVerse-owned/federated execution node exposes direct runtime evidence.

## Cross-repository convergence

```text
MERGED INTO: StegVerse-Labs/.github#12
MERGED INTO: StegVerse-002/micro-node-runtime#16 for ecosystem-wide external-platform retirement
Master Records custody: master-records/orchestration/WORKER_LIFECYCLE_CUSTODY_MIRROR_HANDOFF.md
legacy provider host: master-records/monitoring/MONITORING_MIRROR_HANDOFF.md (SUPERSEDED)
```

No duplicate implementation is authorized in `master-records/monitoring`; its Render path is historical diagnostic only.

## Validation commands

```bash
python -m py_compile scripts/install_sovereign_heartbeat_service.py scripts/run_heartbeat_runtime.py
python -m unittest -v tests.test_sovereign_heartbeat_service
python -m unittest -v tests.test_worker_coordination_subsignal
```

## Archive conditions

This session-specific correction is transferable when the installer/tests/handoffs are merged to main, issue #12 records the no-third-party deployment invariant, and the remaining production observation is durably machine-owned by `SHWP-DURABLE-RUNTIME-ACTIVATION` / `StegVerse-002/micro-node-runtime#16` with a machine-observable release condition.

## Completion metrics

```text
required developed files: 4
currently complete: 1
validation groups: 3
currently validated: 0
integration obligations: 3
currently integrated: 1
session goals transferred/completed: 2/4
scaffolding_or_stubs: 0
```
