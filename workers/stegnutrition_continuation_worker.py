#!/usr/bin/env python3
"""Heartbeat-owned StegNutrition machine-continuation worker.

The worker never fetches source from GitHub and never accepts GitHub credentials.
It operates only on an already locally materialized StegNutrition tree supplied by
STEGVERSE_STEGNUTRITION_ROOT, executes fixed deterministic checks, and writes only
its admitted receipt namespace in the heartbeat repository.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "stegnutrition-continuation").resolve()
EXPECTED_TASK = "SHWP-STEGNUTRITION-CONTINUATION-001"
EXPECTED_INVENTORY = "tasks/STEGNUTRITION-SESSION-20260811.json"


def fail(message: str, code: int) -> int:
    print(message, file=sys.stderr)
    return code


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def blocker(problem: str, next_action: str, *workarounds: str, dependency_class: str = "INTERNAL") -> dict:
    return {
        "dependency_class": dependency_class,
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": dependency_class != "THIRD_PARTY",
        "workaround_candidates": list(workarounds) or [next_action],
        "next_solution_action": next_action,
    }


def _safe_local_root() -> Path | None:
    raw = os.environ.get("STEGVERSE_STEGNUTRITION_ROOT", "").strip()
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        return None
    if not (root / EXPECTED_INVENTORY).is_file():
        return None
    if not (root / "STEGNUTRITION_MIRROR_HANDOFF.md").is_file():
        return None
    return root


def _inventory_rows(inventory: dict) -> dict[str, dict]:
    rows = inventory.get("execution_inventory") or []
    if not isinstance(rows, list):
        raise ValueError("execution_inventory must be a list")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("task_id"):
            raise ValueError("invalid execution inventory row")
        task_id = str(row["task_id"])
        if task_id in result:
            raise ValueError(f"duplicate task id: {task_id}")
        result[task_id] = row
    return result


def _run_full_suite(stegnutrition_root: Path) -> dict:
    tests = stegnutrition_root / "tests"
    if not tests.is_dir():
        return {"state": "BLOCKED", "reason": "tests directory is absent", "returncode": None}
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str((stegnutrition_root / "src").resolve()),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=stegnutrition_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"state": "RETRY", "reason": "full suite exceeded 180 seconds", "returncode": None}
    tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-6000:]
    return {
        "state": "COMPLETE" if proc.returncode == 0 else "FAILED",
        "reason": "pytest completed" if proc.returncode == 0 else "pytest failed",
        "returncode": proc.returncode,
        "output_tail": tail,
    }


def _filesystem_projection(stegnutrition_root: Path) -> dict:
    semantic_model = (
        (stegnutrition_root / "src/stegnutrition/vision/semantic.py").is_file()
        and (stegnutrition_root / "tests/test_semantic_vision.py").is_file()
        and (stegnutrition_root / "models/semantic-food/manifest.json").is_file()
    )
    automatic_portion = (
        (stegnutrition_root / "src/stegnutrition/vision/auto_portion.py").is_file()
        and (stegnutrition_root / "tests/test_auto_portion.py").is_file()
    )
    benchmark_root = stegnutrition_root / "benchmarks/weighed-photo-cases"
    benchmark_cases = 0
    if benchmark_root.is_dir():
        benchmark_cases = sum(1 for path in benchmark_root.rglob("*.json") if path.is_file())
    return {
        "semantic_vision_surfaces_present": semantic_model,
        "automatic_portion_surfaces_present": automatic_portion,
        "real_weighed_benchmark_case_count": benchmark_cases,
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        return fail(f"invalid invocation: {exc}", 2)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return fail("unsupported invocation schema", 3)

    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or epoch < 0 or task.get("task_id") != EXPECTED_TASK:
        return fail("invocation outside admitted StegNutrition continuation task", 4)

    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    allowed_paths = set(execution.get("allowed_paths") or [])
    if "stegnutrition_machine_continuation" not in required:
        return fail("stegnutrition_machine_continuation capability not admitted", 5)
    if "receipts/stegnutrition-continuation/**" not in allowed_paths:
        return fail("StegNutrition continuation receipt namespace not admitted", 6)

    claim_id = task.get("claim_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return fail("fenced claim required", 7)

    stegnutrition_root = _safe_local_root()
    if stegnutrition_root is None:
        current_blocker = blocker(
            "Canonical StegNutrition is not locally materialized on the resident sovereign carrier.",
            "Materialize StegVerse-Labs/StegNutrition locally and set STEGVERSE_STEGNUTRITION_ROOT for the resident heartbeat process.",
            "Use the existing sovereign node materialization path; do not fetch with a GitHub token from this worker.",
        )
        projection = {"local_root_available": False}
        suite = {"state": "BLOCKED", "reason": "local root unavailable", "returncode": None}
        response_state = "BLOCKED"
        transition = "STEGNUTRITION_LOCAL_MATERIALIZATION_REQUIRED"
        next_transition = "STEGNUTRITION_CONTINUATION_RECHECK"
    else:
        try:
            inventory = load(stegnutrition_root / EXPECTED_INVENTORY)
            rows = _inventory_rows(inventory)
        except Exception as exc:
            return fail(f"canonical StegNutrition inventory invalid: {exc}", 8)

        required_task_ids = {
            "STEGNUTRITION-SEMANTIC-VISION-012",
            "STEGNUTRITION-AUTO-PORTION-013",
            "STEGNUTRITION-REAL-BENCHMARK-DATA-014",
            "STEGNUTRITION-LIVE-VISUAL-ROUTE-015",
            "STEGNUTRITION-FULL-VALIDATION-016",
            "STEGNUTRITION-RELEASE-PROPAGATION-017",
        }
        missing = sorted(required_task_ids - set(rows))
        if missing:
            return fail(f"canonical continuation tasks missing from StegNutrition inventory: {missing}", 9)

        projection = {"local_root_available": True, **_filesystem_projection(stegnutrition_root)}
        suite = _run_full_suite(stegnutrition_root)

        heartbeat_state = load(ROOT / "control/heartbeat-state.json")
        resident_epoch = int(heartbeat_state.get("epoch", -1))
        route_observed = resident_epoch > 29 and bool(
            rows["STEGNUTRITION-LIVE-VISUAL-ROUTE-015"].get("activation_receipt_ref")
        )
        projection["resident_heartbeat_epoch"] = resident_epoch
        projection["live_visual_route_receipt_declared"] = route_observed

        blockers = []
        if not projection["semantic_vision_surfaces_present"]:
            blockers.append(blocker(
                "Calibrated semantic food/composition model surfaces and real training-data manifest are not present.",
                "Acquire/curate real labeled food imagery and install the semantic vision model under STEGNUTRITION-SEMANTIC-VISION-012.",
                "Continue using the released low-level visual-evidence model only as evidence extraction; do not relabel it as semantic food recognition.",
                dependency_class="HUMAN_AUTHORITY",
            ))
        if not projection["automatic_portion_surfaces_present"]:
            blockers.append(blocker(
                "Automatic photo-derived scale/height/shape evidence provider is not installed.",
                "Install STEGNUTRITION-AUTO-PORTION-013 against the existing provenance-bearing portion interval contract.",
                "Retain current explicit geometry intervals for deterministic validation until automatic evidence exists.",
            ))
        if projection["real_weighed_benchmark_case_count"] <= 0:
            blockers.append(blocker(
                "No real photographed/weighed benchmark cases are locally present.",
                "Capture real food photographs with immediate mass measurements and preserve ground-truth records under benchmarks/weighed-photo-cases/.",
                "Synthetic fixtures may continue validating metric machinery but do not count as real accuracy evidence.",
                dependency_class="HUMAN_AUTHORITY",
            ))
        if not route_observed:
            blockers.append(blocker(
                f"Resident governed visual route has not been observed after HB29 (current canonical epoch {resident_epoch}).",
                "Allow the existing resident heartbeat/TVC chain to emit and persist the exact no-credential visual route receipt, then recheck.",
                "Do not create a second heartbeat or use GitHub credentials for model discovery, launch, or route admission.",
            ))
        if suite["state"] != "COMPLETE":
            blockers.append(blocker(
                f"Deterministic StegNutrition full-suite state is {suite['state']}: {suite['reason']}.",
                "Resolve the locally observed test/runtime dependency and rerun the fixed no-network pytest command on the next admitted heartbeat.",
                "Keep hosted CI status separate; this worker uses only the locally materialized repository.",
            ))

        release_ready = (
            not blockers
            and projection["semantic_vision_surfaces_present"]
            and projection["automatic_portion_surfaces_present"]
            and projection["real_weighed_benchmark_case_count"] > 0
            and route_observed
            and suite["state"] == "COMPLETE"
        )
        current_blocker = blockers[0] if blockers else None
        if release_ready:
            response_state = "COMPLETED"
            transition = "STEGNUTRITION_RELEASE_CANDIDATE_READY"
            next_transition = None
        else:
            response_state = "BLOCKED"
            transition = "STEGNUTRITION_CONTINUATION_BLOCKED"
            next_transition = "STEGNUTRITION_CONTINUATION_RECHECK"

    receipt_path = (RECEIPT_ROOT / f"{EXPECTED_TASK}.json").resolve()
    if RECEIPT_ROOT not in receipt_path.parents:
        return fail("receipt path escaped admitted namespace", 10)
    prior = load(receipt_path) if receipt_path.exists() else None
    if prior and (prior.get("claim_id") != claim_id or prior.get("fencing_token") != fence):
        return fail("existing continuation receipt belongs to a different claim/fence", 11)
    sequence = 1 if prior is None else int(prior.get("transition_sequence", 0)) + 1

    receipt = {
        "schema": "stegverse.stegnutrition-continuation-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "transition_sequence": sequence,
        "stegnutrition_inventory_ref": EXPECTED_INVENTORY,
        "projection": projection,
        "local_validation": suite,
        "blocker": current_blocker,
        "github_token_required": False,
        "github_repository_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "none_beyond_admitted_continuation_receipt_namespace",
        "completed": response_state == "COMPLETED",
    }
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": response_state,
        "transition_id": transition,
        "transition_sequence": sequence,
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None if response_state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if response_state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": f"receipts/stegnutrition-continuation/{EXPECTED_TASK}.json",
        "evidence_refs": [
            "control/heartbeat-state.json",
            "handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json",
            f"receipts/stegnutrition-continuation/{EXPECTED_TASK}.json",
            "StegVerse-Labs/StegNutrition:STEGNUTRITION_MIRROR_HANDOFF.md",
            f"StegVerse-Labs/StegNutrition:{EXPECTED_INVENTORY}",
        ],
        "blocker": current_blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "stegnutrition_machine_continuation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
