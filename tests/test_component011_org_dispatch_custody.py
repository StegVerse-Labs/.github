"""Existing-organization receipt custody for the component-011 resident selector.

All invocations here are local fixture dispatches; no sovereign runtime proof is claimed.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator as _ImportOrder
from scripts import dispatch_resident_execution_requests as dispatch

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / dispatch.COMPONENT011_REQUEST_REL


def _outcome(*, attempted=True, state="ATTEMPT_RECORDED"):
    return [{
        "consumer": dispatch.COMPONENT011_SELECTOR,
        "consumer_ref": "scripts/consume_ungoverned_ai_defensive_envelope_request.py",
        "attempted": attempted,
        "state": state,
        "returncode": 0 if attempted else None,
        "result": {"state": state} if attempted else None,
    }]


def _request_at(runtime):
    path = runtime / dispatch.COMPONENT011_REQUEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(REQUEST.read_bytes())
    return path


def _stored(root, digest):
    return json.loads((root / "receipts" / (digest[7:] + ".json")).read_text())


def test_attempt_creates_exact_org_receipt_and_immediate_predecessor(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger"
    runtime = tmp_path / "runtime"
    _request_at(runtime)
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))

    first = dispatch.retain_component011_dispatch_in_organization(ROOT, runtime, _outcome())
    assert first["state"] == "RECORDED", first
    assert first["classification"] == "RESIDENT_REQUEST_DISPATCH_OBSERVATION_ONLY"
    assert first["exact_receipt_readback"] == "PASS"
    assert first["immediate_predecessor_sha256"] is None
    assert first["runtime_request_present"] is True
    assert first["attempted"] is True
    assert first["master_records_custody_claimed"] is False
    assert first["runtime_execution_proven"] is False
    source = json.loads((ledger / "source-receipts" / (first["source_transition_sha256"][7:] + ".json")).read_text())
    row = _stored(ledger, first["organization_receipt_sha256"])
    assert row["org_transition_class"] == "RESIDENT_REQUEST_DISPATCH_OBSERVATION"
    assert row["source_transition_sha256"] == first["source_transition_sha256"]
    assert source["transition_evidence"]["dispatch_grants_authority"] is False
    assert source["required_evidence_manifest"][0]["content"]["request_id"] == dispatch.COMPONENT011_REQUEST_ID

    second = dispatch.retain_component011_dispatch_in_organization(
        ROOT, runtime, _outcome(state="FAIL_CLOSED")
    )
    assert second["state"] == "RECORDED", second
    assert second["immediate_predecessor_sha256"] == first["organization_receipt_sha256"]
    assert _stored(ledger, second["organization_receipt_sha256"])["previous_receipt_sha256"] == first["organization_receipt_sha256"]
    assert json.loads((ledger / "HEAD.json").read_text())["receipt_sha256"] == second["organization_receipt_sha256"]


def test_missing_runtime_request_and_consumer_still_retains_exact_source_bound_observation(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    record = dispatch.retain_component011_dispatch_in_organization(
        ROOT, tmp_path / "runtime", _outcome(attempted=False, state="CONSUMER_NOT_MATERIALIZED")
    )
    assert record["state"] == "RECORDED", record
    assert record["runtime_request_present"] is False
    assert record["attempted"] is False
    assert record["consumer_outcome"] == "CONSUMER_NOT_MATERIALIZED"
    source = json.loads((ledger / "source-receipts" / (record["source_transition_sha256"][7:] + ".json")).read_text())
    evidence = source["required_evidence_manifest"][0]["content"]
    assert evidence["runtime_request_present"] is False
    assert evidence["attempted"] is False


def test_mismatched_runtime_request_fails_before_org_append(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger"
    runtime = tmp_path / "runtime"
    path = _request_at(runtime)
    forged = json.loads(path.read_text())
    forged["request_id"] = "FORGED_COMPONENT011_REQUEST"
    path.write_text(json.dumps(forged))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    result = dispatch.retain_component011_dispatch_in_organization(ROOT, runtime, _outcome())
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "COMPONENT011_REQUEST_IDENTITY_MISMATCH"
    assert not (ledger / "HEAD.json").exists()


def test_corrupted_org_predecessor_fails_before_appending(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger"
    runtime = tmp_path / "runtime"
    _request_at(runtime)
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    first = dispatch.retain_component011_dispatch_in_organization(ROOT, runtime, _outcome())
    assert first["state"] == "RECORDED", first
    path = ledger / "receipts" / (first["organization_receipt_sha256"][7:] + ".json")
    row = json.loads(path.read_text())
    row["source_transition_id"] = "FORGED_RECORDED_TRANSITION"
    path.write_text(json.dumps(row))
    result = dispatch.retain_component011_dispatch_in_organization(ROOT, runtime, _outcome())
    assert result["state"] == "BOUNDARY", result
    assert result["reason"] == "COMPONENT011_ORGANIZATION_DISPATCH_CUSTODY_FAILED"
    assert len(list((ledger / "receipts").glob("*.json"))) == 1


def test_dispatch_same_existing_path_retains_component011_org_outcome(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger"
    runtime = tmp_path / "runtime"
    _request_at(runtime)
    consumer = runtime / dict(dispatch.CONSUMERS)[dispatch.COMPONENT011_SELECTOR]
    consumer.parent.mkdir(parents=True, exist_ok=True)
    consumer.write_text("# inert consumer fixture\n")
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    def runner(command, **kwargs):
        assert command[2:] == ["--source-root", str(ROOT), "--runtime-root", str(runtime)]
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"state": "ATTEMPT_RECORDED"}) + "\n",
            stderr="",
        )
    result = dispatch.dispatch(
        ROOT, runtime, only_consumers=(dispatch.COMPONENT011_SELECTOR,),
        runner=runner, env={"PATH": "/bin"},
    )
    assert result["state"] == "DISPATCH_COMPLETE", result
    proof = result["component011_organization_dispatch"]
    assert proof["state"] == "RECORDED", proof
    assert proof["attempted"] is True
    assert proof["exact_receipt_readback"] == "PASS"
    assert _stored(ledger, proof["organization_receipt_sha256"])["source_transition_sha256"] == proof["source_transition_sha256"]


def test_dispatch_org_custody_failure_is_explicit_without_claiming_transition(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    _request_at(runtime)
    consumer = runtime / dict(dispatch.CONSUMERS)[dispatch.COMPONENT011_SELECTOR]
    consumer.parent.mkdir(parents=True, exist_ok=True)
    consumer.write_text("# inert consumer fixture\n")
    source = tmp_path / "incomplete-source"
    source.mkdir()
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "ledger"))
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout='{"state":"ATTEMPT_RECORDED"}\n', stderr="")
    result = dispatch.dispatch(
        source, runtime, only_consumers=(dispatch.COMPONENT011_SELECTOR,),
        runner=runner, env={"PATH": "/bin"},
    )
    assert result["state"] == "DISPATCH_INCOMPLETE"
    assert result["component011_organization_custody_failure"] is True
    assert result["component011_organization_dispatch"]["reason"] == "EXISTING_ORGANIZATION_LEDGER_PRODUCER_NOT_MATERIALIZED"
    assert result["outcomes"][0]["attempted"] is True
    assert not (tmp_path / "ledger" / "HEAD.json").exists()


def test_orphaned_existing_org_receipt_prevents_new_observation(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger"
    runtime = tmp_path / "runtime"
    _request_at(runtime)
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    first = dispatch.retain_component011_dispatch_in_organization(ROOT, runtime, _outcome())
    assert first["state"] == "RECORDED", first
    orphan = ledger / "receipts" / ("f" * 64 + ".json")
    orphan.write_text(json.dumps({"schema": "forged-orphan"}))
    result = dispatch.retain_component011_dispatch_in_organization(ROOT, runtime, _outcome())
    assert result["state"] == "BOUNDARY", result
    assert result["reason"] == "COMPONENT011_ORGANIZATION_DISPATCH_CUSTODY_FAILED"
    assert len(list((ledger / "receipts").glob("*.json"))) == 2
    assert json.loads((ledger / "HEAD.json").read_text())["receipt_sha256"] == first["organization_receipt_sha256"]
