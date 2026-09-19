# SV002 REQUEST_BOUND Evidence Retention Mirror Handoff

Goal Task ID: `SV002-REQUEST-BOUND-EVIDENCE-RETENTION-001`
Parent Goal Task ID: `STEGVERSE-002-EXPERIMENT-RERUN-001`
Root experiment: `STEGVERSE-002-SELF-CHARACTERIZATION-001`
COSV: `50000000107000`
Status: `IN_PROGRESS / SOURCE REPAIR MERGED / AUTHENTIC RESIDENT EVIDENCE PENDING`

## Bounded goal

Close only the isolated first-receipt evidence-loss seam for the frozen v0.3 rerun. Determine from authentic existing resident outputs whether the canonical callable was never invoked or whether it wrote `RERUN_REQUEST_BOUND.json` and then failed later, without adding another request, runtime, scheduler, dispatcher, listener, bridge, Site path, device prerequisite, workflow runtime, or authority plane.

## Parent evidence tail

Direct Master Records review established that the parent rerun has not entered Master Records. The first unproven runtime transition is `REQUEST_BOUND`.

The current resident callable writes:

```text
~/.stegverse/self-characterization-001/RERUN_REQUEST_BOUND.json
~/.stegverse/self-characterization-001/RERUN_REQUEST_SUBMISSION.json
```

and the existing resident executor writes:

```text
resident-runtime/state/resident-executor.latest.json
```

## Isolated defect and repair

Source review found an evidence-loss defect inside the existing callable/executor path:

1. `invoke_sv002_experiment_rerun.py` writes `RERUN_REQUEST_BOUND.json` before federation submission.
2. If federation publication then fails, the prior exception result reported `request_bound_claimed=false` regardless of the already-written bound receipt.
3. `resident_executor.py` then raised on the nonzero child return code and discarded the structured child result before writing its existing heartbeat.

This made “callable invoked + request bound + later publication failure” indistinguishable in the executor heartbeat from a pre-binding failure.

StegVerse-002/.github PR #39 repairs only that evidence loss and merged at:

`3a0033742b1ff311bde6c210681ab47df6b734cd`

The repair preserves validated Goal/COSV/experiment/operation/invocation_count/packet/frame identity in the existing blocked callable result and existing resident executor heartbeat. No new evidence path or execution path is created.

## Runtime nonclaim

The merged source repair does not prove a resident process executed after the repair.

```text
authentic resident executor heartbeat after repair: NOT OBSERVED
authentic RERUN_REQUEST_BOUND.json bytes after repair: NOT OBSERVED
REQUEST_BOUND parent predicate: NOT PROMOTED
downstream parent rerun predicates: NOT ADVANCED
```

## Decision rule

When authentic resident evidence becomes available:

- `sv002_callable_attempted=false` or no callable attempt evidence -> classify invocation-side failure;
- `sv002_callable_attempted=true` plus validated `request_bound_claimed=true` / `sv002_request_bound_observed=true` -> classify binding as successful and failure downstream of REQUEST_BOUND;
- malformed or mismatched Goal/COSV/experiment/operation/invocation_count/packet/frame -> fail closed at the mismatch;
- no authentic resident heartbeat -> outcome remains unresolved.

Only exact authentic bytes may promote the parent `REQUEST_BOUND` predicate.

## Authority

WorkerCoordinator remains execution claim/fence authority. Interlock/InTr remains transition authority. TV/TVC remains credential authority. Master Records remains observed-reality/custody/reconstruction authority. GitHub/CI/source grants no runtime authority.

## Manual work

None.


## 2026-09-18 Master Records chain remediation

Direct receipt-chain review resolved the prior observation-only ambiguity. The deterministic current rerun identity is:

```text
packet_id: SV002-RERUN-C796D0BFD181CEC5D99E4C23
manifest_sha256: 29222a589eb4c2958d2787743e266f067ee07e1373c51f60b553f1f359789828
```

Neither identity existed in canonical Master Records custody. The canonical custody contract requires every observed governed state transition to emit a canonical state receipt and every state receipt to be submitted to Master Records, while the SV002 rerun callable had retained `REQUEST_BOUND` only as resident-local evidence.

StegVerse-002/.github PR #40 repaired that exact seam and merged at:

`70d5179f543b6954b6c574d66fcd9675fcbec79c`

