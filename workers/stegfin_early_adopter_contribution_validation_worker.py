from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

WORKER_ID = "stegfin-early-adopter-contribution-validation-worker"
TASK_ID = "STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-001"
EXPECTED_LEDGER_BLOB = "6557301476c3b7dd42a73d97409c74fc5a604494"
EXPECTED_TEST_BLOB = "380fbb392817f52dad669478b9931865dc850d1b"
LEDGER_PATH = Path("stegwallet/contribution_ledger.py")
TEST_PATH = Path("tests/test_contribution_ledger.py")
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


def _git_blob_sha(repo: Path, path: Path) -> str:
    result = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_sanitized_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"git_hash_object_failed:{path}:{result.stderr.strip()}")
    return result.stdout.strip()


def _sanitized_env() -> dict[str, str]:
    safe: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if any(marker in upper for marker in CREDENTIAL_MARKERS):
            continue
        safe[key] = value
    safe["PYTHONDONTWRITEBYTECODE"] = "1"
    return safe


def validate(repo: Path, python_executable: str = sys.executable) -> dict[str, Any]:
    repo = repo.resolve()
    checks: dict[str, bool] = {
        "repo_exists": repo.is_dir(),
        "ledger_exists": (repo / LEDGER_PATH).is_file(),
        "test_exists": (repo / TEST_PATH).is_file(),
    }
    receipt: dict[str, Any] = {
        "schema": "stegverse.worker-validation-receipt.v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "repo_path": str(repo),
        "network_fetch_used": False,
        "github_token_runtime_authority": False,
        "credential_authority": "TV/TVC",
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
        "checks": checks,
    }

    if not all(checks.values()):
        receipt["state"] = "FAIL_CLOSED"
        receipt["reason"] = "LOCAL_SOURCE_INCOMPLETE"
        return receipt

    try:
        ledger_blob = _git_blob_sha(repo, LEDGER_PATH)
        test_blob = _git_blob_sha(repo, TEST_PATH)
    except RuntimeError as exc:
        receipt["state"] = "FAIL_CLOSED"
        receipt["reason"] = str(exc)
        return receipt

    checks.update(
        {
            "ledger_blob_exact": ledger_blob == EXPECTED_LEDGER_BLOB,
            "test_blob_exact": test_blob == EXPECTED_TEST_BLOB,
        }
    )
    receipt.update(
        {
            "ledger_blob": ledger_blob,
            "expected_ledger_blob": EXPECTED_LEDGER_BLOB,
            "test_blob": test_blob,
            "expected_test_blob": EXPECTED_TEST_BLOB,
        }
    )

    if not checks["ledger_blob_exact"] or not checks["test_blob_exact"]:
        receipt["state"] = "FAIL_CLOSED"
        receipt["reason"] = "SOURCE_BINDING_MISMATCH"
        return receipt

    command = [python_executable, "-m", "pytest", str(TEST_PATH), "-q"]
    result = subprocess.run(
        command,
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_sanitized_env(),
    )
    checks["focused_tests_pass"] = result.returncode == 0
    receipt.update(
        {
            "command": command,
            "returncode": result.returncode,
            "stdout_sha256": _sha256_text(result.stdout),
            "stderr_sha256": _sha256_text(result.stderr),
            "stdout_tail": result.stdout[-4000:],
            "stderr_tail": result.stderr[-4000:],
            "external_provider_contacted": False,
            "trade_execution_attempted": False,
            "wallet_signing_attempted": False,
            "broadcast_attempted": False,
        }
    )
    if result.returncode == 0:
        receipt["state"] = "PASS"
        receipt["reason"] = "EXACT_BOUND_FOCUSED_TESTS_PASS"
    else:
        receipt["state"] = "FAIL_CLOSED"
        receipt["reason"] = "FOCUSED_TESTS_FAILED"
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the exact-bound StegFin early-adopter contribution ledger on a local sovereign source checkout."
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=os.environ.get("STEGFIN_GOVERNANCE_REPO_PATH"),
        help="Existing local stegfin-governance checkout. No network fetch is performed.",
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
