from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "scripts/build_control_plane_source_package.py"

REQUIRED = {
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
