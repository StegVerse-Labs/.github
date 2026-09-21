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
