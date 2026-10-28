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


@pytest.fixture(autouse=True)
def source_only_simulated_resident(monkeypatch):
    # Hosted CI runs local fixtures only; no network or resident state is used.
    for name in consumer.HOSTED_ENV:
        monkeypatch.delenv(name, raising=False)


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
    summary = consumer._process_request(ROOT, runtime)
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
    result = consumer._process_request(ROOT, runtime)
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "READBACK_REQUEST_OWNER_OR_MODE_INVALID"
    assert not (runtime / consumer.OUTPUT_REL).exists()


def test_missing_head_returns_precise_local_boundary_not_intr_deny(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "empty-ledger"))
    request(runtime)
    result = consumer._process_request(ROOT, runtime)
    assert result["state"] == "BOUNDARY", result
    assert result["reason"] == "ORGANIZATION_HEAD_NOT_MATERIALIZED"
    assert result["master_records_reconstruction"] == "NOT_QUERIED"
    assert result["runtime_execution_proven"] is False


def test_unsupplied_ledger_root_is_its_own_boundary_and_nothing_is_derived(monkeypatch, tmp_path):
    # The ledger root is supplied by the materializer, never derived from the
    # host, so an unsupplied one is named as such rather than read from HOME.
    runtime, home = tmp_path / "runtime", tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_ROOT", raising=False)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_STATE_HOME", str(home / "state"))
    request(runtime)
    result = consumer._process_request(ROOT, runtime)
    assert result["state"] == "BOUNDARY", result
    assert result["reason"] == "ledger_location_required_from_materializer: STEGVERSE_ORG_LEDGER_ROOT"
    assert result["runtime_execution_proven"] is False
    assert list(home.iterdir()) == []


SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


@pytest.mark.parametrize("host", [{"CI": "true"}, {"GITHUB_ACTIONS": "true", "CI": "true"}, {}])
def test_bare_request_without_admitted_manifest_route_fails_closed_on_every_host(monkeypatch, tmp_path, host):
    # #1615 lane E: a host label neither admits nor refuses; the result is the same everywhere.
    ledger, runtime = tmp_path / "ledger", tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    for name, value in host.items():
        monkeypatch.setenv(name, value)
    org.aggregate_transition(source("SDK_INTR_DENY", outcome="DENY"))
    request(runtime)
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "FAIL_CLOSED", result
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failure_code"] == "MANIFEST_ROUTE_CONFORMANCE_NOT_ESTABLISHED"
    assert result["failed_predicate"] == "ADMITTED_MANIFEST_CAPABILITY_ROUTE_SELECTS_PROCESSING"
    assert all(isinstance(result[k], str) and result[k] for k in SIX_FIELDS)
    assert result["readback_executed"] is False
    assert "LEGACY_OPTIONAL_DIAGNOSTIC_HOSTED_ENVIRONMENT" not in json.dumps(result)
    assert not (runtime / consumer.OUTPUT_REL).exists()


def test_consumer_reads_no_host_label():
    text = Path(consumer.__file__).read_text(encoding="utf-8")
    assert "os.environ" not in text
    assert "LEGACY_OPTIONAL_DIAGNOSTIC_HOSTED_ENVIRONMENT" not in text


def test_exact_request_retry_keeps_original_immutable_snapshot_after_new_head(monkeypatch, tmp_path):
    ledger, runtime = tmp_path / "ledger", tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    original = org.aggregate_transition(source("FIRST"))
    request(runtime)
    first = consumer._process_request(ROOT, runtime)
    assert first["state"] == "RECORDED_LOCAL_READBACK"
    artifact = runtime / first["private_artifact_location"]
    original_bytes = artifact.read_bytes()
    org.aggregate_transition(source("AFTER_FIRST_READBACK", task="OTHER"))
    retry = consumer._process_request(ROOT, runtime)
    assert retry["state"] == "ALREADY_CONSUMED", retry
    assert retry["head_receipt_sha256"] == original["receipt_sha256"]
    assert retry["private_artifact_sha256"] == first["private_artifact_sha256"]
    assert artifact.read_bytes() == original_bytes
    request(runtime, request_id="custody-probe-2")
    latest = consumer._process_request(ROOT, runtime)
    assert latest["state"] == "RECORDED_LOCAL_READBACK"
    assert latest["receipt_count"] == 2
    assert latest["private_artifact_sha256"] != first["private_artifact_sha256"]


