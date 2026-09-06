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

TVC's existing resident self-heal was originally pinned to an obsolete `.github` control-plane SHA and dispatched only the final SV002 selector. The first merged sequencing repair at `85a6885d9f942c84cc5740f1e1f26bae2e2de03f` established direct exact-selector dispatch through the existing `scripts/dispatch_resident_execution_requests.py` path.

The current canonical TVC binding is the later merged TVC #335 commit:

```text
TVC commit: a7e3ed7611c9abead988ec85b493cc396ac54b94
TVC PR: #335
exact StegVerse-Labs/.github source: 11cad666ff4a0ffeca39a725272f1ab905d9257d
reference mode: IMMUTABLE_COMMIT
selector order:
  astra_class_resilience_awareness
  quantum_resilience_awareness
  sv002_org_runtime_activation
```

That binding incorporates the standing-awareness refresh dependencies, WorkerCoordinator first-cycle ordering repair, and portable selector-admission correction while preserving TVC direct dispatch as the resident self-heal mechanism. TVC #335 additionally requires a current failure-free dispatch receipt, current `COMPLETED` or `ALREADY_CONSUMED` outcomes for all three consumers, and rejects stale terminal SV002 evidence from bypassing current awareness gates.

Moving `main` is not a runtime source identity. The TVC request remains exact-SHA/immutable-commit bound, secret-free, and TV/TVC credential-governed. A later `.github` source change is not automatically a prerequisite for this bounded TVC repair unless the exact runtime behavior it needs is absent from the pinned source.

## README completeness predicate

`README.md` inspected before mutation.

Determination: `NO_README_CHANGE_REQUIRED` for the original `.github` source-refresh dependency repair and for the later immutable-source identity reconciliation.

Evidence-supported reason: the README already defines the externally meaningful resident self-heal/source-refresh contract: local-only refresh of canonical WorkerCoordinator dependencies, no network fetch or credential acquisition, no second carrier/worker/scheduler, preservation of mutable runtime state, and no inference of runtime execution from refresh. The source repair restored omitted static files inside that already-documented parity contract. Replacing stale handoff commit references with the already-merged TVC #335 binding changes no repository behavior, runtime semantics, interface, authority/evidence semantics, prerequisite, dependency, failure behavior, or capability meaning.

Preflight receipt: `receipts/preflight/SV002-TVC-335-SOURCE-IDENTITY-RECONCILIATION-20260906.json`.

Focused test: `tests/test_resident_refresh_awareness_dependencies.py`.

## Evidence boundary

Source merge or CI success proves only source/control completeness. Authentic runtime closure still requires the existing resident path to produce:

- `receipts/sovereign-host/astra-class-resilience-awareness.latest.json` with completed standing awareness;
- `receipts/sovereign-host/quantum-resilience-awareness.latest.json` with completed standing awareness;
- `receipts/sovereign-host/resident-request-dispatch.latest.json` for the exact selector set;
- `receipts/sovereign-host/sv002-org-runtime-activation.latest.json` with `terminal_round_trip_observed=true`.

For the current TVC #335 path, the dispatch receipt must also be current, failure-free, `selection_scope=EXACT_SELECTOR`, and show all three selected consumers with current outcomes `COMPLETED` or `ALREADY_CONSUMED`. Stale terminal SV002 evidence cannot bypass either standing-awareness prerequisite.

HB progression, source presence, source refresh, CI, merge, or TVC materialization alone does not satisfy those runtime predicates.

## User work

NONE. Do not rerun HB30/HB31, do not provision another machine, and do not create or restore a hosted runtime.

## Portable bridge selector admission correction — 2026-09-06

A separate post-merge inspection found a real seam in the canonical one-selector portable bridge: `scripts/refresh_and_dispatch_resident_requests.py` did not admit either standing-awareness selector even though the canonical dispatcher registered both consumers and local source refresh materialized their dependencies.

The existing portable bridge now admits, without changing its one-selector-per-invocation contract:

```text
astra_class_resilience_awareness
quantum_resilience_awareness
sv002_org_runtime_activation
```

Portable one-selector callers may therefore invoke those existing consumers in prerequisite order and must stop before SV002 activation if an awareness dispatch fails.

This portable-bridge correction is **not** the dispatch mechanism used by the current TVC resident self-heal at `a7e3ed7611c9abead988ec85b493cc396ac54b94`. That TVC implementation consumes exact `.github@11cad666ff4a0ffeca39a725272f1ab905d9257d`, refreshes source, and invokes `scripts/dispatch_resident_execution_requests.py` directly with all three exact selectors in one dispatcher visit. The portable correction remains valid for portable callers, but it must not be represented as a missing prerequisite or failure cause for the TVC direct-dispatch path.

This is source/interface clarification only. Authentic standing-awareness receipts and the terminal SV002 round trip remain unobserved.
