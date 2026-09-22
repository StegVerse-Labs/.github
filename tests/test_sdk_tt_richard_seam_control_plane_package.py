from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "scripts/build_control_plane_source_package.py"

REQUIRED = {
    "heartbeat_runtime/worker_runtime.py",
    "heartbeat_runtime/admitted_worker_runtime.py",
    "heartbeat_runtime/worker_assignment_functional_memory.py",
    "workers/canonical_state_transition_custody.py",
    "control/worker-registry.d/stegfin-live-entry-003.json",
    "heartbeat_runtime/worker_runtime_legacy.py",
    "heartbeat_runtime/process_adapter.py",
    "workers/stegagents_governed_runtime_worker.py",
    "handoffs/SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001.json",
    "control/worker-registry.d/sdk-tt-richard-seam-authentic-runtime-001.json",
    "control/resident-execution-request.d/sdk-tt-richard-seam-authentic-runtime-001.json",
    "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py",
}

def test_control_plane_package_carries_complete_test3_atomic_seam_delta():
    source = PACKAGE.read_text(encoding="utf-8")
    for rel in REQUIRED:
        assert f'"{rel}"' in source
        assert source.count(f'"{rel}"') == 1


def test_control_plane_package_reusable_continues_only_through_existing_relay_contract():
    runner = (ROOT / "scripts/build_control_plane_source_package_reusable.py").read_text(encoding="utf-8")
    for rel in (
        "heartbeat_runtime/worker_runtime.py",
        "heartbeat_runtime/admitted_worker_runtime.py",
        "heartbeat_runtime/worker_assignment_functional_memory.py",
        "workers/canonical_state_transition_custody.py",
        "control/worker-registry.d/stegfin-live-entry-003.json",
    ):
        assert rel in runner
    assert 'RELAY_AUTH_ENV = "STEGVERSE_RELAY_EGRESS_AUTHORIZATION"' in runner
    assert 'RELAY_BINDING_ENV = "STEGVERSE_RELAY_EGRESS_BINDING"' in runner
    assert 'STEGOS_ROOT_ENV = "STEGVERSE_STEGOS_ROOT"' in runner
    assert '"state": "SOURCE_MATERIALIZED_VERIFIED"' in runner
    assert '"new_authorization_issued": False' in runner
    assert '"new_binding_created": False' in runner
    assert '"new_transport_created": False' in runner
    assert 'source_materialization_digest_mismatch' in runner
