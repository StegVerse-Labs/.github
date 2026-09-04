from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"workercoordinator/portable_checkout.js"
PACKAGE=ROOT/"control/portable-workercoordinator-packages/sv001-bounded-autonomy.json"
HANDOFF=ROOT/"docs/WORKERCOORDINATOR_PORTABLE_IPHONE_EXECUTION_MIRROR_HANDOFF.md"

def test_sv001_portable_package_preserves_canonical_authority():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert pkg["schema"]=="stegverse.workercoordinator-portable-checkout-package/v1"
    assert pkg["canonical_authority_owner"]=="StegVerse-Labs/.github WorkerCoordinator"
    assert pkg["authority_domain"]=="INDEPENDENT_TASK_CONTROL"
    assert pkg["execution_surface"]=="CURRENT_USER_IPHONE"
    assert pkg["predecessor_generation_floor"]==22
    assert pkg["minimum_fencing_token_exclusive"]==22
    assert pkg["credential_authority"]=="TV/TVC"
    assert pkg["github_token_runtime_authority"]=="NONE"
    assert pkg["heartbeat_grants_execution_authority"] is False
    assert pkg["parallel_workercoordinator_claim_issuance_allowed"] is False
    assert pkg["external_non_stegverse_machine_required"] is False

def test_terminal_package_is_globally_non_checkoutable():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert pkg["task"]["state"]=="COMPLETED"
    assert pkg["task"]["claim_id"]=="SHWP-SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001-G23"
    assert pkg["task"]["worker_id"]=="stegverse001-bounded-autonomy-runtime-worker"
    assert pkg["task"]["admission"]["claim_state"]=="TERMINAL_NO_FURTHER_CLAIM"
    assert pkg["task"]["admission"]["fresh_fence_required"] is False
    assert pkg["execution_authorized"] is False
    assert pkg["authority_effect"]=="CANONICAL_WORKERCOORDINATOR_PORTABLE_TERMINAL_PACKAGE"
    text=MODULE.read_text(encoding="utf-8")
    assert 'task.state !== "HANDOFF_READY"' in text
    assert 'fail("task not clean HANDOFF_READY")' in text

def test_terminal_package_binds_first_canonical_g23_and_retains_duplicates():
    terminal=json.loads(PACKAGE.read_text(encoding="utf-8"))["terminal_execution"]
    assert terminal["canonical_claim_id"]=="SHWP-SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001-G23"
    assert terminal["canonical_fencing_token"]==23
    assert terminal["canonical_node_id"]=="stegnode-web-f24e3bfb7f5343cb37323187a88e51f3"
    assert terminal["canonical_cycle_receipt_sha256"]=="sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35"
    assert terminal["canonical_custody_eligible"] is True
    assert terminal["master_records_custody"]=="PENDING"
    assert terminal["sv002_adversarial_observation"]=="PENDING"
    dup=terminal["duplicates_retained_non_custodial"]
    assert {x["cycle_receipt_sha256"] for x in dup}=={
      "sha256:6bcc1976793657ea849a3678fa324c69134d2b59481e0bc9994c6baa6c4aff79",
      "sha256:7b66f6cf260a46fcb8555d207cd868eaf2d31aa67372f0701841f91c648d00d4",
    }
    assert all(x["custody_eligible"] is False for x in dup)
    reset=next(x for x in dup if x["reason"]=="RESET_LINEAGE_REEXECUTION_AFTER_CANONICAL_TERMINAL")
    assert reset["node_id"]=="stegnode-web-2d6daa94e496d451d16bd5619bd30a25"
    assert reset["checkout_receipt_sha256"]=="sha256:8ef913db2cc4b79fb8b4d78deef9160efd98eacac0a8f2ba8d1fd58433c2223d"
    assert reset["tvc_lease_consumption"]=="CONSUMED"

def test_historical_first_portable_sv001_claim_is_generation_23():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert max(pkg["predecessor_generation_floor"],pkg["minimum_fencing_token_exclusive"])+1==23
    assert pkg["terminal_execution"]["canonical_fencing_token"]==23

def test_portable_checkout_is_distinct_from_stegos_device_fencing():
    text=MODULE.read_text(encoding="utf-8")
    assert '"stegverse.workercoordinator-portable-state/v1"' in text
    assert 'global_workercoordinator_authority: true' in text
    assert 'stegos_device_task_authority: false' in text
    assert "device-task-control-generation" not in text

def test_portable_state_retains_full_checkout_receipt_atomically():
    text=MODULE.read_text(encoding="utf-8")
    assert "last_checkout_receipt: receiptBody" in text
    assert "checkout_tail_sha256: receiptBody.receipt_sha256" in text

def test_sv001_portable_package_is_single_checkout_terminal_safe():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert pkg["single_checkout_per_task_package"] is True
    assert pkg["terminal_reexecution_allowed"] is False
    assert pkg["downstream_retry_after_terminal"] is True

def test_portable_checkout_fails_closed_after_first_local_checkout_too():
    text=MODULE.read_text(encoding="utf-8")
    assert "checkout_count: 0" in text
    assert "inferredCheckoutCount >= 1" in text
    assert "task package already checked out; terminal/downstream continuation must not mint another claim" in text
    assert "checkout_count: inferredCheckoutCount + 1" in text

def test_handoff_records_reset_lineage_without_authority_widening():
    text=HANDOFF.read_text(encoding="utf-8")
    assert "Reset-lineage terminal propagation" in text
    assert "sha256:7b66f6cf260a46fcb8555d207cd868eaf2d31aa67372f0701841f91c648d00d4" in text
    assert "WorkerCoordinator remains" in text
    assert "TV/TVC remains credential authority" in text
