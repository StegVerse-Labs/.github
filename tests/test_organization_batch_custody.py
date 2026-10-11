from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batch  # noqa: E402


def receipt(name: str) -> dict:
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": name,
        "transition_sequence": 1,
        "subject_or_correlation_id": "test-worker",
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [],
    }


def append(monkeypatch, root: Path, name: str) -> tuple[dict, dict]:
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(root))
    source = receipt(name)
    return source, org.aggregate_transition(source)


def test_close_and_verify_two_contiguous_batches(monkeypatch, tmp_path):
    source1, first = append(monkeypatch, tmp_path, "CLAIM")
    source2, second = append(monkeypatch, tmp_path, "WORK")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    assert closed["contiguous_receipt_range"] == [1, 2]
    assert closed["ordered_receipt_hashes"] == [first["receipt_sha256"], second["receipt_sha256"]]
    assert closed["acknowledgement_state"] == batch.ACK
    assert closed["required_evidence_scope"] == "ORGANIZATION_BOUNDARY_REFERENCES_ONLY"
    assert batch.verify_batch(tmp_path, closed["batch_id"])["organization_chain"] == "PASS"
    assert batch.verify_batch(
        tmp_path, closed["batch_id"],
        source_receipts={org.sha(source1): source1, org.sha(source2): source2},
    )["source_reconstruction"] == "SOURCE_DIGESTS_AND_REQUIRED_EVIDENCE_BYTES_PASS"
    assert batch.close_batch("TASK_CLOSURE", root=tmp_path) == closed
    _, third = append(monkeypatch, tmp_path, "EXPIRE")
    after = batch.close_batch("WORKER_EXPIRY", root=tmp_path)
    assert after["contiguous_receipt_range"] == [3, 3]
    assert after["previous_batch_commitment"] == closed["batch_id"]
    assert after["cross_boundary_predecessor_refs"] == [second["receipt_sha256"]]
    assert after["ordered_receipt_hashes"] == [third["receipt_sha256"]]
    assert batch.verify_batch(tmp_path, after["batch_id"])["state"] == "PASS"
    assert len(list((tmp_path / "batches").glob("*.json"))) == 2


def test_missing_or_tampered_individual_receipt_fails_closed(monkeypatch, tmp_path):
    _, first = append(monkeypatch, tmp_path, "CLAIM")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    path = tmp_path / "receipts" / (first["receipt_sha256"][7:] + ".json")
    saved = path.read_text()
    path.write_text(saved.replace("CLAIM", "ALTERED"))
    with pytest.raises(ValueError, match="hash mismatch"):
        batch.verify_batch(tmp_path, closed["batch_id"])
    with pytest.raises(ValueError, match="hash mismatch"):
        batch.close_batch("TASK_CLOSURE", root=tmp_path)
    path.unlink()
    with pytest.raises(ValueError, match="missing"):
        batch.verify_batch(tmp_path, closed["batch_id"])


def test_broken_predecessor_chain_cannot_close(monkeypatch, tmp_path):
    _, first = append(monkeypatch, tmp_path, "CLAIM")
    _, second = append(monkeypatch, tmp_path, "EXECUTION")
    second_path = tmp_path / "receipts" / (second["receipt_sha256"][7:] + ".json")
    altered = json.loads(second_path.read_text())
    altered["previous_receipt_sha256"] = None
    altered_body = dict(altered)
    altered_body.pop("receipt_sha256")
    # An otherwise internally well-hashed forged immutable receipt is still
    # rejected because HEAD and predecessor linkage disagree.
    altered["receipt_sha256"] = org.sha(altered_body)
    forged = tmp_path / "receipts" / (altered["receipt_sha256"][7:] + ".json")
    second_path.unlink()
    forged.write_text(json.dumps(altered))
    head_path = tmp_path / "HEAD.json"
    head = json.loads(head_path.read_text())
    head["receipt_sha256"] = altered["receipt_sha256"]
    head["receipt_path"] = str(forged)
    head_path.write_text(json.dumps(head))
    with pytest.raises(ValueError, match="orphaned or omitted"):
        batch.close_batch("TASK_CLOSURE", root=tmp_path)


