#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.execution-surface-discovery/v1"
CLASSES = {"connected", "ephemeral", "all"}

EPHEMERAL_SURFACES = [
    {
        "surface_id": "STEGVERSE_NODE_EVENT_EPHEMERAL",
        "surface": "StegVerseNode",
        "class": "ephemeral",
        "availability": "AVAILABLE_TO_INVOKE",
        "instance_state": "NOT_MATERIALIZED",
        "runtime_class": "EVENT_EPHEMERAL",
        "materialization": "ON_INVOCATION",
        "persistent_connection_required": False,
        "second_user_operated_device_required": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
        "callable_task": "STEGVERSE-002-EXPERIMENT-RERUN-001",
        "execution_owner": "StegVerse-002/.github",
        "operation": "REQUEST_SELF_CHARACTERIZATION",
        "materialization_path": ["REGISTERED_STEGVERSE_NODE", "INTERLOCK", "UNIVERSAL_INTR_MATERIALIZATION", "BOUNDED_INVOCATION_LEASE", "EVENT_EPHEMERAL", "STEGVERSE_002_ORG_SELF_CHARACTERIZATION_SURFACE"],
    },
    {
        "surface_id": "STEGBROWSER_EVENT_EPHEMERAL",
        "surface": "StegBrowser",
        "class": "ephemeral",
        "availability": "AVAILABLE_TO_INVOKE",
        "instance_state": "NOT_MATERIALIZED",
        "runtime_class": "EVENT_EPHEMERAL",
        "materialization": "ON_INVOCATION",
        "persistent_connection_required": False,
        "second_user_operated_device_required": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
        "callable_task": "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001",
        "execution_owner": "StegVerse-Labs/.github",
        "operation": "STEGBROWSER_MANIFEST_DEFINED_INTR_INGRESS",
        "materialization_path": ["REGISTERED_STEGVERSE_NODE", "INTERLOCK", "UNIVERSAL_INTR_MATERIALIZATION", "BOUNDED_INVOCATION_LEASE", "EVENT_EPHEMERAL_STEGBROWSER"],
    },
]


def _load_connected(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("connected device input must be a JSON array")
    return [{**dict(item), "class": "connected"} for item in value]


def discover(surface_class: str, connected: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if surface_class not in CLASSES:
        raise ValueError("class must be connected, ephemeral, or all")
    connected = list(connected or [])
    connected = [{**dict(item), "class": "connected"} for item in connected]
    surfaces: list[dict[str, Any]] = []
    if surface_class in {"connected", "all"}:
        surfaces.extend(connected)
    if surface_class in {"ephemeral", "all"}:
        surfaces.extend(EPHEMERAL_SURFACES)
    return {
        "schema": SCHEMA,
        "requested_class": surface_class,
        "connected_count": len(connected),
        "ephemeral_count": len(EPHEMERAL_SURFACES) if surface_class in {"ephemeral", "all"} else 0,
        "zero_connected_devices_is_runtime_blocker": False,
        "surfaces": surfaces,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="surface_class", default="all", choices=sorted(CLASSES))
    parser.add_argument("--connected-json")
    args = parser.parse_args()
    result = discover(args.surface_class, _load_connected(args.connected_json))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
