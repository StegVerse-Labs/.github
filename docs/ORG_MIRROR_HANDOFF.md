# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the canonical StegVerse-Labs organization continuation/exit record. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local implementation evidence. Machine-readable state under `control/`, `handoffs/`, `management/`, `receipts/`, `checkpoints/`, `authorizations/`, and `schemas/` supersedes chat history.

## Current goal

```text
goal_id: STEGGATE-TUNNEL-LEASE-CONTINUITY
repository: StegVerse-Labs/.github
branch: main
canonical_owner: StegVerse-Labs/.github#12
single_heartbeat_runtime: heartbeat_runtime.engine_v8.HeartbeatRuntime
transport_signal: control/heartbeat-subsignals.json#steggate_transport_lease
render_dependency: false
current_state: LIVE_LEASE_OPEN
thread_archive_ready: false
```

The older `LIVE-WORKER-RUNTIME-ACTIVATION` goal remains complete: documented workers were actually claimed/executed through the heartbeat and worker registry. The current goal is narrower and newer: correct StegGate transport continuity so a heartbeat is the **carrier of lease subsignals**, not the lease lifetime itself.

## Canonical lease correction

A StegGate tunnel lease is not per heartbeat. Heartbeat epochs provide ordered signaling and observation. The lease persists across heartbeats and is regulated by a dedicated subsignal.

Canonical surfaces:

```text
schemas/heartbeat-subsignal.schema.json
control/heartbeat-subsignals.json
scripts/manage_heartbeat_subsignal.py
.github/workflows/steggate-heartbeat-integration.yml
StegVerse-Labs/StegCore/.github/workflows/steggate-heartbeat-worker-reusable.yml
```

Current subsignal:

```text
kind: transport_lease
lease_id: STEGGATE-TUNNEL-LEASE-001
state: OPEN
lease_action: EXTEND
opened_epoch: 10
wall_clock_expiry_authority: false
```

A lease releases only when one of these governed conditions is observed:

```text
1. explicit CLOSE for the current lease;
2. an accepted successor lease is available for handoff;
3. all declared tunnel-dependent tasks are terminal.
```

Host/runtime time limits may require carrier reconstruction, but do not terminate or redefine the governed lease.

## Dependent-task lifecycle

`scripts/manage_heartbeat_subsignal.py` is the canonical mutation surface for lease participation and lifecycle intent. It supports:

```text
register     add a tunnel-dependent task idempotently
unregister   remove a task from the lease
open         request a named lease opening at a heartbeat epoch
extend       preserve/reconstruct an admitted open lease
close        request governed closure
handoff      declare a distinct successor lease and HANDOFF_READY state
```

The manager rejects duplicate task membership, invalid transitions, wall-clock lease authority, and authority-bearing subsignals. Task completion only participates in automatic release when at least one dependent task is declared; an empty dependent set does not collapse an open lease.

Implementation commit: `26540ef445a90e80b5adfefcf211b735226e33ea`.

## Live activation proof

The lease-bearing integration path is executing successfully.

```text
workflow run: 31325697942
heartbeat job: 93275589574 SUCCESS
heartbeat epoch persisted: 10
micro-node job: 93275629397 IN_PROGRESS
transport opening: SUCCESS
complete public StegGate acceptance: SUCCESS
current micro-node step: Hold and self-heal tunnel under heartbeat lease subsignal
```

Durable lease receipt:

```text
receipts/steggate-transport-lease/STEGGATE-TUNNEL-LEASE-001.json
state: OPEN
runtime_state: LEASE_HOLD_SELF_HEAL_IN_PROGRESS
lease_is_per_heartbeat: false
render_dependency: false
```

This is the decisive semantic proof: the micro-node did not terminate when heartbeat epoch 10 completed. The heartbeat job completed and persisted its epoch while the transport carrier remained active under the lease subsignal.

## Implementation commits

```text
00adef98237b692e65387cffc089cd0602bc8495  define heartbeat subsignal schema
09100d98efe0b043c4382c98727180cf79f76fc0  emit lease subsignal after reusable contract update
2f13e7472377185250c4365460468111a95ea356  bind heartbeat integration to lease + safe persistence rebase
429fb3eac002b4176194abe48931b13964f638c6  persist observed lease-opening receipt
7d073bf302c2c905cb366a59deffa57edb375b76  advance subsignal to OPEN / EXTEND
26540ef445a90e80b5adfefcf211b735226e33ea  install dependent-task/lease lifecycle manager

StegVerse-Labs/StegCore:
229e8c99b77f8965fb3f07eea62d320d2d6d1ec6  lease-bound self-healing reusable micro-node
246e531c1fe26516ee70ef420c67706105f27fe3  reconcile StegCore handoff
```

## Prior worker activation retained

The existing heartbeat worker evidence remains valid and independent of the transport lease correction. The stable-rendezvous worker is claimed/bound and continues to fail closed on missing credential values for the optional named route. That provider-specific route is not an activation dependency for the zero-credential StegGate tunnel.

## Collision and authority boundaries

- There is one canonical StegVerse heartbeat; do not create another scheduler.
- Heartbeat cadence does not grant execution authority.
- Lease state does not grant StegGate policy/execution authority.
- Render is non-authoritative and must not gate StegGate runtime activation.
- A host envelope ending requires lease reconstruction/extension; it does not imply lease expiry.
- Tunnel-dependent task membership is durable and machine-readable before task completion may authorize lease release.

## Remaining work

```text
StegVerse-Labs/.github
  1. make successor-lease acceptance/handoff machine-observable across carriers;
  2. preserve a reconstruction signal when a carrier host envelope ends before the lease releases;
  3. validate the active lease across at least one successor/reconstruction opening.

StegVerse-Labs/StegCore
  1. retain current fail-closed endpoint health semantics;
  2. preserve lease runtime evidence when the current carrier eventually releases/reconstructs.
```

No user/manual action is assigned.

## Completion assessment

```text
prior worker activation goal: 100%
lease semantics contract/install: 100%
first live lease opening: 100%
dependent-task lifecycle control: 100% installed
successor/reconstruction proof: pending
scaffolding/stubs in completed runtime path: 0
archive readiness for current lease-correction goal: NO
```