def test_invalid_source_or_changed_closure_refused(monkeypatch, tmp_path):
    source, _ = append(monkeypatch, tmp_path, "CLAIM")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    with pytest.raises(ValueError, match="conflicting batch closure"):
        batch.close_batch("WORKER_EXPIRY", root=tmp_path)
    with pytest.raises(ValueError, match="source transition receipt missing or invalid"):
        batch.verify_batch(tmp_path, closed["batch_id"], source_receipts={})
    altered = dict(source, transition_id="OTHER")
    with pytest.raises(ValueError, match="source transition receipt missing or invalid"):
        batch.verify_batch(
            tmp_path, closed["batch_id"],
            source_receipts={org.sha(source): altered},
        )


def test_batch_commitment_tamper_and_head_tamper_fail_closed(monkeypatch, tmp_path):
    append(monkeypatch, tmp_path, "CLAIM")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    path = tmp_path / "batches" / (closed["batch_id"][7:] + ".json")
    tampered = dict(closed, closure_reason="WORKER_EXPIRY")
    path.write_text(json.dumps(tampered))
    with pytest.raises(ValueError, match="organization batch hash mismatch"):
        batch.verify_batch(tmp_path, closed["batch_id"])
    path.write_text(json.dumps(closed))
    head_path = tmp_path / "BATCH_HEAD.json"
    head = json.loads(head_path.read_text())
    head["last_org_receipt_sha256"] = "sha256:" + "0" * 64
    head_path.write_text(json.dumps(head))
    with pytest.raises(ValueError, match="organization batch HEAD mismatch"):
        batch.close_batch("TASK_CLOSURE", root=tmp_path)


def test_empty_close_invalid_reason_and_missing_custody_proof(monkeypatch, tmp_path):
    append(monkeypatch, tmp_path, "CLAIM")
    with pytest.raises(ValueError, match="unsupported"):
        batch.close_batch("UNREVIEWED", root=tmp_path)
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    assert batch.verify_batch(tmp_path, closed["batch_id"])["master_records_acknowledgement"] == "NOT_ESTABLISHED"
    assert "master_record_ref" not in closed
    assert closed["authority_effect"] == "NONE_BATCH_CUSTODY_PROPOSAL_ONLY"


def test_parent_manifest_releases_prior_packet_on_next_governed_transition(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    parent_manifest = {
        "schema": "test.parent-manifest/v1",
        "receipt_batch": {"release_condition": {"type": "COUNT", "count": 2}},
    }
    first = org.aggregate_transition(receipt("FIRST"), parent_manifest=parent_manifest)
    second = org.aggregate_transition(receipt("SECOND"), parent_manifest=parent_manifest)
    before = batch.open_packet_state(parent_manifest, root=tmp_path)
    assert before == {
        "receipt_count": 2, "release_count": 2, "release_condition_satisfied": True,
        "establishment_heartbeat_id": None, "expiry_heartbeat_id": None, "expired": False,
    }
    assert not (tmp_path / "BATCH_HEAD.json").exists()

    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id, "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY"
    })
    third = org.aggregate_transition(receipt("THIRD"), parent_manifest=parent_manifest)

    batch_head = json.loads((tmp_path / "BATCH_HEAD.json").read_text())
    released = batch._verified_batch(tmp_path, batch_head["batch_id"])
    assert released["closure_reason"] == "MANIFEST_RELEASE_CONDITION"
    assert released["ordered_receipt_hashes"] == [first["receipt_sha256"], second["receipt_sha256"]]
    assert released["last_org_receipt_sha256"] == second["receipt_sha256"]
    assert third["boundary_evidence"]["parent_manifest_released_batch"] == {
        "batch_id": released["batch_id"],
        "execution_result": "COMPLETED",
        "reason": None,
        "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY",
    }
    after = batch.open_packet_state(parent_manifest, root=tmp_path)
    assert after == {
        "receipt_count": 1, "release_count": 2, "release_condition_satisfied": False,
        "establishment_heartbeat_id": None, "expiry_heartbeat_id": None, "expired": False,
    }
    assert json.loads((tmp_path / "HEAD.json").read_text())["receipt_sha256"] == third["receipt_sha256"]


def test_parent_manifest_batch_release_condition_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    with pytest.raises(ValueError, match="receipt_batch policy required"):
        org.aggregate_transition(receipt("FIRST"), parent_manifest={"schema": "test.parent-manifest/v1"})
    with pytest.raises(ValueError, match="release count invalid"):
        org.aggregate_transition(receipt("FIRST"), parent_manifest={
            "receipt_batch": {"release_condition": {"type": "COUNT", "count": 0}}
        })
    assert not (tmp_path / "HEAD.json").exists()


