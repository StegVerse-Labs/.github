from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts/run_canonical_work_event_bootstrap.py"


def test_canonical_work_ingress_is_applied_to_resident_registry() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    start = text.index("def persist_registry(")
    end = text.index("\ndef main()", start)
    body = text[start:end]

    assert '"--apply"' in body
    assert '"--output"' not in body
    assert "persisted_post_ingress_registry_invalid" in body
    assert "persisted_post_ingress_shard_invalid" in body


def test_bootstrap_receipt_records_persisted_resident_state() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert '"persisted_registry_ref": str(persisted_registry_path)' in text
    assert '"resident_registry_state_persisted": True' in text
