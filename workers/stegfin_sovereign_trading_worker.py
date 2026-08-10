#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-STEGFIN-SOVEREIGN-TRADING-001"
RECEIPT_ROOT = (ROOT / "receipts" / "stegfin-sovereign-trading").resolve()
THIRD_PARTY_ENV_VARS = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment() -> bool:
    return any(truthy(os.environ.get(name)) for name in THIRD_PARTY_ENV_VARS)


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    override = os.environ.get("STEGFIN_ROOT")
    if override:
        roots.append(Path(override).expanduser().resolve())
    roots.extend([
        ROOT / "workloads" / "stegfin-governance",
        Path.home() / ".stegverse" / "workloads" / "stegfin-governance",
        Path("/var/lib/stegverse/workloads/stegfin-governance"),
    ])
    return roots


def find_stegfin_root() -> Path | None:
    for root in candidate_roots():
        if (root / "stegwallet" / "sovereign_market.py").is_file() and (root / "stegwallet" / "sovereign_settlement.py").is_file():
            return root
    return None


def run_activation(root: Path) -> dict:
    runner = root / "scripts" / "run_sovereign_trading_activation_round.py"
    if not runner.is_file():
        return {"attempted": False, "reason": "SOVEREIGN_ROUND_RUNNER_NOT_INSTALLED"}
    process = subprocess.run(
        [sys.executable, str(runner), "--worker-mode"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    return {
        "attempted": True,
        "returncode": process.returncode,
        "reason": "SOVEREIGN_ROUND_EXECUTED" if process.returncode == 0 else "SOVEREIGN_ROUND_INCOMPLETE",
        "stdout_tail": process.stdout[-2000:],
        "stderr_tail": process.stderr[-2000:],
    }


def blocker(reason: str, root: Path | None) -> dict:
    if reason == "THIRD_PARTY_HOST_IS_VALIDATION_ONLY":
        problem = "This invocation is running on a hosted validation surface, which is prohibited from becoming StegFin production worker authority."
        next_action = "Re-run the same admitted claim on the StegVerse heartbeat's native/federated carrier; do not wait for or substitute the hosted runner."
    elif reason == "STEGFIN_CAPSULE_NOT_MATERIALIZED_LOCALLY":
        problem = "The sovereign carrier is present but the StegFin capsule is not yet available at a canonical local workload path."
        next_action = "Materialize the already-built stegfin-governance capsule into the StegVerse workload root and immediately re-execute the same bounded activation task."
    else:
        problem = "The sovereign round runner is not yet complete on the local StegFin capsule."
        next_action = "Install or execute scripts/run_sovereign_trading_activation_round.py and continue until internal settlement, Master Records reconstruction, and E2 proof all pass."
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "workaround_candidates": [
            "Use the canonical StegVerse heartbeat-owned process adapter on the existing sovereign carrier.",
            "Use the released StegVerse-002 sovereign E1/E2 micro-node carrier for the same task without changing financial authority.",
        ],
        "next_solution_action": next_action,
        "machine_observable_release_condition": "worker response reaches STEGFIN_SOVEREIGN_TRADING_ACTIVATED with exact reconstruction evidence bound through E2",
        "third_party_blocker": False,
        "human_action_required": False,
        "stegfin_root": str(root) if root else None,
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 4
    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    for cap in ("bounded_process_execution", "durable_state_reconstruction", "runtime_observation"):
        if cap not in required:
            return 5
    if "receipts/stegfin-sovereign-trading/**" not in set(execution.get("allowed_paths") or []):
        return 6

    hosted = third_party_hosted_environment()
    root = find_stegfin_root()
    blocked = None
    if hosted:
        attempt = {"attempted": False, "reason": "THIRD_PARTY_HOST_IS_VALIDATION_ONLY"}
        state = "BLOCKED"
        transition = "STEGFIN_SOVEREIGN_WORKER_WAITING_FOR_STEGVERSE_CARRIER"
        expected = "STEGFIN_SOVEREIGN_ACTIVATION_EXECUTION"
        blocked = blocker(attempt["reason"], root)
    elif root is None:
        attempt = {"attempted": False, "reason": "STEGFIN_CAPSULE_NOT_MATERIALIZED_LOCALLY"}
        state = "BLOCKED"
        transition = "STEGFIN_CAPSULE_MATERIALIZATION_REQUIRED"
        expected = "STEGFIN_SOVEREIGN_ACTIVATION_EXECUTION"
        blocked = blocker(attempt["reason"], root)
    else:
        attempt = run_activation(root)
        completed = bool(attempt.get("attempted")) and attempt.get("returncode") == 0
        state = "COMPLETED" if completed else "ACTIVE"
        transition = "STEGFIN_SOVEREIGN_TRADING_ACTIVATED" if completed else "STEGFIN_SOVEREIGN_ACTIVATION_EXECUTING"
        expected = None if completed else "STEGFIN_SOVEREIGN_ACTIVATION_EXECUTION"
        if not completed and not attempt.get("attempted"):
            blocked = blocker(str(attempt.get("reason")), root)

    completed = state == "COMPLETED"
    receipt = {
        "schema": "stegverse.stegfin-sovereign-trading-worker-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "state": state,
        "transition_id": transition,
        "stegfin_root": str(root) if root else None,
        "execution_attempt": attempt,
        "blocker": blocked,
        "github_worker_required": False,
        "third_party_worker_required": False,
        "wallet_signing_authority": False,
        "transaction_broadcast_authority": False,
        "custody_authority": False,
        "scale_up_authority": False,
        "completed": completed,
    }
    receipt_path = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": expected,
        "expected_next_earliest_epoch": None if completed else epoch + 1,
        "expected_next_latest_epoch": None if completed else epoch + 1,
        "checkpoint_ref": f"receipts/stegfin-sovereign-trading/{EXPECTED_TASK}.json",
        "evidence_refs": [
            f"receipts/stegfin-sovereign-trading/{EXPECTED_TASK}.json",
            "StegVerse-Labs/.github#66",
            "StegVerse-002/micro-node-runtime#27",
            "StegVerse-Labs/stegfin-governance#51",
            "StegVerse-Labs/stegfin-governance#52",
            "master-records/orchestration#23",
        ],
        "blocker": blocked,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 2 if attempt.get("attempted") else 1,
            "external_cost_usd": 0,
            "task_class": "stegfin_sovereign_trading_activation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