def test_inline_evidence_tampering_detected_before_readback(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    exact = source("BOUND")
    org.aggregate_transition(exact)
    path = ledger / "source-receipts" / (org.sha(exact)[7:] + ".json")
    changed = json.loads(path.read_text())
    changed["required_evidence_manifest"][0]["content"]["event"] = "TAMPERED"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="required evidence digest mismatch"):
        readback.readback(ledger, correlation_ids=("BOUND",))



def test_existing_master_records_exact_reconstruction_must_match_source(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    source_receipt = source("REALISH_INTR_ALLOW", outcome="ALLOW")
    org.aggregate_transition(source_receipt)
    snapshot = readback.readback(ledger, correlation_ids=(source_receipt["subject_or_correlation_id"],))
    digest = org.sha(source_receipt)[7:]
    calls = []
    def fake_get(path, params):
        calls.append((path, params))
        assert path == "/api/master-records/state-transitions/query"
        assert params == {"subject_or_correlation_id": source_receipt["subject_or_correlation_id"],
                          "transition_id": source_receipt["transition_id"]}
        return {"schema": "stegverse.master-records.state-transition-query/v1",
                "subject_or_correlation_id": params["subject_or_correlation_id"],
                "transition_id": params["transition_id"], "count": 1, "records": [{
                    "state": "PASS", "receipt_sha256": digest,
                    "reconstructed_receipt_sha256": digest,
                    "required_evidence_validation_status": "PASS", "receipt": source_receipt,
                }]}
    proof = readback.reconcile_master_records(snapshot, get_json=fake_get)
    assert proof["state"] == "PASS"
    assert len(calls) == 1
    assert proof["canonical_transition_results"][0]["state"] == "MATCHING_INDEPENDENT_RECONSTRUCTION_PASS"


def test_missing_or_mismatched_master_records_cannot_pass(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    source_receipt = source("INTR_DENY", outcome="DENY")
    org.aggregate_transition(source_receipt)
    snapshot = readback.readback(ledger, correlation_ids=(source_receipt["subject_or_correlation_id"],))
    def missing(_path, params):
        return {"schema": "stegverse.master-records.state-transition-query/v1",
                **params, "count": 0, "records": []}
    result = readback.reconcile_master_records(snapshot, get_json=missing)
    assert result["state"] == "INCOMPLETE"
    assert result["canonical_transition_results"][0]["state"] == "MATCH_NOT_FOUND_IN_AUTHENTIC_QUERY"
    def forged(_path, params):
        return {"schema": "stegverse.master-records.state-transition-query/v1",
                **params, "count": 1, "records": [{
                    "state": "PASS", "receipt_sha256": org.sha(source_receipt)[7:],
                    "reconstructed_receipt_sha256": org.sha(source_receipt)[7:],
                    "required_evidence_validation_status": "PASS",
                    "receipt": {**source_receipt, "transition_outcome": "ALLOW"},
                }]}
    with pytest.raises(ValueError, match="MASTER_RECORDS_EXACT_TRANSITION_RECONSTRUCTION_MISMATCH"):
        readback.reconcile_master_records(snapshot, get_json=forged)


def test_existing_master_records_batch_reconstruction_exact_identity(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("BATCHED_INTR_ALLOW"))
    closed = batches.close_batch("TASK_CLOSURE", root=ledger)
    snapshot = readback.readback(ledger, correlation_ids=("NONMATCHING",))
    def fake_get(path, params):
        assert not params
        assert path == "/api/master-records/organization-batches/" + closed["batch_id"] + "/reconstruction"
        return {"schema": "stegverse.master-records.organization-batch-ack/v1",
                "state": "RECORDED", "reconstruction_status": "PASS",
                "required_evidence_validation_status": "PASS",
                "receipt_sha256": "1" * 64, "reconstructed_receipt_sha256": "1" * 64,
                "batch_id": closed["batch_id"], "organization_id": "StegVerse-Labs",
                "organization_receipt_count": 1}
    proof = readback.reconcile_master_records(snapshot, get_json=fake_get)
    assert proof["state"] == "PASS"
    assert proof["batch_results"][0]["state"] == "MATCHING_INDEPENDENT_BATCH_RECONSTRUCTION_PASS"

def _organization_record(name):
    """A submit_state_receipt()-shaped result whose Organization receipt was really appended.

    The ledger root is the tmp STEGVERSE_ORG_LEDGER_ROOT the caller set; Master
    Records reconstruction was not requested, as submit_state_receipt() reports.
    """
    row = org.aggregate_transition(source(name))
    return {"state": "RECORDED", "receipt_sha256": row["source_transition_sha256"][7:],
            "organization_receipt": row, "reconstruction_status": "NOT_REQUESTED",
            "required_evidence_validation_status": "ORGANIZATION_RECORD_ONLY"}

def governed_attempt(runtime, disposition="ALLOW", request_id="governed-1"):
    req_path = request(runtime, request_id=request_id)
    req = json.loads(req_path.read_text())
    req_path.unlink()
    path = runtime / consumer.ATTEMPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {"schema": consumer.ATTEMPT_SCHEMA, "task_id": consumer.TASK_ID,
             "cosv_task_vector": consumer.COSV, "request_id": request_id,
             "presented_to_intr": True, "intr_disposition": disposition,
             "authentic_intr_disposition_observed": True,
             "intr_master_records_organization_record": _organization_record("GOVERNED_INTR_DISPOSITION"),
             "predecessor_master_records_organization_record": _organization_record("GOVERNED_PREDECESSOR"),
             "readback_request": req}
    path.write_text(json.dumps(value))
    return path

def test_governed_intr_deny_is_preserved_without_readback(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "ledger"))
    governed_attempt(runtime, disposition="DENY")
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "DENY"
    assert result["disposition"] == "DENY"
    assert result["readback_executed"] is False
    assert not (runtime / consumer.REQUEST_REL).exists()

def test_governed_allow_executes_without_host_inventory_gate(monkeypatch, tmp_path):
    ledger, runtime = tmp_path / "ledger", tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    org.aggregate_transition(source("GOVERNED_ALLOW"))
    attempt = json.loads(governed_attempt(runtime, disposition="ALLOW").read_text())
    intr = attempt["intr_master_records_organization_record"]
    predecessor = attempt["predecessor_master_records_organization_record"]
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "RECORDED_LOCAL_READBACK"
    assert result["governed_intr_disposition"] == "ALLOW"
    assert result["intr_master_records_receipt_sha256"] == intr["receipt_sha256"]
    assert result["predecessor_master_records_receipt_sha256"] == predecessor["receipt_sha256"]
    assert result["intr_organization_receipt_sha256"] == intr["organization_receipt"]["receipt_sha256"]
    assert result["predecessor_organization_receipt_sha256"] == predecessor["organization_receipt"]["receipt_sha256"]
    # Q74-01: the verified readbacks report their unauthenticated generation-0 basis.
    for key in ("intr_organization_readback_custody_basis", "predecessor_organization_readback_custody_basis"):
        assert result[key] == "PRE_EXISTING_MATERIALIZATION_UNAUTHENTICATED; LOCATION_CHECK_IS_ANOMALY_DETECTION_ONLY"

def test_governed_attempt_master_records_pass_without_organization_receipt_fails_closed(monkeypatch, tmp_path):
    # Master Records reconstruction PASS does not substitute for the verified Organization receipt.
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "ledger"))
    path = governed_attempt(runtime, disposition="ALLOW")
    attempt = json.loads(path.read_text())
    record = attempt["intr_master_records_organization_record"]
    record.pop("organization_receipt")
    record.update(reconstruction_status="PASS", required_evidence_validation_status="PASS",
                  reconstructed_receipt_sha256=record["receipt_sha256"])
    path.write_text(json.dumps(attempt))
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == "GOVERNED_MANIFEST_ATTEMPT_BINDING_AND_CUSTODY"
    assert "ORGANIZATION_RECEIPT_SHA256_ABSENT" in result["reason"]
    assert not (runtime / consumer.REQUEST_REL).exists()

