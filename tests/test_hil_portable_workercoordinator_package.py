from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "control/portable-workercoordinator-packages/hil-sovereign-receiver.json"
TASK_FRAGMENT = ROOT / "control/worker-registry.d/hil-sovereign-receiver-001.json"
HANDOFF = ROOT / "handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json"
STATE_VECTOR = ROOT / "control/task-vectors/SHWP-HIL-SOVEREIGN-RECEIVER-001.json"
REGISTRY = ROOT / "control/worker-registry.json"
PORTABLE = ROOT / "workercoordinator/portable_checkout.js"
MIRROR = ROOT / "docs/HIL_PORTABLE_IPHONE_WORKERCOORDINATOR_PACKAGE_MIRROR_HANDOFF.md"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def package() -> dict:
    return json.loads(PACKAGE.read_text(encoding="utf-8"))


def test_hil_portable_package_preserves_canonical_authority_and_same_device_surface():
    pkg = package()
    assert pkg["schema"] == "stegverse.workercoordinator-portable-checkout-package/v1"
    assert pkg["canonical_authority_owner"] == "StegVerse-Labs/.github WorkerCoordinator"
    assert pkg["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert pkg["execution_surface"] == "CURRENT_USER_IPHONE"
    assert pkg["credential_authority"] == "TV/TVC"
    assert pkg["github_token_runtime_authority"] == "NONE"
    assert pkg["heartbeat_grants_execution_authority"] is False
    assert pkg["parallel_workercoordinator_claim_issuance_allowed"] is False
    assert pkg["governed_transfer_required_before_other_surface_claims"] is True
    assert pkg["external_non_stegverse_machine_required"] is False
    assert pkg["activation_effect"] is False
    assert pkg["runtime_execution_observed"] is False


def test_hil_task_and_worker_are_exactly_bound_to_registered_unclaimed_task():
    pkg = package()
    task = pkg["task"]
    worker = pkg["worker"]
    fragment = json.loads(TASK_FRAGMENT.read_text(encoding="utf-8"))
    registered_task = fragment["tasks"][0]
    registered_worker = fragment["workers"][0]

    assert task["task_id"] == "SHWP-HIL-SOVEREIGN-RECEIVER-001"
    assert task["state"] == registered_task["state"] == "HANDOFF_READY"
    assert task["claim_id"] is registered_task["claim_id"] is None
    assert task["worker_id"] is registered_task["worker_id"] is None
    assert task["admission"]["claim_state"] == registered_task["admission"]["claim_state"]
    assert task["admission"]["fresh_fence_required"] is True
    assert worker["worker_id"] == registered_worker["worker_id"] == "hil-sovereign-receiver-worker"
    assert worker["status"] == registered_worker["status"] == "AVAILABLE"
    assert set(pkg["required_capabilities"]).issubset(set(worker["capabilities"]))
    assert set(pkg["required_capabilities"]).issubset(set(registered_worker["capabilities"]))


def test_hil_portable_package_is_bound_to_current_canonical_source_blobs():
    pkg = package()
    binding = pkg["source_binding"]
    assert binding["task_fragment_git_blob_sha"] == git_blob_sha(TASK_FRAGMENT)
    assert binding["handoff_git_blob_sha"] == git_blob_sha(HANDOFF)
    assert binding["state_vector_git_blob_sha"] == git_blob_sha(STATE_VECTOR)
    assert binding["portable_checkout_git_blob_sha"] == git_blob_sha(PORTABLE)
    assert pkg["predecessor_registry_git_blob_sha"] == git_blob_sha(REGISTRY)


def test_hil_portable_checkout_advances_beyond_observed_g24_floor():
    pkg = package()
    assert pkg["predecessor_generation_floor"] == 24
    assert pkg["minimum_fencing_token_exclusive"] == 24
    assert max(pkg["predecessor_generation_floor"], pkg["minimum_fencing_token_exclusive"]) + 1 == 25
    assert pkg["single_checkout_per_task_package"] is True
    assert pkg["terminal_reexecution_allowed"] is False
    assert pkg["downstream_retry_after_terminal"] is True


def test_native_consumer_binding_does_not_convert_package_into_runtime_evidence():
    pkg = package()
    native = pkg["native_consumer"]
    assert native["repository"] == "StegVerse-Labs/StegOS"
    assert native["source_merge"] == "efc9d5e1e8140759a5f971484ae593cf545b9203"
    assert native["execution_surface"] == "CURRENT_USER_IPHONE"
    assert native["claim_fence_minted_by_native_component"] is False
    assert native["expected_transition"] == "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED"
    assert native["runtime_evidence_required"] is True
    assert native["authority_effect"] == "NONE_BINDING_ONLY"


def test_handoff_keeps_runtime_and_claim_boundaries_explicit():
    text = MIRROR.read_text(encoding="utf-8")
    assert "does not itself create that claim/fence" in text
    assert "PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002" in text
    assert "source/package/CI" in text
    assert "WorkerCoordinator" in text
