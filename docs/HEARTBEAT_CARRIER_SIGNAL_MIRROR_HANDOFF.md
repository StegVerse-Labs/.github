# Heartbeat Carrier Signal Mirror Handoff

Updated: 2026-08-18T17:47:00-05:00

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
```

This handoff is authoritative for heartbeat semantics. The 2026-08-18 oscillator correction supersedes prior wording that allowed heartbeat frequency/progression to be derived from gate passbands, admitted signal load, worker cycles, or control-plane execution opportunities.

## Canonical architecture

Heartbeat is the StegVerse **carrier/synchronization signal only**. It is an independent signal tied to the heartbeat oscillator and its phase travel/reference interval of **10 ms**.

```text
carrier progression dependency: OSCILLATOR_ONLY
phase travel time: 10 ms
reference increment interval: 10 ms
reference rate: 100 Hz
worker/task gating: false
admission gating: false
claim/fence gating: false
route/credential gating: false
observation is causal: false
persisted carrier state: observation/snapshot only
```

Therefore:

```text
HB_n --10 ms oscillator phase travel--> HB_(n+1)
```

No worker, task, G18 state, admission decision, claim, fence, lease, route, credential, repository action, or observer invocation causes, permits, delays, suppresses, or advances that transition.

A consumer may observe HB_n, miss HB_(n+1), and later observe HB_(n+k). The missed references existed independently; the later observation does not create them retroactively.

**Observation does not cause heartbeat progression.** WorkerCoordinator, COSV, StegBrain, domain workers, and Master Records are downstream consumers/observers only.

Heartbeat is not a scheduler, task dispatcher, route executor, claim/fence/lease issuer, credential authority, application message bus, provider/model executor, or Master Records transport.

## Capacity/envelope separation

Carrier-capacity, passband, load, phase-slot, jitter, or deviation analysis may evaluate whether downstream communication can use the heartbeat reference effectively, but such analysis may not set or gate heartbeat progression. Any earlier `GATE_PASSBAND_DERIVED` carrier-frequency statement is superseded for heartbeat progression.

The canonical runtime implementation is:

```text
heartbeat_runtime/independent_oscillator.py
heartbeat_runtime/engine_v12.py
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-observation.schema.json
control/runtime-separation-contract.json
management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json
scripts/advance_heartbeat_transition.py  # compatibility sampler, not a clock
```

`engine_v12.cycle()` samples the independent oscillator-derived reference. Multiple observations inside the same 10 ms quantum cannot advance the heartbeat. A delayed observation can jump across multiple references based on elapsed oscillator quanta.

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

Master Records is terminal transition custody, not deletion. **Master Records is the End-Of-Life state/destination for every Transition Table element.**

## Responsibility and authority

```text
heartbeat = independent carrier/reference signal only
WorkerCoordinator = downstream task/worker observer/coordinator under separate authority
StegBrain = nervous-system observer/evaluator
Master Records = passive custody/evidence
TV/TVC = sole credential/secret/token authority
```

`credential_authority: TV/TVC`

`github_token_runtime_authority: NONE`

Third-party infrastructure may be fallback-only and never primary heartbeat authority.

## Historical provenance

Legacy `control/heartbeat-state.json` remains immutable HB29 provenance. Existing separated carrier snapshots such as persisted HB31 are historical observations, not proof that the oscillator itself stopped at that ordinal. The corrected runtime migrates a pre-fix snapshot by using its observed epoch/time as an oscillator anchor and derives later sampled references from 10 ms quanta.

Historical receipts are not rewritten. Where older receipts or handoffs state that a worker/control-plane execution opportunity causes the next heartbeat, that causal interpretation is superseded by this handoff and `management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json` v2.

## Validation obligation

Required deterministic invariants:

```text
same sample time -> same heartbeat reference
<10 ms from anchor -> no reference increment
exactly 10 ms -> +1 reference
95 ms -> +9 references with 5 ms phase offset
worker/task/admission state absent from oscillator derivation
persisted state explicitly marked observation-only
TV/TVC credential authority preserved
GitHub token runtime authority NONE
```

Canonical tests: `tests/test_independent_heartbeat_oscillator.py`.

## Completion state

The semantic/runtime correction is source-installed but is not declared live-activated until the corrected v12 sampler executes on the sovereign runtime and produces an inspectable oscillator-backed carrier observation. Source completion does not equal live activation.
