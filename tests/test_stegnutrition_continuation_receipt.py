from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "workers/stegnutrition_receipt_contract.py"


def _contract():
    spec = importlib.util.spec_from_file_location("stegnutrition_receipt_contract", CONTRACT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _receipt(completed: bool = False) -> dict:
    blocker = None if completed else {
        "dependency_class": "INTERNAL",
        "problem_statement": "resident route absent",
        "solution_required": True,
        "may_remain_blocked": True,
        "workaround_candidates": ["advance resident heartbeat"],
        "next_solution_action": "advance resident heartbeat",
    }
    return {
        "schema": "stegverse.stegnutrition-continuation-receipt/v0.2",
        "task_id": "SHWP-STEGNUTRITION-CONTINUATION-001",
        "claim_id": "CLAIM-TEST",
        "worker_id": "worker",
        "worker_instance_id": "worker-HB30-G1",
        "heartbeat_epoch": 30,
        "fencing_token": 1,
        "transition_id": "STEGNUTRITION_CONTINUATION_BLOCKED" if not completed else "STEGNUTRITION_RELEASE_CANDIDATE_READY",
        "transition_sequence": 1,
        "stegnutrition_inventory_ref": "tasks/STEGNUTRITION-SESSION-20260811.json",
        "projection": {"local_root_available": True},
        "local_validation": {"state": "FAILED" if not completed else "COMPLETE", "reason": "fixture", "returncode": 1 if not completed else 0},
        "blocker": blocker,
        "github_token_required": False,
        "github_repository_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "none_beyond_admitted_continuation_receipt_namespace",
        "completed": completed,
    }


def test_accepts_blocked_receipt_with_no_token_authority() -> None:
    module = _contract()
    assert module.validate_receipt(_receipt())


def test_accepts_completed_receipt_only_with_complete_validation() -> None:
    module = _contract()
    assert module.validate_receipt(_receipt(completed=True))


def test_rejects_github_token_requirement() -> None:
    module = _contract()
    value = _receipt()
    value["github_token_required"] = True
    try:
        module.validate_receipt(value)
    except module.ReceiptContractError:
        return
    raise AssertionError("token-requiring receipt was accepted")


def test_rejects_completed_receipt_with_blocker() -> None:
    module = _contract()
    value = _receipt(completed=True)
    value["blocker"] = {"solution_required": True, "next_solution_action": "x"}
    try:
        module.validate_receipt(value)
    except module.ReceiptContractError:
        return
    raise AssertionError("completed receipt retained a blocker")
