#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "healer-sovereign-scheduler").resolve()
EXPECTED_TASK = "SHWP-HEALER-SOVEREIGN-SCHEDULER-001"
CURRENT_AUTHORITY = "TV/TVC"


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def _response(state: str, transition: str, checkpoint: str, blocker: dict | None, epoch: int) -> dict:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "HEALER_SOVEREIGN_SCHEDULER_RECHECK",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "healer_sovereign_scheduler",
        },
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid invocation: {exc}", file=sys.stderr)
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 4
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    allowed = set(execution.get("allowed_paths") or [])
    if "healer_sovereign_scheduling" not in required:
        return 6
    if "receipts/healer-sovereign-scheduler/**" not in allowed:
        return 7

    forbidden = [name for name in ("HEALER_GH_TOKEN", "GITHUB_TOKEN", "GH_TOKEN", "HEALER_PAT", "GH_STEGVERSE_AI_TOKEN") if os.getenv(name)]
    healer_raw = os.getenv("STEGVERSE_HEALER_ROOT", "").strip()
    roots_json = os.getenv("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    blocker = None
    child_receipt: dict = {}
    state = "BLOCKED"
    transition = "HEALER_SOVEREIGN_SCHEDULER_BLOCKED"

    if forbidden:
        blocker = {
            "dependency_class": "AUTHORITY_CONFLICT",
            "problem_statement": "Forbidden GitHub credential environment is present in the sovereign Healer worker.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "REMOVE_GITHUB_CREDENTIAL_ENVIRONMENT",
            "forbidden_variables": sorted(forbidden),
        }
    elif not healer_raw:
        blocker = {
            "dependency_class": "LOCAL_RESOURCE",
            "problem_statement": "Locally materialized StegVerse-Healer root is not declared.",
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "MATERIALIZE_AND_DECLARE_STEGVERSE_HEALER_ROOT",
        }
    elif not roots_json:
        blocker = {
            "dependency_class": "LOCAL_RESOURCE",
            "problem_statement": "Locally materialized repository-root map is not declared.",
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "DECLARE_STEGVERSE_REPO_ROOTS_JSON",
        }
    else:
        healer_root = Path(healer_raw).expanduser().resolve()
        entry = healer_root / "app" / "dispatch_orchestrators.py"
        targets = healer_root / "data" / "orchestrator_targets.json"
        if not healer_root.is_dir() or not entry.is_file() or not targets.is_file():
            blocker = {
                "dependency_class": "LOCAL_RESOURCE",
                "problem_statement": "Declared StegVerse-Healer root is incomplete.",
                "solution_required": True,
                "may_remain_blocked": True,
                "next_solution_action": "MATERIALIZE_COMPLETE_STEGVERSE_HEALER_TREE",
            }
        else:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "LANG": os.environ.get("LANG", "C.UTF-8"),
                "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
                "RUN_SCOPE": "all",
                "DISPATCH_MODE": "schedule",
                "TARGETS_FILE": str(targets),
                "STEGVERSE_REPO_ROOTS_JSON": roots_json,
            }
            proc = subprocess.run(
                [sys.executable, str(entry)],
                cwd=healer_root,
                env=env,
                text=True,
                capture_output=True,
                timeout=240,
                check=False,
            )
            try:
                child_receipt = json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception:
                child_receipt = {
                    "state": "FAILED",
                    "error": "INVALID_HEALER_CHILD_RECEIPT",
                    "stdout_tail": proc.stdout[-4000:],
                    "stderr_tail": proc.stderr[-4000:],
                }
            child_state = child_receipt.get("state")
            if proc.returncode == 0 and child_state == "COMPLETE":
                state = "COMPLETED"
                transition = "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"
            elif child_state in {"BLOCKED", "REVIEW_REQUIRED"}:
                state = "BLOCKED"
                transition = "HEALER_SOVEREIGN_SCHEDULER_BLOCKED"
                blocker = {
                    "dependency_class": "INTERNAL_CAPABILITY",
                    "problem_statement": "One or more due Healer targets lack a completed sovereign local handler.",
                    "solution_required": True,
                    "may_remain_blocked": True,
                    "next_solution_action": "COMPLETE_BLOCKED_HEALER_TARGET_ADAPTERS",
                }
            else:
                state = "FAILED"
                transition = "HEALER_SOVEREIGN_SCHEDULER_FAILED"
                blocker = {
                    "dependency_class": "IMPLEMENTATION",
                    "problem_statement": "Sovereign Healer child execution failed.",
                    "solution_required": True,
                    "may_remain_blocked": False,
                    "next_solution_action": "REPAIR_HEALER_SOVEREIGN_SCHEDULER",
                }

    receipt = {
        "schema": "stegverse.healer.sovereign_scheduler_worker_receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "state": state,
        "transition_id": transition,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "github_actions_production_role": False,
        "child_receipt": child_receipt,
        "blocker": blocker,
        "authority_effect": "BOUNDED_LOCAL_SCHEDULER_EXECUTION_ONLY",
    }
    rel = f"receipts/healer-sovereign-scheduler/{EXPECTED_TASK}.json"
    atomic_write(ROOT / rel, receipt)
    json.dump(_response(state, transition, rel, blocker, epoch), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
