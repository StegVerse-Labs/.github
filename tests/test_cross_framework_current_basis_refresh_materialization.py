from pathlib import Path


def test_current_basis_resident_consumer_is_materialized_by_source_refresh():
    source = Path("scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
    assert 'Path("scripts/consume_cross_framework_current_basis_v04_request.py")' in source


def test_current_basis_request_directory_is_materialized_by_source_refresh():
    source = Path("scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
    assert 'Path("control/resident-execution-request.d")' in source
