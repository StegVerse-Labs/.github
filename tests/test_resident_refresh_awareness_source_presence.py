from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_awareness_source_dependencies_exist_in_canonical_checkout():
    required = (
        "scripts/consume_astra_class_resilience_awareness_request.py",
        "scripts/consume_quantum_resilience_awareness_request.py",
        "control/astra-class-adversarial-resilience-contract.json",
        "control/quantum-resilience-contract.json",
        "control/quantum-crypto-census.json",
    )
    missing = [rel for rel in required if not (ROOT / rel).is_file()]
    assert missing == []
