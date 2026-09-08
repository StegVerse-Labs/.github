from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cleanup", ROOT / "scripts/finalize_reviewed_github_email_cleanup.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(M)


def reconciliation(**extra):
    return {
        "schema": M.RECONCILE_SCHEMA,
        "state": "STEGHEALTH_TASK_CREATION_COMPLETE",
        "retry_required": False,
        **extra,
    }


def review(state="RESOLVED", klass="FAILURE"):
    return {
        "schema": M.REVIEW_SCHEMA,
        "incidents": [{
            "notification_class": klass,
            "review_state": "REVIEWED",
            "resolution_state": state,
            "mapped_incident_id": "INC-GITHUB-1",
            "remediation_evidence_refs": ["commit:abc"],
            "gmail_message_ids": ["m1", "m2"],
        }],
    }


def test_reviewed_resolved_failure_is_cleanup_eligible():
    assert M.cleanup_ids(review(), reconciliation()) == ["m1", "m2"]


def test_reviewed_resolved_error_is_cleanup_eligible():
    assert M.cleanup_ids(review(klass="ERROR"), reconciliation()) == ["m1", "m2"]


def test_unresolved_incident_fails_closed():
    try:
        M.cleanup_ids(review(state="REMEDIATION_PENDING"), reconciliation())
    except RuntimeError as exc:
        assert "cleanup eligible" in str(exc)
    else:
        raise AssertionError("unresolved incident must not be trashed")


def test_incomplete_reconciliation_fails_closed():
    try:
        M.cleanup_ids(review(), reconciliation(retry_required=True))
    except RuntimeError as exc:
        assert "retry" in str(exc)
    else:
        raise AssertionError("pending reconciliation must not be trashed")


def test_duplicate_gmail_id_across_incidents_fails_closed():
    value = review()
    value["incidents"].append({
        "notification_class": "ERROR",
        "review_state": "REVIEWED",
        "resolution_state": "RESOLVED",
        "mapped_incident_id": "INC-GITHUB-2",
        "remediation_evidence_refs": ["commit:def"],
        "gmail_message_ids": ["m2"],
    })
    try:
        M.cleanup_ids(value, reconciliation())
    except RuntimeError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate cleanup identity must fail closed")
