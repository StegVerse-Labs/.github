from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "data/canonical-task-records/STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001.json"
CORRECTION = ROOT / "data/canonical-task-records/STEG-BROWSER-HEALER-ROUTING-CORRECTION-001.json"
REQUEST = ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_immutable_stegbrowser_request_has_direct_reusable_owner_without_healer():
    request = load(REQUEST)
    assert request["invocation_request_nonce"] == "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
    assert request["requested_invocation_count"] == 1
    assert request["reusable_task_binding"]["reusable_task_id"] == "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001"
    assert "SHWP-HEALER-SOVEREIGN-SCHEDULER-001" not in json.dumps(request, sort_keys=True)


def test_parent_progression_no_longer_gated_on_healer_carrier():
    parent = load(PARENT)
    assert parent["routing_correction"]["healer_role"] == "TRIGGERED_REMEDIATION_ONLY"
    assert parent["routing_correction"]["healer_required_for_progression"] is False
    assert "OBSERVE_POST_REPAIR_HEALER_CARRIER_PACKET" not in parent["allowed_next_transitions"]
    assert "CONTINUE_DIRECT_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001" in parent["allowed_next_transitions"]
    dep = {row["dependency_id"]: row for row in parent["dependencies"]}
    assert dep["DEP-RESIDENT-CUSTODY-ROOT-OBSERVATION"]["state"] == "DIRECT_OWNER_OBSERVATION_REQUIRED"
    assert "HEALER_NOT_REQUIRED" in dep["DEP-RESIDENT-CUSTODY-ROOT-OBSERVATION"]["disposition"]
    seam = parent["endpoint_binding_terminal_intake"]["retention_seam"]
    assert seam["healer_carrier_required"] is False
    assert seam["healer_role"] == "TRIGGERED_REMEDIATION_ONLY"
    assert seam["direct_execution_owner"] == "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001_VIA_RUN_STEGBROWSER_MANIFEST_BOUND_RUNTIME"


def test_correction_records_exact_insertion_point_and_no_second_invocation():
    correction = load(CORRECTION)
    assert correction["trace_result"]["exact_insertion_point"] == "GENERATION_70_RETENTION_SEAM_RECONCILIATION"
    assert correction["trace_result"]["canonical_request_contains_healer_dependency"] is False
    assert correction["trace_result"]["healer_role"] == "TRIGGERED_REMEDIATION_ONLY"
    assert correction["completion"]["second_invocation_issued"] is False
    assert correction["completion"]["new_runtime_created"] is False
    assert correction["completion"]["new_scheduler_created"] is False
    assert correction["completion"]["new_dispatcher_created"] is False
