#!/usr/bin/env python3
"""Consume one admitted StegBrowser Universal InTr materialization request.

The ingress/consumer is non-authorizing. It validates the exact Universal InTr
request, write-once ingress receipt, and hashed StegBrowser invocation payload,
then dispatches the already-existing manifest-bound StegBrowser runner. The
runner retains sole ownership of the existing EVENT_EPHEMERAL lease/runtime
composition and WorkerCoordinator remains sole claim/fence authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_RECEIPT_DIR_REL = Path("receipts/sovereign-network/stegbrowser-intr-ingress")
CONSUMPTION_DIR_REL = Path("receipts/sovereign-host/stegbrowser-intr-materialization")
BINDING_DIR_REL = Path("intr-payloads/stegbrowser-manifest-invocation")
LATEST_REL = Path("receipts/sovereign-host/stegbrowser-intr-materialization-consumption.latest.json")
RUNNER_REL = Path("scripts/run_stegbrowser_manifest_bound_runtime.py")
GOAL_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
PARENT_TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegBrowser:ManifestInvocation"}
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#1952"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
INGRESS_SCHEMA = "stegverse.stegbrowser-intr-materialization-ingress/v1"

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN",
)


class StegBrowserInTrMaterializationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StegBrowserInTrMaterializationError(f"object_required:{path}")
    return value


def _write_once(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != rendered:
            raise StegBrowserInTrMaterializationError(f"write_once_collision:{path}")
        return json.loads(existing)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    return json.loads(path.read_text(encoding="utf-8"))


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
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise StegBrowserInTrMaterializationError(f"stegbrowser_materialization_{key}_mismatch")
    materialization_id = request.get("materialization_id")
    if not isinstance(materialization_id, str) or not materialization_id.startswith("INTR-MAT-") or len(materialization_id) != 33:
        raise StegBrowserInTrMaterializationError("stegbrowser_materialization_id_invalid")
    for field in ("operation_id", "packet_id", "payload_ref"):
        if not isinstance(request.get(field), str) or not str(request[field]).strip():
            raise StegBrowserInTrMaterializationError(f"stegbrowser_materialization_{field}_required")
    for field in ("transport_intent_hash", "payload_hash", "request_hash"):
        value = request.get(field)
        if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
            raise StegBrowserInTrMaterializationError(f"{field}_invalid")
    if request.get("boundary_path") != ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]:
        raise StegBrowserInTrMaterializationError("stegbrowser_materialization_boundary_path_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    if claimed != digest_uri(body):
        raise StegBrowserInTrMaterializationError("stegbrowser_materialization_request_hash_mismatch")


def scrubbed_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    if any(str(values.get(name, "")).strip().lower() not in {"", "0", "false", "no"} for name in HOSTED_ENV):
        raise StegBrowserInTrMaterializationError("hosted_environment_cannot_execute_stegbrowser_materialization")
    keep = {
        "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
        "STEGVERSE_STEGOS_ROOT", "STEGVERSE_STEGOS_SOURCE_ROOT", "STEGVERSE_EPHEMERAL_RUNTIME_BASE",
        "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    }
    child = {key: values[key] for key in keep if values.get(key)}
    for name in CREDENTIAL_ENV:
        child.pop(name, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def _validate_binding(binding: Mapping[str, Any], *, request: Mapping[str, Any], ingress: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.stegbrowser-universal-intr-invocation-binding/v1",
        "state": "BOUND_FOR_UNIVERSAL_INTR_MATERIALIZATION",
        "goal_task_id": GOAL_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "request_mutated": False,
        "resident_request_sweep_required": False,
        "control_plane_source_package_required": False,
        "credential_authority": "TV/TVC",
        "github_runtime_authority": "NONE",
        "authority_effect": "NONE_BINDING_ONLY",
    }
    for key, wanted in expected.items():
        if binding.get(key) != wanted:
            raise StegBrowserInTrMaterializationError(f"invocation_binding_{key}_mismatch")
    for field in ("manifest_ref", "manifest_sha256", "node_genesis_receipt_ref", "node_id", "interlock_id", "registration_receipt_sha256"):
        if not isinstance(binding.get(field), str) or not str(binding[field]).strip():
            raise StegBrowserInTrMaterializationError(f"invocation_binding_{field}_required")
    if request.get("payload_hash") != digest_uri(binding):
        raise StegBrowserInTrMaterializationError("invocation_binding_payload_hash_mismatch")
    if ingress.get("node_id") != binding.get("node_id") or ingress.get("interlock_id") != binding.get("interlock_id"):
        raise StegBrowserInTrMaterializationError("invocation_binding_node_interlock_mismatch")


def consume_one(source_root: Path, runtime_root: Path, materialization_id: str, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request = _load(runtime / REQUEST_DIR_REL / f"{materialization_id}.json")
    validate_request(request)
    ingress = _load(runtime / INGRESS_RECEIPT_DIR_REL / f"{materialization_id}.json")
    if ingress.get("schema") != INGRESS_SCHEMA or ingress.get("state") != "INGRESS_ADMITTED":
        raise StegBrowserInTrMaterializationError("stegbrowser_ingress_receipt_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        if ingress.get(key) != request.get(key):
            raise StegBrowserInTrMaterializationError(f"stegbrowser_ingress_receipt_binding_mismatch:{key}")
    if ingress.get("transport_origin") != "STEGOS_NODE_OUTBOX" or ingress.get("claim_or_fence_minted") is not False:
        raise StegBrowserInTrMaterializationError("stegbrowser_ingress_authority_boundary_invalid")

    payload_ref = str(request["payload_ref"])
    opaque_prefix = "opaque://stegbrowser-manifest-invocation/"
    if payload_ref.startswith(opaque_prefix):
        digest = payload_ref[len(opaque_prefix):]
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise StegBrowserInTrMaterializationError("stegbrowser_invocation_binding_payload_ref_invalid")
        if request.get("payload_hash") != "sha256:" + digest:
            raise StegBrowserInTrMaterializationError("stegbrowser_invocation_binding_payload_ref_hash_mismatch")
        payload_path = runtime / BINDING_DIR_REL / f"{digest}.json"
    else:
        payload_path = Path(payload_ref).expanduser().resolve()
    if not payload_path.is_file():
        raise StegBrowserInTrMaterializationError("stegbrowser_invocation_binding_payload_missing")
    binding = _load(payload_path)
    _validate_binding(binding, request=request, ingress=ingress)

    runner_path = source / RUNNER_REL
    if not runner_path.is_file():
        raise StegBrowserInTrMaterializationError("stegbrowser_manifest_bound_runner_missing")
    stegos_root = Path(str(binding["stegos_source_root"])).expanduser().resolve()
    node_receipt = Path(str(binding["node_genesis_receipt_ref"])).expanduser().resolve()
    if not node_receipt.is_file() or not (stegos_root / "stegos/network_manifold.py").is_file():
        raise StegBrowserInTrMaterializationError("stegbrowser_node_or_stegos_source_missing")

    params = {
        "source_root": str(source),
        "sovereign_source_root": str(source),
        "runtime_root": str(runtime),
        "stegos_source_root": str(stegos_root),
        "node_genesis_receipt": str(node_receipt),
    }
    runtime_base = str((env or os.environ).get("STEGVERSE_EPHEMERAL_RUNTIME_BASE") or "").strip()
    if runtime_base:
        params["runtime_base"] = runtime_base
    child = scrubbed_env(env)
    child["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = json.dumps(params, sort_keys=True, separators=(",", ":"))
    child["STEGVERSE_REUSABLE_TASK_INVOCATION_ID"] = materialization_id
    child["STEGVERSE_STEGBROWSER_INVOCATION_NONCE"] = NONCE
    child["STEGVERSE_STEGBROWSER_MANIFEST_SHA256"] = str(binding["manifest_sha256"])
    completed = runner([sys.executable, str(runner_path)], cwd=str(source), env=child, check=False, capture_output=True, text=True, timeout=1800)

    boundary_path = runtime / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
    boundary = _load(boundary_path) if boundary_path.is_file() else {}
    projection = boundary.get("runtime_ingress_projection") if isinstance(boundary, dict) else {}
    result = {
        "schema": "stegverse.stegbrowser-intr-materialization-consumption/v1",
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "goal_task_id": GOAL_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "runner_returncode": completed.returncode,
        "runtime_execution_attempted": True,
        "event_ephemeral_runtime_observed": bool(boundary.get("invocation_owned_ephemeral_stegos_materialized") is True or boundary.get("runtime_class") == "EVENT_EPHEMERAL"),
        "workercoordinator_claim_fence_observed": bool(isinstance(projection, dict) and projection.get("workercoordinator_claim_fence_observed") is True),
        "authentic_intr_ingress_observed": bool(isinstance(projection, dict) and projection.get("authentic_intr_ingress_observed") is True),
        "round_trip_1_started": False,
        "request_grants_execution_authority": False,
        "consumer_minted_claim_or_fence": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_CONSUMER_DISPATCH_ONLY",
    }
    persisted = _write_once(runtime / CONSUMPTION_DIR_REL / f"{materialization_id}.json", result)
    latest = runtime / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(persisted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return persisted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    try:
        receipt = consume_one(args.source_root, args.runtime_root, args.materialization_id)
        print(json.dumps(receipt, sort_keys=True))
        return 0 if receipt["state"] == "MATERIALIZATION_EXECUTION_ATTEMPTED" else 2
    except Exception as exc:
        print(json.dumps({"state":"REFUSED","reason":f"{type(exc).__name__}:{exc}","authority_effect":"NONE_FAIL_CLOSED"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
