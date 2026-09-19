#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST3_TASK = "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"
TEST3_COSV = "20010000110000"

DOTGITHUB_TESTS = [
    "tests/test_sdk_tt_purpose_bound_worker_runtime_path.py",
    "tests/test_sdk_tt_richard_atomic_activation_seam.py",
    "tests/test_sdk_tt_richard_seam_resident_carriage.py",
    "tests/test_sdk_tt_richard_seam_resident_materialization.py",
    "tests/test_sdk_tt_richard_seam_control_plane_package.py",
    "tests/test_worker_assignment_functional_memory.py",
]
STEGAGENTS_TEST = "tests/test_purpose_bound_worker_runtime.py"


def run(cmd: list[str], cwd: Path) -> dict:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return {
        "argv": cmd,
        "cwd": str(cwd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the executable Test 3 Richard-seam acceptance suite.")
    parser.add_argument("--stegagents-root", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    stegagents = args.stegagents_root.resolve() if args.stegagents_root else None
    handoff = json.loads((ROOT / "handoffs/SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001.json").read_text())
    owner = json.loads((ROOT / "data/canonical-task-records/SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001.json").read_text())
    fragment = json.loads((ROOT / "control/worker-registry.d/sdk-tt-richard-seam-authentic-runtime-001.json").read_text())

    require(handoff["task"]["task_id"] == TEST3_TASK, "Test 3 handoff task mismatch")
    require(owner["task_id"] == TEST3_TASK, "Test 3 owner task mismatch")
    require(owner["cosv_task_vector"] == TEST3_COSV, "Test 3 COSV mismatch")
    require(handoff["activation"]["atomic_task_worker_binding_required"] is True, "atomic binding requirement missing")
    task = fragment["tasks"][0]
    require(task["task_id"] == TEST3_TASK, "worker-registry Test 3 task mismatch")
    require(task["state"] == "HANDOFF_READY", "Test 3 prestate must be HANDOFF_READY")
    require(task["claim_id"] is None and task["worker_id"] is None and task["worker_instance_id"] is None,
            "Test 3 prestate exposes authoritative worker state")
    require(fragment["workers"] == [], "Test 3 must not register a duplicate worker")

    dotgithub = run([sys.executable, "-m", "pytest", "-q", *DOTGITHUB_TESTS], ROOT)
    validation = json.loads((ROOT / "control/test3-stegagents-validation.json").read_text())
    require(validation["task_id"] == TEST3_TASK, "StegAgents validation task mismatch")
    require(validation["atomic_cosv"] == TEST3_COSV, "StegAgents validation COSV mismatch")
    require(validation["result"].startswith("PASS_"), "StegAgents current validation is not PASS")
    require(validation["purpose_bound_test"] == STEGAGENTS_TEST, "StegAgents Test 3 module mismatch")
    if stegagents is not None:
        steagents_result = run([sys.executable, "-m", "pytest", "-q", STEGAGENTS_TEST], stegagents)
        steagents_pass = steagents_result["returncode"] == 0
        steagents_mode = "LIVE_CHECKOUT"
    else:
        steagents_result = {"returncode": 0, "stdout": validation["result"], "stderr": ""}
        steagents_pass = True
        steagents_mode = "PINNED_CURRENT_MAIN_VALIDATION"

    passed = dotgithub["returncode"] == 0 and steagents_pass
    result = {
        "schema": "stegverse.sdk-tt-richard-seam-test3-acceptance/v1",
        "task_id": TEST3_TASK,
        "cosv_task_vector": TEST3_COSV,
        "state": "PASS" if passed else "FAIL",
        "constitutive_transition": "ACTIVATE_TASK_AND_CREATE_BIND_WORKER",
        "required_order": [
            "HANDOFF_READY_T_NO_AUTHORITATIVE_W",
            "PENDING_FRESH_CLAIM_FENCE",
            "TV_TVC_VERIFIED",
            "INTR_ACTIVATE_T_CREATE_AND_BIND_W_T",
            "MASTER_RECORDS_CLOSED",
            "ACTIVE_T_BOUND_W",
            "INVOCATION_STARTED",
            "TASK_COMPLETED_SAME_LINEAGE",
        ],
        "dotgithub": {
            "tests": DOTGITHUB_TESTS,
            "returncode": dotgithub["returncode"],
            "stdout": dotgithub["stdout"],
            "stderr": dotgithub["stderr"],
        },
        "stegagents": {
            "mode": steagents_mode,
            "test": STEGAGENTS_TEST,
            "current_main_source_sha": validation["current_main_source_sha"],
            "ci_run": validation["ci_run"],
            "returncode": steagents_result["returncode"],
            "stdout": steagents_result["stdout"],
            "stderr": steagents_result["stderr"],
        },
        "execution_authority": "NONE_ACCEPTANCE_VALIDATION_ONLY",
    }
    encoded = json.dumps(result, indent=2, sort_keys=True)
    print(encoded)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(encoded + "\n", encoding="utf-8")
    if passed:
        print("TEST3_RICHARD_SEAM_ACCEPTANCE_PASS")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
