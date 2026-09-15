#!/usr/bin/env python3
"""Consume one admitted StegBrowser Universal InTr materialization request.

This consumer is non-authorizing. It requires the existing shared Universal InTr
INGRESS_ADMITTED receipt, then invokes the already-existing manifest-bound
StegBrowser runner. The downstream runner remains responsible for the existing
EVENT_EPHEMERAL StegOS lease/runtime and WorkerCoordinator claim/fence path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegBrowser:ManifestExecution"}
DOWNSTREAM_OWNER = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
GOAL_TASK_ID = DOWNSTREAM_OWNER
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
INGRESS_SCHEMA = "stegverse.stegbrowser-intr-materialization-ingress/v1"
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_DIR_REL = Path("receipts/sovereign-network/stegbrowser-intr-ingress")
LATEST_REL = Path("receipts/sovereign-host/stegbrowser-intr-materialization-consumption.latest.json")
TARGET_ENTRYPOINT = Path("scripts/run_stegbrowser_manifest_bound_runtime.py")

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "destination": DESTINATION,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        require(request.get(key) == value, f"stegbrowser_materialization_{key}_mismatch")
    mid = request.get("materialization_id")
    require(isinstance(mid, str) and mid.startswith("INTR-MAT-") and len(mid) == 33, "stegbrowser_materialization_id_invalid")
    require(isinstance(request.get("operation_id"), str) and NONCE in str(request.get("operation_id")), "stegbrowser_nonce_binding_missing")
    require(isinstance(request.get("payload_ref"), str) and request.get("payload_ref"), "stegbrowser_manifest_payload_ref_required")
    for field in ("transport_intent_hash", "payload_hash", "request_hash"):
        value = request.get(field)
        require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71, f"{field}_invalid")
    require(request.get("boundary_path") == ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"], "stegbrowser_boundary_path_invalid")
    body = dict(request)
    claimed = body.pop("request_hash", None)
    require(claimed == sha_uri(body), "stegbrowser_materialization_request_hash_mismatch")


def scrubbed_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        values.pop(key, None)
    values["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    values["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    values["STEGVERSE_STEGBROWSER_INTR_ADMITTED"] = "1"
    return values


def consume_one(source_root: Path, runtime_root: Path, materialization_id: str, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request = load(runtime / REQUEST_DIR_REL / f"{materialization_id}.json")
    validate_request(request)
    ingress = load(runtime / INGRESS_DIR_REL / f"{materialization_id}.json")
    require(ingress.get("schema") == INGRESS_SCHEMA and ingress.get("state") == "INGRESS_ADMITTED", "stegbrowser_ingress_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        require(ingress.get(key) == request.get(key), f"stegbrowser_ingress_binding_mismatch:{key}")
    require(isinstance(ingress.get("node_id"), str) and ingress.get("node_id"), "stegbrowser_ingress_node_missing")
    require(isinstance(ingress.get("interlock_id"), str) and ingress.get("interlock_id"), "stegbrowser_ingress_interlock_missing")
    require(ingress.get("claim_or_fence_minted") is False, "stegbrowser_ingress_minted_claim_fence")
    require(ingress.get("credential_authority") == "TV/TVC" and ingress.get("github_token_runtime_authority") == "NONE", "stegbrowser_ingress_authority_boundary_invalid")

    child = scrubbed_env(env)
    child["STEGVERSE_REUSABLE_TASK_INVOCATION_ID"] = materialization_id
    child["STEGVERSE_STEGBROWSER_INTR_INGRESS_RECEIPT"] = str(runtime / INGRESS_DIR_REL / f"{materialization_id}.json")
    completed = runner(
        [sys.executable, str(source / TARGET_ENTRYPOINT)],
        cwd=source,
        env=child,
        text=True,
        capture_output=True,
        check=False,
        timeout=1800,
    )
    receipt = {
        "schema": "stegverse.stegbrowser-intr-materialization-consumption/v1",
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "goal_task_id": GOAL_TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "node_id": ingress["node_id"],
        "interlock_id": ingress["interlock_id"],
        "target_entrypoint": str(TARGET_ENTRYPOINT),
        "target_returncode": completed.returncode,
        "runtime_execution_attempted": True,
        "consumer_grants_execution_authority": False,
        "consumer_claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_POST_ADMISSION_DISPATCH_ONLY",
    }
    latest = runtime / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    try:
        value = consume_one(args.source_root, args.runtime_root, args.materialization_id)
        print(json.dumps(value, sort_keys=True))
        return 0 if value["state"] == "MATERIALIZATION_EXECUTION_ATTEMPTED" else 2
    except Exception as exc:
        print(json.dumps({"state": "REFUSED", "reason": f"{type(exc).__name__}:{exc}", "authority_effect": "NONE_FAIL_CLOSED"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
