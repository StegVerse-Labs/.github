#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "TVC-ODA3-AGGREGATE-RELEASE-027"
CAPABILITY = "tvc_aggregate_release"
RELEASE_SET_ID = "ODA3-EVALUATOR-PATH-2026-08-18-R1"
READINESS_ENTRYPOINT = "tvc.release.aggregate.oda3_r1.readiness"
EXECUTE_ENTRYPOINT = "tvc.release.aggregate.oda3_r1.execute"
VERIFY_ENTRYPOINT = "tvc.release.aggregate.oda3_r1.verify"
CHECKPOINT_REF = "StegVerse-Labs/TVC:receipts/aggregate_release/ODA3-EVALUATOR-PATH-2026-08-18-R1.json"
HOSTED_MARKERS = ("GITHUB_ACTIONS", "RENDER", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "MOONSHOT_API_KEY",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def find_tvc_root() -> Path | None:
    candidates: list[Path] = []
    override = os.environ.get("STEGVERSE_TVC_ROOT")
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        [
            Path.home() / ".stegverse" / "repos" / "StegVerse-Labs" / "TVC",
            Path.home() / "StegVerse" / "TVC",
            Path.home() / "stegverse" / "TVC",
            Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
            Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
            Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
            Path("/opt/stegverse/TVC"),
            Path("/srv/stegverse/TVC"),
        ]
    )
    for candidate in candidates:
        try:
            root = candidate.resolve()
        except Exception:
            continue
        required = (
            root / "tools" / "task_dispatcher.py",
            root / "tasks" / "aggregate_release.py",
            root / "config" / "task_catalog.d" / "aggregate_release_instances.json",
            root / "config" / "oda3_aggregate_release_r1.json",
        )
        if all(path.is_file() for path in required):
            return root
    return None


