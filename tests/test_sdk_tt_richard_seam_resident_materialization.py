from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFRESH = ROOT / "scripts/refresh_sovereign_worker_runtime_source.py"
PACKAGE = ROOT / "scripts/build_control_plane_source_package.py"

REQUEST = "control/resident-execution-request.d/sdk-tt-richard-seam-authentic-runtime-001.json"
CONSUMER = "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py"

def test_local_source_refresh_materializes_test3_consumer():
    source = REFRESH.read_text(encoding="utf-8")
    assert f'Path("{CONSUMER}")' in source
    assert 'Path("control/resident-execution-request.d")' in source

def test_control_plane_delta_carries_test3_request_and_consumer():
    source = PACKAGE.read_text(encoding="utf-8")
    assert f'"{REQUEST}"' in source
    assert f'"{CONSUMER}"' in source
    assert source.count(f'"{REQUEST}"') == 1
    assert source.count(f'"{CONSUMER}"') == 1
