# Quantum Runtime Awareness Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `QUANTUM-RESILIENCE-001` / `.github#1008`  
Issue: `#1011`  
Subgoal: `QUANTUM-RUNTIME-AWARENESS-001`  
State: `SOURCE_MERGED_VALIDATED / RESIDENT_CONSUMPTION_REQUIRED`

## Purpose

Materialize the canonical quantum-resilience contract and crypto census as standing resident awareness for StegVerse-001, StegVerse-002 and SV-011 through the existing HeartBeat-separated native WorkerCoordinator. No new scheduler, heartbeat, credential path or runtime host is introduced.

## Merged source evidence

```text
PR: #1016
head: 4e9f60c9382122cf27f9960a62b0a6ed406bad9c
merge: ed936a020f540b8ba0b66e0156e608a9711235fe
Heartbeat Worker Project run: 33998703226 SUCCESS
Cross-Framework Current-Basis run: 33998703249 SUCCESS
Organization control-plane run: 33998703218 SUCCESS
```

These runs are source/control-plane validation only. They are not sovereign resident execution evidence.

## Source implementation

- `scripts/consume_quantum_resilience_awareness_request.py`
- `control/resident-execution-request.d/quantum-resilience-sv001-awareness-001.json`
- `control/resident-execution-request.d/quantum-resilience-sv002-awareness-001.json`
- `control/resident-execution-request.d/quantum-resilience-sv011-awareness-001.json`
- `tests/test_quantum_resilience_runtime_awareness.py`
- `tests/test_quantum_resilience_dispatch_binding.py`
- `scripts/validate_quantum_resilience_contract.py`
- `tests/test_quantum_resilience_contract.py`
- dispatcher registration: `quantum_resilience_awareness`

The quantum awareness consumer is ordered before the protected SV001/SV002/SV011 consumers. Those protected consumers require both the existing Astra standing-awareness state and the quantum standing-awareness state. Missing or contradictory quantum state fails closed as `QUANTUM_STANDING_AWARENESS_REQUIRED`.

The quantum contract validator was reconciled with the evolved census during PR #1016. It now preserves five known quantum-exposed asymmetric surfaces without misclassifying the two policy-migrated Ed25519 surfaces as still merely `CLASSICAL_ONLY`:

- three `CLASSICAL_ONLY`: current-phone P-256 device possession, continuity-vault-kit SKAP P-256 ECDH, TVC SKAP resident/browser P-256;
- two `HYBRID_MIGRATION_REQUIRED`: StegID Ed25519 continuity receipts and TVC Ed25519 signed policy material;
- zero `PQC_VALIDATED` surfaces.

## Expected resident artifacts

1. `runtime-state/entity-quantum-awareness/stegverse-001.json`
2. `runtime-state/entity-quantum-awareness/stegverse-002.json`
3. `runtime-state/entity-quantum-awareness/sv-011.json`
4. `receipts/sovereign-host/quantum-resilience/stegverse-001.latest.json`
5. `receipts/sovereign-host/quantum-resilience/stegverse-002.latest.json`
6. `receipts/sovereign-host/quantum-resilience/sv-011.latest.json`
7. `receipts/sovereign-host/quantum-resilience-awareness.latest.json`

## Authority invariants

- credential authority remains `TV/TVC`;
- GitHub token runtime authority remains `NONE`;
- HeartBeat grants no execution authority;
- quantum capability grants no authority;
- PQ signature/KEM validity grants no transition authority;
- InTr/Interlock remains the admissible transition boundary;
- existing WorkerCoordinator only;
- no second user-operated machine;
- source/merge/CI/request presence does not establish runtime awareness.

## Current machine task

```text
task: SHWP-QUANTUM-RESILIENCE-AWARENESS-001
selector: quantum_resilience_awareness
owner: existing heartbeat-separated native WorkerCoordinator
state: SOURCE_MERGED_REQUESTED_FOR_RESIDENT_CONSUMPTION
```

The resident runtime must materialize merge `ed936a020f540b8ba0b66e0156e608a9711235fe` or a descendant containing the same source, visit `quantum_resilience_awareness`, and retain the seven exact artifacts above.

## Runtime success gate

Runtime awareness is proven only when the resident WorkerCoordinator consumes `quantum_resilience_awareness` and the aggregate receipt is `COMPLETED` with `entity_count=3`, `runtime_awareness_materialized=true`, `standing_directive_active=true`, exact contract/census hashes, and three matching entity states/receipts.

Until those artifacts exist, state remains `RESIDENT_CONSUMPTION_REQUIRED` and `.github#1011` must remain open.

## Remaining machine work

1. Materialize merge `ed936a020f540b8ba0b66e0156e608a9711235fe` or a source-equivalent descendant into the sovereign resident source tree.
2. Dispatch `quantum_resilience_awareness` through the existing WorkerCoordinator/dispatcher.
3. Verify all seven artifacts and exact contract/census hash agreement.
4. Only after authentic receipt verification classify SV001/SV002/SV011 as quantum-resilience-aware.
5. Continue the parent quantum program's real ML-DSA, ML-KEM, device-possession, wallet, TLS/WebPKI and long-lived confidentiality work independently of this awareness activation gate.
