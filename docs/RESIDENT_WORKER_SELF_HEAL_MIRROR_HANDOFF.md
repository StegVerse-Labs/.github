# Resident Worker Self-Heal Mirror Handoff

Repository: `StegVerse-Labs/.github`
Parent: `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
State: `STALE_PID_RECOVERY_IMPLEMENTED_PENDING_EXACT_HEAD_VALIDATION / AUTHENTIC_RUNTIME_PRESENCE_NOT_YET_OBSERVED`
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

If the existing worker process is alive and produces a fresh task-capable logical tick during the bounded supervision window, it is reused without starting another process.

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
- a worker PID is not sufficient presence evidence without a fresh task-capable logical tick;
- a repaired worker is not considered present until a fresh task-capable worker tick is observed;
- pending resident requests are drained only by the restored WorkerCoordinator under their existing fail-closed consumers.

## Validated presence-projection closure — 2026-09-04

PR #1001 merged as `5187346ce0c1c8da144c1a3743ff063c09501af4`.
Exact validated PR head: `d086a47e98e394a678ba0458d9ad41fe349ae7be`.

Successful validation lanes:
- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: run `33943972408` SUCCESS;
- Validate organization control plane - No GitHub Token Authority: run `33943972425` SUCCESS.

PR #1001 closes the retained presence-projection gap by:
1. preserving canonical engine_v13 / WorkerCoordinator binding;
2. persisting `receipts/sovereign-host/runtime-presence.latest.json` through the canonical projector after authentic worker presence is proven or reused;
3. registering that evidence slot in the shared HB/runtime observability contract;
4. rejecting stale or obsolete worker evidence and avoiding duplicate WorkerCoordinator processes.

This validation is source/deterministic proof only. It does not establish that the sovereign resident carrier has actually performed the supervision visit, that a WorkerCoordinator is currently alive, or that any resident request has been dispatched or consumed.

Current authentic runtime-presence evidence on repository-tracked `main`:
- `receipts/sovereign-host/runtime-presence.latest.json`: NOT PRESENT at the latest reconciliation.

## Self-heal local-binding parity repair — 2026-09-05

Canonical preflight identified a second bounded failure mode in the existing self-heal path: the self-healed WorkerCoordinator was spawned with a narrower non-secret environment allowlist than the canonical worker service. That could restore process liveness while dropping already-local repository/runtime roots needed by request consumers, leaving an apparently alive worker unable to coordinate work that the canonical service could consume.

The repair extends only the existing self-heal process environment and preserves the canonical worker service's approved local bindings, including StegIndex, TV/TVC, Master Records, StegCore, StegOS, KV, Site, TT/RTG/GTG/AE, resident source manifests, and other already-declared local roots. Secret/token/password/API-key/private-key/credential variables remain excluded by the existing sanitizer.

Authority invariants are unchanged:
- same WorkerCoordinator process model;
- no second scheduler or runtime;
- no new claim/fence or InTr authority;
- TV/TVC remains credential authority;
- GitHub token runtime authority remains `NONE`;
- no network source fetch;
- source/validation does not establish authentic runtime presence or request consumption.

README impact: MATERIAL. `README.md` is updated in the same change set because this changes resident failure-recovery behavior and runtime dependency propagation.

## Local source-refresh propagation repair — 2026-09-05

Post-merge continuation found that `scripts/repair_resident_worker_presence.py` was not in the canonical `refresh_sovereign_worker_runtime_source.py::STATIC_FILES` set. An already-materialized resident runtime could therefore refresh its WorkerCoordinator source and continue carrying an older or absent self-heal module even after the canonical source was corrected.

The existing local-only refresh lane now materializes the self-heal module alongside the WorkerCoordinator runtime source. This is source propagation only:
- no network fetch or source transport is introduced;
- mutable runtime state remains preserved;
- no carrier, WorkerCoordinator, scheduler, claim/fence, credential, route, or transition authority is created;
- refresh does not restart the HeartBeat carrier or prove that a running carrier has loaded the new Python module;
- authentic runtime presence, request dispatch, consumption, and StegIndex operational proof remain separate evidence requirements.

README impact: MATERIAL. `README.md` records this local refresh/failure-recovery behavior in the same change set.

## Fresh native materialization parity repair — 2026-09-05

Continuation after local-refresh closure found the same dependency gap on fresh native runtime materialization: `scripts/run_heartbeat_runtime.py` imports the existing self-heal module, but `install_sovereign_heartbeat_service.py::COPY_FILES` did not copy that module and its post-materialization required-file check did not require it. A new resident runtime could therefore materialize the carrier entrypoint without its local supervision dependency and fail before canonical self-heal coordination could operate.

The native installer now:
- copies `scripts/repair_resident_worker_presence.py` with the carrier runner;
- requires the module in the post-materialization completeness predicate;
- validates exact-byte materialization through the existing native runtime materialization test boundary.

This remains dependency/source completeness only. It creates no new carrier, worker, scheduler, claim/fence, credential, route, transition, or network dependency and does not establish authentic resident presence or request execution.

README impact: MATERIAL. `README.md` records the fresh-install dependency/failure behavior in the same change set.

## Bootstrap source-eligibility parity repair — 2026-09-05

Final continuation of the same self-heal capability found a remaining source-completeness inconsistency at sovereign bootstrap eligibility. `install_sovereign_heartbeat_service.py` already required the self-heal module for fresh native materialization, but `bootstrap_sovereign_runtime.py::REQUIRED_SOURCE_FILES` did not. Bootstrap eligibility could therefore report `canonical_source_complete=true` even when the downstream installer would necessarily reject the same source tree because `scripts/repair_resident_worker_presence.py` was absent.

The bounded repair:
- adds `scripts/repair_resident_worker_presence.py` to `bootstrap_sovereign_runtime.py::REQUIRED_SOURCE_FILES`;
- adds a negative-control regression proving that omission of that exact dependency forces `canonical_source_complete=false` and `eligible=false`;
- preserves the existing `RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY` authority effect;
- changes no WorkerCoordinator claim/fence, InTr transition, TV/TVC credential, scheduler, carrier, route, runtime-presence, or request-consumption semantics.

README impact: MATERIAL. `README.md` records that bootstrap source eligibility and downstream native materialization now apply the same self-heal dependency completeness requirement.

This is still source/eligibility correctness only. Passing bootstrap eligibility, validation, merge, source refresh, or native materialization does not prove current carrier presence, current WorkerCoordinator presence, a supervision visit, request dispatch or consumption, claim/fence creation, an InTr transition, resident StegIndex materialization, blocker-derived preflight, StegIndex operational proof, or task completion.

## Stale-but-alive WorkerCoordinator recovery — 2026-09-06

Issue #1078 closes a remaining failure mode inside the **existing** HB/oscillator self-heal implementation. The prior code treated `os.kill(pid, 0)` success as sufficient reason to reuse a WorkerCoordinator. A process could therefore remain PID-alive while its logical runtime stopped advancing; the 100-reference carrier supervision visit would see the PID and decline to repair it, leaving already-local resident requests stalled.

The bounded repair changes no scheduler or authority plane:

1. For an existing live worker PID, capture the current `runtime_tick` and require a newer tick from a task-capable `stegverse.worker-runtime-state/v1` within the existing bounded supervision timeout.
2. If that fresh tick arrives, reuse the existing worker exactly as before.
3. If the PID remains alive but the tick does not advance, classify that process as stale and terminate it before any replacement starts.
4. Restart only the existing canonical `scripts/run_worker_runtime.py --continuous` runner with the already-approved sanitized local bindings.
5. Accept the replacement only after a fresh task-capable tick is observed.
6. If the stale process cannot be stopped, return `STALE_WORKER_REPAIR_BLOCKED` and **do not** create a parallel WorkerCoordinator.
7. Persist stale-process/tick/stop evidence into the same supervision receipt path.

This uses the oscillator-owned 100-reference supervision cadence already installed in `heartbeat_runtime.engine_v13.HeartbeatRuntime`. HeartBeat remains oscillator-only timing/reference; the supervision visit remains non-authorizing. WorkerCoordinator keeps claim/fence/admission authority, InTr/Interlock keeps transition authority, and TV/TVC remains credential authority.

Preflight:

```text
receipts/preflight/RESIDENT-WORKER-STALE-PID-SELF-HEAL-1078.json
result: PASS_FOR_BOUNDED_FUNCTIONAL_MUTATION
README impact: MATERIAL / updated in same change set
open overlapping PR for repair_resident_worker_presence.py: NONE OBSERVED
```

Implementation/test commits on the repair branch before exact-head validation:

```text
2ea9b490fbdff292d62345963591a2039947f2c9  runtime stale-PID recovery
764a417813848ae8b7a9192e9c8f8f82161c2d7f  focused regression tests
06603b0fe6cf8ac933e2f1b923a29ec3d08ed813  README failure-behavior update
```

Until exact-head hosted validation and merge are observed, this section is source implementation evidence only. It does not assert that a deployment-local carrier has loaded the repair or that authentic runtime presence/request consumption has occurred.

## Runtime consequence

A live canonical carrier plus a dead, missing, **or non-advancing stale** WorkerCoordinator is now represented by one existing self-heal design rather than a passive `REQUESTED` backlog state. Authentic runtime presence still requires the canonical presence receipt from a real resident carrier-supervision visit, and authentic task completion still requires each task-specific receipt; source repair and validation do not fabricate those receipts.
