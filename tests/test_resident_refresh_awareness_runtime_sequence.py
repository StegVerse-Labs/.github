from scripts.dispatch_resident_execution_requests import CONSUMERS
from scripts.refresh_and_dispatch_resident_requests import ALLOWED_TARGET_CONSUMERS


def test_sv002_awareness_prerequisites_precede_activation_in_existing_dispatcher():
    names = [name for name, _ in CONSUMERS]
    required = [
        "astra_class_resilience_awareness",
        "quantum_resilience_awareness",
        "sv002_org_runtime_activation",
    ]
    positions = [names.index(name) for name in required]
    assert positions == sorted(positions)
    assert len(set(positions)) == 3


def test_portable_bridge_admits_each_existing_sv002_awareness_sequence_selector():
    required = (
        "astra_class_resilience_awareness",
        "quantum_resilience_awareness",
        "sv002_org_runtime_activation",
    )
    assert all(selector in ALLOWED_TARGET_CONSUMERS for selector in required)