def test_governed_attempt_forged_organization_receipt_fails_closed(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "ledger"))
    path = governed_attempt(runtime, disposition="DENY")
    attempt = json.loads(path.read_text())
    attempt["predecessor_master_records_organization_record"]["organization_receipt"]["receipt_sha256"] = (
        "sha256:" + "d" * 64)
    path.write_text(json.dumps(attempt))
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "FAIL_CLOSED"
    assert "ORGANIZATION_RECEIPT_READBACK_MISSING" in result["reason"]

def test_governed_attempt_missing_master_records_organization_record_fails_closed(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "ledger"))
    path = governed_attempt(runtime, disposition="ALLOW")
    attempt = json.loads(path.read_text())
    del attempt["intr_master_records_organization_record"]
    path.write_text(json.dumps(attempt))
    result = consumer.consume(ROOT, runtime)
    assert result["state"] == "FAIL_CLOSED"
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == "GOVERNED_MANIFEST_ATTEMPT_BINDING_AND_CUSTODY"


# --- #3012: readback surfaces the post-commit Master Records carriage of each released batch ---

COUNT_ONE = {"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}}


def _transport(state, reason=None):
    """A stand-in for the custody client; the readback never calls it."""
    def submit(root, batch_id):
        result = {"state": state, "batch_id": batch_id, "governance_disposition": None, "authority_effect": "NONE"}
        if reason is not None:
            result["reason"] = reason
        return result
    return submit


def _released_batch(monkeypatch, ledger, name, state, reason=None, task="OTHER"):
    """Append a manifest-directed receipt that releases the prior packet; return (receipt, batch id)."""
    monkeypatch.setattr(batches, "submit_released_batch", _transport(state, reason))
    row = org.aggregate_transition(source(name, task=task), parent_manifest=COUNT_ONE)
    return row, row["boundary_evidence"]["parent_manifest_released_batch"]["batch_id"]


def _ledger_snapshot(ledger: Path) -> dict[str, str]:
    return {str(path.relative_to(ledger)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(ledger.rglob("*")) if path.is_file()}


def _submission_of(result, batch_id):
    rows = [row for row in result["batch_submissions"] if row["batch_id"] == batch_id]
    assert len(rows) == 1, result["batch_submissions"]
    return rows[0]


def test_readback_surfaces_recorded_submission_outcomes_without_writing_or_authorizing(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("FIRST", task="OTHER"), parent_manifest=COUNT_ONE)
    second, completed_batch = _released_batch(monkeypatch, ledger, "SECOND", "COMPLETED")
    third, failed_batch = _released_batch(monkeypatch, ledger, "THIRD", "FAILED",
                                          reason="ORGANIZATION_BATCH_CUSTODY_SUBMISSION_FAILED:URLError")
    fourth, not_attempted_batch = _released_batch(monkeypatch, ledger, "FOURTH", "FAIL_CLOSED",
                                                  reason="CANONICAL_CUSTODY_CLIENT_UNAVAILABLE")
    before = _ledger_snapshot(ledger)
    monkeypatch.setattr(batches, "submit_released_batch",
                        lambda root, batch_id: pytest.fail("readback must never carry a batch"))

    result = readback.readback(ledger, correlation_ids=("OTHER",), include_exact=False)

    assert _ledger_snapshot(ledger) == before, "a readback writes nothing under the ledger"
    assert result["state"] == "VERIFIED_LOCAL_READBACK"
    assert result["batch_count"] == 3
    assert [row["batch_id"] for row in result["batch_submissions"]] == [completed_batch, failed_batch, not_attempted_batch]
    completed = _submission_of(result, completed_batch)
    assert completed["released_by_receipt_sha256"] == second["receipt_sha256"]
    assert completed["closure_reason"] == "MANIFEST_RELEASE_CONDITION"
    receipt = batches.released_batch_submission(ledger, completed_batch)
    assert completed["master_records_submission"] == {
        "state": "COMPLETED",
        "receipt_key": batches.submission_key(completed_batch),
        "self_hash_verified": True,
        "submission_receipt_sha256": receipt["receipt_sha256"],
        "reason": None,
        "released_by_receipt_sha256": second["receipt_sha256"],
        "recorded_at": receipt["observed_at"],
        "authority_effect": "NONE",
    }
    failed = _submission_of(result, failed_batch)["master_records_submission"]
    assert failed["state"] == "FAILED"
    assert failed["self_hash_verified"] is True
    assert failed["reason"] == "ORGANIZATION_BATCH_CUSTODY_SUBMISSION_FAILED:URLError"
    assert failed["released_by_receipt_sha256"] == third["receipt_sha256"]
    not_attempted = _submission_of(result, not_attempted_batch)["master_records_submission"]
    assert not_attempted["state"] == "NOT_ATTEMPTED"
    assert not_attempted["self_hash_verified"] is True
    assert not_attempted["reason"] == "CANONICAL_CUSTODY_CLIENT_UNAVAILABLE"
    assert not_attempted["released_by_receipt_sha256"] == fourth["receipt_sha256"]
    # Non-authorizing: the readback result and every carriage row say so, and nothing is an ALLOW.
    assert result["authority_effect"] == "NONE_READBACK_ONLY"
    assert result["runtime_admission_inferred"] is False
    assert result["master_records_acknowledgement"] == "NOT_QUERIED"
    for row in result["batch_submissions"]:
        assert row["master_records_submission"]["authority_effect"] == "NONE"
        assert row["master_records_submission"]["state"] in {"COMPLETED", "FAILED", "NOT_ATTEMPTED"}
    assert "ALLOW" not in json.dumps(result["batch_submissions"])
    # The summary is present without exact bytes; with them, the immutable batch rows are untouched.
    exact = readback.readback(ledger, correlation_ids=("OTHER",))
    assert exact["batch_submissions"] == result["batch_submissions"]
    assert all("master_records_submission" not in item for item in exact["exact_batches"])
    assert _ledger_snapshot(ledger) == before


def test_readback_reports_absent_submission_receipt_as_pending_not_error(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("FIRST", task="OTHER"), parent_manifest=COUNT_ONE)
    second, batch_id = _released_batch(monkeypatch, ledger, "SECOND", "COMPLETED")
    # The process died between the sovereign commit and the submission record: the outbox is the ledger.
    (ledger / batches.submission_key(batch_id)).unlink()
    assert batches.pending_released_batch(ledger)["batch"]["batch_id"] == batch_id
    before = _ledger_snapshot(ledger)
    result = readback.readback(ledger, correlation_ids=("OTHER",), include_exact=False)
    assert _ledger_snapshot(ledger) == before
    assert result["state"] == "VERIFIED_LOCAL_READBACK"
    assert _submission_of(result, batch_id)["master_records_submission"] == {
        "state": "PENDING",
        "pending_reason": "SUBMISSION_RECEIPT_ABSENT",
        "receipt_key": batches.submission_key(batch_id),
        "self_hash_verified": False,
        "authority_effect": "NONE",
    }
    # Still pending after the readback: it drove nothing.
    assert batches.pending_released_batch(ledger)["batch"]["batch_id"] == batch_id


def test_readback_fails_closed_on_tampered_submission_receipt_without_failing_the_chain(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("FIRST", task="OTHER"), parent_manifest=COUNT_ONE)
    _, batch_id = _released_batch(monkeypatch, ledger, "SECOND", "FAILED", reason="TRANSPORT")
    path = ledger / batches.submission_key(batch_id)
    forged = json.loads(path.read_text())
    forged["execution_result"] = "COMPLETED"
    path.write_text(json.dumps(forged))
    before = _ledger_snapshot(ledger)
    result = readback.readback(ledger, correlation_ids=("OTHER",), include_exact=False)
    assert _ledger_snapshot(ledger) == before
    assert result["state"] == "VERIFIED_LOCAL_READBACK"
    assert result["complete_organization_chain"] == "PASS"
    assert _submission_of(result, batch_id)["master_records_submission"] == {
        "state": "FAIL_CLOSED",
        "failed_predicate": "SUBMISSION_RECEIPT_HASH_MISMATCH",
        "receipt_key": batches.submission_key(batch_id),
        "self_hash_verified": False,
        "authority_effect": "NONE",
    }
    assert "COMPLETED" not in json.dumps(result["batch_submissions"]), "a forged outcome is never surfaced"


def test_readback_reports_null_submission_for_batch_released_without_a_key(monkeypatch, tmp_path):
    ledger = tmp_path / "ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(ledger))
    org.aggregate_transition(source("FIRST", task="OTHER"))
    # Closed by the operator: its carriage is the operator's own step, no key is named.
    closed = batches.close_batch("TASK_CLOSURE", root=ledger)
    org.aggregate_transition(source("SECOND", task="OTHER"))
    # Released before the post-commit step existed: the transport's result was inline, no key.
    third, inline_batch = _released_batch(monkeypatch, ledger, "THIRD", "COMPLETED")
    inline = {**third, "boundary_evidence": {**third["boundary_evidence"], "parent_manifest_released_batch": {
        "batch_id": inline_batch, "execution_result": "COMPLETED", "reason": None, "authority_effect": "NONE"}}}
    monkeypatch.setattr(batches, "_verified_receipt", lambda root, digest, _real=batches._verified_receipt: (
        inline if digest == third["receipt_sha256"] else _real(root, digest)))
    result = readback.readback(ledger, correlation_ids=("OTHER",), include_exact=False)
    assert result["batch_count"] == 2
    operator = _submission_of(result, closed["batch_id"])
    assert operator["closure_reason"] == "TASK_CLOSURE"
    assert operator["released_by_receipt_sha256"] is None
    assert operator["master_records_submission"] is None
    assert _submission_of(result, inline_batch)["master_records_submission"] is None
