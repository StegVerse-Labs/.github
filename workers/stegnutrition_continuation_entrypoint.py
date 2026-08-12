#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/stegnutrition_continuation_worker.py"
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from stegnutrition_receipt_contract import ReceiptContractError, validate_receipt


EXPECTED_INVENTORY = "tasks/STEGNUTRITION-SESSION-20260811.json"
FDA_TASK = "STEGNUTRITION-FDA-REFERENCE-020"
FDA_REQUIRED_SURFACES = (
    "src/stegnutrition/fda_reference.py",
    "tests/test_fda_reference.py",
    "tasks/STEGNUTRITION-FDA-REFERENCE-020.json",
)


def _preflight_current_stegnutrition_surface() -> None:
    """Require current canonical extensions when a local StegNutrition tree exists.

    Absence of a local root is handled by the heartbeat worker as an active
    materialization constraint. This preflight only prevents a stale local tree
    from silently omitting canonical task 020 or its FDA source/test surfaces.
    """
    raw = os.environ.get("STEGVERSE_STEGNUTRITION_ROOT", "").strip()
    if not raw:
        return
    root = Path(raw).expanduser().resolve()
    inventory_path = root / EXPECTED_INVENTORY
    if not inventory_path.is_file():
        return
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReceiptContractError(f"canonical StegNutrition inventory unreadable: {exc}") from exc

    rows: list[object] = []
    for section in (
        "execution_inventory",
        "completed_or_released",
        "implemented_pending_activation_or_real_evidence",
        "machine_owned_or_blocked",
        "remaining_assigned_tasks",
        "partially_complete",
    ):
        value = inventory.get(section)
        if isinstance(value, list):
            rows.extend(value)
    task_ids = {
        row if isinstance(row, str) else row.get("task_id")
        for row in rows
        if isinstance(row, (str, dict))
    }
    if FDA_TASK not in task_ids:
        raise ReceiptContractError(f"canonical StegNutrition inventory missing {FDA_TASK}")
    missing = [relative for relative in FDA_REQUIRED_SURFACES if not (root / relative).is_file()]
    if missing:
        raise ReceiptContractError(f"canonical FDA reference surfaces missing: {missing}")


def _project_active_work(response: dict, receipt: dict) -> dict:
    """Remove passive BLOCKED semantics from the operational adapter response."""
    raw_state = response.get("state")
    if raw_state == "BLOCKED":
        response = dict(response)
        response["legacy_worker_state"] = "BLOCKED"
        response["state"] = "ACTIVE"
        response["operational_state"] = "ACTIVE_CONSTRAINT"
        response["legacy_transition_id"] = response.get("transition_id")
        response["transition_id"] = "STEGNUTRITION_ACTIVE_CONSTRAINT"
        response["expected_next_transition"] = (
            response.get("expected_next_transition") or "STEGNUTRITION_CONTINUATION_RECHECK"
        )
        blocker = receipt.get("blocker")
        if isinstance(blocker, dict):
            response["active_constraint"] = {
                "dependency_class": blocker.get("dependency_class"),
                "problem_statement": blocker.get("problem_statement"),
                "next_solution_action": blocker.get("next_solution_action"),
                "stopping_state": False,
            }
    elif raw_state == "COMPLETED":
        response = dict(response)
        response["operational_state"] = "COMPLETE"
    else:
        response = dict(response)
        response["operational_state"] = raw_state or "FAILED"
    return response


def main() -> int:
    raw = sys.stdin.read()
    try:
        _preflight_current_stegnutrition_surface()
    except ReceiptContractError as exc:
        print(f"StegNutrition continuation preflight failed: {exc}", file=sys.stderr)
        return 13

    proc = subprocess.run(
        [sys.executable, str(WORKER)],
        cwd=ROOT,
        input=raw,
        text=True,
        capture_output=True,
        check=False,
        timeout=205,
    )
    if proc.returncode != 0:
        if proc.stdout:
            sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        return proc.returncode
    try:
        response = json.loads(proc.stdout)
        checkpoint_ref = response.get("checkpoint_ref")
        if not isinstance(checkpoint_ref, str) or not checkpoint_ref:
            raise ReceiptContractError("worker response missing checkpoint_ref")
        receipt_path = (ROOT / checkpoint_ref).resolve()
        admitted_root = (ROOT / "receipts/stegnutrition-continuation").resolve()
        if admitted_root not in receipt_path.parents:
            raise ReceiptContractError("checkpoint_ref escaped admitted receipt namespace")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_receipt(receipt)
        if receipt.get("claim_id") != (response.get("claim_id") or receipt.get("claim_id")):
            raise ReceiptContractError("response/receipt claim mismatch")
        response = _project_active_work(response, receipt)
    except (OSError, json.JSONDecodeError, ReceiptContractError) as exc:
        print(f"StegNutrition continuation receipt validation failed: {exc}", file=sys.stderr)
        return 12
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
