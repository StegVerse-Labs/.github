# SV002 HB Awareness Runtime Repair Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Parent authority: `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
Runtime lineage: `SHWP-DURABLE-RUNTIME-ACTIVATION` / `SHWP-SV002-ORG-RUNTIME-ACTIVATION-001`

## Diagnosis

The runtime issue is not HeartBeat progression and must not create another heartbeat, oscillator, scheduler, WorkerCoordinator, resident executor, credential path, or user-operated machine requirement.

Canonical HB state remains:

```text
protocol anchor: HB32
mechanism: INDEPENDENT_PHASE_OSCILLATOR
reference rate: 100 Hz / 10 ms
progression dependency: OSCILLATOR_ONLY
heartbeat grants execution authority: false
```

The existing resident dispatcher correctly protects `sv002_org_runtime_activation` behind the already-created Astra-class and quantum standing-awareness predicates.

The first defect was source-refresh incompleteness: `scripts/refresh_sovereign_worker_runtime_source.py` copied the current dispatcher and the SV002 consumer plus `control/resident-execution-request.d/`, but did not copy:

- `scripts/consume_astra_class_resilience_awareness_request.py`
- `scripts/consume_quantum_resilience_awareness_request.py`
- `control/astra-class-adversarial-resilience-contract.json`
- `control/quantum-resilience-contract.json`
- `control/quantum-crypto-census.json`

A refreshed resident could therefore acquire a dispatcher that required standing awareness while lacking the static consumers/contracts needed to materialize that awareness. TVC's existing SV002 self-heal then selected only `sv002_org_runtime_activation`, causing a fresh/current runtime to fail closed at `STANDING_AWARENESS_REQUIRED` or `QUANTUM_STANDING_AWARENESS_REQUIRED` instead of reaching the already-created runtime solution.

A second integration defect remained after those source dependencies were restored: the generic resident dispatcher already registered both awareness consumers, but `scripts/refresh_and_dispatch_resident_requests.py` did not admit either selector in its exact-consumer allowlist. The existing TVC targeted bridge therefore still could not address the prerequisite consumers even though their source was present.

## Repair

The existing local-only source refresher includes the five static awareness dependencies. `control/resident-execution-request.d/` remains the existing source for the entity awareness requests.

The existing targeted refresh+dispatch bridge now additionally admits exactly these already-registered selector names:

```text
astra_class_resilience_awareness
quantum_resilience_awareness
```

The bridge remains one-selector-per-invocation and still delegates to the same `scripts/dispatch_resident_execution_requests.py` dispatcher. It does not batch the consumers, create a scheduler, derive authority, or alter the historical default selector.

No mutable runtime receipts, checkpoints, carrier state, worker state, claims, or fences are copied from source.

The intended existing runtime sequence is:

```text
HB32 oscillator/reference remains independent
-> existing WorkerCoordinator runtime
-> existing local-only source refresh
-> existing resident dispatcher/targeted bridge
-> astra_class_resilience_awareness
-> quantum_resilience_awareness
-> sv002_org_runtime_activation
-> existing task-specific terminal receipt
```

The three consumers are existing registered consumers of the same dispatcher. This is prerequisite sequencing inside the existing runtime, not a second execution plane.

## TVC continuation

TVC's existing resident self-heal pins an obsolete `.github` control-plane SHA and dispatches only the final SV002 selector. After the targeted-bridge repair merges, TVC must re-resolve this admitted consumer against the exact merged repair SHA, as required by `docs/PRIVATE_SOURCE_READ_MIRROR_HANDOFF.md`, and invoke the same exact-one-selector bridge in this order:

1. `astra_class_resilience_awareness`
2. `quantum_resilience_awareness`
3. `sv002_org_runtime_activation`

Moving `main` is not a runtime source identity. The TVC request must remain exact-SHA/immutable-commit bound, secret-free, and TV/TVC credential-governed.

## README completeness predicate

Material: **YES / SATISFIED IN SAME CHANGE SET** for the targeted-bridge repair because the supported exact-consumer interface changes. README records that the existing bridge may address the two standing-awareness consumers while preserving one-selector execution and all existing authority boundaries.

Focused tests:
- `tests/test_resident_refresh_awareness_dependencies.py`
- `tests/test_sv002_awareness_targeted_bridge.py`

## Evidence boundary

Source merge or CI success will prove only source/control/bridge addressability. Authentic runtime closure still requires the existing resident path to produce:

- `receipts/sovereign-host/astra-class-resilience-awareness.latest.json` with completed standing awareness;
- `receipts/sovereign-host/quantum-resilience-awareness.latest.json` with completed standing awareness;
- `receipts/sovereign-host/resident-request-dispatch.latest.json` for each exact selector invocation;
- `receipts/sovereign-host/sv002-org-runtime-activation.latest.json` with `terminal_round_trip_observed=true`.

HB progression, source presence, source refresh, bridge addressability, CI, merge, or TVC materialization alone does not satisfy those runtime predicates.

## User work

NONE. Do not rerun HB30/HB31, do not provision another machine, and do not create or restore a hosted runtime.
