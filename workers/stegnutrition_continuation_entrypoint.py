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
CURRENT_REQUIRED_SURFACES = (
    "src/stegnutrition/fda_reference.py",
    "tests/test_fda_reference.py",
    "tasks/STEGNUTRITION-FDA-REFERENCE-020.json",
    "src/stegnutrition/ledger.py",
    "schemas/meal-ledger.schema.json",
    "scripts/verify_runtime_custody_no_network.py",
)
LOCAL_ROOT_MARKERS = (
    "STEGNUTRITION_MIRROR_HANDOFF.md",
    EXPECTED_INVENTORY,
)
CUSTODY_VERIFIER = "scripts/verify_runtime_custody_no_network.py"


def _is_canonical_local_root(root: Path) -> bool:
    return root.is_dir() and all((root / relative).is_file() for relative in LOCAL_ROOT_MARKERS)


def _candidate_local_roots() -> list[Path]:
    """Return deterministic local-only StegNutrition candidates.

    No candidate is downloaded, cloned, resolved through GitHub, or selected from a
    hosted provider. The explicit environment override remains supported, but it is
    optional: a standard sibling/canonical sovereign workspace is discovered
    automatically.
    """
    home = Path.home()
    return [
        ROOT.parent / "StegNutrition",
        ROOT.parent.parent / "StegVerse-Labs" / "StegNutrition",
        home / "StegVerse-Labs" / "StegNutrition",
        home / "stegverse" / "StegVerse-Labs" / "StegNutrition",
        Path("/opt/stegverse/StegVerse-Labs/StegNutrition"),
        Path("/srv/stegverse/StegVerse-Labs/StegNutrition"),
        Path("/var/lib/stegverse/StegVerse-Labs/StegNutrition"),
    ]


def _discover_local_stegnutrition_root() -> Path | None:
    explicit = os.environ.get("STEGVERSE_STEGNUTRITION_ROOT", "").strip()
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not _is_canonical_local_root(root):
            raise ReceiptContractError(
                "explicit STEGVERSE_STEGNUTRITION_ROOT is not a canonical locally materialized StegNutrition tree"
            )
        return root

    discovered: list[Path] = []
    seen: set[Path] = set()
    for candidate in _candidate_local_roots():
        root = candidate.expanduser().resolve()
        if root in seen:
            continue
        seen.add(root)
        if _is_canonical_local_root(root):
            discovered.append(root)

    if not discovered:
        return None
    if len(discovered) > 1:
        raise ReceiptContractError(
            "ambiguous locally materialized StegNutrition trees: "
            + ", ".join(str(path) for path in discovered)
        )
    return discovered[0]


def _preflight_current_stegnutrition_surface(root: Path | None) -> Path | None:
    """Require current canonical extensions when a local StegNutrition tree exists."""
    if root is None:
        return None
    inventory_path = root / EXPECTED_INVENTORY
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
    missing = [relative for relative in CURRENT_REQUIRED_SURFACES if not (root / relative).is_file()]
    if missing:
        raise ReceiptContractError(f"canonical StegNutrition continuation surfaces missing: {missing}")
    return root


def _run_runtime_custody_preflight(root: Path | None) -> None:
    if root is None:
        return
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str((root / "src").resolve()),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    try:
        proc = subprocess.run(
            [sys.executable, str((root / CUSTODY_VERIFIER).resolve())],
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReceiptContractError("runtime custody verifier exceeded 30 seconds") from exc
    if proc.returncode != 0:
        tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-3000:]
        raise ReceiptContractError(f"runtime custody verifier failed: {tail}")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ReceiptContractError("runtime custody verifier did not emit JSON") from exc
    if result.get("state") != "PASS":
        raise ReceiptContractError("runtime custody verifier did not report PASS")
    if result.get("github_token_required") is not False:
        raise ReceiptContractError("runtime custody verifier violated no-GitHub-token invariant")
    if result.get("credential_requirement") != "NONE":
        raise ReceiptContractError("runtime custody verifier violated credential NONE invariant")
    if not result.get("replay_binding_retained"):
        raise ReceiptContractError("runtime custody verifier did not retain replay binding")
    if not result.get("token_requiring_binding_rejected"):
        raise ReceiptContractError("runtime custody verifier did not reject token-requiring binding")
    if not result.get("proof_tamper_rejected"):
        raise ReceiptContractError("runtime custody verifier did not reject proof tampering")


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
        local_root = _discover_local_stegnutrition_root()
        local_root = _preflight_current_stegnutrition_surface(local_root)
        _run_runtime_custody_preflight(local_root)
        if local_root is not None:
            os.environ["STEGVERSE_STEGNUTRITION_ROOT"] = str(local_root)
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
