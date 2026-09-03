from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "workercoordinator/portable_checkout.js"
PACKAGE = ROOT / "control/portable-workercoordinator-packages/sv001-bounded-autonomy.json"
HANDOFF = ROOT / "docs/WORKERCOORDINATOR_PORTABLE_IPHONE_EXECUTION_MIRROR_HANDOFF.md"

def test_sv001_portable_package_preserves_canonical_authority():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert pkg["schema"]=="stegverse.workercoordinator-portable-checkout-package/v1"
    assert pkg["canonical_authority_owner"]=="StegVerse-Labs/.github WorkerCoordinator"
    assert pkg["authority_domain"]=="INDEPENDENT_TASK_CONTROL"
    assert pkg["execution_surface"]=="CURRENT_USER_IPHONE"
    assert pkg["predecessor_generation_floor"]==22
    assert pkg["minimum_fencing_token_exclusive"]==22
    assert pkg["predecessor_registry_git_blob_sha"]=="d860e4c09aaeffaf896a3a95b440334984547dce"
    assert pkg["credential_authority"]=="TV/TVC"
    assert pkg["github_token_runtime_authority"]=="NONE"
    assert pkg["heartbeat_grants_execution_authority"] is False
    assert pkg["parallel_workercoordinator_claim_issuance_allowed"] is False
    assert pkg["governed_transfer_required_before_other_surface_claims"] is True
    assert pkg["external_non_stegverse_machine_required"] is False

def test_sv001_portable_package_matches_current_canonical_source_blobs():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    source=pkg["source_binding"]
    assert source["task_fragment_git_blob_sha"]=="1134ecec47457e9a32c7c71eeb4ec607e73abc63"
    assert source["handoff_git_blob_sha"]=="cba7ebf72769aa6bee5c4e71f8c2d12aee6a76df"
    assert source["state_vector_git_blob_sha"]=="228fae603714721dc36c9edc605ee21a7fe70b73"
    assert source["process_adapter_git_blob_sha"]=="b5b4a71c298378fbdf407998e9a04d2b3cdd6543"
    assert pkg["task"]["state"]=="HANDOFF_READY"
    assert pkg["task"]["claim_id"] is None
    assert pkg["task"]["worker_id"] is None
    admission=pkg["task"]["admission"]
    assert admission["claim_state"]=="AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
    assert admission["fresh_fence_required"] is True
    assert admission["heartbeat_grants_execution_authority"] is False

def test_portable_checkout_is_distinct_from_stegos_device_fencing():
    text=MODULE.read_text(encoding="utf-8")
    assert '"stegverse.workercoordinator-portable-state/v1"' in text
    assert '"CANONICAL_WORKERCOORDINATOR_CLAIM_FENCE"' in text
    assert '"CURRENT_USER_IPHONE"' in text
    assert 'global_workercoordinator_authority: true' in text
    assert 'stegos_device_task_authority: false' in text
    assert "device-task-control-generation" not in text
    assert "parallel_workercoordinator_claim_issuance_allowed" in text
    assert "governed_transfer_required_before_other_surface_claims" in text

def test_first_portable_sv001_claim_is_strict_successor_of_generation_22():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    generation=max(pkg["predecessor_generation_floor"],pkg["minimum_fencing_token_exclusive"])+1
    assert generation==23
    assert f'SHWP-{pkg["task"]["task_id"]}-G{generation}'=="SHWP-SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001-G23"

def test_handoff_prohibits_parallel_authority_lineage():
    text=HANDOFF.read_text(encoding="utf-8")
    assert "parallel claim issuance" in text.lower()
    assert "governed transfer" in text.lower()
    assert "second user-operated device required: false" in text
    assert "always-on external host required: false" in text


def test_portable_state_retains_full_checkout_receipt_atomically():
    text=MODULE.read_text(encoding="utf-8")
    assert "last_checkout_receipt: receiptBody" in text
    assert "checkout_tail_sha256: receiptBody.receipt_sha256" in text

def test_sv001_portable_package_is_single_checkout_terminal_safe():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert pkg["single_checkout_per_task_package"] is True
    assert pkg["terminal_reexecution_allowed"] is False
    assert pkg["downstream_retry_after_terminal"] is True

def test_portable_checkout_fails_closed_after_first_checkout():
    text=MODULE.read_text(encoding="utf-8")
    assert "checkout_count: 0" in text
    assert "inferredCheckoutCount >= 1" in text
    assert "task package already checked out; terminal/downstream continuation must not mint another claim" in text
    assert "checkout_count: inferredCheckoutCount + 1" in text
