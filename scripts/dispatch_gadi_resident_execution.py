#!/usr/bin/env python3
"""Dispatch GADI-RESIDENT-EXECUTION-001 through materialization and mandatory preflight gating.

Already-observed local runtime evidence is first projected into the canonical GADI bundle.
The preflight must then return READY_FOR_RESIDENT_CONSUMPTION before the resident consumer
is invoked. Any missing/mismatched source evidence fails closed without execution claims.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = Path("scripts/materialize_gadi_resident_runtime_bundle.py")
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


def resolve(runtime: Path, source: Path, rel: Path) -> Path | None:
    local = runtime / rel
    if local.is_file():
        return local
    source_path = source / rel
    return source_path if source_path.is_file() else None


def dispatch(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    materializer_path = resolve(runtime, source, MATERIALIZER)
    preflight_path = resolve(runtime, source, PREFLIGHT)
    consumer_path = resolve(runtime, source, CONSUMER)

    for label, path in (("MATERIALIZER", materializer_path), ("PREFLIGHT", preflight_path), ("CONSUMER", consumer_path)):
        if path is None:
            result = {"schema":"stegverse.gadi-resident-dispatch/v1","state":"BLOCKED_FAIL_CLOSED","blocker":f"{label}_NOT_MATERIALIZED","consumer_attempted":False,"execution_claimed":False,"activation_claimed":False}
            write_receipt(runtime, result)
            return result

    materialized = runner([sys.executable, str(materializer_path), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    materialized_result = parse_last_json(materialized.stdout)
    if materialized.returncode != 0 or not isinstance(materialized_result, dict) or materialized_result.get("state") != "MATERIALIZED_READY_FOR_PREFLIGHT" or materialized_result.get("ready") is not True or materialized_result.get("blockers") not in ([], None):
        result = {
            "schema":"stegverse.gadi-resident-dispatch/v1",
            "state":"MATERIALIZATION_BLOCKED_FAIL_CLOSED",
            "materializer_returncode":materialized.returncode,
            "materialization":materialized_result,
            "preflight_attempted":False,
            "consumer_attempted":False,
            "execution_claimed":False,
            "activation_claimed":False,
        }
        write_receipt(runtime, result)
        return result

    pre = runner([sys.executable, str(preflight_path), "--source-root", str(source), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    pre_result = parse_last_json(pre.stdout)
    if pre.returncode != 0 or not isinstance(pre_result, dict) or pre_result.get("state") != "READY_FOR_RESIDENT_CONSUMPTION" or pre_result.get("ready") is not True or pre_result.get("blocker_count") != 0:
        result = {
            "schema":"stegverse.gadi-resident-dispatch/v1",
            "state":"PREFLIGHT_BLOCKED_FAIL_CLOSED",
            "materialization":materialized_result,
            "preflight_returncode":pre.returncode,
            "preflight":pre_result,
            "preflight_attempted":True,
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
        "materialization":materialized_result,
        "preflight":pre_result,
        "preflight_returncode":pre.returncode,
        "preflight_attempted":True,
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
