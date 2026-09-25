"""Non-authorizing source tests for the existing resident org-ledger readback."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batches  # noqa: E402
import organization_custody_readback as readback  # noqa: E402
from scripts import consume_organization_custody_readback_request as consumer  # noqa: E402


def source(name, task="SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001", outcome="OBSERVED"):
    content = {"event": name, "task": task}
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": name, "transition_sequence": 1,
        "subject_or_correlation_id": task, "transition_outcome": outcome,
        "required_evidence_manifest": [{
            "evidence_id": "exact:" + name, "evidence_type": "EXACT_SOURCE_BYTES",
            "origin_transition_id": name, "encoding": "canonical-json",
            "sha256": hashlib.sha256(org.canon(content)).hexdigest(),
            "content": content,
        }],
    }


def request(runtime, ids=None, *, request_id="custody-probe-1"):
    path = runtime / consumer.REQUEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {
        "schema": consumer.SCHEMA, "request_id": request_id,
        "task_id": consumer.TASK_ID, "cosv_task_vector": consumer.COSV,
        "mode": consumer.MODE, "state": "REQUESTED",
        "credential_authority": "TV/TVC", "request_grants_authority": False,
        "correlation_ids": ids or ["SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001"],
    }
    path.write_text(json.dumps(value))
    return path


def test_readback_complete_head_and_historical_sdk_match(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    first = org.aggregate_transition(source("SDK_INTR_DENY", outcome="DENY"))
    second = org.aggregate_transition(source("UNRELATED", task="OTHER"))
    result = readback.readback(tmp_path, correlation_ids=("SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001",))
    assert result["state"] == "VERIFIED_LOCAL_READBACK"
    assert result["head_receipt_sha256"] == second["receipt_sha256"]
    assert result["receipt_count"] == 2
    assert result["match_count"] == 1
    assert result["matching_transitions"][0]["organization_receipt_sha256"] == first["receipt_sha256"]
    assert result["matching_transitions"][0]["source_transition_outcome"] == "DENY"
    assert result["exact_source_receipts"][0]["transition_id"] == "SDK_INTR_DENY"
    assert result["master_records_reconstruction"] == "NOT_QUERIED"
    assert result["runtime_admission_inferred"] is False


def test_existing_batch_prefix_verified(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    org.aggregate_transition(source("FIRST"))
    closed = batches.close_batch("TASK_CLOSURE", root=tmp_path)
    org.aggregate_transition(source("SECOND", task="OTHER"))
    result = readback.readback(tmp_path, correlation_ids=("OTHER",))
    assert result["batch_count"] == 1
    assert result["batch_chain"] == "PASS"
    assert result["last_batch_id"] == closed["batch_id"]
    assert result["match_count"] == 1


def test_source_missing_fails_even_if_matching_task_was_unrelated(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    value = source("UNRELATED", task="OTHER")
    org.aggregate_transition(value)
    (tmp_path / "source-receipts" / (org.sha(value)[7:] + ".json")).unlink()
    with pytest.raises(ValueError, match="SOURCE_RECEIPT_MISSING"):
        readback.readback(tmp_path, correlation_ids=("SDK",))


def test_orphaned_receipt_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    a = org.aggregate_transition(source("FIRST"))
    b = org.aggregate_transition(source("SECOND"))
    (tmp_path / "HEAD.json").write_text(json.dumps({
        "organization": "StegVerse-Labs", "receipt_sha256": a["receipt_sha256"],
    }))
    with pytest.raises(ValueError, match="orphaned or omitted"):
        readback.readback(tmp_path, correlation_ids=("FIRST",))
    assert a["receipt_sha256"] != b["receipt_sha256"]


def test_readback_request_requires_private_runtime_file(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    assert consumer.consume(ROOT, runtime)["state"] == "NO_REQUEST"


def test_opt_in_request_writes_private_exact_bytes_and_sanitizes_stdout(monkeypatch, tmp_path):
    ledger, runtime = tmp_path / "ledger", tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("SDK_INTR_DENY", outcome="DENY"))
    request(runtime)
    summary = consumer.consume(ROOT, runtime)
    assert summary["state"] == "RECORDED_LOCAL_READBACK", summary
    assert summary["match_count"] == 1
    assert "exact_source_receipts" not in summary
    assert summary["session_origin_authenticated_by_this_consumer"] is False
    assert summary["master_records_reconstruction"] == "NOT_QUERIED"
    private = runtime / summary["private_artifact_location"]
    assert private.is_file()
    assert private.stat().st_mode & 0o777 == 0o600
    exact = json.loads(private.read_text())
    assert exact["exact_source_receipts"][0]["transition_id"] == "SDK_INTR_DENY"
    assert summary["private_artifact_sha256"] == "sha256:" + hashlib.sha256(org.canon(exact)).hexdigest()


def test_forged_request_scope_fails_without_private_artifact(monkeypatch, tmp_path):
    ledger, runtime = tmp_path / "ledger", tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("FIRST"))
    path = request(runtime)
    forged = json.loads(path.read_text())
    forged["cosv_task_vector"] = "99999999999999"
    path.write_text(json.dumps(forged))
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "READBACK_REQUEST_OWNER_OR_MODE_INVALID"
    assert not (runtime / consumer.OUTPUT_REL).exists()


def test_missing_head_returns_precise_local_boundary_not_intr_deny(tmp_path):
    runtime = tmp_path / "runtime"
    request(runtime)
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "BOUNDARY", result
    assert result["reason"] == "ORGANIZATION_HEAD_NOT_MATERIALIZED"
    assert result["master_records_reconstruction"] == "NOT_QUERIED"
    assert result["runtime_execution_proven"] is False


def test_hosted_source_environment_refused(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime"
    request(runtime)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "HOSTED_ENVIRONMENT_FORBIDDEN"
