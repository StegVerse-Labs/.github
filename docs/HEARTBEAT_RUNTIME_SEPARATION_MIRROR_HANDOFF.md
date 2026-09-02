# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-26T16:18:00-05:00

## Authority and active goal

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
source_correction_task: HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008
resident_start_task: HEARTBEAT-OSCILLATOR-RESIDENT-START-012
live_proof_task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
reference_snapshot_task: GATE-PASSBAND-REFERENCE-SNAPSHOT-010
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#122
canonical_semantics: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
sovereign_deployment_handoff: docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
reference_snapshot_handoff: docs/GATE_PASSBAND_REFERENCE_SNAPSHOT_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
StegVerse primary: true
third_party role: FALLBACK_ONLY
```

## Corrected responsibility split

```text
heartbeat oscillator = independent 10 ms phase-travel/reference progression
heartbeat persisted carrier state = observation/sample of oscillator-derived reference only
reference snapshot = chained non-authorizing completion-monitor observation at a carrier reference
GATE_PASSBAND_DERIVED = reference-snapshot reacquisition rule only
WorkerCoordinator = downstream observer/coordinator; never heartbeat clock
StegBrain = nervous-system contract observer/evaluator
Master Records = passive custody/evidence
TV/TVC = sole credential/secret/token authority
```

The heartbeat is not advanced by `cycle()`, reference-snapshot reacquisition, G18, WorkerCoordinator, task admission, claims, fences, leases, routes, credentials, or repository actions. **Observation does not cause heartbeat progression.**

Canonical oscillator semantics:

```text
mechanism: INDEPENDENT_PHASE_OSCILLATOR
progression_dependency: OSCILLATOR_ONLY
phase_travel_time_ms: 10
reference_increment_interval_ms: 10
reference_frequency_hz: 100
worker_or_task_gating: false
admission_gating: false
claim_or_fence_gating: false
route_or_credential_gating: false
observation_is_causal: false
```

## Reference snapshot semantics

The historical term `snapshot` is narrowed to a monitoring object rather than a heartbeat state-transition mechanism. `GATE_PASSBAND_DERIVED` is retained only as the snapshot reacquisition policy. Reacquisition never creates the reference it records.

The first configured monitor remains `SHWP-DURABLE-RUNTIME-ACTIVATION-REFERENCE-MONITOR`. Historical HB31 is an initial observed reference, not oscillator-live proof.

## Installed correction

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/oscillator_producer.py
heartbeat_runtime/engine_v13.py                 # canonical carrier sampler
heartbeat_runtime/engine_v12.py                 # inherited compatibility/base implementation, not canonical package carrier
heartbeat_runtime/runtime_separation.py
heartbeat_runtime/carrier_envelope.py
heartbeat_runtime/reference_snapshot.py
heartbeat_runtime/worker_runtime.py              # independent downstream task-control runtime
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-observation.schema.json
schemas/worker-control-plane-coordination.schema.json
schemas/heartbeat-reference-snapshot.schema.json
control/runtime-separation-contract.json
control/heartbeat-reference-snapshot-policy.json
control/heartbeat-reference-snapshot.json
management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json
scripts/advance_heartbeat_transition.py
scripts/install_sovereign_heartbeat_carrier.py
scripts/verify_sovereign_heartbeat_carrier_activation.py
scripts/run_heartbeat_runtime.py
scripts/run_worker_runtime.py
scripts/run_live_009_resident.py                 # post-start verification only
scripts/reacquire_heartbeat_reference_snapshot.py
scripts/validate_heartbeat_carrier_contract.py
tests/test_independent_heartbeat_oscillator.py
tests/test_heartbeat_carrier_envelope.py
tests/test_heartbeat_runtime_separation.py
tests/test_reference_snapshot_reacquisition.py
tests/test_install_sovereign_heartbeat_carrier.py
tests/test_verify_sovereign_heartbeat_carrier_activation.py
tests/test_live_009_resident_runner.py
receipts/heartbeat/HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008-source-validation.json
receipts/heartbeat-reference-snapshots/
```

`heartbeat_runtime.engine_v13.HeartbeatRuntime` is the canonical package carrier. It preserves the v12 oscillator-derived sampling behavior and adds authority-neutral registry-fragment observation before deriving compatibility assignment-trigger packets. Those packets have no claim, fence, credential, execution, merge, or repository authority. WorkerCoordinator no longer requires such a packet for independently authorized task control.

`heartbeat_runtime.oscillator_producer.OscillatorProducer` supplies oscillator-derived phase deadlines/references. Runtime invocation observes references; it does not generate heartbeat progression.

Existing pre-correction carrier state remains historical provenance. Legacy `control/heartbeat-state.json` remains immutable HB29 provenance.

## 2026-08-26 terminal heartbeat reconciliation

The later protocol-anchor correction in `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` supersedes the resident-start/live-proof gating text that previously lived here.

Current authoritative state:

