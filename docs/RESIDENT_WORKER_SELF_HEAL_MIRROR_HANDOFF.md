# Resident Worker Self-Heal Mirror Handoff

Repository: `StegVerse-Labs/.github`
Parent: `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
State: `SOURCE_MERGED_VALIDATED / AUTHENTIC_RUNTIME_PRESENCE_NOT_YET_OBSERVED`
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

If the existing worker process is alive, fresh, and task-capable, it is retained.

If the carrier is alive and the worker is absent, local supervision starts the existing `scripts/run_worker_runtime.py --continuous` process, requires a fresh task-capable worker tick, and persists repaired process-presence evidence. The WorkerCoordinator then visits `scripts/dispatch_resident_execution_requests.py` on its own first logical tick and independently performs all task admission/claim/fence/InTr/TV-TVC checks.

If the WorkerCoordinator PID is alive but its canonical runtime-presence freshness predicate says the task-capable cycle is stale, or the worker is structurally no longer task-capable, the carrier-side self-heal now reuses the existing controlled process-termination helper from `scripts/restart_sovereign_ephemeral_node.py`, recycles only that WorkerCoordinator process, starts the same canonical `run_worker_runtime.py --continuous` runner, and requires a new task-capable worker tick before repaired presence is reported. The HB32 carrier and oscillator continue independently and are not restarted by this worker-only recycle.

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
- a live PID is insufficient without a fresh task-capable worker cycle;
- a repaired or recycled worker is not considered present until a fresh task-capable worker tick is observed;
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

## Alive-but-stale WorkerCoordinator recycle repair — 2026-09-06

A further HB/runtime review found that the self-heal path correctly repaired a missing WorkerCoordinator but accepted an alive PID without first applying the canonical worker-cycle freshness result. This left a failure mode where a wedged WorkerCoordinator could remain alive while `runtime_tick`/`last_cycle_at` stopped advancing; resident requests could then remain pending because missing-process self-heal never fired.

PR #1084 fixes that gap by reusing existing runtime machinery rather than creating another execution path:
- canonical freshness comes from `heartbeat_runtime/runtime_presence_projection.py`;
- controlled process termination is reused from `scripts/restart_sovereign_ephemeral_node.py`;
- the same canonical `scripts/run_worker_runtime.py --continuous` WorkerCoordinator is restarted;
- a fresh task-capable worker tick remains mandatory before presence can be reported;
- the HB32 `INDEPENDENT_PHASE_OSCILLATOR` carrier continues independently and remains non-authorizing.

Preflight: `receipts/preflight/HB32-STALE-WORKER-SELF-HEAL-001.json`.
Validated PR head: `c545610cdab1a866ca298b46dac23b375bcd4fd7`.
Validation:
- Heartbeat Worker Project run `34033510178`: SUCCESS;
- organization control-plane run `34033510188`: SUCCESS.
Merge commit: `511b82e26dcfce0d799f861df23b605fb837ac56`.

README impact: MATERIAL. `README.md` was updated in PR #1084 in the same functional change set to document alive-but-stale worker recycling and preservation of the HB32 oscillator/carrier authority boundary.

## Runtime consequence

A live canonical carrier plus either a dead/missing WorkerCoordinator **or an alive-but-stale/non-task-capable WorkerCoordinator** is now a validated self-healing runtime state rather than a passive `REQUESTED` backlog state. Authentic runtime presence still requires the canonical presence receipt from a real resident carrier-supervision visit, and authentic task completion still requires each task-specific receipt; this repair does not fabricate those receipts.
