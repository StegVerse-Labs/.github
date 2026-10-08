"""The verified Organization receipt, not Master Records reconstruction, closes custody gates.

submit_state_receipt() appends to the Organization ledger and reports
reconstruction_status NOT_REQUESTED. Every gate that admits a successor calls
organization_batch_custody.verified_organization_receipt, which reads the
receipt back from the ledger root the append used and binds it to the exact
state receipt. Anything else is refused with the kernel's typed disposition
(deterministic DENY, otherwise FAIL_CLOSED with a retry entrypoint) and no
effect. Ledger roots come from tmp dirs, never from the host.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "workers"), str(ROOT / "resident-runtime")]

TRANSITION_ID = "ORG_RECORD_GATE_REGRESSION"


def _custody():
    import organization_batch_custody

    return organization_batch_custody


def _recorded(monkeypatch, tmp_path, transition_id=TRANSITION_ID, prior=None, sequence=1):
    # Ledger roots are supplied, never derived from the host.
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "org"))
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", str(tmp_path / "repo"))
    import heartbeat_runtime.worker_runtime_legacy  # noqa: F401  (import order)
    from workers.canonical_state_transition_custody import build_state_receipt, sha256_uri, submit_state_receipt

    receipt = build_state_receipt(
        transition_id=transition_id,
        transition_sequence=sequence,
        subject_or_correlation_id=TRANSITION_ID,
        transition_outcome="EXECUTED",
        prior_state_ref_or_hash=prior,
        resulting_state_ref_or_hash=None,
        governance_decision_ref_where_applicable=None,
        transition_evidence={"regression": True, "transition": transition_id},
    )
    return receipt, sha256_uri(dict(receipt)), submit_state_receipt(receipt)


def _head(tmp_path):
    return (tmp_path / "org" / "HEAD.json").read_text(encoding="utf-8")


def _forge(tmp_path, row, **changes):
    """Write a self-consistent receipt that the real producer never appended."""
    custody = _custody()
    body = {key: value for key, value in row.items() if key != "receipt_sha256"}
    body.update(changes)
    digest = custody.org.sha(body)
    path = tmp_path / "org" / "receipts" / (digest[7:] + ".json")
    path.write_text(json.dumps({**body, "receipt_sha256": digest}), encoding="utf-8")
    return digest


def _refused(callable_, *, disposition, predicate):
    custody = _custody()
    with pytest.raises(custody.OrganizationReceiptRefused) as caught:
        callable_()
    refusal = caught.value.refusal()
    assert refusal["disposition"] == disposition
    assert refusal["failed_predicate"] == predicate
    assert refusal["consequence_committed"] is False
    assert refusal["authority_effect"] == "NONE_REFUSAL_ONLY"
    if disposition == "DENY":
        assert refusal["retry_entrypoint"] is None
    else:
        assert refusal["retry_entrypoint"] == custody.RECEIPT_REFUSAL_RETRY_ENTRYPOINT
    return refusal


# --- the wrapper -----------------------------------------------------------

def test_real_producer_result_is_accepted_from_the_append_root(monkeypatch, tmp_path):
    _, receipt_uri, result = _recorded(monkeypatch, tmp_path)
    assert result["state"] == "RECORDED"
    assert result["reconstruction_status"] == "NOT_REQUESTED"
    assert "reconstructed_receipt_sha256" not in result
    org = result["organization_receipt"]
    custody = _custody()
    for root in (tmp_path / "org", None):  # supplied root, then the existing ledger_root() fallback
        row = custody.verified_organization_receipt(
            root, org["receipt_sha256"], state_receipt_sha256=result["receipt_sha256"],
            expected_transition_id=TRANSITION_ID)
        assert row["receipt_sha256"] == org["receipt_sha256"]
        assert row["source_transition_sha256"] == receipt_uri
    assert custody.verified_organization_record(None, result)["receipt_sha256"] == org["receipt_sha256"]


def test_forged_digest_is_refused(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    custody = _custody()
    state = result["receipt_sha256"]
    _refused(lambda: custody.verified_organization_receipt(
        None, "sha256:" + "0" * 64, state_receipt_sha256=state),
        disposition="FAIL_CLOSED", predicate="ORGANIZATION_RECEIPT_READBACK_MISSING")
    _refused(lambda: custody.verified_organization_receipt(None, "not-a-digest", state_receipt_sha256=state),
             disposition="DENY", predicate="ORGANIZATION_RECEIPT_SHA256_INVALID")
    # A file stored under a digest its bytes do not hash to.
    org = result["organization_receipt"]
    path = tmp_path / "org" / "receipts" / (org["receipt_sha256"][7:] + ".json")
    path.write_text(json.dumps(dict(org, boundary_evidence={"forged": True})), encoding="utf-8")
    _refused(lambda: custody.verified_organization_receipt(None, org["receipt_sha256"], state_receipt_sha256=state),
             disposition="DENY", predicate="ORGANIZATION_RECEIPT_VERIFICATION_FAILED")


def test_wrong_organization_is_refused(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    forged = _forge(tmp_path, result["organization_receipt"], organization="Some-Other-Org")
    _refused(lambda: _custody().verified_organization_receipt(
        None, forged, state_receipt_sha256=result["receipt_sha256"]),
        disposition="DENY", predicate="ORGANIZATION_RECEIPT_VERIFICATION_FAILED")


def test_receipt_of_a_different_state_receipt_is_refused(monkeypatch, tmp_path):
    _, _, first = _recorded(monkeypatch, tmp_path, transition_id="FIRST")
    _, _, second = _recorded(monkeypatch, tmp_path, transition_id="SECOND")
    _refused(lambda: _custody().verified_organization_receipt(
        None, first["organization_receipt"]["receipt_sha256"], state_receipt_sha256=second["receipt_sha256"]),
        disposition="DENY", predicate="ORGANIZATION_RECEIPT_NOT_BOUND_TO_STATE_RECEIPT")


def test_wrong_transition_is_refused(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    _refused(lambda: _custody().verified_organization_record(None, result, expected_transition_id="SOME_OTHER"),
             disposition="DENY", predicate="ORGANIZATION_RECEIPT_TRANSITION_MISMATCH")


def test_absent_source_is_refused(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    forged = _forge(tmp_path, result["organization_receipt"], source_transition_sha256=None,
                    canonical_state_transition_receipt_sha256=None)
    _refused(lambda: _custody().verified_organization_receipt(
        None, forged, state_receipt_sha256=result["receipt_sha256"]),
        disposition="DENY", predicate="ORGANIZATION_RECEIPT_SOURCE_ABSENT")


def test_absent_state_receipt_and_absent_record_are_refused(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    custody = _custody()
    digest = result["organization_receipt"]["receipt_sha256"]
    _refused(lambda: custody.verified_organization_receipt(None, digest, state_receipt_sha256=None),
             disposition="FAIL_CLOSED", predicate="STATE_RECEIPT_SHA256_ABSENT")
    _refused(lambda: custody.verified_organization_record(None, dict(result, receipt_sha256=None)),
             disposition="FAIL_CLOSED", predicate="STATE_RECEIPT_SHA256_ABSENT")
    _refused(lambda: custody.verified_organization_record(None, {"state": "RECORDED", "receipt_sha256": "a" * 64}),
             disposition="FAIL_CLOSED", predicate="ORGANIZATION_RECEIPT_SHA256_ABSENT")
    _refused(lambda: custody.verified_organization_record(None, dict(result, state="BOUNDARY")),
             disposition="FAIL_CLOSED", predicate="ORGANIZATION_RECORD_NOT_RECORDED")


def test_nested_and_top_level_conflict_is_refused(monkeypatch, tmp_path):
    _, _, first = _recorded(monkeypatch, tmp_path, transition_id="FIRST")
    _, _, second = _recorded(monkeypatch, tmp_path, transition_id="SECOND")
    custody = _custody()
    conflicting = dict(second, organization_receipt_sha256=first["organization_receipt"]["receipt_sha256"])
    _refused(lambda: custody.verified_organization_record(None, conflicting),
             disposition="DENY", predicate="ORGANIZATION_RECEIPT_TOP_LEVEL_NESTED_CONFLICT")
    conflicting = dict(second, organization_source_transition_sha256="sha256:" + "1" * 64)
    _refused(lambda: custody.verified_organization_record(None, conflicting),
             disposition="DENY", predicate="ORGANIZATION_RECEIPT_TOP_LEVEL_NESTED_CONFLICT")


def test_stale_predecessor_is_refused(monkeypatch, tmp_path):
    _, first_uri, _ = _recorded(monkeypatch, tmp_path, transition_id="FIRST")
    _, stale_uri, _ = _recorded(monkeypatch, tmp_path, transition_id="STALE")
    _, _, successor = _recorded(monkeypatch, tmp_path, transition_id="SUCCESSOR", prior=first_uri, sequence=2)
    custody = _custody()
    accepted = custody.verified_organization_record(None, successor, expected_transition_id="SUCCESSOR",
                                                    expected_predecessor=first_uri)
    assert accepted["source_transition_id"] == "SUCCESSOR"
    _refused(lambda: custody.verified_organization_record(None, successor, expected_predecessor=stale_uri),
             disposition="DENY", predicate="ORGANIZATION_RECEIPT_PREDECESSOR_STALE")


def test_root_different_from_the_append_root_is_refused(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    other = tmp_path / "another-ledger"
    other.mkdir()
    _refused(lambda: _custody().verified_organization_record(other, result),
             disposition="FAIL_CLOSED", predicate="ORGANIZATION_RECEIPT_READBACK_MISSING")
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_ROOT")
    _refused(lambda: _custody().verified_organization_record(None, result),
             disposition="FAIL_CLOSED", predicate="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")


def test_refusal_has_no_effect_on_the_ledger(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    head = _head(tmp_path)
    receipts = sorted(p.name for p in (tmp_path / "org" / "receipts").iterdir())
    from workers.canonical_state_transition_custody import organization_receipt_gate

    gate = organization_receipt_gate(dict(result, receipt_sha256="b" * 64))
    assert gate == {"verified": False, "organization_receipt_sha256": None, "refusal": gate["refusal"]}
    assert gate["refusal"]["disposition"] == "DENY"
    assert _head(tmp_path) == head
    assert sorted(p.name for p in (tmp_path / "org" / "receipts").iterdir()) == receipts


# --- the gates that call it ---------------------------------------------------

def _worker():
    from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator

    return WorkerCoordinator


def test_worker_gate_accepts_real_producer_and_assignment_projection(monkeypatch, tmp_path):
    _, _, result = _recorded(monkeypatch, tmp_path)
    assert _worker()._master_records_organization_record_recorded(dict(result, transition_id=TRANSITION_ID), TRANSITION_ID)
    org = result["organization_receipt"]
    # Shape returned by WorkerCoordinator._custody_assignment_transition.
    row = {
        "state": result["state"],
        "transition_id": TRANSITION_ID,
        "receipt_sha256": result["receipt_sha256"],
        "organization_receipt_sha256": org["receipt_sha256"],
        "organization_source_transition_sha256": org["source_transition_sha256"],
    }
    assert _worker()._organization_record_refusal(row, TRANSITION_ID) is None


@pytest.mark.parametrize("mutate,disposition", [
    (lambda row: row["organization_receipt"].update(source_transition_sha256="sha256:" + "0" * 64), "DENY"),
    (lambda row: row["organization_receipt"].update(receipt_sha256="not-a-digest"), "DENY"),
    (lambda row: row["organization_receipt"].update(receipt_sha256="sha256:" + "0" * 64), "FAIL_CLOSED"),
    (lambda row: row.pop("organization_receipt"), "FAIL_CLOSED"),
    (lambda row: row.update(state="BOUNDARY"), "FAIL_CLOSED"),
    (lambda row: row.update(transition_id="SOME_OTHER_TRANSITION"), "DENY"),
])
def test_worker_gate_refuses_with_typed_disposition(monkeypatch, tmp_path, mutate, disposition):
    _, _, result = _recorded(monkeypatch, tmp_path)
    row = dict(result, transition_id=TRANSITION_ID)
    row["organization_receipt"] = dict(result["organization_receipt"])
    mutate(row)
    refusal = _worker()._organization_record_refusal(row, TRANSITION_ID)
    assert refusal is not None and refusal["disposition"] == disposition
    assert refusal["consequence_committed"] is False
    assert not _worker()._master_records_organization_record_recorded(row, TRANSITION_ID)


def test_kv_gates_bind_the_exact_state_receipt(monkeypatch, tmp_path):
    from scripts import consume_kv_publisher_return_materialization_request as consumer

    _, _, result = _recorded(monkeypatch, tmp_path, transition_id="RTC-SDK-RETURN-006")
    digest = result["organization_receipt"]["receipt_sha256"]
    predecessor = {"state": "RECORDED", "organization_receipt_sha256": digest,
                   "receipt_sha256": result["receipt_sha256"],
                   "reconstruction_status": "NOT_REQUESTED", "reconstructed_receipt_sha256": None}
    assert consumer.require_organization_recorded_predecessor(
        predecessor, predecessor_transition_id="RTC-SDK-RETURN-006", successor_transition_id="T") == digest
    for forged, disposition in (
        (dict(predecessor, organization_receipt_sha256=None), "FAIL_CLOSED"),
        (dict(predecessor, state="BOUNDARY"), "FAIL_CLOSED"),
        (dict(predecessor, receipt_sha256="1" * 64), "DENY"),
        (dict(predecessor, organization_receipt_sha256="sha256:" + "2" * 64), "FAIL_CLOSED"),
    ):
        with pytest.raises(consumer.KVOrganizationReceiptRefused, match="predecessor Organization record refused") as caught:
            consumer.require_organization_recorded_predecessor(
                forged, predecessor_transition_id="RTC-SDK-RETURN-006", successor_transition_id="T")
        assert caught.value.refusal["disposition"] == disposition
    with pytest.raises(consumer.KVOrganizationReceiptRefused) as caught:
        consumer.require_organization_recorded_predecessor(
            predecessor, predecessor_transition_id="WRONG", successor_transition_id="T")
    assert caught.value.refusal["failed_predicate"] == "ORGANIZATION_RECEIPT_TRANSITION_MISMATCH"


def test_stegagents_gate_refuses_without_effect(monkeypatch, tmp_path):
    import stegagents_governed_runtime_worker as worker

    _, _, result = _recorded(monkeypatch, tmp_path)
    row = dict(result, transition_id=TRANSITION_ID)
    assert worker._closed_transition(row, TRANSITION_ID)["transition_id"] == TRANSITION_ID
    worker._require_closed_transition(row, TRANSITION_ID)
    # Master Records reconstruction PASS without an Organization receipt is not closure.
    reconstructed_only = {"transition_id": TRANSITION_ID, "state": "RECORDED", "receipt_sha256": "c" * 64,
                          "reconstruction_status": "PASS", "required_evidence_validation_status": "PASS",
                          "reconstructed_receipt_sha256": "c" * 64}
    with pytest.raises(worker.OrganizationReceiptRefused) as caught:
        worker._closed_transition(reconstructed_only, TRANSITION_ID)
    response = worker.fail_closed(caught.value)
    assert response["organization_receipt_refusal"]["disposition"] == "FAIL_CLOSED"
    assert response["organization_receipt_refusal"]["consequence_committed"] is False
    assert response["authority_effect"] == "NONE_FAIL_CLOSED"


def test_sdk_diagnostic_closure_gate(monkeypatch, tmp_path):
    import sdk_manifest_diagnostic_admitted_consumer as consumer

    _, first_uri, _ = _recorded(monkeypatch, tmp_path, transition_id="SDK_ECOSYSTEM_DIAGNOSTIC_EVENT_EPHEMERAL_BOUND")
    _, _, closure = _recorded(monkeypatch, tmp_path, transition_id=consumer.EXECUTION_TRANSITION,
                              prior=first_uri, sequence=2)
    row = consumer._verified_organization_closure(closure)
    assert row["previous_receipt_sha256"] is not None
    with pytest.raises(consumer.DiagnosticExecutionFailClosed, match="ORGANIZATION_EXACT_CLOSURE_REQUIRED:DENY"):
        consumer._verified_organization_closure(dict(closure, receipt_sha256="d" * 64))


def test_manifest_ingress_closure_gate(monkeypatch, tmp_path):
    from workers import manifest_state_transition_intr_ingress as ingress

    _, _, result = _recorded(monkeypatch, tmp_path)
    assert ingress._closed(dict(result, transition_id=TRANSITION_ID), TRANSITION_ID)["state"] == "RECORDED"
    with pytest.raises(ValueError, match="organization_receipt_refused:FAIL_CLOSED:ORGANIZATION_RECEIPT_SHA256_ABSENT"):
        ingress._closed({"transition_id": TRANSITION_ID, "state": "RECORDED", "receipt_sha256": "e" * 64,
                         "reconstruction_status": "PASS", "reconstructed_receipt_sha256": "e" * 64}, TRANSITION_ID)
