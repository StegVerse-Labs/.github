from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.d" / "erl-ai-economic-transparency-review-001.json"
HANDOFF = ROOT / "handoffs" / "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json"


def test_erl_review_uses_existing_no_carrier_event_workercoordinator_path() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    task = registry["tasks"][0]
    admission = task["admission"]
    assert task["state"] == "HANDOFF_READY"
    assert task["claim_id"] is None
    assert task["worker_id"] is None
    assert admission["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert admission["claim_state"] == "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
    assert admission["fresh_fence_required"] is True
    assert admission["carrier_trigger_required"] is False
    assert admission["heartbeat_reference_only"] is True
    assert admission["heartbeat_grants_execution_authority"] is False


def test_erl_handoff_does_not_restore_superseded_heartbeat_event_gating() -> None:
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    authority = handoff["authority"]
    activation = handoff["activation"]
    assert authority["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert authority["claim_state"] == "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
    assert authority["fresh_fence_required"] is True
    assert authority["carrier_trigger_required"] is False
    assert authority["heartbeat_grants_execution_authority"] is False
    assert activation["carrier_event_prerequisite"] is False
    assert "each admitted heartbeat" not in activation["recheck_trigger"]
