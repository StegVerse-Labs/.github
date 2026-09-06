from pathlib import Path

from scripts import refresh_sovereign_worker_runtime_source as refresh


def test_protected_consumer_awareness_dependencies_are_refreshed():
    required = {
        Path("scripts/consume_astra_class_resilience_awareness_request.py"),
        Path("scripts/consume_quantum_resilience_awareness_request.py"),
        Path("control/astra-class-adversarial-resilience-contract.json"),
        Path("control/quantum-resilience-contract.json"),
        Path("control/quantum-crypto-census.json"),
    }
    copied = set(refresh.STATIC_FILES) | set(refresh.CONTROL_FILES)
    assert required <= copied


def test_awareness_dependencies_are_static_not_runtime_state():
    for rel in (
        Path("scripts/consume_astra_class_resilience_awareness_request.py"),
        Path("scripts/consume_quantum_resilience_awareness_request.py"),
        Path("control/astra-class-adversarial-resilience-contract.json"),
        Path("control/quantum-resilience-contract.json"),
        Path("control/quantum-crypto-census.json"),
    ):
        refresh._assert_static_path(rel)