def run_dispatch(tvc_root: Path, task_name: str) -> tuple[int, dict[str, Any] | None, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(tvc_root),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    tvc_token = os.environ.get("TVC_EPHEMERAL_GITHUB_TOKEN")
    if tvc_token:
        env["TVC_EPHEMERAL_GITHUB_TOKEN"] = tvc_token
    process = subprocess.run(
        [sys.executable, "tools/task_dispatcher.py", task_name],
        cwd=tvc_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    parsed = None
    try:
        parsed = json.loads(process.stdout)
    except Exception:
        pass
    return process.returncode, parsed, process.stderr[-2000:]


def nested_readiness_decision(report: dict[str, Any] | None) -> str | None:
    if not isinstance(report, dict):
        return None
    result = report.get("result")
    if not isinstance(result, dict):
        return None
    readiness = result.get("readiness")
    if not isinstance(readiness, dict):
        return None
    value = readiness.get("decision")
    return str(value) if value is not None else None


def verified_release(report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict) or report.get("status") != "ok":
        return False
    result = report.get("result")
    return isinstance(result, dict) and result.get("valid") is True


def blocker(reason: str, release_condition: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": reason,
        "solution_required": True,
        "may_remain_blocked": True,
        "next_solution_action": "RECHECK_TVC_RELEASE_CAPABILITY_THEN_EXECUTE_GENERALIZED_AGGREGATE_RELEASE",
        "machine_observable_release_condition": release_condition,
    }


def response(
    *,
    state: str,
    epoch: int,
    reason: str,
    blocker_value: dict[str, Any] | None,
    stderr_tail: str | None = None,
) -> dict[str, Any]:
    completed = state == "COMPLETED"
    evidence = [
        "handoffs/TVC-ODA3-AGGREGATE-RELEASE-027.json",
        "StegVerse-Labs/TVC:docs/AGGREGATE_RELEASE_MIRROR_HANDOFF.md",
    ]
    if completed:
        evidence.append(CHECKPOINT_REF)
    result: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": f"TVC_AGGREGATE_RELEASE_{state}",
        "transition_sequence": 1,
        "expected_next_transition": None if completed else "TVC_AGGREGATE_RELEASE_RECHECK",
        "expected_next_earliest_epoch": None if completed else epoch + 1,
        "expected_next_latest_epoch": None if completed else epoch + 1,
        "checkpoint_ref": CHECKPOINT_REF if completed else None,
        "evidence_refs": evidence,
        "blocker": blocker_value,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "tvc_aggregate_release",
        },
        "result": {
            "release_set_id": RELEASE_SET_ID,
            "reason": reason,
            "credential_authority": "TV/TVC",
            "non_tv_tvc_credential_used": False,
            "credential_value_exposed": False,
            "github_actions_release_authority": False,
        },
    }
    if stderr_tail:
        result["result"]["stderr_tail"] = stderr_tail
    return result


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3

    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    scope = invocation.get("scope") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID:
        return 4

    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 5

    execution = handoff.get("execution") or {}
    required_capabilities = set(execution.get("required_capabilities") or [])
    allowed_paths = set(execution.get("allowed_paths") or [])
    if CAPABILITY not in required_capabilities:
        return 6
    if "receipts/tvc-aggregate-release/**" not in allowed_paths:
        return 7
    if CAPABILITY not in set(scope.get("required_capabilities") or []):
        return 8

    if any(truthy(os.environ.get(name)) for name in HOSTED_MARKERS):
        value = response(
            state="FAILED",
            epoch=epoch,
            reason="HOSTED_RUNTIME_NOT_AUTHORIZED",
            blocker_value=blocker(
                "HOSTED_RUNTIME_NOT_AUTHORIZED",
                "WorkerCoordinator invokes this worker on the authorized StegVerse sovereign runtime",
            ),
        )
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    forbidden_present = [name for name in FORBIDDEN_ENV if os.environ.get(name)]
    if forbidden_present:
        value = response(
            state="FAILED",
            epoch=epoch,
            reason="NON_TVC_SECRET_OR_TOKEN_PRESENT",
            blocker_value=blocker(
                "NON_TVC_SECRET_OR_TOKEN_PRESENT",
                "No GITHUB_TOKEN, GH_TOKEN, or provider API credential is present in the worker environment",
            ),
        )
        value["result"]["forbidden_fields"] = forbidden_present
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    tvc_root = find_tvc_root()
    if tvc_root is None:
        value = response(
            state="BLOCKED",
            epoch=epoch,
            reason="TVC_ROOT_NOT_MATERIALIZED",
            blocker_value=blocker(
                "TVC_ROOT_NOT_MATERIALIZED",
                "The TVC repository is materialized on the authorized StegVerse host with the generalized aggregate-release dispatcher and instance catalog present",
            ),
        )
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    readiness_rc, readiness, readiness_err = run_dispatch(tvc_root, READINESS_ENTRYPOINT)
    decision = nested_readiness_decision(readiness)
    if readiness_rc != 0 or decision not in {"READY", "BLOCKED_DEPENDENCY"}:
        value = response(
            state="FAILED",
            epoch=epoch,
            reason="READINESS_EVALUATION_FAILED",
            blocker_value=blocker(
                "READINESS_EVALUATION_FAILED",
                "The generalized TVC readiness entrypoint returns READY or BLOCKED_DEPENDENCY for the exact release-set policy",
            ),
            stderr_tail=readiness_err,
        )
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if decision != "READY":
        value = response(
            state="BLOCKED",
            epoch=epoch,
            reason="TVC_RELEASE_CAPABILITY_NOT_READY",
            blocker_value=blocker(
                "TVC_RELEASE_CAPABILITY_NOT_READY",
                "TVC_EPHEMERAL_GITHUB_TOKEN is present only inside the authorized TVC-owned release environment and generalized readiness returns READY",
            ),
        )
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    execute_rc, _, execute_err = run_dispatch(tvc_root, EXECUTE_ENTRYPOINT)
    if execute_rc != 0:
        value = response(
            state="FAILED",
            epoch=epoch,
            reason="RELEASE_EXECUTION_FAILED",
            blocker_value=blocker(
                "RELEASE_EXECUTION_FAILED",
                "The generalized TVC aggregate release executor completes all exact immutable tag/release mutations without conflict",
            ),
            stderr_tail=execute_err,
        )
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    verify_rc, verify, verify_err = run_dispatch(tvc_root, VERIFY_ENTRYPOINT)
    if verify_rc != 0 or not verified_release(verify):
        value = response(
            state="FAILED",
            epoch=epoch,
            reason="AGGREGATE_RELEASE_VERIFICATION_FAILED",
            blocker_value=blocker(
                "AGGREGATE_RELEASE_VERIFICATION_FAILED",
                "The retained stegverse.tvc.aggregate-release-receipt.v1 verifies every exact tag-to-commit and release object in the frozen release-set policy",
            ),
            stderr_tail=verify_err,
        )
        json.dump(value, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    value = response(
        state="COMPLETED",
        epoch=epoch,
        reason="AGGREGATE_RELEASE_VERIFIED",
        blocker_value=None,
    )
    json.dump(value, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
