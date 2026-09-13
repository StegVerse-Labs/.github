# Site ECE / Healer Carrier Deadlock Repair Reconciliation

Goal Task: `SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001`
COSV: `71000000102000`
Shared carrier task: `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`

The first absent state-transition cause was identified in the existing standing Healer scheduler carrier, not in ECE publication logic.

Before this repair, `scripts/consume_healer_sovereign_scheduler_request.py` required the resident runtime to already contain `control/resident-execution-request.d/healer-sovereign-scheduler-001.json`. When that runtime copy was absent or stale, the consumer could return `NO_REQUEST` and never invoke the scheduler. That created a circular dependency because the scheduler is itself a carrier for reusable source-refresh work.

The repair reuses the existing carrier and authority model:

- resolve the distinct already-local canonical source root;
- validate the canonical standing request;
- exact-synchronize that non-authorizing request into the resident runtime when missing or stale;
- execute the canonical source copy of `scripts/refresh_and_execute_resident_task.py` so stale runtime source is refreshed before targeted WorkerCoordinator execution;
- retain WorkerCoordinator as sole claim/fence owner;
- retain Interlock/InTr as transition authority;
- retain TV/TVC as credential authority;
- retain KV/SKAP Vault as sole user-verification authority.

No second scheduler, executor, device-verification process, repository-writeback runtime, or synthetic evidence path is introduced.

This repair changes source reachability only. `AUTHENTIC_SITE_SAFE_PROJECTION_MATERIALIZED` and `SITE_LIVE_CONTINUITY_PROJECTION_OBSERVED` remain unsatisfied until authentic runtime evidence proves them.
