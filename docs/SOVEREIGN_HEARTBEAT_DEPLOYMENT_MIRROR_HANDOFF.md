# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-21T10:26:00-05:00

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

This handoff owns sovereign deployment and worker-runtime activation only. Heartbeat progression semantics remain authoritative in `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md`.

## Canonical heartbeat architecture

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

```text
HB_n --10 ms oscillator phase travel--> HB_(n+1)
```

No worker state change, task completion, G18 transition, repository action, observer, or assignment-trigger packet causes or advances heartbeat progression. Historical HB31 is a persisted observation only.

## Runtime separation

```text
heartbeat_runtime/independent_oscillator.py
  independent oscillator/reference derivation

heartbeat_runtime/oscillator_producer.py
  oscillator-produced phase deadlines/reference availability

heartbeat_runtime.engine_v13.HeartbeatRuntime
  canonical carrier sampler; observes/persists oscillator-backed references

heartbeat_runtime.engine_v12.HeartbeatRuntime
  compatibility/base implementation inherited by v13; not canonical current carrier

heartbeat_runtime.worker_runtime.WorkerCoordinator
  independent downstream task/claim/fence/worker runtime

scripts/run_heartbeat_runtime.py
  resident carrier sampler process

scripts/run_worker_runtime.py
  independently scheduled task-capable worker process
```

WorkerCoordinator may observe heartbeat references but does not advance, permit, delay, suppress, or schedule them. The carrier grants no worker execution authority. Independently authorized `HANDOFF_READY` work does not require a heartbeat-carried assignment trigger; such packets are non-authorizing compatibility evidence only.

## Historical state

Repository HB31/generation31 and the corresponding worker observation are historical snapshots. Legacy HB29 remains immutable provenance. Do not report worker-runtime inactivity, assignment packets, G18 state, task state, or claim/fence state as heartbeat progression blockers.

## Worker/runtime activation lane

Task-capable WorkerCoordinator execution remains a separate open runtime goal under `.github#122/#12`. It may require claims/fences, receipts, G18 terminalization, downstream inference, or reconstruction. None are heartbeat progression predicates.

## Machine-observable heartbeat activation proof

Heartbeat activation requires resident StegVerse evidence that:

1. canonical v13 samples the independent oscillator;
2. `OscillatorProducer`/oscillator state derives references from elapsed 10 ms phase quanta;
3. persisted carrier state is observation-only;
4. worker/task/admission/claim/fence/lease state is absent from reference derivation;
5. same-quantum observations do not create additional references;
6. delayed observation exposes elapsed oscillator progression;
7. no GitHub/third-party/provider credential becomes heartbeat authority;
8. TV/TVC remains sole credential authority where credentials are involved elsewhere.

WorkerCoordinator execution is not part of the heartbeat-specific progression condition, although the separate live-proof task may independently observe the resident carrier as evidence.

## Live proof and worker/runtime release

```text
task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
state: HANDOFF_READY
carrier: heartbeat_reference_only
carrier_trigger_required: false
required terminal result: COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
```

Do not create a second oscillator, scheduler, or WorkerCoordinator. Do not manually mint claims/fences or manufacture runtime receipts. GitHub-hosted validation cannot substitute for resident execution.

## Completion accounting

```text
heartbeat independent-oscillator semantics: COMPLETE_SOURCE
canonical resident sampler source: engine_v13
oscillator producer source: COMPLETE
heartbeat progression dependency on worker/state changes: NONE
persisted HB31: HISTORICAL OBSERVATION ONLY
oscillator-backed sovereign runtime observation: PENDING MACHINE EXECUTION
live proof 009: HANDOFF_READY / PENDING MACHINE EXECUTION
worker task-capable runtime: SEPARATE OPEN LANE
worker/G18/downstream activation: SEPARATE OPEN LANE
archive: prohibited while required deployment/runtime goals remain nonterminal
```

The deployment workstream remains open for actual resident evidence. Heartbeat progression must never again be reported as blocked on WorkerCoordinator state, G18, assignment packets, task state, or another application/control-plane transition.
