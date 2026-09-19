from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_sdk_tt_richard_seam_test3.py"

def test_test3_runner_binds_exact_task_and_suite():
    source = RUNNER.read_text(encoding="utf-8")
    assert 'SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001' in source
    assert '20010000110000' in source
    assert 'ACTIVATE_TASK_AND_CREATE_BIND_WORKER' in source
    assert 'tests/test_sdk_tt_richard_atomic_activation_seam.py' in source
    assert 'tests/test_sdk_tt_richard_seam_resident_carriage.py' in source
    assert 'tests/test_sdk_tt_richard_seam_resident_materialization.py' in source
    assert 'tests/test_sdk_tt_richard_seam_control_plane_package.py' in source
    assert 'tests/test_purpose_bound_worker_runtime.py' in source
    assert 'TEST3_RICHARD_SEAM_ACCEPTANCE_PASS' in source
