from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

WORKER_ID = "legacy-continuity-validation-worker"
TASK_ID = "LEGACY-CONTINUITY-VALIDATION-WORKER-001"
EXPECTED_HEAD = "0b814c0d0028e98a67c751ef2aa1768b17da743f"
FOCUSED_TESTS = (
    "tests/test_legacy_trigger.py",
    "tests/test_legacy_participation.py",
    "tests/test_legacy_release_coordination.py",
)
CREDENTIAL_MARKERS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PRIVATE_KEY",
    "API_KEY",
    "ACCESS_KEY",
    "GITHUB_",
    "GH_",
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sanitized_env() -> dict[str, str]:
    safe: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if any(marker in upper for marker in CREDENTIAL_MARKERS):
            continue
        safe[key] = value
    safe["PYTHONDONTWRITEBYTECODE"] = "1"
    return safe


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_sanitized_env(),
    )


def validate(repo: Path, python_executable: str = sys.executable) -> dict[str, Any]:
    repo = repo.resolve()
    receipt: dict[str, Any] = {
        "schema": "stegverse.worker-validation-receipt.v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "repo_path": str(repo),
        "expected_head": EXPECTED_HEAD,
        "network_fetch_used": False,
        "github_token_runtime_authority": False,
        "credential_authority": "TV/TVC",
        "death_determination_performed": False,
        "recipient_notification_performed": False,
        "capsule_arming_performed": False,
        "economic_transfer_performed": False,
    }

    if not repo.is_dir():
        receipt.update(state="FAIL_CLOSED", reason="LOCAL_REPO_PATH_REQUIRED")
        return receipt

    for relative in FOCUSED_TESTS:
        if not (repo / relative).is_file():
            receipt.update(state="FAIL_CLOSED", reason=f"MISSING_FOCUSED_TEST:{relative}")
            return receipt

    head = _git(repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        receipt.update(state="FAIL_CLOSED", reason="GIT_HEAD_UNAVAILABLE")
        return receipt
    actual_head = head.stdout.strip()
    receipt["actual_head"] = actual_head
    if actual_head != EXPECTED_HEAD:
        receipt.update(state="FAIL_CLOSED", reason="SOURCE_BINDING_MISMATCH")
        return receipt

    status = _git(repo, "status", "--porcelain")
    if status.returncode != 0:
        receipt.update(state="FAIL_CLOSED", reason="WORKTREE_STATUS_UNAVAILABLE")
        return receipt
    if status.stdout.strip():
        receipt.update(state="FAIL_CLOSED", reason="WORKTREE_NOT_CLEAN")
        return receipt

    command = [python_executable, "-m", "pytest", *FOCUSED_TESTS, "-q"]
    result = subprocess.run(
        command,
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_sanitized_env(),
    )
    receipt.update(
        command=command,
        returncode=result.returncode,
        stdout_sha256=_sha256_text(result.stdout),
        stderr_sha256=_sha256_text(result.stderr),
        stdout_tail=result.stdout[-4000:],
        stderr_tail=result.stderr[-4000:],
    )
    if result.returncode == 0:
        receipt.update(state="PASS", reason="EXACT_BOUND_LEGACY_TESTS_PASS")
    else:
        receipt.update(state="FAIL_CLOSED", reason="FOCUSED_TESTS_FAILED")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate exact-bound private Continuity legacy source locally.")
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=os.environ.get("STEGVERSE_CONTINUITY_REPO_PATH"),
        help="Existing authorized local Continuity checkout. No network fetch is performed.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.repo_path is None:
        receipt = {
            "schema": "stegverse.worker-validation-receipt.v1",
            "task_id": TASK_ID,
            "worker_id": WORKER_ID,
            "state": "FAIL_CLOSED",
            "reason": "LOCAL_REPO_PATH_REQUIRED",
            "network_fetch_used": False,
            "github_token_runtime_authority": False,
            "credential_authority": "TV/TVC",
        }
    else:
        receipt = validate(args.repo_path)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if receipt.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
