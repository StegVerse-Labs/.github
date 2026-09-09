#!/usr/bin/env python3
"""Dispatch GADI-RESIDENT-EXECUTION-001 through mandatory preflight gating.

The preflight must return READY_FOR_RESIDENT_CONSUMPTION before the canonical
resident consumer is invoked. A blocked preflight is terminal for this dispatch
attempt and does not claim execution, activation, or authority.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = Path("scripts/preflight_gadi_resident_execution.py")
CONSUMER = Path("control/resident-execution-request.d/consume-gadi-resident-execution.py")
RECEIPT_REL = Path("receipts/sovereign-host/gadi-resident-dispatch.latest.json")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def write_receipt(runtime: Path, payload: dict[str, Any]) -> None:
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def dispatch(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    preflight_path = runtime / PREFLIGHT
    if not preflight_path.is_file():
        preflight_path = source / PREFLIGHT
    consumer_path = runtime / CONSUMER
    if not consumer_path.is_file():
        consumer_path = source / CONSUMER

    if not preflight_path.is_file():
        result = {"schema":"stegverse.gadi-resident-dispatch/v1","state":"BLOCKED_FAIL_CLOSED","blocker":"PREFLIGHT_NOT_MATERIALIZED","execution_claimed":False,"activation_claimed":False}
        write_receipt(runtime, result)
        return result
    if not consumer_path.is_file():
        result = {"schema":"stegverse.gadi-resident-dispatch/v1","state":"BLOCKED_FAIL_CLOSED","blocker":"CONSUMER_NOT_MATERIALIZED","execution_claimed":False,"activation_claimed":False}
        write_receipt(runtime, result)
        return result

    pre = runner([sys.executable, str(preflight_path), "--source-root", str(source), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    pre_result = parse_last_json(pre.stdout)
    if pre.returncode != 0 or not isinstance(pre_result, dict) or pre_result.get("state") != "READY_FOR_RESIDENT_CONSUMPTION" or pre_result.get("ready") is not True or pre_result.get("blocker_count") != 0:
        result = {
            "schema":"stegverse.gadi-resident-dispatch/v1",
            "state":"PREFLIGHT_BLOCKED_FAIL_CLOSED",
            "preflight_returncode":pre.returncode,
            "preflight":pre_result,
            "consumer_attempted":False,
            "execution_claimed":False,
            "activation_claimed":False,
        }
        write_receipt(runtime, result)
        return result

    consumed = runner([sys.executable, str(consumer_path), "--source-root", str(source), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=1200)
    consume_result = parse_last_json(consumed.stdout)
    state = consume_result.get("state") if isinstance(consume_result, dict) else "NO_MACHINE_RESULT"
    result = {
        "schema":"stegverse.gadi-resident-dispatch/v1",
        "state":state,
        "preflight":pre_result,
        "preflight_returncode":pre.returncode,
        "consumer_attempted":True,
        "consumer_returncode":consumed.returncode,
        "consumer":consume_result,
        "execution_claimed":state == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED",
        "activation_claimed":False,
    }
    write_receipt(runtime, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = dispatch(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
