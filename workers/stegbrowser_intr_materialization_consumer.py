#!/usr/bin/env python3
"""Consume one admitted StegBrowser Universal InTr materialization event.

This reuses the validated StegVerse-002 event-ephemeral architecture. The ingress
is non-authorizing; this consumer validates the exact write-once admission and
then delegates to the existing manifest-bound StegBrowser runner. It creates no
listener, scheduler, WorkerCoordinator, alternate runtime architecture, or
second-device dependency.
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
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegBrowser:ManifestIngress"}
DOWNSTREAM_OWNER = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
BOUNDARY_PATH = ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]
INGRESS_SCHEMA = "stegverse.stegbrowser-intr-materialization-ingress/v1"
CONSUMPTION_SCHEMA = "stegverse.stegbrowser-intr-materialization-consumption/v1"
MANIFEST_REF = "control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json"
GOAL = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
COSV = "40000100100000"
RUNNER = Path("scripts/run_stegbrowser_manifest_bound_runtime.py")
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


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
        "boundary_path": BOUNDARY_PATH,
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
        "goal_task_id": GOAL,
        "cosv_task_vector": COSV,
        "manifest_ref": MANIFEST_REF,
    }
    for key, wanted in expected.items():
        require(request.get(key) == wanted, f"stegbrowser_materialization_{key}_mismatch")
    for field in (
        "materialization_id", "operation_id", "packet_id", "payload_ref",
        "transport_intent_hash", "payload_hash", "request_hash",
        "node_genesis_receipt_ref", "registration_receipt_sha256", "manifest_sha256",
    ):
        require(isinstance(request.get(field), str) and bool(request[field]), f"stegbrowser_materialization_{field}_required")
    require(str(request["materialization_id"]).startswith("INTR-MAT-") and len(str(request["materialization_id"])) == 33, "stegbrowser_materialization_id_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    require(claimed == sha_uri(body), "stegbrowser_materialization_request_hash_mismatch")


def scrubbed_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    require(not any(str(values.get(k, "")).strip().lower() not in {"", "0", "false", "no"} for k in HOSTED), "hosted_environment_cannot_execute_stegbrowser_materialization")
    keep = {
        "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
        "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_STEGOS_SOURCE_ROOT",
        "STEGVERSE_EPHEMERAL_RUNTIME_BASE",
    }
    child = {k: values[k] for k in keep if values.get(k)}
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def consume_one(source_root: Path, runtime_root: Path, materialization_id: str, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    request_path = runtime / "intr-materialization" / f"{materialization_id}.json"
    ingress_path = runtime / "receipts/sovereign-network/stegbrowser-intr-ingress" / f"{materialization_id}.json"
    request = load(request_path)
    validate_request(request)
    ingress = load(ingress_path)
    require(ingress.get("schema") == INGRESS_SCHEMA and ingress.get("state") == "INGRESS_ADMITTED", "stegbrowser_ingress_receipt_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id", "node_id", "interlock_id", "registration_receipt_sha256", "manifest_sha256"):
        require(ingress.get(key) == request.get(key), f"stegbrowser_ingress_binding_mismatch:{key}")
    require(ingress.get("claim_or_fence_minted") is False and ingress.get("credential_authority") == "TV/TVC", "stegbrowser_ingress_authority_boundary_invalid")

    manifest_path = source / MANIFEST_REF
    require(manifest_path.is_file(), "stegbrowser_manifest_missing")
    require(hashlib.sha256(manifest_path.read_bytes()).hexdigest() == request["manifest_sha256"], "stegbrowser_manifest_sha256_mismatch")
    receipt_path = Path(str(request["node_genesis_receipt_ref"])).expanduser().resolve()
    require(receipt_path.is_file(), "stegbrowser_node_genesis_receipt_missing")
    receipt = load(receipt_path)
    require(receipt.get("schema") == "stegos.node_handoff_receipt.v1" and receipt.get("receipt_number") == 1, "stegbrowser_node_genesis_receipt_invalid")
    require(receipt.get("node_id") == request["node_id"] and receipt.get("interlock_id") == request["interlock_id"], "stegbrowser_node_interlock_receipt_mismatch")
    require(receipt.get("receipt_sha256") == request["registration_receipt_sha256"], "stegbrowser_registration_receipt_sha256_mismatch")

    params = {
        "source_root": str(source),
        "sovereign_source_root": str(source),
        "runtime_root": str(runtime),
        "node_genesis_receipt": str(receipt_path),
    }
    safe = scrubbed_env(env)
    safe["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = json.dumps(params, sort_keys=True, separators=(",", ":"))
    completed = runner([sys.executable, str(source / RUNNER)], cwd=source, env=safe, text=True, capture_output=True, check=False, timeout=1800)

    boundary_path = runtime / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
    boundary = load(boundary_path) if boundary_path.is_file() else {}
    projection = boundary.get("runtime_ingress_projection") if isinstance(boundary.get("runtime_ingress_projection"), dict) else {}
    result = {
        "schema": CONSUMPTION_SCHEMA,
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "node_id": request["node_id"],
        "interlock_id": request["interlock_id"],
        "registration_receipt_sha256": request["registration_receipt_sha256"],
        "manifest_sha256": request["manifest_sha256"],
        "node_genesis_receipt_ref": str(receipt_path),
        "runtime_execution_attempted": True,
        "downstream_runner": str(RUNNER),
        "downstream_returncode": completed.returncode,
        "workercoordinator_claim_fence_observed": projection.get("workercoordinator_claim_fence_observed") is True,
        "organization_local_intr_ingress_receipt_verified": projection.get("organization_local_intr_ingress_receipt_verified") is True,
        "authentic_intr_ingress_observed": projection.get("authentic_intr_ingress_observed") is True,
        "claim_id": projection.get("claim_ref"),
        "fencing_token": projection.get("fence_ref"),
        "lease_id": projection.get("lease_id"),
        "runtime_id": projection.get("runtime_id"),
        "state_root_binding": projection.get("state_root_binding"),
        "round_trip_1_started": False,
        "second_listener_created": False,
        "second_scheduler_created": False,
        "second_runtime_architecture_created": False,
        "second_user_device_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "consumer_grants_execution_authority": False,
        "authority_effect": "NONE_DISPATCH_AND_EVIDENCE_ONLY",
    }
    out = runtime / "receipts/sovereign-host/stegbrowser-intr-materialization" / f"{materialization_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if out.exists():
        require(load(out) == result, "stegbrowser_consumption_write_once_collision")
    else:
        out.write_text(raw, encoding="utf-8")
    latest = runtime / "receipts/sovereign-host/stegbrowser-intr-materialization-consumption.latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    print(json.dumps(consume_one(args.source_root, args.runtime_root, args.materialization_id), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
