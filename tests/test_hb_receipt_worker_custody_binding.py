from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_carrier_self_heal_preserves_canonical_master_records_binding_names() -> None:
    text = (ROOT / "scripts/repair_resident_worker_presence.py").read_text(encoding="utf-8")
    for name in (
        "STEGVERSE_MASTER_RECORDS_ENDPOINT",
        "STEGVERSE_MASTER_RECORDS_TOKEN",
        "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
        "MASTER_RECORDS_DB",
        "MASTER_RECORDS_RECEIPT_KEY",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
    ):
        assert name in text
    assert "CANONICAL_CUSTODY_ENV" in text
    assert "name not in CANONICAL_CUSTODY_ENV" in text


def test_direct_worker_service_preserves_same_canonical_custody_binding_names() -> None:
    text = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
    for name in (
        "STEGVERSE_MASTER_RECORDS_ENDPOINT",
        "STEGVERSE_MASTER_RECORDS_TOKEN",
        "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
        "MASTER_RECORDS_DB",
        "MASTER_RECORDS_RECEIPT_KEY",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
    ):
        assert name in text


def test_clean_native_materialization_carries_existing_hb_checkpoint_consumer() -> None:
    text = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
    assert '"scripts/consume_ecosystem_receipt_hb_checkpoint.py"' in text


def test_carrier_registration_preserves_bindings_for_self_healed_worker(tmp_path) -> None:
    from scripts import install_sovereign_heartbeat_service as installer

    config = tmp_path / "config"
    runtime = tmp_path / "runtime"
    values = {
        "XDG_CONFIG_HOME": str(config),
        "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(ROOT),
        "STEGVERSE_MASTER_RECORDS_ENDPOINT": "http://127.0.0.1:8765",
        "STEGVERSE_MASTER_RECORDS_TOKEN": "canonical-local-token",
        "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS": "10",
        "MASTER_RECORDS_DB": str(tmp_path / "master-records.db"),
        "MASTER_RECORDS_RECEIPT_KEY": "canonical-local-key",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
        "GITHUB_TOKEN": "must-not-propagate",
    }
    rendered = installer.materialize_service(runtime, system="linux", env=values)
    carrier = Path(rendered["carrier_registration_path"]).read_text(encoding="utf-8")
    worker = Path(rendered["worker_registration_path"]).read_text(encoding="utf-8")
    for name in installer.WORKER_SAFE_LOCAL_BINDINGS:
        if values.get(name):
            assert f"Environment={name}={values[name]}" in carrier
            assert f"Environment={name}={values[name]}" in worker
    assert "GITHUB_TOKEN" not in carrier
    assert "GITHUB_TOKEN" not in worker
