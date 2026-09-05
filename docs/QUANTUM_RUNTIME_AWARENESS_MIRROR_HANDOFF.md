# Quantum Runtime Awareness Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `QUANTUM-RESILIENCE-001` / `.github#1008`  
Issue: `#1011`  
Subgoal: `QUANTUM-RUNTIME-AWARENESS-001`  
State: `SOURCE_IMPLEMENTED / RESIDENT_CONSUMPTION_REQUIRED`

## Purpose

Materialize the canonical quantum-resilience contract and crypto census as standing resident awareness for StegVerse-001, StegVerse-002 and SV-011 through the existing HeartBeat-separated native WorkerCoordinator. No new scheduler, heartbeat, credential path or runtime host is introduced.

## Source implementation

- `scripts/consume_quantum_resilience_awareness_request.py`
- `control/resident-execution-request.d/quantum-resilience-sv001-awareness-001.json`
- `control/resident-execution-request.d/quantum-resilience-sv002-awareness-001.json`
- `control/resident-execution-request.d/quantum-resilience-sv011-awareness-001.json`
- `tests/test_quantum_resilience_runtime_awareness.py`
- `tests/test_quantum_resilience_dispatch_binding.py`
- dispatcher registration: `quantum_resilience_awareness`

The quantum awareness consumer is ordered before the protected SV001/SV002/SV011 consumers. Those protected consumers require both the existing Astra standing-awareness state and the quantum standing-awareness state. Missing or contradictory quantum state fails closed as `QUANTUM_STANDING_AWARENESS_REQUIRED`.

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

## Runtime success gate

Runtime awareness is proven only when the resident WorkerCoordinator consumes `quantum_resilience_awareness` and the aggregate receipt is `COMPLETED` with `entity_count=3`, `runtime_awareness_materialized=true`, `standing_directive_active=true`, exact contract/census hashes, and three matching entity states/receipts.

Until those artifacts exist, state remains `RESIDENT_CONSUMPTION_REQUIRED` and `.github#1011` must remain open.
