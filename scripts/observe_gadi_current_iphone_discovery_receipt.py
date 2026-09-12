#!/usr/bin/env python3
from __future__ import annotations

"""Observe the existing StegOSMobile current-iPhone discovery receipt read surface.

This adapter is evidence-only. It reads the already-persisted receipt through the
existing bounded localhost listener, validates it with the canonical retained-node
projector, and never creates runtime presence, supervision, WorkerCoordinator
claim/fence, InTr admission, credentials, leases, or execution authority.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from scripts import materialize_gadi_retained_node_discovery as retained_projector
except ModuleNotFoundError:
    import materialize_gadi_retained_node_discovery as retained_projector

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
FETCH_SCHEMA = "stegos.stegbrowser.current-iphone-rendezvous-observation-fetch/v1"
OUTPUT_SCHEMA = "stegverse.gadi-current-iphone-discovery-receipt-readback/v1"
OUTPUT_REL = Path("state/gadi-resident-execution/current-iphone-discovery-receipt-readback.json")
LOCAL_BASES = ("http://127.0.0.1:8000", "http://localhost:8000")
NODE_RE = re.compile(r"^SV-NODE-[0-9a-f]{24}$")
EXPECTED_WRAPPER_FIELDS = {
    "schema", "state", "target_node_ref", "gateway_execution_authority",
    "credential_authority", "evidence_grants_authority", "authority_effect", "evidence",
}


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _validate_wrapper(value: Any, node_ref: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != EXPECTED_WRAPPER_FIELDS:
        raise ValueError("current-iPhone receipt wrapper fields invalid")
    if value.get("schema") != FETCH_SCHEMA:
        raise ValueError("current-iPhone receipt wrapper schema invalid")
    if value.get("target_node_ref") != node_ref:
        raise ValueError("current-iPhone receipt wrapper node mismatch")
    if value.get("gateway_execution_authority") != "NONE":
        raise ValueError("current-iPhone receipt wrapper gateway authority invalid")
    if value.get("credential_authority") != "TV/TVC":
        raise ValueError("current-iPhone receipt wrapper credential authority invalid")
    if value.get("evidence_grants_authority") is not False:
        raise ValueError("current-iPhone receipt wrapper may not grant authority")
    if value.get("authority_effect") != "NONE_EVIDENCE_READ_ONLY":
        raise ValueError("current-iPhone receipt wrapper authority effect invalid")
    state = value.get("state")
    if state not in ("EVIDENCE_AVAILABLE", "NO_EVIDENCE"):
        raise ValueError("current-iPhone receipt wrapper state invalid")
    if state == "NO_EVIDENCE":
        if value.get("evidence") is not None:
            raise ValueError("NO_EVIDENCE wrapper must not carry evidence")
        return dict(value)
    evidence = value.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("current-iPhone receipt evidence object required")
    projected = retained_projector.project(evidence)
    if projected.get("node_ref") != node_ref:
        raise ValueError("current-iPhone receipt projected node mismatch")
    return {**dict(value), "_projected": projected}


def _probe(base: str, node_ref: str, timeout: float = 3.0) -> tuple[str, bytes | None, dict[str, Any] | None]:
    url = base + "/api/resident-rendezvous/v1/evidence/current-iphone-discovery?target_node_ref=" + node_ref
    request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "StegVerse-GADI-Current-iPhone-Receipt/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        if exc.code >= 500 or exc.code == 404:
            return "UNAVAILABLE", None, None
        raise ValueError(f"current-iPhone receipt read rejected request: HTTP {exc.code}") from exc
    except (URLError, TimeoutError, ConnectionError, OSError):
        return "UNAVAILABLE", None, None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("current-iPhone receipt read returned malformed JSON") from exc
    return "REACHABLE", raw, _validate_wrapper(value, node_ref)


def observe(runtime_root: Path, node_ref: str) -> dict[str, Any]:
    if NODE_RE.fullmatch(node_ref) is None:
        raise ValueError("canonical retained node ref required")
    runtime = runtime_root.expanduser().resolve()
    output = runtime / OUTPUT_REL
    attempted: list[str] = []
    saw_no_evidence = False
    for base in LOCAL_BASES:
        attempted.append(base)
        state, raw, wrapper = _probe(base, node_ref)
        if state != "REACHABLE":
            continue
        assert raw is not None and wrapper is not None
        if wrapper.get("state") == "NO_EVIDENCE":
            saw_no_evidence = True
            continue
        projected = wrapper.pop("_projected")
        result = {
            "schema": OUTPUT_SCHEMA,
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "state": "CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED",
            "target_node_ref": node_ref,
            "source_endpoint": base + "/api/resident-rendezvous/v1/evidence/current-iphone-discovery",
            "source_response_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "source_receipt_sha256": projected["source_receipt_sha256"],
            "source_envelope_sha256": projected["source_envelope_sha256"],
            "retained_node_observation_ref": projected["observation_ref"],
            "runtime_presence_observed": False,
            "runtime_subject_bound": False,
            "claim_or_fence_granted": False,
            "intr_admission_granted": False,
            "execution_authority_granted": False,
            "hosted_fallback_used": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_EVIDENCE_READ_ONLY",
        }
        _write(output, result)
        return result

    result = {
        "schema": OUTPUT_SCHEMA,
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "state": "CURRENT_IPHONE_RECEIPT_READBACK_UNOBSERVED_FAIL_CLOSED",
        "target_node_ref": node_ref,
        "attempted_local_bases": attempted,
        "listener_reachable_without_evidence": saw_no_evidence,
        "hosted_fallback_used": False,
        "runtime_presence_observed": False,
        "runtime_subject_bound": False,
        "claim_or_fence_granted": False,
        "intr_admission_granted": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_EVIDENCE_READ_ONLY",
    }
    _write(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--node-ref", required=True)
    args = parser.parse_args()
    result = observe(args.runtime_root, args.node_ref)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
