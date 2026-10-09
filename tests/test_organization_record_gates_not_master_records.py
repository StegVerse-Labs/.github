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


# --- RESPONSE-015 (StegVerse-Labs/.github#3012) -------------------------------


def _refusal_rows(tmp_path):
    custody = _custody()
    ledger = tmp_path / "org"
    head = json.loads(_head(tmp_path))["receipt_sha256"]
    rows = custody._segment(ledger, head, None)
    out = []
    for row in rows:
        if row.get("source_transition_id") == "ORGANIZATION_RECEIPT_GATE_REFUSED":
            source = custody.org.load(ledger / "source-receipts" / (row["source_transition_sha256"][7:] + ".json"))
            out.append((row, source))
    return out


def test_not_recorded_refusal_carries_the_producer_reason():
    custody = _custody()
    refusal = _refused(lambda: custody.verified_organization_record(
        None, {"state": "BOUNDARY", "reason": "ORGANIZATION_TRANSITION_RECEIPT_RECORDING_FAILED:LedgerLocationRequired"}),
        disposition="FAIL_CLOSED", predicate="ORGANIZATION_RECORD_NOT_RECORDED")
    assert refusal["detail"] == "ORGANIZATION_TRANSITION_RECEIPT_RECORDING_FAILED:LedgerLocationRequired"
    # Nothing else changes: a result without a reason carries no detail.
    assert "detail" not in _refused(lambda: custody.verified_organization_record(None, {"state": "BOUNDARY"}),
                                    disposition="FAIL_CLOSED", predicate="ORGANIZATION_RECORD_NOT_RECORDED")
    from workers.canonical_state_transition_custody import organization_receipt_gate
    gate = organization_receipt_gate({"state": "BOUNDARY", "reason": "CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH"})
    assert gate["refusal"]["detail"] == "CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH"


def test_refusal_inside_attempted_transition_is_appended_once(monkeypatch, tmp_path):
    from workers.canonical_state_transition_custody import organization_receipt_gate

    _, uri, result = _recorded(monkeypatch, tmp_path)
    forged = dict(result, organization_receipt=None, organization_receipt_sha256="sha256:" + "d" * 64)
    first = organization_receipt_gate(forged, expected_transition_id=TRANSITION_ID, record_refusal=True)
    assert first["verified"] is False
    refusal = first["refusal"]
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["failed_predicate"] == "ORGANIZATION_RECEIPT_READBACK_MISSING"
    assert refusal["consequence_committed"] is False
    assert refusal["refusal_recorded"] is True
    rows = _refusal_rows(tmp_path)
    assert len(rows) == 1
    row, source = rows[0]
    assert row["receipt_sha256"] == refusal["refusal_organization_receipt_sha256"]
    assert source["transition_outcome"] == "FAIL_CLOSED"
    assert source["prior_state_ref_or_hash"] == uri
    assert source["transition_evidence"]["gated_transition_id"] == TRANSITION_ID
    assert source["transition_evidence"]["consequence_committed"] is False
    # The refusal record never closes the attempted transition.
    assert organization_receipt_gate(dict(result, organization_receipt_sha256=row["receipt_sha256"],
                                          organization_receipt=None),
                                     expected_transition_id=TRANSITION_ID)["verified"] is False
    # A retry refused the same way returns the receipt already recorded.
    head = _head(tmp_path)
    again = organization_receipt_gate(forged, expected_transition_id=TRANSITION_ID, record_refusal=True)
    assert again["refusal"]["refusal_organization_receipt_sha256"] == refusal["refusal_organization_receipt_sha256"]
    assert _head(tmp_path) == head and len(_refusal_rows(tmp_path)) == 1
    # Without record_refusal a gate only reads.
    assert "refusal_recorded" not in organization_receipt_gate(forged, expected_transition_id=TRANSITION_ID)["refusal"]
    assert _head(tmp_path) == head


def test_refusal_without_supplied_ledger_is_unrecorded_not_host_derived(monkeypatch, tmp_path):
    from workers.canonical_state_transition_custody import record_organization_receipt_refusal

    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_ROOT", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    recorded = record_organization_receipt_refusal(
        {"disposition": "FAIL_CLOSED", "failed_predicate": "X", "retry_entrypoint": "r", "consequence_committed": False},
        gated_transition_id=TRANSITION_ID, state_receipt_sha256="e" * 64)
    assert recorded["refusal_recorded"] is False
    assert recorded["refusal_recording_reason"] == "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"
    assert not (tmp_path / "home").exists()