def test_submit_released_batch_fail_closed_without_authentic_custody_surface(monkeypatch, tmp_path):
    source, _ = append(monkeypatch, tmp_path, "BATCH-CUSTODY")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    monkeypatch.delenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", raising=False)
    monkeypatch.delenv("STEGVERSE_MASTER_RECORDS_TOKEN", raising=False)
    result = batch.submit_released_batch(tmp_path, closed["batch_id"])
    assert result["state"] == "FAILED"
    assert result["execution_result"] == "FAILED"
    assert result["governance_disposition"] is None
    assert result["reason"] == "ORGANIZATION_BATCH_AUTHENTIC_CUSTODY_SURFACE_UNAVAILABLE"
    assert result["batch_id"] == closed["batch_id"]



def test_parent_manifest_release_preserves_failed_custody_execution_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    parent_manifest = {"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}}
    org.aggregate_transition(receipt("FIRST"), parent_manifest=parent_manifest)
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "FAILED", "execution_result": "FAILED", "batch_id": batch_id,
        "reason": "ORGANIZATION_BATCH_AUTHENTIC_CUSTODY_SURFACE_UNAVAILABLE",
        "governance_disposition": None, "authority_effect": "NONE",
    })
    successor = org.aggregate_transition(receipt("SECOND"), parent_manifest=parent_manifest)
    evidence = successor["boundary_evidence"]["parent_manifest_released_batch"]
    assert evidence["execution_result"] == "FAILED"
    assert evidence["reason"] == "ORGANIZATION_BATCH_AUTHENTIC_CUSTODY_SURFACE_UNAVAILABLE"
    assert evidence["batch_id"] == json.loads((tmp_path / "BATCH_HEAD.json").read_text())["batch_id"]



# --- Manifested receipt packet: t(0) establishment and HB(delta) expiry ---

sys.path.insert(0, str(ROOT))
from heartbeat_runtime import independent_oscillator as osc  # noqa: E402


def hb_now_ns(epoch: int) -> int:
    """Exact wall time at a heartbeat epoch; HB is derived, never sampled."""
    return osc.PROTOCOL_ANCHOR_UNIX_NS + (epoch - osc.PROTOCOL_ANCHOR_EPOCH) * osc.OSCILLATOR_PERIOD_NS


T0_EPOCH = osc.PROTOCOL_ANCHOR_EPOCH + 1_000
DELTA = 500


def established_manifest(count: int = 3, delta: int = DELTA, epoch: int = T0_EPOCH) -> dict:
    return {
        "schema": "test.parent-manifest/v1",
        "receipt_batch": {
            "release_condition": {"type": "COUNT", "count": count},
            "establishment": {
                "heartbeat_id": osc.encode_heartbeat_id(epoch),
                "expiry_delta_heartbeats": delta,
            },
        },
    }


def test_t0_establishment_is_the_packets_own_first_receipt(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    manifest = established_manifest()
    first = org.aggregate_transition(
        receipt("FOUR-PART-ASSIGNMENT"), parent_manifest=manifest,
        establishes_packet=True, now_ns=hb_now_ns(T0_EPOCH),
    )
    record = first["boundary_evidence"][batch.ESTABLISHMENT_KEY]
    assert record["establishment_kind"] == "MANIFEST_ASSIGNMENT_T0"
    assert record["establishment_heartbeat_id"] == osc.encode_heartbeat_id(T0_EPOCH)
    assert record["expiry_heartbeat_id"] == osc.encode_heartbeat_id(T0_EPOCH + DELTA)
    assert record["release_authorized_at_establishment"] is True
    assert record["released_batch"] is None

    state = batch.open_packet_state(manifest, root=tmp_path, now_ns=hb_now_ns(T0_EPOCH))
    assert state["receipt_count"] == 1
    assert state["establishment_heartbeat_id"] == osc.encode_heartbeat_id(T0_EPOCH)
    assert state["expired"] is False
    assert state["release_condition_satisfied"] is False


def test_expiry_releases_a_short_packet_from_its_own_t0(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    manifest = established_manifest(count=3)
    org.aggregate_transition(
        receipt("FOUR-PART-ASSIGNMENT"), parent_manifest=manifest,
        establishes_packet=True, now_ns=hb_now_ns(T0_EPOCH),
    )
    # One receipt short of COUNT; without expiry this packet would never release.
    before = batch.open_packet_state(manifest, root=tmp_path, now_ns=hb_now_ns(T0_EPOCH + DELTA - 1))
    assert before["expired"] is False and before["release_condition_satisfied"] is False
    at_expiry = batch.open_packet_state(manifest, root=tmp_path, now_ns=hb_now_ns(T0_EPOCH + DELTA))
    assert at_expiry["expired"] is True and at_expiry["release_condition_satisfied"] is True

    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id,
        "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY",
    })
    work = org.aggregate_transition(
        receipt("WORK"), parent_manifest=manifest, now_ns=hb_now_ns(T0_EPOCH + DELTA),
    )
    head = json.loads((tmp_path / "BATCH_HEAD.json").read_text())
    released = batch._verified_batch(tmp_path, head["batch_id"])
    assert released["closure_reason"] == "MANIFEST_RELEASE_DELTA_EXPIRY"
    assert len(released["ordered_receipt_hashes"]) == 1  # short batch, below COUNT
    assert json.loads((tmp_path / "HEAD.json").read_text())["receipt_sha256"] == work["receipt_sha256"]


