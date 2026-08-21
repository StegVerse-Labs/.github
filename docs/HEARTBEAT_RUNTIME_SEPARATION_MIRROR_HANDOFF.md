# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-21T10:26:00-05:00

## Authority and active goal

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
source_correction_task: HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008
live_proof_task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
reference_snapshot_task: GATE-PASSBAND-REFERENCE-SNAPSHOT-010
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#122
canonical_semantics: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
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
scripts/run_heartbeat_runtime.py
scripts/run_worker_runtime.py
scripts/reacquire_heartbeat_reference_snapshot.py
scripts/validate_heartbeat_carrier_contract.py
tests/test_independent_heartbeat_oscillator.py
tests/test_heartbeat_carrier_envelope.py
tests/test_heartbeat_runtime_separation.py
tests/test_reference_snapshot_reacquisition.py
receipts/heartbeat/HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008-source-validation.json
receipts/heartbeat-reference-snapshots/
```

`heartbeat_runtime.engine_v13.HeartbeatRuntime` is the canonical package carrier. It preserves the v12 oscillator-derived sampling behavior and adds authority-neutral registry-fragment observation before deriving compatibility assignment-trigger packets. Those packets have no claim, fence, credential, execution, merge, or repository authority. WorkerCoordinator no longer requires such a packet for independently authorized `HANDOFF_READY` task control.

`heartbeat_runtime.oscillator_producer.OscillatorProducer` supplies oscillator-derived phase deadlines/references. Runtime invocation observes references; it does not generate heartbeat progression.

Existing pre-correction carrier state remains historical provenance. Legacy `control/heartbeat-state.json` remains immutable HB29 provenance.

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
```

Retained:

```text
GATE_PASSBAND_DERIVED = completion-monitor snapshot reacquisition policy only
engine_v12 = inherited compatibility/base implementation beneath canonical v13
heartbeat assignment-trigger packet = optional non-authorizing compatibility evidence only
```

## Validation

Canonical invariants require same-instant stability, <10 ms no increment, exactly 10 ms +1, delayed observation may skip references, oscillator-only derivation, observation-only persistence, TV/TVC credential authority, v13 canonical carrier separation, and WorkerCoordinator independence from heartbeat timing/trigger authority.

Repository deterministic validation has reached 457/457 PASS on the oscillator conversion lineage. Subsequent validation repaired stale v12 compatibility assertions and projection semantics; exact-head hosted convergence after the latest reconciliation remains evidence to observe, not activation authority.

## Live proof task

```text
task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
handoff: handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json
registry: control/worker-registry.d/heartbeat-independent-oscillator-live-009.json
adapter: control/process-worker-adapters.d/heartbeat-independent-oscillator-live-009.json
worker: workers/independent_heartbeat_live_proof_worker.py
state: HANDOFF_READY
canonical owner: StegVerse-Labs/.github#122
carrier: heartbeat_reference_only
carrier_trigger_required: false
```

The one-shot worker may complete only from inspectable resident oscillator-backed carrier evidence. Worker execution does not advance the oscillator. Independently authorized task control may acquire the task without waiting for a heartbeat-carried assignment trigger; any such trigger is reference evidence only with authority effect NONE.

## Live state / activation distinction

Historical HB31 is not corrected oscillator-live proof. Live completion still requires `HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009` through the canonical resident runtime and return of `COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED` with inspectable v13 oscillator-backed persisted carrier evidence.

## Collision boundaries

Do not create another heartbeat, oscillator, scheduler, or WorkerCoordinator. Do not let snapshots, WorkerCoordinator, G18, COSV, StegBrain, Master Records, TV/TVC, a model/provider, GitHub Actions, or a third party become heartbeat timing authority. Do not mint claims/fences manually. Third-party surfaces remain fallback-only.

## Completion accounting

```text
semantic defect identified: COMPLETE
independent oscillator source correction: COMPLETE_RELEASED
v13 canonical sampling integration: COMPLETE_SOURCE
v12 role: COMPATIBILITY_BASE_ONLY
independent WorkerCoordinator admission: COMPLETE_SOURCE
runtime/state/observation contracts: COMPLETE_SOURCE
reference snapshot redefinition: COMPLETE_SOURCE
initial HB31 monitoring snapshot: ACQUIRED / HISTORICAL / GATE OPEN
live proof worker/handoff/registry/adapter: INSTALLED / HANDOFF_READY
live corrected oscillator-backed carrier observation: PENDING MACHINE EXECUTION
archive eligible: false while required live correction evidence remains nonterminal
```
