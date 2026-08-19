# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-18T19:21:00-05:00

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

The historical term `snapshot` is now narrowed to a monitoring object rather than a heartbeat state-transition mechanism.

A reference snapshot binds:

- the carrier epoch/generation observed at acquisition;
- the monitored goal and required-state set;
- direct observed values and evidence refs for each required state;
- OPEN/CLOSED gate state;
- a passband width expressed in carrier references;
- the reason a new snapshot was acquired;
- the previous snapshot identity/hash;
- explicit `authority_effect=NONE`.

`GATE_PASSBAND_DERIVED` is retained prospectively as this snapshot reacquisition policy:

```text
INITIAL -> acquire first monitoring reference
REQUIRED_STATE_CHANGED -> reacquire immediately, even inside passband
PASSBAND_CROSSED -> reacquire unresolved state at the new carrier reference
TERMINAL_GATE_CLOSED -> acquire final evidenced snapshot
NONE_TERMINAL -> stop periodic reacquisition for the closed goal
```

The gate is the required completion-state set. The passband is the maximum carrier-reference delta during which an unchanged unresolved snapshot may remain current. Reacquisition never creates the reference it records.

The first configured monitor is `SHWP-DURABLE-RUNTIME-ACTIVATION-REFERENCE-MONITOR`. Its current latest snapshot is:

```text
control/heartbeat-reference-snapshot.json
reference: heartbeat_epoch:31
carrier_frequency_rule_observed: GATE_PASSBAND_DERIVED
reacquisition_rule: GATE_PASSBAND_DERIVED
gate: OPEN
complete: 0/3
pending: 3/3
authority_effect: NONE
snapshot_controls_carrier_progression: false
```

This does not rewrite HB31. It makes HB31 the first observed reference in a new completion-monitoring chain. A later carrier reference or required-state change produces a new hash-linked snapshot.