def test_refusal_recording_never_extends_an_unverified_ledger(monkeypatch, tmp_path):
    from workers.canonical_state_transition_custody import organization_receipt_gate

    _, _, result = _recorded(monkeypatch, tmp_path)
    forged = dict(result, organization_receipt=None, organization_receipt_sha256="sha256:" + "d" * 64)
    # An append the real producer never made: the ledger no longer replays.
    _forge(tmp_path, result["organization_receipt"], source_transition_id="ORPHAN")
    head = _head(tmp_path)
    receipts = sorted(p.name for p in (tmp_path / "org" / "receipts").iterdir())
    gate = organization_receipt_gate(forged, expected_transition_id=TRANSITION_ID, record_refusal=True)
    assert gate["verified"] is False
    refusal = gate["refusal"]
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["consequence_committed"] is False
    assert refusal["refusal_recorded"] is False
    assert refusal["refusal_organization_receipt_sha256"] is None
    assert refusal["refusal_recording_reason"].startswith("ORGANIZATION_REFUSAL_RECORDING_FAILED:")
    assert _head(tmp_path) == head
    assert sorted(p.name for p in (tmp_path / "org" / "receipts").iterdir()) == receipts


def _diagnostic_chain(monkeypatch, tmp_path):
    """Real producer appends: ingress ALLOW, then the runtime binding that names it."""
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "org"))
    import heartbeat_runtime.worker_runtime_legacy  # noqa: F401  (import order)
    from workers.canonical_state_transition_custody import build_state_receipt, sha256_uri, submit_state_receipt
    import sdk_manifest_diagnostic_admitted_consumer as consumer

    ingress = build_state_receipt(
        transition_id="SDK_MANIFEST_INTR_ADMITTED", transition_sequence=1, subject_or_correlation_id=consumer.GOAL,
        transition_outcome="ALLOW", prior_state_ref_or_hash=None, resulting_state_ref_or_hash=None,
        governance_decision_ref_where_applicable=None,
        transition_evidence={"request_sha256": "8" * 64, "wire_manifest_sha256": "7" * 64})
    ingress_uri = sha256_uri(dict(ingress))
    binding = build_state_receipt(
        transition_id=consumer.BINDING_TRANSITION, transition_sequence=2, subject_or_correlation_id=consumer.GOAL,
        transition_outcome="OBSERVED", prior_state_ref_or_hash=ingress_uri, resulting_state_ref_or_hash=None,
        governance_decision_ref_where_applicable=None,
        transition_evidence={"runtime_binding": {"request_sha256": "8" * 64, "lease_state": "LEASE_OPEN"}})
    binding_uri = sha256_uri(dict(binding))
    assert submit_state_receipt(ingress)["state"] == "RECORDED"
    assert submit_state_receipt(binding)["state"] == "RECORDED"
    return consumer, ingress, ingress_uri[7:], binding, binding_uri[7:]


def test_diagnostic_ancestry_reads_organization_retained_sources_not_master_records(monkeypatch, tmp_path):
    from workers import canonical_state_transition_custody as cstc

    consumer, ingress, ingress_hash, binding, binding_hash = _diagnostic_chain(monkeypatch, tmp_path)

    def no_master_records(*_args, **_kwargs):
        raise AssertionError("Master Records reconstruction must not gate predecessor ancestry")

    monkeypatch.setattr(cstc, "reconstruct_state_receipt", no_master_records)
    read = consumer._organization_source_receipts(ROOT)
    actual_binding, actual_ingress = consumer._prove_ancestry(read, binding_hash, ingress_hash)
    assert actual_binding == binding and actual_ingress == ingress
    assert actual_ingress["transition_outcome"] == "ALLOW"

    # A state receipt the Organization ledger never recorded is refused.
    with pytest.raises(consumer.DiagnosticAdmissionError, match="ORGANIZATION_PREDECESSOR_RECEIPT_REQUIRED"):
        consumer._prove_ancestry(read, "f" * 64, ingress_hash)
    # A tampered retained source no longer binds to its Organization receipt.
    retained = tmp_path / "org" / "source-receipts" / (binding_hash + ".json")
    tampered = json.loads(retained.read_text(encoding="utf-8"))
    tampered["prior_state_ref_or_hash"] = "sha256:" + "a" * 64
    retained.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(consumer.DiagnosticAdmissionError, match="ORGANIZATION_SOURCE_TRANSITION_BINDING_MISMATCH"):
        consumer._prove_ancestry(read, binding_hash, ingress_hash)
    # No supplied ledger root: typed refusal, never a host path.
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_ROOT")
    with pytest.raises(consumer.DiagnosticAdmissionError, match="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"):
        consumer._organization_source_receipts(ROOT)