The merged callable now reuses the existing canonical Master Records state-transition custody client, emits one canonical `SV002_REQUEST_BOUND` receipt bound to the exact Goal/COSV/experiment/operation/invocation_count/packet/request/manifest/frame identity, requires `state=RECORDED` plus `reconstruction_status=PASS`, retains the returned custody/master-record identity, and only then permits the existing federation publication path to continue.

This is source repair only. Authentic resident execution after the merge and authentic Master Records `RECORDED + PASS` for the real rerun remain unobserved. The parent `REQUEST_BOUND` predicate therefore remains unpromoted.


## 2026-09-18 canonical resident-carrier binding repair

Tracing the deterministic packet upstream from absent Master Records custody established that the existing canonical resident request had not been reaching the current rerun callable. The already-requested `RESIDENT-EXEC-SV002-ORG-RUNTIME-ACTIVATION-001` / selector `sv002_org_runtime_activation` still invoked the retired `StegVerse-org/.github/resident-runtime/run_sv002_self_characterization_roundtrip.py` one-shot path. That path is excluded by the experiment attempt map and cannot produce the current deterministic rerun packet.

The existing request has therefore been retained in place and rebound to:

```text
Goal: STEGVERSE-002-EXPERIMENT-RERUN-001
COSV: 50000000107000
operation: REQUEST_SELF_CHARACTERIZATION
packet: SV002-RERUN-C796D0BFD181CEC5D99E4C23
callable: StegVerse-002/.github:resident-runtime/invoke_sv002_experiment_rerun.py
```

The same `sv002_org_runtime_activation` consumer now invokes that current callable through the existing HeartBeat-separated native WorkerCoordinator/dispatcher. The dispatcher also preserves the already-defined canonical Master Records endpoint/token/local-source bindings and existing federation gateway/root bindings needed by that callable, while GitHub credentials remain excluded.

No new resident request, scheduler, dispatcher, WorkerCoordinator, resident executor, custody authority, transition authority, Site path, or user-operated device is introduced. Authentic runtime consumption remains unclaimed until the existing carrier emits its real request-consumption/custody evidence.


## 2026-09-18 canonical carrier reconciliation after source merges

Two source repairs are now immutable:

```text
StegVerse-002/.github PR #41
merge: 9d79719995edb30ef60f6764331d97506977522f
effect: exact RERUN_REQUEST_BOUND.json bytes are required evidence in canonical Master Records custody

StegVerse-Labs/.github PR #2165
merge: b50c124aca3ec12a7e1d8734a268b81c61b1650f
effect: the existing RESIDENT-EXEC-SV002-ORG-RUNTIME-ACTIVATION-001 request/selector invokes the current deterministic rerun callable rather than the retired one-shot path
```

The child runtime observation owner is therefore the existing canonical HeartBeat-separated WorkerCoordinator request-consumption path, not a second StegVerse-002 persistent resident executor. The first authentic evidence now required is the existing `sv002_org_runtime_activation` consumption/dispatch evidence carrying the exact current Goal/COSV/packet and Master Records REQUEST_BOUND custody result.

Runtime completion remains unclaimed until that authentic consumption exists.


## 2026-09-18 TVC self-heal current-source repair

Tracing the canonical WorkerCoordinator chain one level further upstream found that the existing TVC root self-heal still pinned its immutable `StegVerse-Labs/.github` runtime source to historical `a5d69cdd0c0c039a6ec48c5c7fda800384089a16`. That source predates the current `sv002_org_runtime_activation` -> deterministic rerun callable repair, so a healthy self-heal cycle could refresh the resident with stale source and never expose the current rerun to the existing dispatcher.

TVC PR #443 repaired only that existing private-source/self-heal seam and merged at:

```text
StegVerse-Labs/TVC@35247b583b363f84c2edb5c77474bced729190ae
target immutable runtime source:
StegVerse-Labs/.github@c5e6a7939db85063f49fc0b3010bd6462d13006b
```

The existing three-selector sequence remains unchanged:

```text
astra_class_resilience_awareness
quantum_resilience_awareness
sv002_org_runtime_activation
```

No new request, self-heal supervisor, runtime, dispatcher, WorkerCoordinator, scheduler, credential path, custody authority, transition authority, or device dependency was introduced.

Authentic runtime evidence is still required. The source repair does not prove that TVC materialized the new immutable source, that the resident dispatcher ran, that the current callable executed, or that REQUEST_BOUND reached Master Records.


