from __future__ import annotations

from typing import Any

EXPECTED_SCHEMA = "stegverse.stegnutrition-continuation-receipt/v0.2"
EXPECTED_TASK_ID = "SHWP-STEGNUTRITION-CONTINUATION-001"
ALLOWED_SUITE_STATES = {"COMPLETE", "BLOCKED", "RETRY", "FAILED"}


class ReceiptContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptContractError(message)


def validate_receipt(value: Any) -> dict:
    _require(isinstance(value, dict), "receipt must be an object")
    _require(value.get("schema") == EXPECTED_SCHEMA, "unsupported receipt schema")
    _require(value.get("task_id") == EXPECTED_TASK_ID, "unexpected task_id")
    _require(isinstance(value.get("claim_id"), str) and bool(value["claim_id"]), "claim_id required")
    _require(isinstance(value.get("heartbeat_epoch"), int) and value["heartbeat_epoch"] >= 0, "heartbeat_epoch must be nonnegative integer")
    _require(isinstance(value.get("fencing_token"), int) and value["fencing_token"] >= 0, "fencing_token must be nonnegative integer")
    _require(isinstance(value.get("transition_id"), str) and bool(value["transition_id"]), "transition_id required")
    _require(isinstance(value.get("transition_sequence"), int) and value["transition_sequence"] >= 1, "transition_sequence must be positive integer")
    _require(value.get("stegnutrition_inventory_ref") == "tasks/STEGNUTRITION-SESSION-20260811.json", "canonical inventory ref required")
    _require(isinstance(value.get("projection"), dict), "projection must be object")
    suite = value.get("local_validation")
    _require(isinstance(suite, dict), "local_validation must be object")
    _require(suite.get("state") in ALLOWED_SUITE_STATES, "invalid local_validation state")
    _require(value.get("github_token_required") is False, "github_token_required must be false")
    _require(value.get("github_repository_fetch_performed") is False, "github_repository_fetch_performed must be false")
    _require(value.get("credential_authority") == "TV/TVC", "credential_authority must be TV/TVC")
    _require(value.get("authority_effect") == "none_beyond_admitted_continuation_receipt_namespace", "unexpected authority effect")
    _require(isinstance(value.get("completed"), bool), "completed must be boolean")
    blocker = value.get("blocker")
    if value["completed"]:
        _require(suite.get("state") == "COMPLETE", "completed receipt requires COMPLETE local validation")
        _require(blocker is None, "completed receipt must not retain blocker")
    else:
        _require(blocker is None or isinstance(blocker, dict), "blocker must be object or null")
        if isinstance(blocker, dict):
            _require(blocker.get("solution_required") is True, "blocker must require a solution")
            _require(isinstance(blocker.get("next_solution_action"), str) and bool(blocker["next_solution_action"]), "blocker next_solution_action required")
    return value