def test_release_and_successor_establishment_are_one_receipt_at_member_one(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    manifest = established_manifest(count=2)
    org.aggregate_transition(
        receipt("FOUR-PART-ASSIGNMENT"), parent_manifest=manifest,
        establishes_packet=True, now_ns=hb_now_ns(T0_EPOCH),
    )
    org.aggregate_transition(receipt("WORK-1"), parent_manifest=manifest, now_ns=hb_now_ns(T0_EPOCH + 1))
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "FAILED", "execution_result": "FAILED", "batch_id": batch_id,
        "reason": "ORGANIZATION_BATCH_AUTHENTIC_CUSTODY_SURFACE_UNAVAILABLE",
        "governance_disposition": None, "authority_effect": "NONE",
    })
    work2 = org.aggregate_transition(receipt("WORK-2"), parent_manifest=manifest, now_ns=hb_now_ns(T0_EPOCH + 2))

    head = json.loads((tmp_path / "BATCH_HEAD.json").read_text())
    released = batch._verified_batch(tmp_path, head["batch_id"])
    rows = batch._segment(tmp_path, work2["receipt_sha256"], released["last_org_receipt_sha256"])
    assert len(rows) == 2, "successor packet is establishment receipt + the work receipt"
    establishment, work_row = rows
    assert establishment["org_transition_class"] == "ORGANIZATION_RECEIPT_PACKET_ESTABLISHMENT"
    record = establishment["boundary_evidence"][batch.ESTABLISHMENT_KEY]
    assert record["establishment_kind"] == "PRIOR_PACKET_RELEASE"
    # The release carries its own identity on its own receipt, and a FAILED
    # carriage is retained rather than discarded.
    assert record["released_batch"]["batch_id"] == released["batch_id"]
    assert record["released_batch"]["execution_result"] == "FAILED"
    assert establishment["boundary_evidence"]["parent_manifest_released_batch"]["batch_id"] == released["batch_id"]
    assert work_row["receipt_sha256"] == work2["receipt_sha256"]
    assert batch.ESTABLISHMENT_KEY not in work_row["boundary_evidence"]


def test_manifested_packet_without_t0_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    legacy = {"receipt_batch": {"release_condition": {"type": "COUNT", "count": 5}}}
    org.aggregate_transition(receipt("UNESTABLISHED"), parent_manifest=legacy)
    with pytest.raises(ValueError, match="no t\\(0\\) establishment record"):
        batch.open_packet_state(established_manifest(count=5), root=tmp_path, now_ns=hb_now_ns(T0_EPOCH))


