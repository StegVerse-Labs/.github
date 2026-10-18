#!/usr/bin/env python3
"""Resident dispatcher consumer for RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013.

The readback runs because a committed manifest asks for it: each
``control/resident-execution-request.d/repository-ledger-genesis-readback-*.json``
in the resident runtime (carried there by the existing source refresh) is one
request. This consumer is visited by the existing resident request dispatcher.
It owns no schedule, loop, clock or retry.

The component is loaded from the dispatcher's ``--source-root``. Each answer is
retained once, keyed by (request digest, fetched organization-ledger head),
under ``receipts/sovereign-host/repository-ledger-genesis-readback/`` of the
runtime. Nothing is written to any ledger or ref. An organization or
repository in a request never selects the fetch source; the component derives
it from the organization.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("control/resident-execution-request.d")
REQUEST_GLOB = "repository-ledger-genesis-readback-*.json"
OUTPUT_REL = Path("receipts/sovereign-host/repository-ledger-genesis-readback")
COMPONENT_REL = Path("resident-runtime/repository_ledger_genesis_readback.py")
RESULT_SCHEMA = "stegverse.repository-ledger-genesis-readback-dispatch-result/v1"


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_component(source: Path):
    path = source / COMPONENT_REL
    if not path.is_file():
        raise FileNotFoundError(str(COMPONENT_REL))
    spec = importlib.util.spec_from_file_location("rtc013_repository_ledger_genesis_readback", path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(str(COMPONENT_REL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _retain(runtime: Path, result: dict[str, Any]) -> tuple[str, str]:
    """Write the answer once; an identical answer already retained is ALREADY_RECORDED."""
    key = result["request_sha256"][len("sha256:"):] + "-" + result["observed_organization_ledger_head"]
    path = runtime / OUTPUT_REL / (key + ".json")
    body = json.dumps(result, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(body)
        return "RECORDED_LOCAL_READBACK", str(OUTPUT_REL / path.name)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != body:
            raise ValueError("RETAINED_READBACK_DIFFERS_FOR_SAME_REQUEST_AND_HEAD: " + path.name)
        return "ALREADY_RECORDED", str(OUTPUT_REL / path.name)


def consume(source_root: Path, runtime_root: Path, *, _ledger_source: str | None = None) -> dict[str, Any]:
    source, runtime = Path(source_root).resolve(), Path(runtime_root).resolve()
    requests = sorted((runtime / REQUEST_DIR_REL).glob(REQUEST_GLOB))
    if not requests:
        return {"schema": RESULT_SCHEMA, "state": "NO_REQUEST", "authority_effect": "NONE_READBACK_ONLY"}
    try:
        component = load_component(source)
    except FileNotFoundError as exc:
        return {"schema": RESULT_SCHEMA, "state": "BOUNDARY", "reason": "COMPONENT_NOT_MATERIALIZED: " + str(exc),
                "authority_effect": "NONE_READBACK_ONLY"}
    rows, states = [], []
    for path in requests:
        try:
            request = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            request = {"_unreadable": type(exc).__name__}
        result = component.evaluate(request, ledger_source=_ledger_source)
        row = {"request_ref": str(REQUEST_DIR_REL / path.name), "disposition": result["disposition"],
               "failure_code": result.get("failure_code"), "decision_sha256": result["decision_sha256"],
               "observed_organization_ledger_head": result.get("observed_organization_ledger_head")}
        if result.get("observed_organization_ledger_head") and result.get("request_sha256"):
            state, retained = _retain(runtime, result)
            row["retained_ref"] = retained
        else:
            # A malformed request or an unfetched ref has no stable key; it is reported, not retained.
            state = "BOUNDARY"
        row["state"] = state
        rows.append(row)
        states.append(state)
    if "BOUNDARY" in states:
        overall = "BOUNDARY"
    elif all(state == "ALREADY_RECORDED" for state in states):
        overall = "ALREADY_RECORDED"
    else:
        overall = "RECORDED_LOCAL_READBACK"
    return {"schema": RESULT_SCHEMA, "state": overall, "request_count": len(rows), "readbacks": rows,
            "dispatch_result_sha256": "sha256:" + hashlib.sha256(canon(rows)).hexdigest(),
            "authority_effect": "NONE_READBACK_ONLY"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST", "RECORDED_LOCAL_READBACK", "ALREADY_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
