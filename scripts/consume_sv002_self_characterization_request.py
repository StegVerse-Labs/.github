#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REQUEST_REL = Path("control/resident-execution-request.d/sv002-self-characterization-001.json")
RECEIPT_REL = Path("receipts/sovereign-host/sv002-self-characterization-request-consumption.latest.json")
TASK_ID = "SHWP-SV002-SELF-CHARACTERIZATION-001"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def stable(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def terminal_execution_observed(value: Any) -> bool:
    if isinstance(value, list):
        return any(terminal_execution_observed(item) for item in value)
    if not isinstance(value, dict):
        return False
    if (
        value.get("state") == "COMPLETED"
        and value.get("transition_id") == "SV002_SELF_CHARACTERIZATION_COMPLETED"
    ):
        return True
    principal = value.get("principal_result")
    if isinstance(principal, dict):
        if (
            principal.get("state") == "COMPLETED"
            and principal.get("principal_run_completed") is True
        ):
            return True
    return any(
        terminal_execution_observed(item)
        for item in value.values()
        if isinstance(item, (dict, list))
    )


def prior_terminally_consumed(
    prior_receipt: dict[str, Any],
    request_hash: str,
) -> bool:
    return bool(
        prior_receipt.get("request_sha256") == request_hash
        and prior_receipt.get("terminal_execution_observed") is True
    )


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "terminal_execution_observed": False,
            "authority_effect": "NONE",
        }

    request = load(request_path)
    if (
        request.get("schema") != "stegverse.resident-execution-request/v1"
        or request.get("task_id") != TASK_ID
        or request.get("state") != "REQUESTED"
    ):
        raise RuntimeError("SV002 self-characterization resident request contract mismatch")

    request_hash = stable(request)
    receipt_path = runtime / RECEIPT_REL
    if receipt_path.is_file():
        try:
            prior = load(receipt_path)
        except Exception:
            prior = {}
        if prior_terminally_consumed(prior, request_hash):
            return {
                "schema": "stegverse.resident-execution-request-consumption/v1",
                "state": "ALREADY_CONSUMED",
                "request_id": request.get("request_id"),
                "request_sha256": request_hash,
                "task_id": TASK_ID,
                "runtime_execution_attempted": False,
                "terminal_execution_observed": True,
                "request_granted_authority": False,
                "network_source_fetch_performed": False,
                "second_machine_required": False,
                "authority_effect": "NONE_REQUEST_ONLY",
            }

    command = [
        sys.executable,
        str(runtime / "scripts/refresh_and_execute_resident_task.py"),
        "--source-root",
        str(source),
        "--runtime-root",
        str(runtime),
        "--task-id",
        TASK_ID,
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        timeout=2000,
    )
    result = parse_last_json(completed.stdout)
    terminal = terminal_execution_observed(result)
    receipt = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "COMPLETED" if terminal else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "runtime_execution_attempted": True,
        "execution_returncode": completed.returncode,
        "execution_result": result,
        "terminal_execution_observed": terminal,
        "retry_allowed": not terminal,
        "exactly_once_after_terminal": True,
        "request_granted_authority": False,
        "network_source_fetch_performed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema": "stegverse.resident-execution-request-consumption/v1",
                    "state": "BLOCKED",
                    "reason": str(exc),
                    "runtime_execution_attempted": False,
                    "terminal_execution_observed": False,
                    "authority_effect": "NONE",
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
