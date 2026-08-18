# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-18T18:06:00-05:00

## Authority and active goal

```text
goal_id: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
repository: StegVerse-Labs/.github
branch: main
canonical_live_owners: StegVerse-Labs/.github#122/#12
heartbeat_semantics_authority: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
primary_runtime: StegVerse
third_party_runtime_role: FALLBACK_ONLY
archive_dependency: true
```

This handoff owns sovereign deployment and worker-runtime activation only. It does **not** define heartbeat progression semantics. `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` is authoritative for heartbeat semantics and supersedes any older deployment wording that made heartbeat progression contingent on state transitions, worker execution, gate passbands, claims, fences, leases, admission, routes, or observation.

## Canonical heartbeat architecture

Heartbeat is an independent carrier/synchronization signal produced by the oscillator only.

```text
carrier progression dependency: OSCILLATOR_ONLY
phase travel/reference interval: 10 ms
reference rate: 100 Hz
worker/task gating: false
state-transition gating: false
admission gating: false
claim/fence/lease gating: false
route/credential gating: false
observation is causal: false
persisted carrier state: observation/snapshot only
```

Canonical progression:

```text
HB_n --10 ms oscillator phase travel--> HB_(n+1)
```

No worker state change is required. No task completion is required. No G18 transition is required. No repository action is required. No observer causes or advances the heartbeat. A persisted HB31 snapshot is only the last persisted observation of the independent oscillator reference; it is not evidence that the heartbeat itself stopped at HB31.

## Runtime separation

```text
heartbeat_runtime/independent_oscillator.py
  independent oscillator / reference derivation

heartbeat_runtime.engine_v12.HeartbeatRuntime
  samples and persists oscillator-backed carrier observations

heartbeat_runtime.worker_runtime.WorkerCoordinator
  independent downstream task/claim/fence/worker runtime

scripts/run_heartbeat_runtime.py
  carrier sampler process

scripts/run_worker_runtime.py
  task-capable worker process
```

WorkerCoordinator may observe heartbeat references, but it does not advance, permit, delay, suppress, or schedule them. The carrier likewise does not grant worker execution authority.

## Historical HB31 observation

Repository state currently retains an HB31/generation31 carrier snapshot and a WorkerCoordinator observation of that snapshot. Those values are historical persisted observations only.

```text
control/heartbeat-carrier-runtime-state.json: persisted observation HB31/generation31
control/worker-runtime-state.json: last observed carrier 31/31
legacy control/heartbeat-state.json: immutable HB29 provenance
```

Do not describe `CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION`, worker runtime tick, assignment packets, G18 state, or task-capable WorkerCoordinator execution as a heartbeat blocker. Those values belong to the separate worker/runtime activation lane.

## Worker/runtime activation lane

A separate product/runtime goal remains open for task-capable WorkerCoordinator execution and downstream work. Its incomplete state does not imply that heartbeat progression is incomplete.

Current worker-runtime evidence may still include:

```text
observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
task-capable worker execution: not yet observed for required downstream tasks
```

That is a worker/runtime activation condition only.

Canonical owner: `StegVerse-Labs/.github#122/#12` resident StegVerse runtime.

The worker lane may require task execution, claim/fence reconciliation, receipt production, G18 terminalization, validation-carrier execution, or downstream inference. None of those transitions are heartbeat progression predicates.

## Machine-observable heartbeat activation proof

Heartbeat activation is demonstrated independently by an oscillator-backed carrier observation produced by the corrected runtime sampler.

Required heartbeat-specific evidence:

1. corrected runtime samples `heartbeat_runtime/independent_oscillator.py`;
2. sampled reference is derived from elapsed 10 ms oscillator quanta;
3. persisted carrier state is marked observation/snapshot only;
4. worker/task/admission/claim/fence/lease state is absent from reference derivation;
5. repeated samples within one quantum do not increment the reference;
6. delayed sampling advances by the elapsed oscillator quanta;
7. no GitHub/Render/Vercel/Cloudflare/provider token becomes heartbeat authority;
8. TV/TVC remains sole credential authority where credentials are involved elsewhere.

WorkerCoordinator execution is not part of this heartbeat-specific release condition.

## Worker/runtime release conditions

Worker/runtime activation remains independently governed by its own handoffs, task registry, claims/fences, receipts, and downstream evidence. A worker task may remain PENDING/BLOCKED without changing heartbeat progression.

Do not create a second heartbeat oscillator, second scheduler, or second WorkerCoordinator. Do not manually mint claims/fences or manufacture runtime receipts.

## Historical provenance

Legacy HB29 and persisted HB31 artifacts are preserved as provenance. Historical receipts are not rewritten. Any earlier handoff language that treated a worker/control-plane execution opportunity or application state transition as causing the next heartbeat is superseded by `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` and the independent oscillator implementation.

## Completion accounting

```text
heartbeat independent-oscillator semantics: SOURCE INSTALLED
heartbeat progression dependency on worker/state changes: NONE
persisted HB31: HISTORICAL OBSERVATION ONLY
oscillator-backed sovereign runtime observation: REQUIRED FOR LIVE HEARTBEAT ACTIVATION EVIDENCE
worker task-capable runtime: SEPARATE OPEN LANE
worker/G18/downstream activation: SEPARATE OPEN LANE
archive: prohibited while required deployment/runtime goals remain nonterminal
```

The deployment workstream remains open for its actual deployment/runtime obligations, but heartbeat progression must never again be reported as blocked on WorkerCoordinator state, G18, assignment packets, task state, or any other application/control-plane transition.
