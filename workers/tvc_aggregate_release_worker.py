#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

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
            Path.home() / "StegVerse" / "TVC",
            Path.home() / "stegverse" / "TVC",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Invoke a task-bound TVC aggregate-release instance through the generalized TVC dispatcher.")
    parser.add_argument("--release-set-id", required=True)
    parser.add_argument("--readiness", required=True)
    parser.add_argument("--execute", required=True)
    parser.add_argument("--verify", required=True)
    args = parser.parse_args(argv)

    if any(truthy(os.environ.get(name)) for name in HOSTED_MARKERS):
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "HOSTED_RUNTIME_NOT_AUTHORIZED"}))
        return 2
    forbidden_present = [name for name in FORBIDDEN_ENV if os.environ.get(name)]
    if forbidden_present:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "NON_TVC_SECRET_OR_TOKEN_PRESENT", "fields": forbidden_present}))
        return 2

    tvc_root = find_tvc_root()
    if tvc_root is None:
        print(json.dumps({"status": "BLOCKED", "reason": "TVC_ROOT_NOT_MATERIALIZED", "release_set_id": args.release_set_id}))
        return 0

    readiness_rc, readiness, readiness_err = run_dispatch(tvc_root, args.readiness)
    decision = nested_readiness_decision(readiness)
    if readiness_rc != 0 or decision not in {"READY", "BLOCKED_DEPENDENCY"}:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "READINESS_EVALUATION_FAILED", "release_set_id": args.release_set_id, "stderr_tail": readiness_err}))
        return 2
    if decision != "READY":
        print(json.dumps({"status": "BLOCKED", "reason": "TVC_RELEASE_CAPABILITY_NOT_READY", "release_set_id": args.release_set_id, "credential_value_exposed": False}))
        return 0

    execute_rc, execute, execute_err = run_dispatch(tvc_root, args.execute)
    if execute_rc != 0:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "RELEASE_EXECUTION_FAILED", "release_set_id": args.release_set_id, "stderr_tail": execute_err}))
        return 2

    verify_rc, verify, verify_err = run_dispatch(tvc_root, args.verify)
    if verify_rc != 0:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "RELEASE_VERIFICATION_FAILED", "release_set_id": args.release_set_id, "stderr_tail": verify_err}))
        return 2

    verified = False
    if isinstance(verify, dict):
        result = verify.get("result")
        verified = isinstance(result, dict) and result.get("valid") is True
    if not verified:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": "AGGREGATE_RECEIPT_NOT_VERIFIED", "release_set_id": args.release_set_id}))
        return 2

    print(json.dumps({"status": "COMPLETE", "release_set_id": args.release_set_id, "credential_authority": "TV/TVC", "non_tv_tvc_credential_used": False, "credential_value_exposed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