```text
heartbeat protocol: ACTIVE_PROTOCOL_VERIFIED
protocol anchor: HB32 / 2026-08-23T19:00:00.000Z
period: 10 ms / 100 Hz
progression dependency: OSCILLATOR_ONLY
continuous resident process required: false
resident sampler role: OPTIONAL_OBSERVER_AND_PERSISTENCE
HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009: COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
heartbeat activation issue #12: CLOSED / COMPLETED
issue #122: OPEN only for runtime/control-plane separation and downstream cleanup; not a heartbeat activation gate
```

Resident task `HEARTBEAT-OSCILLATOR-RESIDENT-START-012` may still be used when persistent observation is desired, but it is not a heartbeat existence/progression predicate and LIVE-009 no longer depends on it.

The separate `SHWP-DURABLE-RUNTIME-ACTIVATION` / G18 lane remains a worker/runtime substrate concern. It may block downstream machine-owned workers that require a sovereign node, but it does not block or advance heartbeat progression.

## Superseded and retained semantics

Superseded:

```text
GATE_PASSBAND_DERIVED as heartbeat progression/frequency rule
next admitted worker/control-plane execution opportunity causes next HB
one runtime invocation == one heartbeat
WorkerCoordinator checkpoint required for heartbeat reference existence
carrier assignment trigger required before independently authorized task admission
G18 completion required before HB can progress
persisted HB ordinal == live oscillator position
engine_v12 as the canonical current package carrier
LIVE-009 combined runner installs/starts the resident carrier
LIVE-009 directly claimable before resident-start receipt exists
```

Retained:

```text
GATE_PASSBAND_DERIVED = completion-monitor snapshot reacquisition policy only
engine_v12 = inherited compatibility/base implementation beneath canonical v13
heartbeat assignment-trigger packet = optional non-authorizing compatibility evidence only
```

## Validation

Canonical invariants require same-instant stability, <10 ms no increment, exactly 10 ms +1, delayed observation may skip references, oscillator-only derivation, observation-only persistence, TV/TVC credential authority, v13 canonical carrier separation, and WorkerCoordinator independence from heartbeat timing/trigger authority.

Repository deterministic validation has reached 457/457 PASS on the oscillator conversion lineage. Subsequent validation repaired stale v12 compatibility assertions and projection semantics. The 2026-08-22 source reconciliation added a fail-closed activation receipt verifier and focused tests, plus post-start-only LIVE-009 runner tests. These source changes are not resident runtime proof.

## Live proof and current state

```text
LIVE-009 state: COMPLETED
transition: INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
verification mode: DIRECT_DETERMINISTIC_PROTOCOL_DERIVATION
canonical status: control/heartbeat-live-status.json = ACTIVE_PROTOCOL_VERIFIED
focused protocol-anchor tests: 6/6 PASS
exact-head retained validation: PASS
resident sampler required for progression: false
```

Historical `control/heartbeat-carrier-runtime-state.json` and `control/heartbeat-carrier-observation.json` remain HB31 provenance and intentionally retain pre-anchor fields. They are not current oscillator authority. The current authority is `control/heartbeat-protocol-anchor.json` plus `heartbeat_runtime/independent_oscillator.py`.

