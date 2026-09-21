import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workers"))
SPEC = importlib.util.spec_from_file_location("conversation_evidence_ingestion", ROOT / "workers" / "conversation_evidence_ingestion.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)

def fixture():
    return {
        "record_id":"CASE-001",
        "capture_method":"platform_export",
        "source_platform":"example",
        "source_locator_or_export_identity":"export-001",
        "captured_at":"2026-09-19T19:00:00Z",
        "conversation_start":"2026-09-01T00:00:00Z",
        "conversation_end":"2026-09-02T00:00:00Z",
        "participant_assertions":[{"participant_id":"p1"},{"participant_id":"p2"}],
        "message_sequence":[
            {"ordinal":1,"source_message_id":"m1","speaker_assertion":"p1","timestamp_assertion":"2026-09-01T00:00:00Z","timestamp_precision":"second","exact_content":"Service offered","attachment_ids":[]},
            {"ordinal":2,"source_message_id":"m2","speaker_assertion":"p2","timestamp_assertion":"2026-09-01T00:01:00Z","timestamp_precision":"second","exact_content":"Payment sent","attachment_ids":["receipt.bin"]},
        ],
        "authenticity":{"state":"PARTICIPANT_ATTESTED","verified_claims":["p2 submitted export"],"evidence_refs":[]},
        "transaction_binding":{"service_representation":"m1","payment_evidence":"receipt.bin","finding_state":"NOT_EVALUATED"},
    }

def test_package_is_deterministic_and_preserves_attachment_hash():
    source=fixture()
    a=mod.build_ingestion_package(source,{"receipt.bin":b"paid"})
    b=mod.build_ingestion_package(source,{"receipt.bin":b"paid"})
    assert a==b
    assert a["evidence_original"]["attachment_manifest"][0]["sha256"]==mod.digest_bytes(b"paid")
    assert a["transaction_binding"]["finding_state"]=="NOT_EVALUATED"
    assert a["authority_effect"]=="NONE_EVIDENCE_INGESTION_ONLY"

def test_write_once_rejects_second_materialization(tmp_path):
    package=mod.build_ingestion_package(fixture(),{"receipt.bin":b"paid"})
    mod.persist_ingestion_package(package,{"receipt.bin":b"paid"},tmp_path)
    try:
        mod.persist_ingestion_package(package,{"receipt.bin":b"paid"},tmp_path)
        assert False, "expected FileExistsError"
    except FileExistsError:
        pass

def test_custody_requires_exact_master_records_closure(monkeypatch):
    package=mod.build_ingestion_package(fixture(),{"receipt.bin":b"paid"})
    captured={}
    def fake_submit(receipt):
        captured["receipt"]=receipt
        digest=mod.sha256_uri(receipt).split(":",1)[1]
        return {
            "state":"RECORDED",
            "reconstruction_status":"PASS",
            "required_evidence_validation_status":"PASS",
            "receipt_sha256":digest,
            "reconstructed_receipt_sha256":digest,
            "master_records_grants_transition_authority":False,
        }
    monkeypatch.setattr(mod,"submit_state_receipt",fake_submit)
    result=mod.custody_ingestion(package)
    assert result["state"]=="RECORDED"
    manifest=captured["receipt"]["required_evidence_manifest"]
    assert [x["evidence_type"] for x in manifest]==[
        "CONVERSATION_EVIDENCE_ORIGINAL",
        "CONVERSATION_AUTHENTICITY_ENVELOPE",
        "SERVICE_TRANSACTION_BINDING",
    ]
    assert all(x["origin_transition_id"]==mod.TRANSITION_ID for x in manifest)
    assert captured["receipt"]["transition_evidence"]["publication_performed"] is False
    assert captured["receipt"]["transition_evidence"]["adjudication_performed"] is False

def test_custody_fails_closed_on_digest_mismatch(monkeypatch):
    package=mod.build_ingestion_package(fixture(),{"receipt.bin":b"paid"})
    monkeypatch.setattr(mod,"submit_state_receipt",lambda receipt:{
        "state":"RECORDED","reconstruction_status":"PASS",
        "required_evidence_validation_status":"PASS",
        "receipt_sha256":"a"*64,"reconstructed_receipt_sha256":"b"*64,
    })
    result=mod.custody_ingestion(package)
    assert result["state"]=="BOUNDARY"

def test_contract_is_consumed_unchanged_by_reference():
    contract=json.loads((ROOT/"contracts"/"conversation-evidence-service-performance-publication-contract.v1.json").read_text())
    assert contract["schema"]==mod.CONTRACT_SCHEMA
    assert contract["invariants"]["original_is_immutable"] is True
    assert contract["invariants"]["publication_is_not_adjudication"] is True
    assert contract["master_records"]["required_transition_results"]==[
        "RECORDED","reconstruction_status=PASS","required_evidence_validation_status=PASS","receipt_sha256==reconstructed_receipt_sha256"
    ]


def test_custody_binds_exact_predecessor_master_records_closure(monkeypatch):
    package=mod.build_ingestion_package(fixture(),{"receipt.bin":b"paid"})
    predecessor="a"*64
    closure={
        "transition_id":"WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
        "state":"RECORDED",
        "reconstruction_status":"PASS",
        "required_evidence_validation_status":"PASS",
        "receipt_sha256":predecessor,
        "reconstructed_receipt_sha256":predecessor,
        "master_record_ref":"master-record:state-transition:sha256:"+predecessor,
        "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }
    pred_evidence={
        "evidence_id":"predecessor-master-records-closure:"+mod.TRANSITION_ID,
        "evidence_type":"PREDECESSOR_MASTER_RECORDS_CLOSURE",
        "origin_transition_id":mod.TRANSITION_ID,
        "encoding":"canonical-json",
        "sha256":mod.sha256_uri(closure).split(":",1)[1],
        "content":closure,
    }
    monkeypatch.setattr(
        mod,
        "require_predecessor_master_records_closure",
        lambda receipt_sha256, successor_transition_id: (
            "sha256:"+predecessor,
            [pred_evidence],
        ) if receipt_sha256==predecessor and successor_transition_id==mod.TRANSITION_ID else (_ for _ in ()).throw(AssertionError("wrong predecessor")),
    )
    captured={}
    def fake_submit(receipt):
        captured["receipt"]=receipt
        digest=mod.sha256_uri(receipt).split(":",1)[1]
        return {
            "state":"RECORDED",
            "reconstruction_status":"PASS",
            "required_evidence_validation_status":"PASS",
            "receipt_sha256":digest,
            "reconstructed_receipt_sha256":digest,
        }
    monkeypatch.setattr(mod,"submit_state_receipt",fake_submit)
    result=mod.custody_ingestion(package,predecessor_receipt_sha256=predecessor)
    assert result["state"]=="RECORDED"
    receipt=captured["receipt"]
    assert receipt["prior_state_ref_or_hash"]=="sha256:"+predecessor
    assert receipt["required_evidence_manifest"][0]["evidence_type"]=="PREDECESSOR_MASTER_RECORDS_CLOSURE"
    assert receipt["required_evidence_manifest"][0]["content"]["receipt_sha256"]==predecessor
