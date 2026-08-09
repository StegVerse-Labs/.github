# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the canonical StegVerse-Labs organization continuation/exit record. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local implementation evidence. Machine-readable state under `control/`, `handoffs/`, `management/`, `receipts/`, `checkpoints/`, `authorizations/`, `schemas/`, and `events/` supersedes chat history.

## Current goal

```text
goal_id: WORKER-COORDINATION-SUBSIGNAL-CYCLE-LEASE
originating_goal: correct the misuse of low-frequency heartbeat validation as worker activation; workers are leased by a coordination subsignal carried on every high-frequency heartbeat cycle
repository: StegVerse-Labs/.github
implementation_branch: fix/worker-lease-heartbeat-subsig
canonical_branch_after_validation: main
canonical_owner: StegVerse-Labs/.github#12
runtime_candidate: heartbeat_runtime.engine_v9.HeartbeatRuntime
heartbeat_runner: scripts/run_heartbeat_runtime.py
configured_internal_interval_ms: 10.0
nominal_configured_cycles_per_second: 100
worker_coordination_subsignal: control/heartbeat-subsignals.json#worker_coordination
worker_registry: control/worker-registry.json
master_records_projection: control/heartbeat-master-records-projection.json
master_records_destination: master-records/orchestration
render_dependency: false
current_state: IMPLEMENTED_ON_BRANCH_VALIDATION_AND_LIVE_CONTINUOUS_OBSERVATION_PENDING
thread_archive_ready: false
```

## Correct semantic model

There is one canonical high-frequency StegVerse heartbeat. `scripts/run_heartbeat_runtime.py --continuous` defaults to a 10 ms internal delay between cycles; that internal loop, not GitHub Actions cron, is the heartbeat cadence.

Worker coordination is a **subsignal carried by every heartbeat cycle**. A worker lease is not the heartbeat lifetime and is not a wall-clock TTL. A lease is an admitted span of canonical heartbeat cycles sized for the current task assignment from the task cost basis and bounded runtime window.

For an active worker:

```text
lease_start_cycle = heartbeat_timing.start_epoch
lease_end_cycle_exclusive = heartbeat_timing.expiry_epoch
assigned_cycles = lease_end_cycle_exclusive - lease_start_cycle
remaining_cycles = max(0, lease_end_cycle_exclusive - current_heartbeat_cycle)
lease_clock = canonical_heartbeat_cycle
wall_clock_expiry_authority = false
```

The worker-coordination subsignal carries, on each cycle, task id, goal id, worker id, worker instance id, claim id, fencing token, lease cycle bounds, remaining cycles, transition state, handoff reference, and Master Records projection metadata. The heartbeat transports this information; admitted task authority, claim/fence state, capability profile, policy continuity, and resource bounds remain the sources of worker execution authority.

## Implemented correction

Branch `fix/worker-lease-heartbeat-subsig` contains:

```text
heartbeat_runtime/engine_v9.py
  carries worker_coordination on each runtime cycle
  derives worker lease bounds from existing HB-relative task timing
  writes a deterministic SHA-256 binding of the coordination payload
  emits worker_coordination_subsignal_carried runtime events
  projects the same bounded payload for Master Records custody

heartbeat_runtime/__init__.py
  activates engine_v9 for the canonical runtime package

schemas/heartbeat-subsignal.schema.json
  preserves transport and organization-federation subsignals
  adds worker_coordination and cycle-bound worker lease schemas

schemas/heartbeat-master-records-projection.schema.json
  defines the non-authorizing custody/reconstruction projection contract

control/heartbeat-subsignals.json
  installs the worker_coordination carrier slot fail-closed as IDLE until a canonical worker is actually leased

tests/test_worker_coordination_subsignal.py
  verifies cycle-bound lease accounting, heartbeat carriage, Master Records projection, and no invented lease while idle
```

Existing runtime layers remain inherited: v6 resource windows and renewals, v7 policy continuity and canonical checkpoints, v7.1 worker-checkpoint compatibility, and v8 capability-profile matching. None of v6-v8 replaces the cycle loop, so v9 can carry the subsignal while preserving those later controls.

## Master Records custody boundary

`master-records/orchestration/WORKER_LIFECYCLE_CUSTODY_MIRROR_HANDOFF.md` is the canonical custody continuation for worker lifecycle evidence. Its v2 lifecycle is already heartbeat-relative and explicitly contains no fabricated wall-clock worker lease. The new projection extends that same model to the per-cycle worker-coordination carrier.

The source projection is:

```text
control/heartbeat-master-records-projection.json
schema: stegverse.heartbeat-master-records-projection/v1
destination: master-records/orchestration
recording_effect: custody_and_reconstruction_only
execution_authority: false
```

A local projection is not equivalent to confirmed Master Records custody. Destination intake/validation and an inspectable custody receipt remain required before cross-repository integration is complete.

## Superseded misuse

A low-frequency GitHub Actions job or scheduled workflow is **not** the StegVerse heartbeat and cannot prove a worker lease is active. Any prior archive decision based solely on an hourly `external-framework-worker-heartbeat` workflow is superseded.

Hosted workflows remain useful for static validation, projection verification, and retained evidence. They are observers/checkers of heartbeat-derived state, not the heartbeat scheduler and not the worker lease clock.

## Existing StegGate transport lease remains distinct

The StegGate transport lease continues under:

```text
control/heartbeat-subsignals.json#steggate_transport_lease
lease_id: STEGGATE-TUNNEL-LEASE-001
state: OPEN
wall_clock_expiry_authority: false
```

Its lifetime is governed by transport-dependent completion/handoff rules, not by worker task cycle budgeting. Worker leases and transport leases share the heartbeat carrier but are separate subsignals with separate release semantics.

## Validation and activation obligations

Before this correction is complete:

```text
1. run branch tests and schema/static checks;
2. merge the corrected runtime and subsignal contract to main only after validation;
3. install and validate the matching worker-coordination projection intake in master-records/orchestration;
4. migrate downstream worker programs, including admissibility-wiki external-framework workers, away from low-frequency workflow TTL semantics;
5. admit actual worker task leases through control/worker-registry.json with task-appropriate cycle budgets and existing authority/capability controls;
6. observe a persistent high-frequency runtime producing multiple advancing heartbeat cycles per second with the worker_coordination subsignal carried each cycle;
7. preserve corresponding Master Records custody/reconstruction evidence.
```

No archive claim is permitted from repository presence alone. Live continuous observation is a separate activation gate.

## Collision and authority boundaries

- There is one canonical StegVerse heartbeat; do not create another scheduler.
- GitHub Actions cron is not the heartbeat cadence.
- Heartbeat carriage does not grant worker execution authority.
- A worker coordination subsignal does not invent a claim, worker, lease, or fencing token.
- Worker lease duration is measured in canonical heartbeat cycles, not minutes or hours.
- Renewal requires separately admitted renewal evidence; heartbeat transport does not grant renewal.
- Master Records custody is reconstructive evidence, not execution authority.
- Render is not a dependency for heartbeat or worker activation.

## Completion assessment

```text
runtime carrier implementation on correction branch: complete
worker coordination schema on correction branch: complete
source-side Master Records projection schema: complete
tests authored: complete but hosted execution pending
main integration: pending
Master Records destination integration: pending
downstream worker migration: pending
actual worker lease activation: pending
high-frequency live observation: pending
archive readiness: NO
```