## Installed correction

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/engine_v12.py
heartbeat_runtime/runtime_separation.py
heartbeat_runtime/carrier_envelope.py
heartbeat_runtime/reference_snapshot.py
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-observation.schema.json
schemas/worker-control-plane-coordination.schema.json
schemas/heartbeat-reference-snapshot.schema.json
control/runtime-separation-contract.json
control/heartbeat-reference-snapshot-policy.json
control/heartbeat-reference-snapshot.json
management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json
scripts/advance_heartbeat_transition.py
scripts/reacquire_heartbeat_reference_snapshot.py
control/heartbeat-documentation-semantics-audit.json
scripts/validate_heartbeat_carrier_contract.py
tests/test_independent_heartbeat_oscillator.py
tests/test_heartbeat_carrier_envelope.py
tests/test_heartbeat_runtime_separation.py
tests/test_reference_snapshot_reacquisition.py
receipts/heartbeat/HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008-source-validation.json
receipts/heartbeat-reference-snapshots/
```

`heartbeat_runtime.engine_v12.HeartbeatRuntime.cycle()` is a sampler. It derives the observed heartbeat ordinal from an oscillator anchor and elapsed 10 ms quanta. Two observations at the same instant return the same reference. If a consumer does not sample for 95 ms, the next observation may be nine references later with a 5 ms phase offset. Intermediate references existed independently; they are not generated by the observation call.

Existing pre-correction separated carrier state is migrated without rewriting historical provenance: its persisted epoch/time become the last-known oscillator anchor. Legacy `control/heartbeat-state.json` remains immutable HB29 provenance.

`scripts/advance_heartbeat_transition.py` is retained for compatibility but is semantically a sampler/verifier. Its carrier release predicates are oscillator/reconstruction predicates only. Worker/control-plane observations are recorded separately and may not gate carrier existence.

`scripts/reacquire_heartbeat_reference_snapshot.py` evaluates only configured completion evidence and the currently persisted carrier reference. It may write a new latest snapshot plus immutable history record; it cannot mutate carrier state, mint claims/fences, or grant execution authority.

## Superseded and retained semantics

The following interpretations remain explicitly superseded:

```text
GATE_PASSBAND_DERIVED as the heartbeat progression/frequency rule
next admitted worker/control-plane execution opportunity causes next HB
one runtime invocation == one heartbeat
WorkerCoordinator checkpoint required for a heartbeat reference to exist
G18 completion required before HB can progress
persisted HB ordinal == live oscillator position
```

The following interpretation is now retained:

```text
GATE_PASSBAND_DERIVED as the policy for reacquiring completion-monitoring reference snapshots while a monitored gate is OPEN
```

Capacity, passband, load, deviation, and snapshot mechanics may observe/assess the carrier but may not control oscillator progression.

## Validation

Canonical oscillator tests require:

```text
same sample instant -> same HB
<10 ms -> no HB increment
10 ms -> exactly +1 HB
95 ms -> +9 HB with 5 ms phase remainder
delayed observation may skip references
no worker/task/admission/claim/fence/route/credential input participates in oscillator derivation
snapshot marked observation-only
TV/TVC credential boundary preserved
```

Reference-snapshot tests in `tests/test_reference_snapshot_reacquisition.py` require:

```text
initial snapshot acquisition
no reacquisition inside passband without state change
state progress reacquires inside passband
passband crossing reacquires unresolved state
terminal progress reacquires and closes gate
closed gate stops periodic reacquisition
carrier reference regression fails closed
historical GATE_PASSBAND_DERIVED carrier can be observed without rewrite
snapshot grants no carrier/task/claim/fence authority
```

Bounded oscillator source validation receipt remains:

```text
receipts/heartbeat/HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008-source-validation.json
state: SOURCE_VALIDATED_BOUNDED
deterministic replay: 3/3 PASS
hosted workflow success claimed: false
live corrected runtime claimed: false
```

The new snapshot source/tests are installed but a hosted exact-head test PASS is not yet claimed.

## Live proof task

The remaining live oscillator correction is installed as the canonical WorkerCoordinator task:

```text
task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
handoff: handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json
registry: control/worker-registry.d/heartbeat-independent-oscillator-live-009.json
adapter: control/process-worker-adapters.d/heartbeat-independent-oscillator-live-009.json
worker: workers/independent_heartbeat_live_proof_worker.py
state: HANDOFF_READY
canonical owner: StegVerse-Labs/.github#122
```

The worker is one-shot and can complete only after the corrected StegVerse sampler persists oscillator-backed carrier evidence. Its invocation does not advance the oscillator; it merely samples the oscillator-derived reference.

## Live state / activation distinction

The repository still contains historical persisted carrier observation `HB31` from the pre-correction implementation. It contains `frequency_rule=GATE_PASSBAND_DERIVED` and is **not** live proof of corrected oscillator progression.

It is now valid as the **initial monitoring reference snapshot source**. This is a different claim: the snapshot records what HB31 currently says and keeps the monitored gate OPEN. It does not reinterpret HB31 as oscillator proof.

Live oscillator completion still requires `HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009` to execute through the canonical WorkerCoordinator/runtime owner and return `COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED` with inspectable persisted oscillator-backed carrier evidence. When that evidence changes the monitored required-state set, the snapshot policy reacquires a new reference snapshot automatically on its next invocation.

## Collision boundaries

Do not create another heartbeat or scheduler. Do not let reference snapshots, WorkerCoordinator, G18, COSV, StegBrain, Master Records, TV/TVC, a model/provider, or a third party become heartbeat timing authority. Do not mutate protected credential/route/wallet state. Third-party surfaces remain fallback-only.

## Completion accounting

```text
semantic defect identified: COMPLETE
independent oscillator source correction: COMPLETE_RELEASED
v12 sampling integration: COMPLETE_SOURCE
runtime/state/observation contracts: COMPLETE_SOURCE
reference snapshot redefinition: COMPLETE_SOURCE
GATE_PASSBAND_DERIVED snapshot reacquisition implementation: COMPLETE_SOURCE
initial HB31 monitoring snapshot: ACQUIRED / GATE OPEN 0/3
snapshot deterministic tests: INSTALLED / EXACT-HEAD EXECUTION NOT YET OBSERVED
live proof worker/handoff/registry/adapter: INSTALLED / HANDOFF_READY
live corrected oscillator-backed carrier observation: PENDING MACHINE EXECUTION
archive eligible: false while required live correction evidence remains nonterminal
```
