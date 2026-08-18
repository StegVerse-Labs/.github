# Heartbeat Carrier Envelope Mirror Handoff

Updated: 2026-08-18T18:09:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-CARRIER-ENVELOPE-183
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#183 CLOSED_COMPLETED
canonical_pr: StegVerse-Labs/.github#188 MERGED
parent_semantics: StegVerse-Labs/.github#120 / docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
archive_dependency: false for this bounded source lane
```

This handoff is authoritative for the carrier-envelope source/schema only. The parent heartbeat semantic handoff supersedes every earlier statement that allowed gate/passband, worker, task, admission, claim, fence, lease, route, credential, capacity, or observed state to determine heartbeat progression.

## Canonical heartbeat relationship

Heartbeat progression is oscillator-only:

```text
HB_n -- 10 ms oscillator phase travel --> HB_(n+1)
reference_rate: 100 Hz
progression_dependency: OSCILLATOR_ONLY
worker_or_task_gating: false
admission_gating: false
claim_or_fence_gating: false
route_or_credential_gating: false
capacity_or_passband_gating: false
observation_is_causal: false
```

The carrier envelope does **not** calculate heartbeat cadence. It assesses whether downstream consumers, signaling load, phase usage, and tolerances are compatible with the already-existing independent 100 Hz / 10 ms heartbeat reference.

A downstream constraint that cannot tolerate or sustain that heartbeat is rejected or reported as a downstream compatibility/deviation condition. It never slows, accelerates, suppresses, advances, or reschedules the heartbeat.

## Canonical envelope model

`heartbeat_runtime/carrier_envelope.py` emits:

```text
schema: stegverse.heartbeat-carrier-envelope/v2
frequency.rule: INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL
frequency.nominal_hz: 100
frequency.nominal_period_ms: 10
frequency.progression_dependency: OSCILLATOR_ONLY
frequency.downstream_constraints_may_change_frequency: false
phase_plan.phase_plan_changes_reference_interval: false
recalculation.recalculation_changes_heartbeat_frequency: false
```

Capacity, phase slots, jitter, phase error, frequency drift, growth reserve, and admitted signal characteristics are observations/constraints on downstream use of the reference. They are not heartbeat transition predicates.

## Applied semantic reconciliation

The implementation had already been corrected to oscillator-only envelope v2 semantics, but `schemas/heartbeat-carrier-envelope.schema.json` and this handoff still encoded the older gate/passband-derived model. That mismatch was a real source regression because a schema consumer could reject the current v2 envelope or reintroduce state-dependent heartbeat semantics.

Applied on main:

```text
2589a04b22332f6c72eae60692417cb96fec1a2d
  schemas/heartbeat-carrier-envelope.schema.json
  -> schema v2
  -> fixed independent oscillator rule
  -> OSCILLATOR_ONLY progression
  -> no downstream frequency mutation
  -> no phase-plan reference-interval mutation
  -> no recalculation heartbeat-frequency mutation

6eaaf8b832c41f2900a85ddc94b99442c76011f6
  tests/test_heartbeat_carrier_envelope.py
  -> regression guard binds implementation and schema to oscillator-only semantics
```

## Installed source surfaces

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/carrier_envelope.py
schemas/heartbeat-carrier-envelope.schema.json
tests/test_independent_heartbeat_oscillator.py
tests/test_heartbeat_carrier_envelope.py
schemas/heartbeat-carrier-observation.schema.json
control/runtime-separation-contract.json
docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
docs/HEARTBEAT_CARRIER_ENVELOPE_MIRROR_HANDOFF.md
```

## Authority and collision boundaries

```text
heartbeat = carrier/reference signal only
carrier envelope = downstream compatibility/capacity/deviation assessment only
WorkerCoordinator = separate downstream consumer/coordinator
StegBrain = separate observer/evaluator
Master Records = custody/evidence only
TV/TVC = sole credential authority
GitHub Actions = no production/runtime/control-plane authority
third party = fallback only
```

This lane does not mutate persisted heartbeat snapshots, worker claims/fences/leases, resident processes, or credential state.

## Validation obligation

Required source invariants are:

```text
implementation schema == stegverse.heartbeat-carrier-envelope/v2
schema const == stegverse.heartbeat-carrier-envelope/v2
frequency rule == INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL
nominal frequency == 100 Hz
nominal period == 10 ms
progression dependency == OSCILLATOR_ONLY
downstream constraints cannot change heartbeat frequency
phase planning cannot change reference interval
recalculation cannot change heartbeat frequency
heartbeat grants no execution authority
credential authority remains TV/TVC
```

The source/schema regression is repaired. Hosted workflow success is not required to establish heartbeat runtime progression and must never be treated as heartbeat activation proof.

## Completion accounting

```text
carrier-envelope implementation: developed
schema alignment to implementation: repaired
oscillator-only regression test: installed
scaffolding/stubs: 0 known
heartbeat progression dependency on state changes: NONE
runtime heartbeat progression: independent of this source lane
```

This source lane is terminal when direct repository validation confirms the corrected source/schema contract. Any separate worker/runtime task remains separate and cannot be described as a heartbeat blocker.
