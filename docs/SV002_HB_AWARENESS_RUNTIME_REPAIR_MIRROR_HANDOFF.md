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

The defect was source-refresh incompleteness: `scripts/refresh_sovereign_worker_runtime_source.py` copied the current dispatcher and the SV002 consumer plus `control/resident-execution-request.d/`, but did not copy:

- `scripts/consume_astra_class_resilience_awareness_request.py`
- `scripts/consume_quantum_resilience_awareness_request.py`
- `control/astra-class-adversarial-resilience-contract.json`
- `control/quantum-resilience-contract.json`
- `control/quantum-crypto-census.json`

A refreshed resident could therefore acquire a dispatcher that required standing awareness while lacking the static consumers/contracts needed to materialize that awareness. TVC's existing SV002 self-heal then selected only `sv002_org_runtime_activation`, causing a fresh/current runtime to fail closed at `STANDING_AWARENESS_REQUIRED` or `QUANTUM_STANDING_AWARENESS_REQUIRED` instead of reaching the already-created runtime solution.

## Repair

The existing local-only source refresher now includes those five static awareness dependencies. `control/resident-execution-request.d/` remains the existing source for the entity awareness requests.

No mutable runtime receipts, checkpoints, carrier state, worker state, claims, or fences are copied from source.

The intended existing runtime sequence is:

```text
HB32 oscillator/reference remains independent
-> existing WorkerCoordinator runtime
-> existing local-only source refresh
-> existing resident dispatcher
-> astra_class_resilience_awareness
-> quantum_resilience_awareness
-> sv002_org_runtime_activation
-> existing task-specific terminal receipt
```

The three consumers are existing registered consumers of the same dispatcher. This is prerequisite sequencing inside the existing runtime, not a second execution plane.

## TVC continuation

TVC's existing resident self-heal was originally pinned to an obsolete `.github` control-plane SHA and dispatched only the final SV002 selector. The original merged repair at `StegVerse-Labs/TVC@85a6885d9f942c84cc5740f1e1f26bae2e2de03f` re-resolved the admitted source to exact `.github` commit `543fb39498cdba042796a09d70292c2bd7396e1a`, refreshed the resident runtime from that exact source, and invoked the existing `scripts/dispatch_resident_execution_requests.py` directly with the exact selector set `astra_class_resilience_awareness`, `quantum_resilience_awareness`, and `sv002_org_runtime_activation` in canonical order.

That original repair remains historical lineage. A later TVC exact-source rebind advanced the current source to `11cad666ff4a0ffeca39a725272f1ab905d9257d` through TVC merge `a7e3ed7611c9abead988ec85b493cc396ac54b94`. That lineage also remains historical.

The current validated TVC exact-source binding now supersedes both earlier coordinates:

```text
current exact runtime source: StegVerse-Labs/.github@a5d69cdd0c0c039a6ec48c5c7fda800384089a16
native email integration source: StegVerse-Labs/.github#1119
TVC exact-source rebind PR: StegVerse-Labs/TVC#342
TVC exact-source rebind merge: StegVerse-Labs/TVC@e51ca9b5d39d891c8df087b0fa430eea98cdfadc
TVC validation reconciliation merge: StegVerse-Labs/TVC@fafe0c79c9a9b7782f25fccc20d6b18fd02aeee9
private-source-read-validation: run 34055625562 / SUCCESS
TVC Credential Model Consistency Validation: run 34055625565 / SUCCESS
TVC task: TVC-RESIDENT-SERVICE-SELF-HEAL-001
consumer task: SHWP-SV002-ORG-RUNTIME-ACTIVATION-001
```

The current TVC task record reports that exact source as source-rebind-validated and keeps authentic host execution unobserved. The native-email integration extends the refreshed resident source with the existing standing native-email task, consumer, monitor, normalizer, and dispatcher registration. It does not change the SV002 direct-dispatch mechanism, its Astra/quantum prerequisite ordering, the HB/oscillator role, WorkerCoordinator claim/fence authority, InTr transition authority, or TV/TVC credential boundary.

