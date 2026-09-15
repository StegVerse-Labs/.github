#!/usr/bin/env python3
"""Submit the unchanged StegBrowser one-shot invocation through shared Universal InTr.

This composes existing StegOS Universal InTr builders, the existing shared
/intr/materialization listener, and the existing StegBrowser manifest-bound
runner. It creates no additional listener implementation, runtime, scheduler,
WorkerCoordinator, transport, endpoint, credential path, or authority surface.
"""
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
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
GOAL_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
PARENT_TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
REQUEST_REL = Path("control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json")
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
BINDING_DIR_REL = Path("intr-payloads/stegbrowser-manifest-invocation")
OUTBOX_DIR_REL = Path("intr-outbox/stegbrowser-manifest-invocation")
DESTINATION_SUBSYSTEM = "StegBrowser:ManifestInvocation"
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#1952"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + sha256_hex(raw)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object_required:{path}")
    return value


def write_once(path: Path, value: Mapping[str, Any]) -> Path:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"write_once_collision:{path}")
        return path
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    if path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"write_readback_mismatch:{path}")
    return path


def validate_unchanged_request(value: Mapping[str, Any]) -> None:
    expected = {
        "requested_goal_task_id": GOAL_ID,
        "requested_test_scope": "A0_A4_SINGLE_INVOCATION",
        "requested_invocation_count": 1,
        "invocation_request_nonce": NONCE,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise RuntimeError(f"unchanged_one_shot_request_{key}_mismatch")


def load_shared_ingress() -> Any:
    installer = ROOT / "scripts/install_stegbrowser_universal_intr_route.py"
    subprocess.run([sys.executable, str(installer)], cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, str(installer), "--check"], cwd=str(ROOT), check=True)
    path = ROOT / "workers/universal_intr_profiled_ingress.py"
    spec = importlib.util.spec_from_file_location("stegbrowser_shared_intr", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("shared_intr_import_spec_missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_binding(*, source_root: Path, runtime_root: Path, stegos_root: Path, node_receipt_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    stegos = stegos_root.resolve()
    one_shot = load(source / REQUEST_REL)
    validate_unchanged_request(one_shot)
    manifest_path = source / MANIFEST_REL
    manifest_raw = manifest_path.read_bytes()
    manifest = load(manifest_path)
    if manifest.get("task_id") != PARENT_TASK_ID or str(manifest.get("cosv_task_vector")) != COSV:
        raise RuntimeError("manifest_task_cosv_mismatch")
    if not node_receipt_path.is_file():
        raise RuntimeError("node_genesis_receipt_missing")
    sys.path.insert(0, str(stegos))
    from stegos.network_manifold import validate_node_genesis_receipt
    from stegos.universal_intr_transport import build_transport_intent, sha256_uri as stegos_sha256_uri
    from stegos.universal_intr_materialization import build_materialization_request

    node = load(node_receipt_path)
    validate_node_genesis_receipt(node)
    node_id = str(node.get("node_id") or "")
    interlock_id = str(node.get("interlock_id") or "")
    registration_receipt_sha256 = str(node.get("receipt_sha256") or "")
    if not node_id or not interlock_id or not registration_receipt_sha256:
        raise RuntimeError("node_binding_incomplete")

    binding = {
        "schema": "stegverse.stegbrowser-universal-intr-invocation-binding/v1",
        "state": "BOUND_FOR_UNIVERSAL_INTR_MATERIALIZATION",
        "goal_task_id": GOAL_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "manifest_ref": str(manifest_path),
        "manifest_sha256": sha256_hex(manifest_raw),
        "node_genesis_receipt_ref": str(node_receipt_path.resolve()),
        "node_id": node_id,
        "interlock_id": interlock_id,
        "registration_receipt_sha256": registration_receipt_sha256,
        "stegos_source_root": str(stegos),
        "request_mutated": False,
        "resident_request_sweep_required": False,
        "control_plane_source_package_required": False,
        "credential_authority": "TV/TVC",
        "github_runtime_authority": "NONE",
        "authority_effect": "NONE_BINDING_ONLY",
    }
    binding_hash = sha256_hex(canonical_bytes(binding))
    binding_path = runtime / BINDING_DIR_REL / f"{binding_hash}.json"
    write_once(binding_path, binding)
    payload_hash = stegos_sha256_uri(binding)
    intent = build_transport_intent(
        operation_id=f"STEGBROWSER:{GOAL_ID}:{NONCE}",
        payload_hash=payload_hash,
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="StegBrowser:ManifestRequest",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem=DESTINATION_SUBSYSTEM,
    )
    request = build_materialization_request(intent, payload_ref=str(binding_path), downstream_owner_ref=DOWNSTREAM_OWNER)
    entry_body = {
        "schema": "stegos.node_intr_outbox_entry.v1",
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "response_sha256": binding_hash,
        "provenance_sha256": sha256_uri({"manifest_sha256": binding["manifest_sha256"], "nonce": NONCE}),
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
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
    entry = {**entry_body, "outbox_entry_hash": sha256_uri(entry_body)}
    trigger_body = {
        "schema": "stegos.node_intr_materialization_trigger.v1",
        "transport_origin": "STEGOS_NODE_OUTBOX",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    trigger = {**trigger_body, "trigger_sha256": sha256_uri(trigger_body)}
    write_once(runtime / OUTBOX_DIR_REL / f"{request['materialization_id']}.json", trigger)
    return binding, request, trigger


def submit_once(*, source_root: Path, runtime_root: Path, stegos_root: Path, node_receipt_path: Path) -> dict[str, Any]:
    _binding, request, trigger = build_binding(source_root=source_root, runtime_root=runtime_root, stegos_root=stegos_root, node_receipt_path=node_receipt_path)
    shared = load_shared_ingress()
    server = shared.Server(("127.0.0.1", 0), runtime_root.resolve(), 1)
    host, port = server.server_address
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    raw = canonical_bytes(trigger)
    req = urllib.request.Request(
        f"http://{host}:{port}{shared.INGRESS_PATH}",
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": "STEGOS_NODE_OUTBOX",
            "X-StegVerse-Payload-SHA256": sha256_hex(raw),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            receipt = json.loads(response.read().decode("utf-8"))
            if int(response.status) != 202:
                raise RuntimeError("stegbrowser_intr_ingress_http_status_invalid")
    finally:
        thread.join(timeout=10)
        server.server_close()
    if not isinstance(receipt, dict) or receipt.get("schema") != "stegverse.stegbrowser-intr-materialization-ingress/v1" or receipt.get("state") != "INGRESS_ADMITTED":
        raise RuntimeError("stegbrowser_intr_ingress_not_admitted")
    if receipt.get("materialization_id") != request.get("materialization_id") or receipt.get("request_hash") != request.get("request_hash"):
        raise RuntimeError("stegbrowser_intr_ingress_request_binding_mismatch")
    return {
        "schema": "stegverse.stegbrowser-universal-intr-submission/v1",
        "state": "INGRESS_ADMITTED",
        "goal_task_id": GOAL_ID,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "ingress_receipt": receipt,
        "consumer_dispatch_attempted": bool((receipt.get("dispatch") or {}).get("consumer_dispatch_attempted") is True),
        "runtime_predicates_promoted": False,
        "round_trip_1_started": False,
        "authority_effect": "NONE_SUBMISSION_AND_ADMISSION_EVIDENCE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--stegos-root", type=Path)
    parser.add_argument("--node-genesis-receipt", type=Path)
    args = parser.parse_args()
    stegos_root = (args.stegos_root or Path(os.environ.get("STEGVERSE_STEGOS_SOURCE_ROOT") or args.source_root.parent / "StegOS")).expanduser().resolve()
    node_receipt = (args.node_genesis_receipt or Path(os.environ.get("STEGVERSE_NODE_GENESIS_RECEIPT") or "")).expanduser().resolve()
    result = submit_once(source_root=args.source_root.expanduser().resolve(), runtime_root=args.runtime_root.expanduser().resolve(), stegos_root=stegos_root, node_receipt_path=node_receipt)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
