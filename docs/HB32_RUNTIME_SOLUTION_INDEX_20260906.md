# HB32 Runtime Solution Index — 2026-09-06

This index is a continuation aid for runtime failures. It does not create authority or a new runtime path.

When a resident runtime symptom appears, inspect and reuse these existing solutions before proposing new implementation:

1. `heartbeat_runtime.independent_oscillator` — canonical HB32 independent oscillator/reference producer.
2. `heartbeat_runtime.engine_v13.HeartbeatRuntime` — canonical non-authorizing carrier.
3. `scripts/install_sovereign_heartbeat_carrier.py` — carrier-only native installer; activation requires persisted oscillator epoch progression.
4. `scripts/repair_resident_worker_presence.py` — carrier-owned WorkerCoordinator self-heal.
5. `heartbeat_runtime.runtime_presence_projection.py` — canonical worker-cycle freshness/presence semantics.
6. `scripts/restart_sovereign_ephemeral_node.py::_terminate` — controlled worker-only termination used for previously proven stale WorkerCoordinator recycling.
7. `scripts/refresh_sovereign_worker_runtime_source.py` — already-local source refresh; no network source fetch.
8. `scripts/run_worker_runtime.py --continuous` — canonical resident WorkerCoordinator runtime.
9. `scripts/dispatch_resident_execution_requests.py` — existing resident request dispatcher.
10. Task-specific resident consumers such as `scripts/consume_hil_resident_execution_request.py` — exact request consumption; request intent does not grant authority.

Current failure classes already covered:

- carrier entrypoint cannot resolve repository package -> direct CLI package-resolution repair;
- supervisor reports start but oscillator did not progress -> fail closed until persisted epoch progression;
- WorkerCoordinator missing -> existing HB carrier self-heal starts canonical worker;
- WorkerCoordinator previously proven but stale/non-task-capable -> existing controlled worker-only recycle (PR #1084);
- newly spawned WorkerCoordinator alive but first tick delayed by pre-cycle resident work -> pending-first-tick retention (`HB32-SELF-HEAL-STARTUP-GRACE-002`);
- resident source missing a corrected worker/runtime module -> existing local-only source refresh/materialization parity repairs;
- task runtime absent at a downstream lane -> route through the existing HB/oscillator self-heal and resident dispatcher before creating another runtime.

Authority remains separated: HB/oscillator is timing/reference/supervision only; WorkerCoordinator owns claim/fence/admission; InTr/Interlock owns governed transitions; TV/TVC owns credentials. Source/CI never substitutes for authentic runtime evidence.