## 2026-09-18 first unresolved runtime owner corrected

After the TVC self-heal source rebind, no authentic `c5e6a7939db85063f49fc0b3010bd6462d13006b` materialization was found in TVC, Labs, or Master Records. Tracing one transition earlier established that the existing owner is already canonical:

```text
TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006
owner: TV/TVC runtime authority
service: stegtvc-primary-runtime.service
required before self-heal materialization:
  root_primary_runtime_restart_observed = true
  current_source_loaded_on_host_observed = true
```

The TVC activation-delivery handoff currently records both predicates as false/unobserved. Therefore the correct first unresolved boundary is not Astra/quantum or the SV002 callable. It is the existing root primary runtime loading the current TVC checkout that contains merged TVC self-heal repair `35247b583b363f84c2edb5c77474bced729190ae`.

The existing source-level restart repair already exists: `scripts/install_tvc_primary_runtime_service.py --activate` restarts the same fixed `stegtvc-primary-runtime.service`. No second service/runtime is needed. The StegBrowser exact-source promotion request is task-scoped to a separate immutable SHA and is not reused or mutated for SV002.

No authentic runtime restart/current-source receipt is claimed by this reconciliation.


## 2026-09-18 retained TVC startup-source evidence repair

The existing TVC activation owner had one retained-evidence defect after the current-source reload source repair: a legitimate restart could enter `tvc_primary_runtime_activation_task.py` without retaining the exact checkout/source identity imported by that running process. That prevented canonical observation of `current_source_loaded_on_host_observed` from the existing path.

StegVerse-Labs/TVC PR #444 repaired only that evidence gap and merged at:

```text
StegVerse-Labs/TVC@576943af53fce4952a4d2d9f10c432875908123a
```

The existing activation task now retains `reports/runtime/primary-runtime-startup.latest.json` after the existing TV/TVC preflight passes, binding the same `stegtvc-primary-runtime.service`, runtime/process identity, repository root, Git HEAD when available, activation-source path/SHA-256, and timestamp. This does not create another runtime, service, dispatcher, source-promotion request, credential path, scheduler, custody authority, transition authority, Site path, or device prerequisite.

This source repair does not promote runtime truth. Canonical predicates remain:

```text
root_primary_runtime_restart_observed = false
current_source_loaded_on_host_observed = false
```

The next authentic observation must correlate the existing service restart with a startup-source receipt whose TVC source contains merge `35247b583b363f84c2edb5c77474bced729190ae`. Only then may the existing self-heal supervisor be followed toward exact `StegVerse-Labs/.github@c5e6a7939db85063f49fc0b3010bd6462d13006b` materialization.


## 2026-09-19 TVC restart/startup correlation repair

No authentic host observation was available from repository/Master Records evidence, and no connected authorized remote device was online for direct inspection. The next concrete failure was therefore the existing activation path's inability to bind a successful service restart to the process-local startup-source receipt emitted by that same restarted runtime.

StegVerse-Labs/TVC PR #445 repaired only that evidence seam and merged at:

```text
StegVerse-Labs/TVC@4c303fbaf03edd1c7d82e38a0352b094147ddc31
```

The existing `scripts/install_tvc_primary_runtime_service.py --activate` path now snapshots the prior startup-receipt identity, restarts the same `stegtvc-primary-runtime.service`, and fails closed unless a new `PRIMARY_RUNTIME_SOURCE_IMPORTED` receipt appears with a new identity, non-null process ID, and non-null repository HEAD. No new runtime, service, dispatcher, listener, scheduler, bridge, source-promotion request, credential path, Site path, device prerequisite, custody authority, or transition authority was added.

Runtime predicates remain unpromoted:

```text
root_primary_runtime_restart_observed = false
current_source_loaded_on_host_observed = false
```

The next authentic host execution must produce the correlated receipt and show that its `repo_head` contains TVC merge `35247b583b363f84c2edb5c77474bced729190ae`. Only then may this dependency resolve and the existing self-heal supervisor be followed toward exact `StegVerse-Labs/.github@c5e6a7939db85063f49fc0b3010bd6462d13006b` materialization.


## 2026-09-19 reusable TVC service-delivery carriage repair

