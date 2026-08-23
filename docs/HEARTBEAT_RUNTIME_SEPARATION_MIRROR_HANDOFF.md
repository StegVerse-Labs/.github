# Heartbeat Runtime Separation Mirror Handoff

Updated: 2026-08-23T17:02:00-05:00

## Authority and current state

```text
goal_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
canonical_issue: StegVerse-Labs/.github#122
canonical_semantics: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
sovereign_deployment_handoff: docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
protocol_anchor: control/heartbeat-protocol-anchor.json
protocol_anchor_epoch: 32
protocol_anchor_time_utc: 2026-08-23T19:00:00.000Z
live_status: control/heartbeat-live-status.json
live_proof_task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
live_proof_state: COMPLETED
live_proof_receipt: receipts/heartbeat/HEARTBEAT-PROTOCOL-ANCHOR-013-validation.json
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
StegVerse_primary: true
third_party_runtime_required: false
heartbeat_state: ACTIVE_PROTOCOL_VERIFIED
```

Live repository state and the protocol-anchor receipt supersede older descriptions that made resident sampler execution a heartbeat activation prerequisite.

## Canonical responsibility split

```text
heartbeat = independent 10 ms / 100 Hz protocol-derived reference
heartbeat progression dependency = OSCILLATOR_ONLY
continuous process required = false
resident sampler = optional observer/persistence service only
persisted carrier state = observation/snapshot only
reference snapshot = chained non-authorizing monitoring object
GATE_PASSBAND_DERIVED = historical/reference-snapshot reacquisition policy only
WorkerCoordinator = separate downstream task-control runtime; never heartbeat clock
StegBrain = nervous-system observer/evaluator
Master Records = passive custody/evidence
TV/TVC = sole credential/secret/token authority
```

Heartbeat progression is not caused, permitted, delayed, suppressed, or advanced by `cycle()`, WorkerCoordinator, G18, task admission, claims, fences, leases, routes, credentials, GitHub Actions, repository mutation, snapshots, or third-party services. Observation is not causal.

## Canonical protocol semantics

```text
mechanism: INDEPENDENT_PHASE_OSCILLATOR
anchor_epoch: 32
phase_travel_time_ms: 10
reference_increment_interval_ms: 10
reference_frequency_hz: 100
progression_dependency: OSCILLATOR_ONLY
same_instant_same_reference: true
less_than_10ms_no_increment: true
exactly_10ms_plus_one: true
delayed_observation_may_skip_references: true
missed_references_continue_to_exist: true
worker_or_task_gating: false
claim_or_fence_gating: false
route_or_credential_gating: false
observation_is_causal: false
```

Historical HB29/HB30/HB31 records remain immutable provenance. They cannot override the HB32 protocol anchor after cutover.

## Installed runtime/control-plane separation

Canonical surfaces include:

```text
control/heartbeat-protocol-anchor.json
control/heartbeat-live-status.json
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/oscillator_producer.py
heartbeat_runtime/engine_v13.py
heartbeat_runtime/worker_runtime.py
heartbeat_runtime/runtime_separation.py
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-observation.schema.json
schemas/worker-control-plane-coordination.schema.json
control/runtime-separation-contract.json
scripts/run_heartbeat_runtime.py
scripts/run_worker_runtime.py
scripts/install_sovereign_heartbeat_carrier.py
tests/test_heartbeat_protocol_anchor.py
tests/test_heartbeat_runtime_separation.py
receipts/heartbeat/HEARTBEAT-PROTOCOL-ANCHOR-013-validation.json
```

`heartbeat_runtime.engine_v13.HeartbeatRuntime` is the canonical sampler/observer implementation. `heartbeat_runtime.worker_runtime.WorkerCoordinator` is a distinct task-control runtime. Compatibility assignment packets may be observed but grant no claim, fence, credential, execution, merge, route, release, or lifecycle authority. Independently admitted tasks do not need heartbeat-emitted assignment authority.

