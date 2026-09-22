from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "consume_ecosystem_receipt_hb_checkpoint.py"
SPEC = importlib.util.spec_from_file_location("hb_checkpoint_observer_test", MODULE_PATH)
assert SPEC and SPEC.loader
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)


def _creation() -> dict:
    return {
        "schema": "stegverse.heartbeat-reference/v1",
        "protocol": "STEGVERSE_HEARTBEAT_100HZ_OSCILLATOR_V1",
        "heartbeat_id": "HB-0000002S",
        "heartbeat_epoch": 100,
        "heartbeat_generation": 100,
        "sampled_unix_ns": 1787511600680000000,
        "reference_frame": "heartbeat_epoch:100",
        "authority_effect": "NONE_REFERENCE_ONLY",
        "grants_execution_authority": False,
        "grants_transition_authority": False,
        "grants_custody_authority": False,
        "grants_credential_authority": False,
    }


def _projection(receipt_sha: str) -> dict:
    return {
        "state": "PASS",
        "schema": "stegverse.master-records.receipt-set-commitment/v1",
        "master_records_commitment_profile": "ORDERED_CANONICAL_RECEIPT_SHA256_BOUNDED_RANGE_V1",
        "master_records_receipt_set_root_sha256": "2" * 64,
        "master_records_receipt_count": 1,
        "master_records_query_floor": 1,
        "master_records_query_ceiling": 1,
        "ordered_receipt_identities": [{"custody_ordinal": 1, "receipt_sha256": receipt_sha}],
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE_CUSTODY_COMMITMENT_ONLY",
    }


def test_waits_without_authentic_hb_successor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        observer,
        "build_master_records_receipt_set_commitment",
        lambda floor, ceiling: {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_HB_SUCCESSOR_RANGE_NOT_AVAILABLE",
            "authority_effect": "NONE",
        },
    )
    result = observer.observe(tmp_path)
    assert result["state"] == "WAITING_FOR_MASTER_RECORDS_HB_SUCCESSOR"
    assert result["runtime_checkpoint_created"] is False
    assert result["node_kv_witness_advanced"] is False
    assert result["external_anchor_advanced"] is False


def test_commits_only_after_exact_reconstruction_and_both_hb_refs(monkeypatch, tmp_path: Path) -> None:
    receipt_sha = "a" * 64
    creation = _creation()
    recording = {**_creation(), "heartbeat_id": "HB-0000002T", "heartbeat_epoch": 101, "heartbeat_generation": 101, "reference_frame": "heartbeat_epoch:101"}
    monkeypatch.setattr(observer, "build_master_records_receipt_set_commitment", lambda floor, ceiling: _projection(receipt_sha))
    monkeypatch.setattr(
        observer,
        "reconstruct_state_receipt",
        lambda value: {
            "state": "PASS",
            "receipt_sha256": receipt_sha,
            "reconstructed_receipt_sha256": receipt_sha,
            "required_evidence_validation_status": "PASS",
            "master_record_ref": "master-record:state-transition:sha256:" + receipt_sha,
            "receipt": {"hb_creation_reference": creation},
            "hb_recording_reference": recording,
            "recorded_receipt_sha256": receipt_sha,
            "master_records_custody_ordinal": 1,
            "hb_evidence_class": "HB_BOUND_SUCCESSOR",
            "master_records_grants_transition_authority": False,
        },
    )
    monkeypatch.setattr(observer, "current_hb_creation_reference", lambda: {**_creation(), "heartbeat_epoch": 102, "heartbeat_generation": 102, "heartbeat_id": "HB-0000002U", "reference_frame": "heartbeat_epoch:102"})
    result = observer.observe(tmp_path)
    assert result["state"] == "AUTHENTIC_FIRST_SUCCESSOR_CHECKPOINT_COMMITTED"
    assert result["receipt_sha256"] == receipt_sha
    assert result["reconstructed_receipt_sha256"] == receipt_sha
    assert result["hb_creation_reference"] == creation
    assert result["hb_recording_reference"] == recording
    assert result["master_records_receipt_set_commitment"]["master_records_query_floor"] == 1
    assert result["master_records_receipt_set_commitment"]["master_records_query_ceiling"] == 1
    assert result["hb_checkpoint_commitment"]["master_records_receipt_set_root_sha256"] == "2" * 64
    assert result["hb_checkpoint_commitment"]["anchor_inheritance_floor_hb_reference"] == creation
    assert result["node_kv_witness_advanced"] is False
    assert result["external_anchor_advanced"] is False


def test_fails_closed_if_recording_hb_metadata_is_missing(monkeypatch, tmp_path: Path) -> None:
    receipt_sha = "b" * 64
    monkeypatch.setattr(observer, "build_master_records_receipt_set_commitment", lambda floor, ceiling: _projection(receipt_sha))
    monkeypatch.setattr(
        observer,
        "reconstruct_state_receipt",
        lambda value: {
            "state": "PASS",
            "receipt_sha256": receipt_sha,
            "reconstructed_receipt_sha256": receipt_sha,
            "required_evidence_validation_status": "PASS",
            "receipt": {"hb_creation_reference": _creation()},
            "hb_recording_reference": None,
            "recorded_receipt_sha256": receipt_sha,
            "master_records_custody_ordinal": 1,
            "hb_evidence_class": "HB_BOUND_SUCCESSOR",
            "master_records_grants_transition_authority": False,
        },
    )
    try:
        observer.observe(tmp_path)
    except RuntimeError as exc:
        assert str(exc) == "first successor recording HB reference missing"
    else:
        raise AssertionError("missing recording HB metadata must fail closed")


def test_dispatcher_and_refresh_carry_existing_observer() -> None:
    dispatcher = (ROOT / "scripts" / "dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
    refresh = (ROOT / "scripts" / "refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
    custody = (ROOT / "workers" / "canonical_state_transition_custody.py").read_text(encoding="utf-8")
    assert '("ecosystem_receipt_hb_checkpoint", "scripts/consume_ecosystem_receipt_hb_checkpoint.py")' in dispatcher
    assert '"WAITING_FOR_MASTER_RECORDS_HB_SUCCESSOR", "AUTHENTIC_FIRST_SUCCESSOR_CHECKPOINT_COMMITTED"' in dispatcher
    assert 'Path("scripts/consume_ecosystem_receipt_hb_checkpoint.py")' in refresh
    assert "canonical_state_transition_hb_recording_metadata" in custody
    assert "build_master_records_receipt_set_commitment" in custody
