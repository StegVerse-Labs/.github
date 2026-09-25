# Healer Standing Request Self-Materialization Mirror Handoff

Updated: 2026-09-13

Purpose: remove the circular dependency in the existing sovereign Healer scheduler carrier without creating another scheduler or authority path.

Canonical behavior:

- `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` remains the standing WorkerCoordinator task.
- `control/resident-execution-request.d/healer-sovereign-scheduler-001.json` remains non-authorizing (`NONE_REQUEST_ONLY`).
- The resident consumer may exact-copy that request from an already-local distinct canonical source root when the runtime copy is missing.
- Exact-copying the request grants no claim, fence, credential, transition, publication, or user-verification authority.
- WorkerCoordinator still must independently claim/fence the scheduler task before worker execution.
- Interlock/InTr remains transition authority; TV/TVC remains credential authority; KV/SKAP Vault remains sole user-verification authority.
- No device-verification process or second user-operated machine is introduced.

Failure being repaired:

`consume_healer_sovereign_scheduler_request.py` previously returned `NO_REQUEST` whenever the resident runtime had not already received the standing request. That could prevent the scheduler from running even though that scheduler is itself responsible for driving reusable source-refresh work. The result was a bootstrap circularity.

Required repair:

1. Resolve the existing distinct already-local canonical source root.
2. If the runtime request is missing, validate the canonical source request before copying it.
3. Copy exact request bytes atomically into the resident runtime.
4. Re-read and validate the runtime copy.
5. Continue through the existing `refresh_and_execute_resident_task.py` path.
6. Preserve standing recurrence and all existing WorkerCoordinator admission requirements.

Runtime evidence is not claimed by this source repair. A later authentic resident scheduler cycle must still produce its normal scheduler and reusable-task receipts.

## 2026-09-24 first-boundary observation retention

The existing consumer had one unretained outcome before canonical source/self-materialization: when no resident request was present **and** no distinct local canonical source could be resolved, it returned `NO_REQUEST` without writing `receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json`. This is a source-observed evidence production gap; no actual resident failure is inferred.

The bounded existing-owner repair writes that `NO_REQUEST` observation atomically to the same preexisting receipt path with the exact task/mode, source-resolution reason, unconsumed standing-request semantics, explicit absence of execution/claim/authority, and a retry indication. Existing request-but-source-unavailable `ATTEMPT_RECORDED` and normal consumed-cycle receipts use the same atomic helper. Negative tests prove the no-request path does not invoke the worker; the recovery test proves a later materialized request can overwrite the observation with an ordinary cycle result. No new runtime, device, scheduler, dispatcher, receipt store, or governance path is created. Validation is source-only; authentic dispatch and organization receipts remain separate evidence.
