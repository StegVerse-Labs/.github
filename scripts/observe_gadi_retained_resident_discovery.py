#!/usr/bin/env python3
from __future__ import annotations

"""Observe the existing same-device retained resident discovery contract for GADI.

This adapter does not create a listener, runtime, claim/fence, admission, credential,
or execution authority. It probes only the existing localhost StegBrowser/StegOS
resident-rendezvous discovery endpoint and persists exact observation evidence.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
DISCOVERY_SCHEMA = "stegverse.resident-rendezvous.discovery/v1"
OUTPUT_SCHEMA = "stegverse.gadi-retained-resident-discovery-observation/v1"
OUTPUT_REL = Path("state/gadi-resident-execution/retained-resident-discovery.json")
LOCAL_BASES = ("http://127.0.0.1:8000", "http://localhost:8000")
NODE_RE = re.compile(r"^SV-NODE-[0-9a-f]{24}$")
EXPECTED_FIELDS = {
    "schema", "state", "target_node_ref", "gateway_execution_authority",
    "credential_authority", "discovery_grants_authority", "authority_effect",
}


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _validate(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != EXPECTED_FIELDS:
        raise ValueError("resident discovery fields invalid")
    if value.get("schema") != DISCOVERY_SCHEMA or value.get("state") != "AVAILABLE":
        raise ValueError("resident discovery state/schema invalid")
    node_ref = str(value.get("target_node_ref") or "")
    if not NODE_RE.fullmatch(node_ref):
        raise ValueError("resident discovery node ref invalid")
    if value.get("gateway_execution_authority") != "NONE":
        raise ValueError("resident discovery gateway authority invalid")
    if value.get("credential_authority") != "TV/TVC":
        raise ValueError("resident discovery credential authority invalid")
    if value.get("discovery_grants_authority") is not False:
        raise ValueError("resident discovery may not grant authority")
    if value.get("authority_effect") != "NONE_DISCOVERY_ONLY":
        raise ValueError("resident discovery authority effect invalid")
    return dict(value)


def _probe(base: str, timeout: float = 3.0) -> tuple[str, bytes | None, dict[str, Any] | None]:
    url = base + "/api/resident-rendezvous/v1/discovery"
    request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "StegVerse-GADI-Discovery/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        if exc.code >= 500 or exc.code == 404:
            return "UNAVAILABLE", None, None
        raise ValueError(f"resident discovery rejected request: HTTP {exc.code}") from exc
    except (URLError, TimeoutError, ConnectionError, OSError):
        return "UNAVAILABLE", None, None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("resident discovery returned malformed JSON") from exc
    return "REACHABLE", raw, _validate(value)


def observe(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    output = runtime / OUTPUT_REL
    attempted: list[str] = []
    for base in LOCAL_BASES:
        attempted.append(base)
        state, raw, discovery = _probe(base)
        if state != "REACHABLE":
            continue
        assert raw is not None and discovery is not None
        result = {
            "schema": OUTPUT_SCHEMA,
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "state": "CURRENT_RETAINED_RESIDENT_DISCOVERY_OBSERVED",
            "target_node_ref": discovery["target_node_ref"],
            "discovery_schema": discovery["schema"],
            "source_endpoint": base + "/api/resident-rendezvous/v1/discovery",
            "source_response_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "discovery_grants_authority": False,
            "runtime_binding_granted": False,
            "claim_or_fence_granted": False,
            "intr_admission_granted": False,
            "execution_authority_granted": False,
            "hosted_fallback_used": False,
            "authority_effect": "NONE_DISCOVERY_ONLY",
        }
        _write(output, result)
        return result

    result = {
        "schema": OUTPUT_SCHEMA,
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "state": "RETAINED_RESIDENT_DISCOVERY_UNOBSERVED_FAIL_CLOSED",
        "target_node_ref": None,
        "attempted_local_bases": attempted,
        "hosted_fallback_used": False,
        "runtime_binding_granted": False,
        "claim_or_fence_granted": False,
        "intr_admission_granted": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }
    _write(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "CURRENT_RETAINED_RESIDENT_DISCOVERY_OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
