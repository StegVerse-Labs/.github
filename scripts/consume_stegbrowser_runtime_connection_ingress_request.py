#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/stegbrowser-runtime-connection-ingress-001.json")
CANONICAL_WORK_REQUEST_REL = Path("control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json")
TASK_ID = "STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001"
PARENT_TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
GOAL_TASK_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
COSV = "40000100100000"
MANIFEST_REF = "control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json"
OBS_SCHEMA = "stegverse.intr-runtime-connection-transition-observation/v1"
CANONICAL_NODE_SELECTOR = "CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING"
NODE_PATH_ENV = "STEGVERSE_NODE_GENESIS_RECEIPT"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_request(value: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv_task_vector": COSV,
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "entrypoint": "scripts/consume_stegbrowser_runtime_connection_ingress_request.py",
        "manifest_ref": MANIFEST_REF,
        "node_binding_selector": CANONICAL_NODE_SELECTOR,
        "canonical_node_receipt_path_parameter": "node_genesis_receipt",
        "canonical_node_receipt_path_environment": NODE_PATH_ENV,
        "round_trip_1_payload_processing_allowed": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        require(value.get(key) == wanted, f"request_{key}_mismatch")


def resolve_registered_node_receipt(request: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    require(request.get("node_binding_selector") == CANONICAL_NODE_SELECTOR, "canonical_node_selector_mismatch")
    raw = str(os.environ.get(NODE_PATH_ENV) or "").strip()
    require(raw, "canonical_registered_stegverse_node_receipt_1_not_available")
    path = Path(raw).expanduser().resolve()
    require(path.is_file(), "canonical_registered_stegverse_node_receipt_1_path_missing")
    receipt = load(path)
    require(receipt.get("schema") == "stegos.node_handoff_receipt.v1", "node_receipt_schema_mismatch")
    require(receipt.get("receipt_number") == 1 and receipt.get("transition") == "NODE_REGISTERED", "node_receipt_number_or_transition_mismatch")
    for key in ("node_id", "interlock_id", "device_binding_sha256", "receipt_sha256"):
        require(isinstance(receipt.get(key), str) and receipt[key], f"node_receipt_{key}_required")
    body = dict(receipt)
    claimed = body.pop("receipt_sha256")
    require(claimed == hashlib.sha256(canonical(body)).hexdigest(), "node_receipt_sha256_mismatch")
    return path, receipt


def install_and_load_shared_ingress(source_root: Path) -> Any:
    for rel in ("scripts/install_canonical_work_universal_intr_route.py", "scripts/install_stegbrowser_universal_intr_route.py"):
        installer = source_root / rel
        require(installer.is_file(), f"installer_missing:{rel}")
        subprocess.run([sys.executable, str(installer)], cwd=str(source_root), check=True)
        subprocess.run([sys.executable, str(installer), "--check"], cwd=str(source_root), check=True)
    path = source_root / "workers/universal_intr_profiled_ingress.py"
    spec = importlib.util.spec_from_file_location("stegbrowser_shared_intr", path)
    require(spec is not None and spec.loader is not None, "shared_intr_import_spec_missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_materialization(source_root: Path, runtime_root: Path, node_path: Path, node: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = source_root / MANIFEST_REF
    require(manifest_path.is_file(), "manifest_missing")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    canonical_work = load(source_root / CANONICAL_WORK_REQUEST_REL)
    nonce = canonical_work.get("invocation_request_nonce")
    require(isinstance(nonce, str) and nonce, "invocation_request_nonce_missing")
    seed = hashlib.sha256((nonce + "|" + manifest_sha + "|" + node["receipt_sha256"]).encode()).hexdigest()
    materialization_id = "INTR-MAT-" + seed[:24]
    payload = {
        "schema": "stegverse.stegbrowser-manifest-materialization-payload/v1",
        "goal_task_id": GOAL_TASK_ID,
        "cosv_task_vector": COSV,
        "manifest_ref": MANIFEST_REF,
        "manifest_sha256": manifest_sha,
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "registration_receipt_sha256": node["receipt_sha256"],
        "invocation_request_nonce": nonce,
        "round_trip_1_allowed": False,
        "authority_effect": "NONE_BINDING_ONLY",
    }
    payload_dir = runtime_root / "intr-payloads/stegbrowser-manifest"
    payload_dir.mkdir(parents=True, exist_ok=True)
    payload_path = payload_dir / f"{materialization_id}.json"
    atomic_json(payload_path, payload)
    request = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "materialization_id": materialization_id,
        "operation_id": "STEGBROWSER-A0-A4-" + seed[24:40],
        "packet_id": "STEGBROWSER-MAT-" + seed[40:56],
        "payload_ref": "runtime://intr-payloads/stegbrowser-manifest/" + payload_path.name,
        "payload_hash": sha_uri(payload),
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": sha_uri({"nonce": nonce, "manifest_sha256": manifest_sha, "node_id": node["node_id"], "interlock_id": node["interlock_id"]}),
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegBrowser:ManifestIngress"},
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": GOAL_TASK_ID,
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
        "goal_task_id": GOAL_TASK_ID,
        "cosv_task_vector": COSV,
        "manifest_ref": MANIFEST_REF,
        "manifest_sha256": manifest_sha,
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "node_genesis_receipt_ref": str(node_path),
        "registration_receipt_sha256": node["receipt_sha256"],
    }
    request["request_hash"] = sha_uri(request)
    entry = {
        "schema": "stegos.node_intr_outbox_entry.v1",
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
        "registration_receipt_sha256": request["registration_receipt_sha256"],
        "manifest_sha256": request["manifest_sha256"],
        "materialization_request": request,
        "network_delivery_observed": False,
        "runtime_materialization_observed": False,
        "receiver_receipt_observed": False,
        "tvc_receipt_observed": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
    }
    entry["outbox_entry_hash"] = sha_uri(entry)
    trigger = {
        "schema": "stegos.node_intr_materialization_trigger.v1",
        "transport_origin": "STEGOS_NODE_OUTBOX",
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    trigger["trigger_sha256"] = sha_uri(trigger)
    return request, trigger


def post_trigger(module: Any, runtime_root: Path, trigger: dict[str, Any]) -> dict[str, Any]:
    server = module.Server(("127.0.0.1", 0), runtime_root, 1)
    host, port = server.server_address
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    raw = canonical(trigger)
    req = urllib.request.Request(
        f"http://{host}:{port}{module.INGRESS_PATH}", data=raw, method="POST",
        headers={"Content-Type": "application/json", "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": "STEGOS_NODE_OUTBOX", "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest()},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            require(int(response.status) == 202, "intr_materialization_http_status_invalid")
            receipt = json.loads(response.read().decode("utf-8"))
    finally:
        thread.join(timeout=10)
        server.server_close()
    require(isinstance(receipt, dict) and receipt.get("schema") == "stegverse.stegbrowser-intr-materialization-ingress/v1", "stegbrowser_intr_ingress_receipt_schema_invalid")
    require(receipt.get("state") == "INGRESS_ADMITTED", "stegbrowser_intr_materialization_not_admitted")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    active_hosted = [name for name in HOSTED if truthy(os.environ.get(name))]
    require(not active_hosted, "hosted_environment_forbidden:" + ",".join(active_hosted))
    source_root = args.source_root.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    runtime_root.mkdir(parents=True, exist_ok=True)
    resident_request = load(source_root / REQUEST_REL)
    validate_request(resident_request)
    node_path, node = resolve_registered_node_receipt(resident_request)
    materialization_request, trigger = build_materialization(source_root, runtime_root, node_path, node)
    shared_intr = install_and_load_shared_ingress(source_root)
    ingress = post_trigger(shared_intr, runtime_root, trigger)

    observation = {
        "schema": OBS_SCHEMA,
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv": COSV,
        "manifest_ref": MANIFEST_REF,
        "authority_owner": "Interlock/InTr",
        "authority_effect": "OBSERVATION_ONLY",
        "observation_source": "VALIDATED_SV002_NODE_BOUND_WRITE_ONCE_UNIVERSAL_INTR_MATERIALIZATION_PATTERN",
        "callable": True,
        "refreshable": False,
        "applicable_protocol_resolved": True,
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "materialization_id": materialization_request["materialization_id"],
        "ingress_receipt_schema": ingress["schema"],
        "ingress_state": ingress["state"],
        "always_on_runtime_source_assumed": False,
        "second_user_operated_device_required": False,
    }
    observation_path = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json"
    atomic_json(observation_path, observation)
    result = {
        "schema": "stegverse.stegbrowser-runtime-connection-a1-a4-observation/v3",
        "state": "A1_NODE_BOUND_A2_INTR_MATERIALIZATION_ADMITTED",
        "task_id": TASK_ID,
        "goal_task_id": GOAL_TASK_ID,
        "cosv": COSV,
        "observation_ref": str(observation_path),
        "materialization_id": materialization_request["materialization_id"],
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "registration_receipt_sha256": node["receipt_sha256"],
        "manifest_sha256": materialization_request["manifest_sha256"],
        "intr_materialization_admitted": True,
        "invocation_scoped_lease_observed": False,
        "event_ephemeral_runtime_observed": False,
        "workercoordinator_claim_or_fence_observed": False,
        "authentic_intr_ingress_observed": False,
        "round_trip_1_payload_processing_attempted": False,
        "external_runtime_device_host_discovery_performed": False,
        "second_listener_implementation_created": False,
        "second_scheduler_created": False,
        "second_user_device_required": False,
        "authority_effect": "NONE_OBSERVATION_AND_EXISTING_AUTHORITY_COMPOSITION_ONLY",
    }
    out = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json"
    atomic_json(out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
