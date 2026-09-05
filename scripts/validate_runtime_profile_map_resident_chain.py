#!/usr/bin/env python3
"""Validate the canonical Runtime Profile Map resident chain fail-closed.

This is a source-integrity validator only. It verifies that every staged resident
request is paired with the expected consumer and registered selector, and that
request declarations preserve non-authorizing HB/oscillator/credential semantics.
It does not execute the resident chain or infer runtime evidence from source state.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

STAGES = (
    ("runtime_profile_map", "control/resident-execution-request.d/runtime-profile-map-build-001.json", "control/resident-execution-request.d/consume-runtime-profile-map-build.py"),
    ("runtime_profile_map_custody", "control/resident-execution-request.d/runtime-profile-map-custody-001.json", "control/resident-execution-request.d/consume-runtime-profile-map-custody.py"),
    ("runtime_profile_map_reconciliation", "control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json", "control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py"),
    ("runtime_profile_map_transition_readiness", "control/resident-execution-request.d/runtime-profile-map-transition-readiness-001.json", "control/resident-execution-request.d/consume-runtime-profile-map-transition-readiness.py"),
    ("runtime_profile_map_governance_review", "control/resident-execution-request.d/runtime-profile-map-governance-review-001.json", "control/resident-execution-request.d/consume-runtime-profile-map-governance-review.py"),
)
DISPATCHER = "scripts/dispatch_resident_execution_requests.py"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required:{path}")
    return value


def dispatcher_consumers(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CONSUMERS" for t in node.targets):
            value = ast.literal_eval(node.value)
            require(isinstance(value, tuple), "dispatcher CONSUMERS must be tuple")
            out: dict[str, str] = {}
            for row in value:
                require(isinstance(row, tuple) and len(row) == 2 and all(isinstance(x, str) for x in row), "dispatcher consumer row invalid")
                require(row[0] not in out, f"duplicate dispatcher selector:{row[0]}")
                out[row[0]] = row[1]
            return out
    raise RuntimeError("FAIL_CLOSED: dispatcher CONSUMERS not found")


def validate(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    dispatcher_path = root / DISPATCHER
    require(dispatcher_path.is_file(), "resident dispatcher missing")
    registered = dispatcher_consumers(dispatcher_path)
    rows: list[dict[str, Any]] = []

    for selector, request_rel, consumer_rel in STAGES:
        request_path = root / request_rel
        consumer_path = root / consumer_rel
        require(request_path.is_file(), f"request missing:{request_rel}")
        require(consumer_path.is_file(), f"consumer missing:{consumer_rel}")
        require(registered.get(selector) == consumer_rel, f"dispatcher binding mismatch:{selector}")
        request = load_object(request_path)
        require(request.get("schema") == "stegverse.resident-execution-request/v1", f"request schema mismatch:{selector}")
        require(request.get("state") == "REQUESTED", f"request state mismatch:{selector}")
        require(request.get("entrypoint") == consumer_rel, f"request entrypoint mismatch:{selector}")
        require(request.get("credential_authority") == "TV/TVC", f"credential authority mismatch:{selector}")
        require(request.get("github_token_required") is False, f"GitHub token prohibited:{selector}")
        require(request.get("github_token_runtime_authority") == "NONE", f"GitHub runtime authority mismatch:{selector}")
        require(request.get("heartbeat_grants_execution_authority") is False, f"heartbeat authority prohibited:{selector}")
        require(request.get("oscillator_grants_execution_authority") is False, f"oscillator authority prohibited:{selector}")
        require(request.get("second_machine_required") is False, f"second machine prohibited:{selector}")
        require(request.get("network_source_fetch_allowed") is False, f"network source fetch prohibited:{selector}")
        require(request.get("request_granted_authority") is False, f"request authority prohibited:{selector}")
        require(request.get("authority_effect") == "NONE_REQUEST_ONLY", f"request authority effect mismatch:{selector}")
        rows.append({
            "selector": selector,
            "request_ref": request_rel,
            "consumer_ref": consumer_rel,
            "task_id": request.get("task_id"),
            "mode": request.get("mode"),
            "registered": True,
            "authority_effect": "NONE_SOURCE_VALIDATION_ONLY",
        })

    expected_selectors = [row[0] for row in STAGES]
    require(all(name in registered for name in expected_selectors), "runtime profile selector set incomplete")
    return {
        "schema": "stegverse.runtime-profile-map-resident-chain-validation/v1",
        "state": "SOURCE_CHAIN_VALID",
        "stage_count": len(rows),
        "stages": rows,
        "dispatcher_ref": DISPATCHER,
        "runtime_execution_observed": False,
        "runtime_receipts_validated": False,
        "task_state_changed": False,
        "claim_or_fence_minted": False,
        "heartbeat_or_oscillator_advanced": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_SOURCE_VALIDATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