Moving `main` is not a runtime source identity. The TVC request remains exact-SHA/immutable-commit bound, secret-free, and TV/TVC credential-governed. A later `.github` source change is not automatically a prerequisite for that bounded TVC repair unless the exact runtime behavior it needs is absent from the pinned source.

## README completeness predicate

`README.md` inspected before the original source-refresh mutation.

Determination: `NO_README_CHANGE_REQUIRED` for the original `.github` source-refresh dependency repair.

Evidence-supported reason: the README already defines the externally meaningful resident self-heal/source-refresh contract: local-only refresh of canonical WorkerCoordinator dependencies, no network fetch or credential acquisition, no second carrier/worker/scheduler, preservation of mutable runtime state, and no inference of runtime execution from refresh. The repair restored omitted static files inside that already-documented parity contract and did not change its authority model.

For the earlier TVC exact-source handoff reconciliation, `receipts/preflight/SV002-TVC-EXACT-SOURCE-HANDOFF-RECONCILIATION-20260906.json` records a separate `NO_README_CHANGE_REQUIRED` determination.

For the current native-email rebind handoff reconciliation, `receipts/preflight/SV002-TVC-NATIVE-EMAIL-REBIND-HANDOFF-RECONCILIATION-20260906.json` records another `NO_README_CHANGE_REQUIRED` determination because this change only updates provenance to already-merged and already-validated TVC state and changes no repository behavior, runtime semantics, interface, authority boundary, evidence semantics, prerequisite, dependency, failure behavior, or capability meaning.

Focused test for the original refresh repair: `tests/test_resident_refresh_awareness_dependencies.py`.

## Evidence boundary

Source merge or CI success proves only source/control completeness. Authentic runtime closure still requires the existing resident path to produce:

- `receipts/sovereign-host/astra-class-resilience-awareness.latest.json` with completed standing awareness;
- `receipts/sovereign-host/quantum-resilience-awareness.latest.json` with completed standing awareness;
- `receipts/sovereign-host/resident-request-dispatch.latest.json` for the exact selector set;
- `receipts/sovereign-host/sv002-org-runtime-activation.latest.json` with `terminal_round_trip_observed=true`.

The native-email extension separately requires authentic resident receipts:

- `receipts/sovereign-host/native-email-action-monitor-request-consumption.latest.json`;
- `receipts/sovereign-host/native-email-action-monitor.latest.json`.

HB progression, source presence, source refresh, CI, merge, TVC materialization, or native-email source eligibility alone does not satisfy those runtime predicates.

## User work

NONE. Do not rerun HB30/HB31, do not provision another machine, do not create or restore a hosted runtime, and do not create another monitor or dispatcher.

If the exact Gmail owner session is absent or requires renewed Google consent, that provider-native owner-presence boundary remains separately receipt-bound and must not be replaced with a second credential path.

## Portable bridge selector admission correction — 2026-09-06

A separate post-merge inspection found a real seam in the canonical one-selector portable bridge: `scripts/refresh_and_dispatch_resident_requests.py` did not admit either standing-awareness selector even though the canonical dispatcher registered both consumers and local source refresh materialized their dependencies.

The existing portable bridge now admits, without changing its one-selector-per-invocation contract:

```text
astra_class_resilience_awareness
quantum_resilience_awareness
sv002_org_runtime_activation
```

Portable one-selector callers may therefore invoke those existing consumers in prerequisite order and must stop before SV002 activation if an awareness dispatch fails.

This portable-bridge correction is **not** the dispatch mechanism used by the current TVC resident self-heal lineage. That TVC implementation refreshes source and invokes `scripts/dispatch_resident_execution_requests.py` directly with all three exact selectors in one dispatcher visit. The portable correction remains valid for portable callers, but it must not be represented as a missing prerequisite or failure cause for the merged TVC direct-dispatch path.

This is source/interface clarification only. Authentic standing-awareness receipts, native-email receipts, and the terminal SV002 round trip remain unobserved.
