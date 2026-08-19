# Heartbeat Carrier Signal Mirror Handoff

Updated: 2026-08-18T20:08:00-05:00

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

This handoff is authoritative for heartbeat semantics. The oscillator correction supersedes prior wording that allowed heartbeat frequency/progression to be derived from gate passbands, admitted signal load, worker cycles, state transitions, or control-plane execution opportunities.

## Canonical architecture

Heartbeat is the StegVerse carrier/synchronization signal only. It is an independent signal tied to the heartbeat oscillator and its phase-travel/reference interval of 10 ms.

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

Therefore:

```text
HB_n --10 ms oscillator phase travel--> HB_(n+1)
```

No worker, task, G18 state, application/domain state transition, admission decision, claim, fence, lease, route, credential, repository action, carrier-capacity calculation, passband, or observer invocation causes, permits, delays, suppresses, or advances that transition.

A consumer may observe HB_n, miss HB_(n+1), and later observe HB_(n+k). The missed references existed independently; the later observation does not create them retroactively.

Observation does not cause heartbeat progression. WorkerCoordinator, COSV, StegBrain, domain workers, and Master Records are downstream consumers/observers only. Heartbeat is not a scheduler, task dispatcher, route executor, claim/fence/lease issuer, credential authority, application message bus, provider/model executor, or Master Records transport.

## Capacity/envelope separation

Carrier-capacity, passband, load, phase-slot, jitter, or deviation analysis may evaluate whether downstream communication can use the heartbeat reference effectively, but may not set or gate heartbeat progression. Any earlier `GATE_PASSBAND_DERIVED` carrier-frequency statement is superseded for heartbeat progression.

Current canonical implementation surfaces:

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/engine_v12.py
heartbeat_runtime/carrier_envelope.py
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-envelope.schema.json
schemas/heartbeat-carrier-observation.schema.json
control/runtime-separation-contract.json
management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json
scripts/advance_heartbeat_transition.py  # compatibility sampler, not a clock
scripts/verify_iphone_heartbeat_transition_receipt.py  # cutover verifier/materializer, not a clock
```

`engine_v12.cycle()` samples the independent oscillator-derived reference. Multiple observations inside the same 10 ms quantum cannot advance the heartbeat. A delayed observation can jump across multiple references based on elapsed oscillator quanta.

## 2026-08-18 stale cutover-semantics repair

Direct inspection found that the historical iPhone HB29->HB30 materializer still emitted `frequency_rule=GATE_PASSBAND_DERIVED` and made worker checkpoint state part of heartbeat release. That contradicted this canonical architecture even though the independent oscillator implementation had already been installed.

Applied on `main`:

```text
6b3658ecf4ca24fdf4cfdd4ff8f93bd9e1eee826
  scripts/verify_iphone_heartbeat_transition_receipt.py
  - emits INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL
  - installs a 10 ms / 100 Hz oscillator anchor at the verified HB30 observation
  - records progression_dependency=OSCILLATOR_ONLY
  - marks persisted carrier state observation-only
  - removes WorkerCoordinator/task state from heartbeat transition/release predicates
  - records downstream worker runtime as a separate non-heartbeat lane

0dde633f54d960a8aee64a24a3983d71a25f2b54
  tests/test_iphone_heartbeat_transition_receipt.py
  - asserts oscillator-only materialization
  - asserts worker checkpoint is not a heartbeat predicate
  - repairs fallback tests to exercise the actual hosted-environment mechanism
  - proves explicit third-party fallback remains FALLBACK_ONLY with StegVerse runtime authority