Successor work is downstream consumer propagation and separation cleanup, tracked separately (including issue #263). Do not reopen heartbeat activation or require a daemon to satisfy that successor work.

## Collision boundaries

Do not create another heartbeat, oscillator, scheduler, or WorkerCoordinator. Do not let snapshots, WorkerCoordinator, G18, COSV, StegBrain, Master Records, TV/TVC, a model/provider, GitHub Actions, or a third party become heartbeat timing authority. Do not mint claims/fences manually. Third-party surfaces remain fallback-only.

## 2026-08-22 reconciliation commits

```text
9f1b8b300272c2c5f59887649aa45bfde0f8bd02  activation receipt verifier
786a37d82087e450955c1b1d7158172e2dafe32d  verifier tests
49ec81ec7068289b871c527d23f9369099373ce9  LIVE-009 handoff dependency correction
db87e70381ea8612033096dcb55daccfc5d24f79  LIVE-009 registry dependency gate
9eeaf74970a88fc9d40bb052371fd0e78be18a77  resident execution handoff correction
c82c7835f822882a131aef90505b3ddcbd14f0b7  LIVE-009 runner post-start-only correction
a343a4880a118c71f2abccdae10445ce0c5e51e6  LIVE-009 runner dependency tests
6cdbf064bf872d46ddc8c6f4eaa09e97c2d07001  sovereign deployment handoff reconciliation
```

## Completion accounting

```text
semantic defect identified: COMPLETE
independent oscillator source correction: COMPLETE_RELEASED
canonical protocol anchor: INSTALLED
heartbeat protocol progression: ACTIVE_PROTOCOL_VERIFIED
LIVE-009: COMPLETED / TERMINAL / NON-REACQUIRABLE
heartbeat activation issue #12: CLOSED / COMPLETED
resident sampler 012: OPTIONAL OBSERVER ONLY
historical HB29/HB30/HB31: IMMUTABLE PROVENANCE
worker-trigger causality: NONE
GitHub runtime authority: NONE
third-party runtime requirement: NONE
credential authority: TV/TVC
heartbeat activation archive eligibility: true
separate runtime/control-plane cleanup: ACTIVE under issue #122 and downstream handoffs
```

Heartbeat activation is terminal. Keep issue #122 open only for its distinct separation/integration obligations; do not use its open state to reclassify heartbeat activation as incomplete.


## 2026-08-31 native resident request-consumption repair

A runtime liveness gap remained after heartbeat/runtime separation: the native WorkerCoordinator service could run continuously while already-materialized resident execution requests were only visited by bootstrap-time dispatch or by an explicitly configured external rendezvous poll. That allowed the resident worker process to remain alive without consuming locally available request files.

The repair is intentionally inside the existing native worker runtime. No second scheduler, heartbeat, hosted monitor, claim source, or execution authority is introduced.

Canonical behavior:

```text
native WorkerCoordinator process
-> every 100 worker-runtime logical ticks
-> visit scripts/dispatch_resident_execution_requests.py against the same resident root
-> each request-specific consumer validates its own request
-> each task-specific WorkerCoordinator path owns claim/fence/admission
-> durable consumer/task receipts remain completion evidence
```

The 100-tick visit cadence is only a local liveness trigger aligned with the existing 100 Hz HB-scale runtime rhythm. It does not derive execution authority from HeartBeat, does not advance HeartBeat, and does not turn wall-clock time into task authority.

Files:

```text
scripts/run_worker_runtime.py
tests/test_worker_runtime_local_request_dispatch.py
```

Required evidence after deployment-local execution remains:

```text
receipts/sovereign-host/resident-request-dispatch.latest.json
request-specific consumption receipt
fresh task claim/fence where required
task-specific durable completion receipt
same-execution reconstruction where required
```

This repair closes the source-level defect in which a live native worker could fail to visit already-local resident requests. It does not fabricate deployment-local execution evidence and does not convert repository validation into runtime proof.


## 2026-08-31 native canonical-source refresh closure

The native resident WorkerCoordinator now carries the canonical already-local source
root as an explicit non-secret service environment binding:

```text
STEGVERSE_HEARTBEAT_SOURCE_ROOT=<distinct already-local canonical checkout>
```

Every 100 worker-runtime logical ticks, before the local resident-request sweep,
the worker invokes the already-materialized local-only source refresher against
that source root and the resident runtime root. The refresher performs no clone,
fetch, pull, credential acquisition, hosted source lookup, or repository mutation.
It preserves mutable resident state, including carrier/worker state, claims,
fences, receipts, checkpoints, and runtime-owned evidence.

The resulting native sequence is:

```text
already-local canonical source advances
-> native WorkerCoordinator observes configured source root
-> local static source refresh
-> resident request dispatcher visits already-materialized requests
-> request-specific consumer validates intent
-> task-specific WorkerCoordinator admission/claim/fence
-> execution receipt
```

This path is native to the existing worker service and therefore does not depend
on the Linux-only systemd path watcher. The Linux path watcher remains a faster
filesystem-event accelerator where available; it is no longer the only automatic
local source-refresh mechanism.

The carrier service does not receive the canonical source-root binding and remains
independent. Source-refresh cadence is liveness only and grants no HeartBeat,
execution, claim, fence, credential, route, or repository authority.

Files:

```text
scripts/run_worker_runtime.py
scripts/install_sovereign_heartbeat_service.py
tests/test_worker_runtime_local_request_dispatch.py
tests/test_sovereign_heartbeat_service.py
```

This closes the machine-executable stale-resident source seam after the
request-consumption repair. Authentic deployment-local receipts remain the next
runtime evidence goal.


## 2026-09-02 final issue #122 separation reconciliation

The remaining stale source obligation under issue #122 was the first `GATE-PASSBAND-REFERENCE-SNAPSHOT-010` monitor, whose required-state set still encoded the retired G18 downstream gate.

That monitor is now terminalized as **superseded historical monitoring provenance**, without rewriting its OPEN 0/3 snapshot. The reference-snapshot mechanism remains available for new explicit policy revisions, but the obsolete G18 monitor is no longer a current runtime or archive gate.

Issue #263 already completed declared HB32 downstream consumer propagation. Current heartbeat/control-plane source separation is therefore complete:

```text
heartbeat activation: TERMINAL ACTIVE_PROTOCOL_VERIFIED
carrier progression: OSCILLATOR_ONLY
WorkerCoordinator: separate authority
HB-derived transport/carrier authority: NONE
G18 downstream gate: RETIRED
historical snapshot chain: PRESERVED / NON-AUTHORITATIVE
downstream HB32 propagation: COMPLETE
TV/TVC credential authority: PRESERVED
GitHub runtime authority: NONE
third-party runtime authority: NONE
```

Independent consumer/runtime issues remain governed by their own handoffs and must not be reclassified as heartbeat blockers.