Post-PR #445 runtime review found the next concrete execution defect in the already-existing SV002-adjacent TVC reusable path. `scripts/run_tvc_runtime_boundary_reusable.py` performed TVC preflight and then invoked `tvc.primary_runtime_binder.activate` directly. That bypassed `TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006`'s approved `scripts/install_tvc_primary_runtime_service.py --activate` leg, so the same-service restart and the new post-#445 restart/startup receipt correlation could never be produced by this reusable carrier.

The repair keeps the existing Healer/reusable-task/TVC path and changes only that carriage:

```text
existing reusable TVC runner
-> tvc.primary_runtime_binder.preflight
-> existing install_tvc_primary_runtime_service.py --activate
-> same stegtvc-primary-runtime.service restart
-> correlated PRIMARY_RUNTIME_SOURCE_IMPORTED receipt required by TVC PR #445
-> existing TVC runtime-boundary observer
```

No new request, scheduler, runtime, service, dispatcher, listener, bridge, credential path, source-promotion request, Site path, device prerequisite, custody authority, or transition authority is introduced. Runtime predicates remain unpromoted until this repaired path executes authentically.


## 2026-09-19 reusable TVC service-delivery repair merged

StegVerse-Labs/.github PR #2222 merged at `f5c64120d381842db16ca1a5156bb881c8e383f8`.

The existing SV002-adjacent `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001` runner now retains the released TVC preflight, invokes the existing `install_tvc_primary_runtime_service.py --activate` service-delivery leg against already-local TVC source, and only then runs the existing runtime observer. The former direct dispatcher-activation bypass is removed from this reusable carrier.

This makes TVC PR #445's same-service restart/startup-source correlation reachable through the existing Healer/reusable-task path. It is source/carriage evidence only: `root_primary_runtime_restart_observed=false` and `current_source_loaded_on_host_observed=false` remain unchanged until authentic execution produces the correlated receipt and proves the loaded TVC source contains merge `35247b583b363f84c2edb5c77474bced729190ae`.


## 2026-09-19 TVC service-owned preflight correction

After the reusable service-delivery carriage repair, source tracing found that the neutral Healer/reusable runner still executed `tvc.primary_runtime_binder.preflight` before invoking the TVC service installer. That preflight requires `STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY=TV/TVC`, while the neutral Healer carrier intentionally does not mint or inject TV/TVC authority. This created an ambient-authority dependency before the execution path could enter the existing TVC-owned service.

The reusable runner now enters the released `install_tvc_primary_runtime_service.py --activate` path directly after resolving already-local TVC source. The restarted `stegtvc-primary-runtime.service` retains `Environment=STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY=TV/TVC`, retains the vault-socket `ExecStartPre`, and invokes `tvc.primary_runtime_binder.activate`, whose existing `task_activate` executes `task_preflight` before serving. The neutral carrier therefore neither bypasses TVC preflight nor manufactures TV/TVC authority; the preflight remains inside its existing authority owner.

No runtime predicate is promoted by this source correction.


## 2026-09-19 PR #2236 canonical reconciliation

StegVerse-Labs/.github PR #2236 merged at `bf0e936c7da481e7935e7accd959034471def69b`. The existing neutral reusable TVC runner now enters the released same-service installer directly and leaves the activation-authority declaration, vault-socket guard, and `task_activate -> task_preflight` sequence inside the existing TVC-owned `stegtvc-primary-runtime.service`.

This is source/carriage evidence only. `root_primary_runtime_restart_observed=false` and `current_source_loaded_on_host_observed=false` remain unchanged until authentic execution produces the required restart/startup correlation.


## 2026-09-19 strict state-transition dependency correction

The execution chain is now represented as a strict predecessor/successor graph rather than a set of independently satisfiable predicates. Every successor is admissible only after authentic evidence consumes its immediate predecessor state.

The neutral reusable scheduler also no longer reports `ALL_DUE_REUSABLE_TASKS_ADVANCED_TO_COMPLETION_OR_AUTHENTIC_BOUNDARY` unconditionally. A due child in `DEFERRED` or any other non-advanced state keeps the scheduler successor transition inadmissible, clears scheduler completion predicates, records the blocking child state, and returns non-success so the existing reusable trigger retains the boundary instead of projecting a later state.

For this SV002 path, the only currently admissible successor is `REUSABLE_TVC_INVOCATION_OBSERVED`. Restart, loaded-source, self-heal, exact c5e6a793 materialization, Astra, quantum, SV002 runtime activation, and REQUEST_BOUND custody are all explicitly `BLOCKED_ON_PREDECESSOR`.