```

No historical persisted receipt was rewritten. Legacy HB29 remains immutable provenance. Existing HB30/HB31 repository snapshots are historical observations; their ordinal does not indicate that the oscillator stopped there.

Current GitHub combined-status observation for `0dde633f54d960a8aee64a24a3983d71a25f2b54` returned no status contexts. Therefore these source changes are installed but no hosted check is claimed as PASS, and hosted workflow status would not constitute sovereign runtime activation in any case.

## 2026-08-18 current-state schema hardening

Direct inspection after the cutover repair found one remaining current-schema compatibility hole: `schemas/heartbeat-carrier-runtime-state.schema.json` still allowed `GATE_PASSBAND_DERIVED` at arbitrary future heartbeat ordinals and did not require oscillator provenance for a current carrier observation. That allowed newly materialized state to satisfy the schema while violating this handoff.

Applied on `main`:

```text
7106ad597d0e677accebd36b8e0a1d5883baa3be
  schemas/heartbeat-carrier-runtime-state.schema.json
  - requires nested oscillator provenance for current canonical carrier state
  - constrains current frequency_rule to INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL
  - permits GATE_PASSBAND_DERIVED only as pre-correction historical HB29-HB31 observation compatibility
  - prevents the historical rule from validating at HB32+

66ba8ff9fa65303977427fe61010e2e6599ba7d6
  tests/test_independent_heartbeat_oscillator.py
  - locks the schema branch to oscillator provenance for current state
  - asserts the historical compatibility branch cannot extend past HB31
```

This hardening does not rewrite `control/heartbeat-carrier-runtime-state.json`; that HB31 file remains historical observation evidence. It changes what future current state is allowed to validate as canonical.

## Communication and lifecycle

Subsystem communication remains:

```text
manifest packet + expiration wrapper + data packet
```

Terminal lifecycle remains:

```text
manifest + expiration wrapper + data
-> ENDPOINT_OBJECTIVE_COMPLETE | EXPIRED
-> Master Records packet
-> Master Records custody
-> END_OF_LIFE
```

Master Records is terminal transition custody, not deletion. Master Records is the End-Of-Life state/destination for every Transition Table element.

## Responsibility and authority

```text
heartbeat = independent carrier/reference signal only
WorkerCoordinator = downstream task/worker observer/coordinator under separate authority
StegBrain = nervous-system observer/evaluator
Master Records = passive custody/evidence
TV/TVC = sole credential/secret/token authority
```

Third-party infrastructure may be fallback-only and never primary heartbeat authority.

## Historical provenance

Legacy `control/heartbeat-state.json` remains immutable HB29 provenance. Existing separated carrier snapshots such as persisted HB31 are historical observations, not proof that the oscillator itself stopped at that ordinal. The corrected runtime migrates a pre-fix snapshot by using its observed epoch/time as an oscillator anchor and derives later sampled references from 10 ms quanta.

Historical receipts are not rewritten. Where older receipts or handoffs state that a worker/control-plane/state transition causes the next heartbeat, that causal interpretation is superseded by this handoff and `management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json` v2.

## Validation obligation

Required deterministic invariants:

```text
same sample time -> same heartbeat reference
<10 ms from anchor -> no reference increment
exactly 10 ms -> +1 reference
95 ms -> +9 references with 5 ms phase offset
worker/task/state/admission absent from oscillator derivation
persisted state explicitly observation-only
current runtime schema requires oscillator provenance
GATE_PASSBAND_DERIVED cannot validate as current state after HB31
cutover materialization emits oscillator-only semantics
worker checkpoint is not a heartbeat release predicate
TV/TVC credential authority preserved
GitHub token runtime authority NONE
```

Canonical tests include:

```text
tests/test_independent_heartbeat_oscillator.py
tests/test_heartbeat_carrier_envelope.py
tests/test_iphone_heartbeat_transition_receipt.py
```

## Completion state

The semantic/source correction is installed. Source completion is not sovereign runtime activation. Required remaining heartbeat evidence is an inspectable oscillator-backed observation from the StegVerse sovereign runtime using the corrected implementation. Any worker/runtime activation work remains a separate downstream lane and must not be represented as a heartbeat progression dependency.

The separate live-proof task remains `HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009`. Its current durable handoff is still `HANDOFF_READY`; that state is a downstream runtime-evidence obligation, not a heartbeat progression blocker.

```text
DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
```
