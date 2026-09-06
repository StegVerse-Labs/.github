from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "control/portable-workercoordinator-packages/ecosystem-chat-sovereign-inference.json"
FRAGMENT = ROOT / "control/worker-registry.d/ecosystem-chat-sovereign-inference-parent-001.json"
HANDOFF = ROOT / "handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
VECTOR = ROOT / "control/task-vectors/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
MODULE = ROOT / "workercoordinator/portable_checkout.js"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_package_reuses_canonical_workercoordinator_authority():
    pkg = load(PACKAGE)
    assert pkg["schema"] == "stegverse.workercoordinator-portable-checkout-package/v1"
    assert pkg["portable_authority_epoch"] == "WC-PORTABLE-IPHONE-20260902"
    assert pkg["canonical_authority_owner"] == "StegVerse-Labs/.github WorkerCoordinator"
    assert pkg["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert pkg["execution_surface"] == "CURRENT_USER_IPHONE"
    assert pkg["credential_authority"] == "TV/TVC"
    assert pkg["github_token_runtime_authority"] == "NONE"
    assert pkg["heartbeat_grants_execution_authority"] is False
    assert pkg["parallel_workercoordinator_claim_issuance_allowed"] is False
    assert pkg["governed_transfer_required_before_other_surface_claims"] is True
    assert pkg["external_non_stegverse_machine_required"] is False


def test_package_binds_exact_current_parent_sources():
    pkg = load(PACKAGE)
    fragment = load(FRAGMENT)
    handoff = load(HANDOFF)
    vector = load(VECTOR)
    task = fragment["tasks"][0]
    worker = fragment["workers"][0]

    assert pkg["task"]["task_id"] == task["task_id"] == "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
    assert pkg["task"]["state"] == task["state"] == handoff["state"] == "HANDOFF_READY"
    assert pkg["task"]["claim_id"] is None and task["claim_id"] is None
    assert pkg["task"]["worker_id"] is None and task["worker_id"] is None
    assert pkg["task"]["admission"]["claim_state"] == task["admission"]["claim_state"]
    assert pkg["task"]["admission"]["fresh_fence_required"] is True
    assert pkg["worker"]["worker_id"] == worker["worker_id"]
    assert pkg["worker"]["status"] == worker["status"] == "AVAILABLE"
    assert set(pkg["required_capabilities"]) <= set(worker["capabilities"])
    assert vector["vector"] == "50000000100000"


def test_reset_lineage_floor_advances_beyond_every_observed_portable_fence():
    pkg = load(PACKAGE)
    assert pkg["predecessor_generation_floor"] == 24
    assert pkg["minimum_fencing_token_exclusive"] == 24
    assert max(pkg["predecessor_generation_floor"], pkg["minimum_fencing_token_exclusive"]) + 1 == 25
    assert "G23" in pkg["bootstrap_floor_reason"]
    assert "G24" in pkg["bootstrap_floor_reason"]


def test_package_is_checkoutable_but_nonexecuted_static_binding():
    pkg = load(PACKAGE)
    assert pkg["dependencies_complete"] is True
    assert pkg["execution_authorized"] is True
    assert pkg["semantic_state_current"] is True
    assert pkg["worker_resolved"] is True
    assert pkg["single_checkout_per_task_package"] is True
    assert pkg["terminal_reexecution_allowed"] is False
    assert pkg["runtime_execution_observed"] is False
    assert pkg["activation_effect"] is False
    assert pkg["authority_effect"] == "CANONICAL_WORKERCOORDINATOR_PORTABLE_PACKAGE"


def test_generic_checkout_enforces_fresh_distinct_task_fence():
    text = MODULE.read_text(encoding="utf-8")
    assert 'task.state !== "HANDOFF_READY"' in text
    assert "priorTaskIds.indexOf(pkg.task.task_id) !== -1" in text
    assert "var nextGeneration = generation + 1" in text
    assert 'global_workercoordinator_authority: true' in text
    assert 'stegos_device_task_authority: false' in text
    assert 'github_token_runtime_authority: "NONE"' in text
