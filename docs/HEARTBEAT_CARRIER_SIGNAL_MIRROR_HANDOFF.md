# Heartbeat Carrier Signal Mirror Handoff

Updated: 2026-08-21T10:26:00-05:00

## Canonical authority

```text
goal_id: HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120
runtime_correction_id: HEARTBEAT-INDEPENDENT-OSCILLATOR-10MS-008
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#120
runtime_owner: StegVerse-Labs/.github#122
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
archive_ready: false
```

This handoff is authoritative for heartbeat semantics. Heartbeat is the StegVerse carrier/synchronization signal only and is produced by an independent 10 ms phase oscillator.

## Canonical architecture

```text
carrier progression dependency: OSCILLATOR_ONLY
phase travel time: 10 ms
reference increment interval: 10 ms
reference rate: 100 Hz
worker/task gating: false
state-transition gating: false
admission gating: false
claim/fence/lease gating: false
route/credential gating: false
capacity/passband gating: false
observation is causal: false
persisted carrier state: observation/snapshot only
```

```text
HB_n --10 ms oscillator phase travel--> HB_(n+1)
```

No worker, task, G18 state, application/domain transition, admission decision, claim, fence, lease, route, credential, repository action, carrier-capacity calculation, passband, observer invocation, or assignment-trigger packet causes, permits, delays, suppresses, or advances heartbeat progression.

A consumer may observe HB_n, miss HB_(n+1), and later observe HB_(n+k). Missed references existed independently. Observation does not create them retroactively.

## Canonical implementation surfaces

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/oscillator_producer.py
heartbeat_runtime/engine_v13.py                 # canonical package carrier sampler
heartbeat_runtime/engine_v12.py                 # compatibility/base beneath v13
heartbeat_runtime/worker_runtime.py              # separate downstream task control
heartbeat_runtime/carrier_envelope.py
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-envelope.schema.json
schemas/heartbeat-carrier-observation.schema.json
control/runtime-separation-contract.json
management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json
scripts/run_heartbeat_runtime.py
scripts/run_worker_runtime.py
scripts/advance_heartbeat_transition.py          # compatibility sampler/verifier, not a clock
scripts/verify_iphone_heartbeat_transition_receipt.py
```

`engine_v13.HeartbeatRuntime` is the canonical carrier class. It inherits oscillator-derived sampling behavior and applies authority-neutral registry-fragment observation before optional compatibility assignment-trigger derivation. Those packets grant no execution authority and are not prerequisites for independently authorized WorkerCoordinator admission.

`OscillatorProducer` derives phase deadlines/references independently. Runtime observation is non-causal.

## Capacity/envelope separation

Carrier-capacity, passband, load, phase-slot, jitter, or deviation analysis may assess use of heartbeat references but may not set or gate progression. `GATE_PASSBAND_DERIVED` is superseded as a carrier-frequency rule and retained only for completion-monitor snapshot reacquisition.

## Historical provenance

Legacy HB29 and persisted HB30/HB31 remain immutable/historical observations. Their ordinal does not indicate oscillator stoppage. Historical receipts are not rewritten. Current-state schema requires oscillator provenance and does not allow historical `GATE_PASSBAND_DERIVED` semantics to extend to HB32+.

## Responsibility and authority

```text
heartbeat = independent carrier/reference signal only
WorkerCoordinator = separate downstream task-control observer/coordinator
StegBrain = nervous-system observer/evaluator
Master Records = passive custody/evidence
TV/TVC = sole credential/secret/token authority
GitHub Actions = validation only; no production heartbeat authority
```

Heartbeat is not a scheduler, task dispatcher, route executor, claim/fence/lease issuer, credential authority, application message bus, provider/model executor, or Master Records transport.

## Validation obligation

Required deterministic invariants include same-sample stability, <10 ms no increment, 10 ms exactly +1, delayed observation skipping references according to elapsed phase, oscillator-only derivation, observation-only persistence, v13 canonical carrier identity, WorkerCoordinator independence, TV/TVC credential authority, and GitHub-token runtime authority NONE.

Repository deterministic validation reached 457/457 PASS on the oscillator conversion lineage. Later corrections reconciled stale v12 compatibility assertions and worker projection semantics. Hosted validation remains validation evidence only.

## Live proof

The separate live-proof task is:

```text
HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
state: HANDOFF_READY
carrier: heartbeat_reference_only
carrier_trigger_required: false
```

Source completion is not sovereign runtime activation. Required heartbeat activation evidence remains an inspectable oscillator-backed observation from the resident StegVerse runtime using the canonical v13 sampler. Worker/runtime activation is a separate downstream lane and must never be represented as a heartbeat progression dependency.

## Completion state

```text
independent oscillator semantics: COMPLETE_SOURCE
canonical carrier implementation: engine_v13
engine_v12: COMPATIBILITY_BASE_ONLY
oscillator producer: COMPLETE_SOURCE
worker-trigger causality: NONE
resident oscillator-backed observation: PENDING MACHINE EXECUTION
live proof 009: HANDOFF_READY / NOT COMPLETED
archive_ready: false
```

DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
