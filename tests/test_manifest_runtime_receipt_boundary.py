"""The missing runtime receipt is an actionable profile verdict, not an InTr receipt."""
import json
from unittest.mock import patch

from workers import manifest_state_transition_intr_ingress as ingress


def test_missing_purpose_receipt_returns_immutable_nonallow(tmp_path):
    request = {
        "canonical_task_id": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
        "graph_id": "svg-governance-cycle",
        "processing_capability": "svg_governance_cycle",
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
    assert first["organization_master_records_closure_observed"] is False
    assert first["failed_predicate"] == "EXACT_REQUEST_BOUND_PURPOSE_RUNTIME_RECEIPT_PRESENT"
    with open(first["source_disposition_ref"], encoding="utf-8") as stream:
        persisted = json.load(stream)
    assert persisted["request_sha256"] == request["request_sha256"]
    assert persisted["authority_effect"] == "NONE_PROFILE_BOUNDARY_DISPOSITION_ONLY"
