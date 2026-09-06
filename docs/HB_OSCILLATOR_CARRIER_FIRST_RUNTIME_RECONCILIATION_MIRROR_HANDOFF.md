# HB Oscillator Carrier-First Runtime Reconciliation Mirror Handoff

Updated: 2026-09-06
Issue: #1091
State: SOURCE_REPAIR_IN_VALIDATION
Authority effect: NONE_SOURCE_COORDINATION_ONLY
Credential authority: TV/TVC
GitHub token runtime authority: NONE

## Problem resolved in source

The canonical HB/oscillator runtime had already established two reusable runtime solutions:

1. `HEARTBEAT-OSCILLATOR-RESIDENT-START-012`: direct carrier-only native startup through `scripts/install_sovereign_heartbeat_carrier.py`, with no WorkerCoordinator startup prerequisite.
2. `RESIDENT_WORKER_SELF_HEAL`: after oscillator-produced carrier references exist, `scripts/run_heartbeat_runtime.py` invokes `scripts/repair_resident_worker_presence.py` downstream to restore/observe the existing task-capable WorkerCoordinator without creating a second worker, scheduler, heartbeat, or authority plane.

The durable sovereign bootstrap and activation verifier had drifted behind those solutions. Bootstrap still entered the combined carrier+worker installer, and the verifier still required the combined activation receipt and restarted both carrier and WorkerCoordinator directly.

## Corrected source sequence

```text
existing engine_v13 carrier-only installer
→ validate carrier-activation.latest.json
→ oscillator-produced references exist
→ existing carrier-side WorkerCoordinator self-heal/presence evidence
→ existing resident request dispatch / WorkerCoordinator admission
→ carrier-first sovereign activation verifier
→ controlled carrier-only restart
→ require carrier reconstruction plus independent worker progress after restart
```

The carrier installer must prove:
- `activation_scope=CARRIER_ONLY`;
- `carrier_active=true`;
- `worker_start_attempted=false`;
- `worker_runtime_dependency_for_carrier_start=false`;
- oscillator production is `OSCILLATOR_PHASE_DRIVEN`, 10 ms / 100 Hz, `OSCILLATOR_ONLY`;
- no network, hosted process host, hosted scheduler, GitHub runtime, or credential dependency;
- canonical runtime is `heartbeat_runtime.engine_v13.HeartbeatRuntime`;
- credential authority remains TV/TVC.

The activation verifier no longer treats direct WorkerCoordinator restart as part of heartbeat restart. It restarts only the existing carrier-native supervision entry and requires independently observed WorkerCoordinator presence/progress afterward.

## Preserved boundaries

- HB/oscillator grants no execution, admission, claim/fence, credential, routing, transition, custody, publication, receiving, or consequence authority.
- WorkerCoordinator remains the existing task admission/claim/fence authority.
- Interlock/InTr remains transition/admissibility authority.
- TV/TVC remains sole credential authority.
- No second WorkerCoordinator, scheduler, heartbeat, oscillator, carrier, provider, or host is created.
- No second user-operated machine is introduced.
- Source, CI, merge, or receipt schema presence does not prove authentic resident runtime activation.

## README impact

Material README impact: REQUIRED. This correction changes effective bootstrap ordering, restart/failure behavior, and activation-evidence interpretation. The repository README must be updated in the same PR before merge.

## Runtime evidence still required after merge

Authentic activation remains unproved until a sovereign resident execution produces all required current-runtime predicates, including carrier epoch advancement, independent task-capable WorkerCoordinator progress, controlled carrier-only restart/reconstruction, no duplicate claim/fence, and retained runtime proof.