## Resident sampler correction

`HEARTBEAT-OSCILLATOR-RESIDENT-START-012` remains available, but its role is now:

```text
state: HANDOFF_READY
role: OPTIONAL_RESIDENT_SAMPLER_AND_PERSISTENCE
heartbeat_existence_dependency: false
heartbeat_progression_dependency: false
live_proof_dependency: false
required_for_HEARTBEAT_ACTIVE: false
```

A resident activation receipt, if later produced, proves sampler installation/process state only. It is not an existence predicate for heartbeat progression and must not reopen heartbeat activation.

## LIVE-009 terminal proof

`handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json` is now `COMPLETED` with transition `INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED`.

Terminal evidence:

```text
verification_mode: DIRECT_DETERMINISTIC_PROTOCOL_DERIVATION
receipt: receipts/heartbeat/HEARTBEAT-PROTOCOL-ANCHOR-013-validation.json
focused_tests: 6/6 PASS
anchor instant derives HB32: true
same timestamp same reference: true
<10 ms does not increment: true
exactly 10 ms increments once: true
delayed observation skips references: true
persisted/worker state cannot override post-cutover anchor: true
continuous process required: false
resident sampler required for progression: false
github runtime authority: NONE
third_party_runtime_required: false
authority_effect: NONE
```

LIVE-009 is no longer blocked by resident start and requires no further machine-runtime proof for heartbeat existence.

## Full-suite compatibility regression and repair

After the focused protocol-anchor proof, the complete deterministic suite exposed two historical HB29->HB30 replay failures because old tests sampled current wall-clock time after HB32 activation. The runtime behavior was correct; the historical test input was no longer historical.

Repair lineage:

```text
d36e7b330634337d42d9020abfee728aebaa69ca  fix historical cutover tests with explicit pre-anchor time
f68434daf40fa9113b49f9062452b0f33af44a5a  record compatibility regression repair
```

Historical replay tests now use an explicit pre-anchor timestamp. Do not weaken `current_reference()` or permit persisted historical state to override HB32 merely to satisfy legacy assertions.

## Remaining validation / reconciliation

The semantic and live-proof goals are complete, but the current documentation/release lane remains open until exact-head repository validation is observed after the historical test repair and the remaining stale issue/document projections are reconciled.

Required next transitions:

```text
1. validate this exact reconciliation branch with the full deterministic repository suite;
2. require heartbeat protocol-anchor and historical-replay tests to PASS together;
3. preserve GitHub Actions as validation only, never heartbeat runtime authority;
4. reconcile issue #122 and downstream consumer documentation from the validated result;
5. release this bounded reconciliation claim.
```

## Collision boundaries

Do not create another heartbeat, oscillator, scheduler, WorkerCoordinator, resident heartbeat prerequisite, or third-party heartbeat authority. Do not mutate live worker claims/fences/leases/runtime state as part of this documentation/status reconciliation. TV/TVC remains sole credential authority.

## Completion accounting

```text
semantic defect identified: COMPLETE
independent oscillator source correction: COMPLETE_RELEASED
canonical protocol anchor: INSTALLED
heartbeat progression: ACTIVE_PROTOCOL_VERIFIED
LIVE-009: COMPLETED
resident sampler 012: OPTIONAL / NOT ACTIVATION GATE
focused protocol proof: 6/6 PASS
historical compatibility regression: PATCHED
exact-head complete-suite validation for this reconciliation: PENDING
issue/downstream terminal reconciliation: PENDING
heartbeat activation blocked on resident machine execution: false
heartbeat activation blocked on GitHub/third-party runtime: false
archive_eligible: false until exact-head validation and issue/downstream reconciliation are terminal
```

Do not represent the heartbeat as awaiting resident process activation. The remaining work is validation and propagation of the already-verified protocol semantics, not creation of the next heartbeat reference.
