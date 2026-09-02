#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


SCHEMA = "stegverse.hb-runtime-presence-resident-observability/v1"


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def first_json(paths: list[Path]) -> tuple[Path | None, dict[str, Any] | None]:
    for path in paths:
        value = read_json(path)
        if value is not None:
            return path, value
    return None, None


def node_candidates(runtime_root: Path, env: dict[str, str]) -> list[Path]:
    values: list[Path] = []
    marker = str(env.get("STEGVERSE_SOVEREIGN_NODE_MARKER") or "").strip()
    if marker:
        values.append(Path(marker).expanduser())
    values.extend([
        Path.home() / ".stegverse" / "node.json",
        Path("/etc/stegverse/node.json"),
        runtime_root / "control" / "sovereign-node-declaration.json",
    ])
    return values


def evidence_ref(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def project(runtime_root: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    root = runtime_root.expanduser().resolve()

    node_path, node = first_json(node_candidates(root, values))
    anchor = read_json(root / "control/heartbeat-protocol-anchor.json")
    carrier = read_json(root / "control/heartbeat-carrier-runtime-state.json")
    worker = read_json(root / "control/worker-runtime-state.json")
    coordination = read_json(root / "control/worker-control-plane-coordination.json")
    dispatch_path = root / "receipts/sovereign-host/resident-request-dispatch.latest.json"
    dispatch = read_json(dispatch_path)

    node_observed = bool(node and node.get("declared") is True and node.get("node_id"))
    worker_observed = worker is not None
    dispatch_observed = dispatch is not None

    hb_reference = {
        "state": "OBSERVED" if anchor else "NOT_OBSERVED",
        "protocol_anchor": anchor,
        "carrier_runtime_observation_state": "OBSERVED" if carrier else "NOT_OBSERVED",
        "carrier_runtime_observation": carrier,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }

    resident = {
        "state": "OBSERVED" if worker_observed else "NOT_OBSERVED",
        "node_identity_state": "OBSERVED" if node_observed else "NOT_OBSERVED",
        "node_id": node.get("node_id") if node else None,
        "node_declaration_ref": evidence_ref(node_path, root) if node_path else None,
        "worker_runtime_state": worker,
        "worker_control_plane_coordination": coordination,
    }

    request = {
        "dispatch_state": "OBSERVED" if dispatch_observed else "NOT_OBSERVED",
        "dispatch_receipt_ref": evidence_ref(dispatch_path, root) if dispatch_observed else None,
        "dispatch_receipt": dispatch,
        "request_consumption_state": "NOT_OBSERVED",
        "request_consumption_receipt_ref": None,
    }

    return {
        "schema": SCHEMA,
        "runtime_root": str(root),
        "resident": resident,
        "hb_reference": hb_reference,
        "governed_request": request,
        "execution": {
            "state": "NOT_OBSERVED",
            "execution_receipt_ref": None,
            "state_transition": None,
        },
        "retained_evidence": {
            "state": "NOT_OBSERVED",
            "receipt_refs": [],
            "reconstruction_state": "NOT_OBSERVED",
            "reconstruction_receipt_ref": None,
        },
        "authority": {
            "heartbeat_grants_execution_authority": False,
            "heartbeat_grants_admission_authority": False,
            "heartbeat_grants_claim_or_fence_authority": False,
            "interlock_intr_governs_transition": True,
            "worker_coordinator_remains_admission_claim_fence_authority": True,
            "credential_authority": "TV/TVC",
            "github_runtime_authority": "NONE",
            "authority_effect": "NONE_OBSERVATION_ONLY",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = project(Path(args.runtime_root))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
