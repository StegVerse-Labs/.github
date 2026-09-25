from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batches  # noqa: E402


def source(name: str, *, evidence: bool = True) -> dict:
    value={
        "schema":"stegverse.canonical-state-transition-receipt/v1",
        "transition_id":name,
        "transition_sequence":1,
        "subject_or_correlation_id":"task:local-replay",
        "transition_outcome":"OBSERVED",
        "required_evidence_manifest":[],
    }
    if evidence:
        content={"transition":name,"result":"exact"}
        value["required_evidence_manifest"]=[{
            "evidence_id":"evidence:"+name,
            "evidence_type":"EXACT_LOCAL_REPLAY",
            "origin_transition_id":name,
            "encoding":"canonical-json",
            "sha256":hashlib.sha256(org.canon(content)).hexdigest(),
            "content":content,
        }]
    return value


def test_org_exact_source_and_evidence_can_be_replayed_and_exported_offline(monkeypatch,tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT",str(tmp_path))
    claim=source("CLAIM")
    work=source("WORK")
    first=org.aggregate_transition(claim)
    second=org.aggregate_transition(work)
    batch=batches.close_batch("TASK_CLOSURE",root=tmp_path)
    prepared=batches.export_batch(tmp_path,batch["batch_id"])
    assert prepared["schema"]=="stegverse.master-records.organization-batch-submission/v1"
    assert prepared["batch"]==batch
    assert prepared["organization_receipts"]==[first,second]
    assert prepared["source_receipts"]==[claim,work]
    assert prepared["authority_requested"] is False
    assert prepared["custody_requested"] is True
    assert prepared["reconstruction_requested"] is True
    assert batch["acknowledgement_state"]=="PENDING_MASTER_RECORDS"
    assert not (tmp_path/"MASTER_RECORDS_ACK.json").exists()
    assert batches.export_batch(tmp_path,batch["batch_id"])==prepared
    source_dir=tmp_path/"source-receipts"
    assert len(list(source_dir.glob("*.json")))==2


def test_missing_source_blocks_export_without_claiming_master_records(monkeypatch,tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT",str(tmp_path))
    value=source("CLAIM")
    org.aggregate_transition(value)
    batch=batches.close_batch("TASK_CLOSURE",root=tmp_path)
    sidecar=tmp_path/"source-receipts"/(org.sha(value)[7:]+".json")
    sidecar.unlink()
    with pytest.raises(ValueError,match="source receipt unavailable"):
        batches.export_batch(tmp_path,batch["batch_id"])
    assert batches.verify_batch(tmp_path,batch["batch_id"])["master_records_acknowledgement"]=="NOT_ESTABLISHED"


def test_source_tamper_and_changed_context_fail_closed(monkeypatch,tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT",str(tmp_path))
    value=source("CLAIM")
    org.aggregate_transition(value)
    batch=batches.close_batch("TASK_CLOSURE",root=tmp_path)
    sidecar=tmp_path/"source-receipts"/(org.sha(value)[7:]+".json")
    modified=json.loads(sidecar.read_text())
    modified["required_evidence_manifest"][0]["content"]["result"]="forged"
    sidecar.write_text(json.dumps(modified))
    with pytest.raises(ValueError,match="required evidence digest mismatch"):
        batches.export_batch(tmp_path,batch["batch_id"])
    with pytest.raises(ValueError,match="retained organization source receipt conflict"):
        org.aggregate_transition(value)


def test_invalid_inline_required_evidence_never_appends_an_org_receipt(monkeypatch,tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT",str(tmp_path))
    value=source("CLAIM")
    value["required_evidence_manifest"][0]["sha256"]="0"*64
    with pytest.raises(ValueError,match="required evidence digest mismatch"):
        org.aggregate_transition(value)
    assert not (tmp_path/"HEAD.json").exists()
    assert not list((tmp_path/"receipts").glob("*.json"))


def test_exact_retry_reuses_org_receipt_and_retained_source_without_new_transition(monkeypatch,tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT",str(tmp_path))
    value=source("CLAIM")
    first=org.aggregate_transition(value)
    other=org.aggregate_transition(source("UNRELATED"))
    head=json.loads((tmp_path/"HEAD.json").read_text())
    again=org.aggregate_transition(value)
    assert again==first
    assert again["receipt_sha256"]!=other["receipt_sha256"]
    assert json.loads((tmp_path/"HEAD.json").read_text())==head
    assert len(list((tmp_path/"source-receipts").glob("*.json")))==2
    batch=batches.close_batch("TASK_CLOSURE",root=tmp_path)
    assert batches.export_batch(tmp_path,batch["batch_id"])["source_receipts"][0]==value
