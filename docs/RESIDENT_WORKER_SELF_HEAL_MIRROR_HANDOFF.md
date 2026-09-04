# Resident Worker Self-Heal Mirror Handoff

Repository: `StegVerse-Labs/.github`
Parent: `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
State: `SOURCE_IMPLEMENTED / VALIDATION_PENDING`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`

## Failure corrected

A canonical 100 Hz HeartBeat carrier could remain live while the resident WorkerCoordinator process was absent. In that state, already-materialized resident requests could remain `REQUESTED` indefinitely even though the node-presence signal carrier was available.

`REQUESTED` is not an acceptable resting state solely because the worker process disappeared.

## Repair

- `scripts/repair_resident_worker_presence.py`
- `scripts/run_heartbeat_runtime.py`
- `tests/test_resident_worker_presence_self_heal.py`

The oscillator-produced carrier remains non-authorizing. After each 100 observed references (approximately one second), and strictly after those references already exist, the carrier process asks the local supervision layer to verify resident WorkerCoordinator presence.

If the existing worker process is alive, nothing is changed.

If the carrier is alive and the worker is absent, local supervision starts the existing `scripts/run_worker_runtime.py --continuous` process, requires a fresh task-capable worker tick, and persists repaired process-presence evidence. The WorkerCoordinator then visits `scripts/dispatch_resident_execution_requests.py` on its own first logical tick and independently performs all task admission/claim/fence/InTr/TV-TVC checks.

The carrier does **not** grant execution authority. It supplies node-presence evidence used by local supervision. WorkerCoordinator remains the execution/admission runtime; InTr/Interlock remains transition governance; TV/TVC remains credential authority.

## Required invariants

- no second heartbeat;
- no second WorkerCoordinator;
- no second scheduler;
- no second user-operated machine;
- no GitHub runtime authority;
- no hosted runtime repair;
- no non-TV/TVC credential propagation;
- a pulse must exist before worker-presence repair is evaluated;
- a repaired worker is not considered present until a fresh task-capable worker tick is observed;
- pending resident requests are drained only by the restored WorkerCoordinator under their existing fail-closed consumers.

## Runtime consequence

A live canonical carrier plus a dead/missing WorkerCoordinator is now a self-healing runtime state rather than a passive `REQUESTED` backlog state. Authentic task completion still requires each task-specific receipt; this repair does not fabricate those receipts.
