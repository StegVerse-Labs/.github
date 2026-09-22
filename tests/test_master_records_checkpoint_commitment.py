from __future__ import annotations

from heartbeat_runtime.master_records_checkpoint_commitment import build_checkpoint_commitment, verify_checkpoint_commitment


def hb(epoch: int = 100) -> dict:
    return {
        "schema": "stegverse.heartbeat-reference/v1",
        "protocol": "STEGVERSE_HEARTBEAT_100HZ_OSCILLATOR_V1",
        "heartbeat_id": "HB-0000002S",
        "heartbeat_epoch": epoch,
        "heartbeat_generation": epoch,
        "sampled_unix_ns": 1787511600680000000,
        "reference_frame": f"heartbeat_epoch:{epoch}",
        "authority_effect": "NONE_REFERENCE_ONLY",
        "grants_execution_authority": False,
        "grants_transition_authority": False,
        "grants_custody_authority": False,
        "grants_credential_authority": False,
    }


def projection() -> dict:
    return {
        "schema": "stegverse.master-records.receipt-set-commitment/v1",
        "master_records_commitment_profile": "ORDERED_CANONICAL_RECEIPT_SHA256_BOUNDED_RANGE_V1",
        "master_records_receipt_set_root_sha256": "1" * 64,
        "master_records_receipt_count": 3,
        "master_records_query_floor": 7,
        "master_records_query_ceiling": 9,
        "authority_effect": "NONE_CUSTODY_COMMITMENT_ONLY",
    }


def test_checkpoint_binds_exact_master_records_root_and_hb_reference() -> None:
    value = build_checkpoint_commitment(hb_reference=hb(), master_records_projection=projection())
    assert value["master_records_receipt_set_root_sha256"] == "1" * 64
    assert value["master_records_query_floor"] == 7
    assert value["master_records_query_ceiling"] == 9
    assert value["hb_reference"]["heartbeat_epoch"] == 100
    assert value["authority_effect"] == "NONE_EVIDENCE_COMMITMENT_ONLY"
    assert verify_checkpoint_commitment(value)


def test_checkpoint_tamper_changes_digest() -> None:
    value = build_checkpoint_commitment(hb_reference=hb(), master_records_projection=projection())
    altered = dict(value)
    altered["master_records_receipt_set_root_sha256"] = "2" * 64
    assert not verify_checkpoint_commitment(altered)


def test_checkpoint_rejects_noncontiguous_projection() -> None:
    bad = projection()
    bad["master_records_receipt_count"] = 2
    try:
        build_checkpoint_commitment(hb_reference=hb(), master_records_projection=bad)
    except ValueError as exc:
        assert str(exc) == "master_records_query_bounds_not_contiguous"
    else:
        raise AssertionError("expected fail-closed")