def test_establishment_declaration_is_validated_and_required(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    with pytest.raises(ValueError, match="requires a manifest establishment declaration"):
        org.aggregate_transition(
            receipt("NO-DECLARATION"),
            parent_manifest={"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}},
            establishes_packet=True,
        )
    bad_hb = established_manifest()
    bad_hb["receipt_batch"]["establishment"]["heartbeat_id"] = "NOT-AN-HB"
    with pytest.raises(ValueError, match="establishment heartbeat invalid"):
        batch.open_packet_state(bad_hb, root=tmp_path)
    bad_delta = established_manifest()
    bad_delta["receipt_batch"]["establishment"]["expiry_delta_heartbeats"] = 0
    with pytest.raises(ValueError, match="expiry delta invalid"):
        batch.open_packet_state(bad_delta, root=tmp_path)
    assert not (tmp_path / "HEAD.json").exists()


def test_t0_cannot_also_release_a_prior_packet(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    manifest = established_manifest(count=1)
    org.aggregate_transition(
        receipt("FOUR-PART-ASSIGNMENT"), parent_manifest=manifest,
        establishes_packet=True, now_ns=hb_now_ns(T0_EPOCH),
    )
    with pytest.raises(ValueError, match="cannot also release a prior packet"):
        org.aggregate_transition(
            receipt("SECOND-T0"), parent_manifest=manifest,
            establishes_packet=True, now_ns=hb_now_ns(T0_EPOCH + 1),
        )
# --- Only the batched record crosses the organization boundary ---


def test_export_batch_record_carries_commitment_without_receipt_contents(monkeypatch, tmp_path):
    source1, _ = append(monkeypatch, tmp_path, "CLAIM")
    source2, _ = append(monkeypatch, tmp_path, "WORK")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)

    record = batch.export_batch_record(tmp_path, closed["batch_id"])
    assert record["schema"] == "stegverse.master-records.organization-batch-record-submission/v1"
    assert record["batch"] == closed
    assert record["receipt_contents_scope"] == "ORGANIZATION_LOCAL_ONLY_NOT_TRANSMITTED"
    # The organization proved reconstruction locally and carries the RESULT only.
    assert record["local_verification"] == {
        "organization_chain": "PASS",
        "source_reconstruction": "SOURCE_DIGESTS_AND_REQUIRED_EVIDENCE_BYTES_PASS",
        "receipt_count": 2,
    }
    assert "organization_receipts" not in record
    assert "source_receipts" not in record

    # No individual receipt body, source body or evidence byte may appear anywhere
    # in the serialized envelope - the commitment hashes are all that cross.
    blob = json.dumps(record, sort_keys=True)
    for transition_id in ("CLAIM", "WORK"):
        assert transition_id not in blob
    for schema in ("stegverse.organization-transition-receipt/v1",
                   "stegverse.canonical-state-transition-receipt/v1"):
        assert schema not in blob
    assert "required_evidence_manifest" not in blob


def test_released_batch_carriage_submits_the_record_not_the_contents(monkeypatch, tmp_path):
    append(monkeypatch, tmp_path, "CARRIED")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    captured = {}

    class FakeCustody:
        @staticmethod
        def submit_organization_batch(envelope):
            captured["envelope"] = envelope
            return {"state": "COMPLETED", "execution_result": "COMPLETED",
                    "batch_id": envelope["batch"]["batch_id"],
                    "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY"}

    def fake_spec(name, path):
        class Loader:
            @staticmethod
            def exec_module(module):
                module.submit_organization_batch = FakeCustody.submit_organization_batch
        class Spec:
            loader = Loader()
        return Spec()

    monkeypatch.setattr(batch.importlib.util, "spec_from_file_location", fake_spec)
    monkeypatch.setattr(batch.importlib.util, "module_from_spec", lambda spec: type("M", (), {})())
    result = batch.submit_released_batch(tmp_path, closed["batch_id"])
    assert result["state"] == "COMPLETED"
    sent = captured["envelope"]
    assert sent["schema"] == "stegverse.master-records.organization-batch-record-submission/v1"
    assert "organization_receipts" not in sent and "source_receipts" not in sent


def test_master_records_transport_is_not_invoked_inside_sovereign_append_lock():
    """Regression for #3080: downstream transport must not hold sovereign append hostage.

    This intentionally fails until the release path is split into an immutable
    committed outbox and post-commit delivery. A 10-second timeout is not enough.
    """
    import inspect

    held_source = inspect.getsource(org._aggregate_transition_held)
    assert "submit_released_batch(" not in held_source, (
        "Master Records transport still runs within the organization append lock; "
        "persist release evidence first and deliver outside the CAS transaction"
    )


def test_master_records_transport_does_not_determine_organization_receipt():
    """The sovereign receipt cannot depend on downstream network result fields."""
    import inspect

    held_source = inspect.getsource(org._aggregate_transition_held)
    assert 'release_execution_result = batches.submit_released_batch' not in held_source
    assert 'release_execution_result["state"]' not in held_source
