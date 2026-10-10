"""The missing runtime receipt is an actionable profile verdict, not an InTr receipt.

Only the purpose/atomic worker capabilities reach the worker-result attachment
boundary; every other capability fails closed earlier at the Universal InTr
capability dispatch (#2832), so this test drives the purpose-bound worker.
"""
import json
from unittest.mock import patch

from workers import manifest_state_transition_intr_ingress as ingress


def test_missing_purpose_receipt_returns_immutable_nonallow(tmp_path):
    request = {
        "canonical_task_id": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
        "graph_id": "svg-governance-cycle",
        "processing_capability": "purpose_bound_worker",
        "route_id": "SDK:ManifestStateTransition",
        "request_sha256": "a" * 64,
        "canonical_manifest_sha256": "b" * 64,
    }
    with patch.object(ingress, "validate_request", return_value=request), \
         patch.object(ingress, "persist_request"), \
         patch.object(ingress, "load_adapters", return_value={}), \
         patch.object(ingress, "WorkerCoordinator") as worker:
        worker.return_value.cycle.return_value = {"state": "ATTEMPTED"}
        first = ingress.execute(tmp_path, request)
        second = ingress.execute(tmp_path, request)
    assert first == second
    assert first["disposition"] == "FAIL_CLOSED"
    assert first["evaluation_boundary"] == "SDK_MANIFEST_WORKER_RESULT_ATTACHMENT"
    assert first["authentic_intr_disposition_observed"] is False
    assert first["organization_master_records_organization_record_observed"] is False
    assert first["failed_predicate"] == "EXACT_REQUEST_BOUND_PURPOSE_RUNTIME_RECEIPT_PRESENT"
    with open(first["source_disposition_ref"], encoding="utf-8") as stream:
        persisted = json.load(stream)
    assert persisted["request_sha256"] == request["request_sha256"]
    assert persisted["authority_effect"] == "NONE_PROFILE_BOUNDARY_DISPOSITION_ONLY"
    assert_six_field_non_allow(first, owning_existing_goal=request["canonical_task_id"])


SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def assert_six_field_non_allow(record, *, owning_existing_goal):
    assert record["disposition"] != "ALLOW"
    for field in SIX_FIELDS:
        assert record.get(field), field
    assert record["owning_existing_goal"] == owning_existing_goal


def test_capability_dispatch_fail_closed_carries_six_fields(tmp_path):
    request = {
        "canonical_task_id": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
        "graph_id": "svg-governance-cycle",
        "processing_capability": "svg_governance_cycle",
        "route_id": "SDK:ManifestStateTransition",
        "request_sha256": "c" * 64,
        "canonical_manifest_sha256": "d" * 64,
    }
    record = ingress._capability_dispatch_fail_closed(tmp_path, request)
    assert record["evaluation_boundary"] == "UNIVERSAL_INTR_MANIFEST_CAPABILITY_DISPATCH"
    assert record["failed_predicate"] == "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND"
    assert record["retry_entrypoint"] == "EXISTING_SDK_MANIFEST_UNIVERSAL_INTR_INGRESS"
    assert_six_field_non_allow(record, owning_existing_goal=request["canonical_task_id"])
    # A relocated capability names the owner it moved to as the retry entrypoint.
    relocated = ingress._capability_dispatch_fail_closed(
        tmp_path, {**request, "processing_capability": "stegbrowser", "request_sha256": "e" * 64})
    assert relocated["retry_entrypoint"] == ingress.RELOCATED_CAPABILITY_OWNERS["stegbrowser"]
    assert_six_field_non_allow(relocated, owning_existing_goal=request["canonical_task_id"])