def test_diagnostic_ancestry_rejects_broken_or_replayed_ingress_binding_chain(monkeypatch, tmp_path):
    from workers.canonical_state_transition_custody import build_state_receipt, sha256_uri, submit_state_receipt

    consumer, ingress, ingress_hash, binding, binding_hash = _diagnostic_chain(monkeypatch, tmp_path)

    def appended(transition_id, sequence, outcome, prior, evidence):
        receipt = build_state_receipt(
            transition_id=transition_id, transition_sequence=sequence, subject_or_correlation_id=consumer.GOAL,
            transition_outcome=outcome, prior_state_ref_or_hash=prior, resulting_state_ref_or_hash=None,
            governance_decision_ref_where_applicable=None, transition_evidence=evidence)
        assert submit_state_receipt(receipt)["state"] == "RECORDED"
        return sha256_uri(dict(receipt))[7:]

    # Replayed: a later ingress ALLOW for the same request. The recorded binding
    # names the first one, so it never proves admission by the replay.
    replayed = appended("SDK_MANIFEST_INTR_ADMITTED", 1, "ALLOW", None,
                        {"request_sha256": "8" * 64, "wire_manifest_sha256": "7" * 64, "replay": 1})
    read = consumer._organization_source_receipts(ROOT)
    with pytest.raises(consumer.DiagnosticAdmissionError, match="CANONICAL_IMMEDIATE_PREDECESSOR_REQUIRED"):
        consumer._prove_ancestry(read, binding_hash, replayed)
    # Broken: a binding whose predecessor the Organization ledger never recorded.
    broken = appended(consumer.BINDING_TRANSITION, 2, "OBSERVED", "sha256:" + "e" * 64,
                      {"runtime_binding": {"request_sha256": "8" * 64, "lease_state": "LEASE_OPEN"}})
    read = consumer._organization_source_receipts(ROOT)
    with pytest.raises(consumer.DiagnosticAdmissionError, match="ORGANIZATION_PREDECESSOR_RECEIPT_REQUIRED"):
        consumer._prove_ancestry(read, broken, ingress_hash)
    # The recorded chain itself still proves its own ingress ALLOW.
    assert consumer._prove_ancestry(read, binding_hash, ingress_hash) == (binding, ingress)


def test_diagnostic_closure_refusal_emits_outer_fail_closed_record(monkeypatch, tmp_path):
    from workers import manifest_state_transition_intr_ingress as ingress_worker

    # The module the ingress boundary imports, so it catches this exception class.
    from workers import sdk_manifest_diagnostic_admitted_consumer as consumer

    _, first_uri, _ = _recorded(monkeypatch, tmp_path, transition_id="SDK_ECOSYSTEM_DIAGNOSTIC_EVENT_EPHEMERAL_BOUND")
    _, _, closure = _recorded(monkeypatch, tmp_path, transition_id=consumer.EXECUTION_TRANSITION,
                              prior=first_uri, sequence=2)
    forged = dict(closure, organization_receipt=None, organization_receipt_sha256="sha256:" + "d" * 64)

    def refused_consume(*_args, **_kwargs):
        consumer._verified_organization_closure(forged)
        raise AssertionError("forged closure must be refused")

    monkeypatch.setattr(consumer, "consume", refused_consume)
    monkeypatch.setattr(ingress_worker, "validate_request", lambda request: dict(request))
    monkeypatch.setattr(ingress_worker, "persist_request", lambda *_args: None)
    request = {"processing_capability": "ecosystem_diagnostic", "canonical_task_id": None,
               "request_sha256": "8" * 64, "graph_id": "RTC-GOVERNED-PROCESSING-002:ECOSYSTEM_DIAGNOSTIC",
               "canonical_manifest_sha256": "9" * 64, "wire_manifest_sha256": "7" * 64,
               "canonical_manifest": {"payload": {"goal_task_id": consumer.GOAL, "cosv": consumer.COSV}}}
    runtime = tmp_path / "runtime"
    record = ingress_worker.execute(runtime, request)
    assert record["disposition"] == "FAIL_CLOSED" and record["terminal"] is True
    assert record["failed_predicate"] == "ORGANIZATION_EXACT_CLOSURE_REQUIRED:FAIL_CLOSED:ORGANIZATION_RECEIPT_READBACK_MISSING"
    assert record["consequence_committed"] is False
    assert record["retry_entrypoint"] == _custody().RECEIPT_REFUSAL_RETRY_ENTRYPOINT
    refusal = record["organization_receipt_refusal"]
    assert refusal["failed_predicate"] == "ORGANIZATION_RECEIPT_READBACK_MISSING"
    assert refusal["refusal_recorded"] is True
    assert record["authority_effect"] == "NONE_SOURCE_PROFILE_DISPOSITION_ONLY"
    assert "disposition" in record and record["disposition"] != "ALLOW"
    rows = _refusal_rows(tmp_path)
    assert [row["receipt_sha256"] for row, _ in rows] == [refusal["refusal_organization_receipt_sha256"]]
    assert rows[0][1]["transition_evidence"]["gated_transition_id"] == consumer.EXECUTION_TRANSITION
    # Retry: same record, same refusal receipt, nothing new appended.
    head = _head(tmp_path)
    assert ingress_worker.execute(runtime, request)["source_disposition_ref"] == record["source_disposition_ref"]
    assert _head(tmp_path) == head
