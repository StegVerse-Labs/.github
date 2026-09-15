#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
GOAL_TASK_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
RUNNER_REL = Path("scripts/run_stegbrowser_runtime_consumption_reusable.py")
BINDING_RECEIPT_REL = Path("receipts/sovereign-host/stegbrowser-manifest-binding.latest.json")
INSTALLER_REL = Path("scripts/install_stegbrowser_universal_intr_route.py")


def fail(reason: str) -> None:
    print(json.dumps({"state":"BOUNDARY","reason":reason,"task_id":TASK_ID,"goal_task_id":GOAL_TASK_ID,"authority_effect":"NONE"}, sort_keys=True))
    raise SystemExit(2)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"json_load_failed:{path}:{exc}")
    if not isinstance(value, dict):
        fail(f"json_object_required:{path}")
    return value


def params() -> dict:
    raw = os.environ.get("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "")
    if not raw:
        fail("reusable_task_parameters_missing")
    try:
        value = json.loads(raw)
    except Exception:
        fail("reusable_task_parameters_invalid_json")
    if not isinstance(value, dict):
        fail("reusable_task_parameters_object_required")
    return value


def resolve_root(value: object, env_name: str, fallback: Path | None = None) -> Path:
    raw = str(value or os.environ.get(env_name) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    if fallback is not None:
        return fallback.resolve()
    fail(f"required_path_missing:{env_name}")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: object) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema") != "stegverse.interlock-intr-manifest/v1": fail("manifest_schema_mismatch")
    if manifest.get("task_id") != TASK_ID or manifest.get("cosv_task_vector") != COSV: fail("manifest_task_cosv_mismatch")
    if manifest.get("path_source") != "MANIFEST" or manifest.get("route_owner") != "STEGVERSE": fail("manifest_route_owner_or_source_invalid")
    if manifest.get("endpoint_discovery_required") is not False or manifest.get("receiver_discovery_required") is not False: fail("manifest_discovery_must_be_false")
    if manifest.get("undeclared_endpoint_or_receiver_substitution_allowed") is not False: fail("manifest_substitution_must_be_forbidden")
    outbound = manifest.get("outbound") or {}
    if outbound.get("ecosystem_boundary") != "STEGVERSE_ECOSYSTEM" or outbound.get("interlock_intr_endpoint") != "STEGVERSE_OWNED_INTR_EGRESS_ENDPOINT": fail("manifest_outbound_binding_mismatch")
    if outbound.get("receiver") != "STEGVERSE_OWNED_MIRROR_REFLECTOR" or outbound.get("receiver_role") != "OWNED_MIRROR_REFLECTOR": fail("manifest_owned_mirror_receiver_mismatch")
    if outbound.get("expected_action") != "REFLECT_DECLARED_RECORDS_PACKET": fail("manifest_reflection_action_mismatch")
    rt1 = manifest.get("round_trip_1") or {}
    if rt1.get("return_target") != "MASTER_RECORDS_RECORDING_SURFACE" or rt1.get("terminal_predicate") != "SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED": fail("manifest_round_trip_1_contract_mismatch")
    between = manifest.get("between_round_trips") or {}
    if between.get("processing_boundary") != "STEGVERSE_OWNED_MIRROR_BOUNDARY": fail("manifest_mirror_boundary_mismatch")
    rt2 = manifest.get("round_trip_2") or {}
    if rt2.get("interlock_intr_endpoint") != "STEGVERSE_OWNED_INTR_ECOSYSTEM_RETURN_ENDPOINT" or rt2.get("receiver") != "STEGVERSE_ECOSYSTEM" or rt2.get("terminal_predicate") != "SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED": fail("manifest_round_trip_2_contract_mismatch")
    if manifest.get("overall_terminal_predicate") != "SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED": fail("manifest_overall_terminal_predicate_mismatch")


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_ingress_module(source: Path):
    installer = source / INSTALLER_REL
    subprocess.run([sys.executable, str(installer)], cwd=source, check=True)
    subprocess.run([sys.executable, str(installer), "--check"], cwd=source, check=True)
    path = source / "workers/stegbrowser_intr_ingress.py"
    spec = importlib.util.spec_from_file_location("stegbrowser_intr_ingress", path)
    if spec is None or spec.loader is None: fail("stegbrowser_ingress_loader_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_node_trigger(*, source: Path, resident_root: Path, stegos: Path, manifest_path: Path, manifest_sha256: str, p: dict) -> tuple[dict, dict]:
    node_receipt_path = resolve_root(p.get("node_genesis_receipt"), "STEGVERSE_NODE_GENESIS_RECEIPT")
    if not node_receipt_path.is_file(): fail("registered_stegverse_node_receipt_1_missing")
    sys.path.insert(0, str(stegos))
    try:
        from stegos.network_manifold import validate_node_genesis_receipt
        from stegos.universal_intr_transport import build_transport_intent
        from stegos.universal_intr_materialization import build_materialization_request
    except Exception as exc:
        fail(f"stegos_universal_intr_import_failed:{type(exc).__name__}:{exc}")
    genesis = load_json(node_receipt_path)
    try:
        validate_node_genesis_receipt(genesis)
    except Exception as exc:
        fail(f"registered_stegverse_node_receipt_1_invalid:{type(exc).__name__}:{exc}")
    node_id = str(genesis.get("node_id") or "")
    interlock_id = str(genesis.get("interlock_id") or "")
    if not node_id or not interlock_id: fail("registered_stegverse_node_binding_incomplete")
    payload_hash = "sha256:" + manifest_sha256
    intent = build_transport_intent(
        operation_id=f"{GOAL_TASK_ID}:{NONCE}",
        payload_hash=payload_hash,
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="StegBrowser:ManifestInvocation",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem="StegBrowser:ManifestExecution",
    )
    request = build_materialization_request(intent, payload_ref=str(manifest_path), downstream_owner_ref=GOAL_TASK_ID)
    entry = {
        "schema": "stegos.node_intr_outbox_entry.v1",
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
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
    entry["outbox_entry_hash"] = digest_uri(entry)
    trigger = {
        "schema": "stegos.node_intr_materialization_trigger.v1",
        "transport_origin": "STEGOS_NODE_LOCAL_OUTBOX",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    trigger["trigger_sha256"] = digest_uri(trigger)
    os.environ["STEGVERSE_NODE_GENESIS_RECEIPT"] = str(node_receipt_path)
    return trigger, request


def main() -> int:
    p = params()
    source = resolve_root(p.get("sovereign_source_root") or p.get("source_root"), "STEGVERSE_HEARTBEAT_SOURCE_ROOT", ROOT)
    resident_root = resolve_root(p.get("runtime_root") or p.get("resident_runtime_root"), "STEGVERSE_HEARTBEAT_ROOT")
    stegos = resolve_root(p.get("stegos_source_root"), "STEGVERSE_STEGOS_SOURCE_ROOT", source.parent / "StegOS")
    manifest_path = source / MANIFEST_REL
    runner_path = source / RUNNER_REL
    if not manifest_path.is_file(): fail("manifest_missing")
    if not runner_path.is_file(): fail("runtime_runner_missing")
    manifest = load_json(manifest_path)
    validate_manifest(manifest)
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    binding = {
        "schema":"stegverse.stegbrowser-manifest-binding/v1", "state":"MANIFEST_BOUND_TO_INVOCATION",
        "task_id":TASK_ID, "goal_task_id":GOAL_TASK_ID, "cosv_task_vector":COSV,
        "invocation_request_nonce":NONCE, "manifest_ref":str(manifest_path), "manifest_sha256":digest,
        "route_owner":"STEGVERSE", "shared_intr_materialization_path":"/intr/materialization",
        "outbound_interlock_intr_endpoint":manifest["outbound"]["interlock_intr_endpoint"],
        "far_end_receiver":manifest["outbound"]["receiver"], "far_end_receiver_role":manifest["outbound"]["receiver_role"],
        "round_trip_1_return_target":manifest["round_trip_1"]["return_target"],
        "mirror_processing_boundary":manifest["between_round_trips"]["processing_boundary"],
        "round_trip_2_interlock_intr_endpoint":manifest["round_trip_2"]["interlock_intr_endpoint"],
        "round_trip_2_receiver":manifest["round_trip_2"]["receiver"],
        "endpoint_discovery_required":False, "receiver_discovery_required":False,
        "undeclared_endpoint_or_receiver_substitution_allowed":False, "authority_effect":"NONE_ROUTE_BINDING_ONLY"
    }
    atomic_json(resident_root / BINDING_RECEIPT_REL, binding)

    if os.environ.get("STEGVERSE_STEGBROWSER_INTR_ADMITTED") == "1":
        env = dict(os.environ)
        env["STEGVERSE_STEGBROWSER_MANIFEST_SHA256"] = digest
        completed = subprocess.run([sys.executable, str(runner_path)], cwd=source, env=env, text=True, capture_output=False, check=False)
        return completed.returncode

    trigger, request = _build_node_trigger(source=source, resident_root=resident_root, stegos=stegos, manifest_path=manifest_path, manifest_sha256=digest, p=p)
    ingress = _load_ingress_module(source)
    body = canonical(trigger)
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "STEGOS_NODE_LOCAL_OUTBOX",
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }
    receipt = ingress.admit(runtime_root=resident_root, body=body, headers=headers)
    if receipt.get("state") != "INGRESS_ADMITTED" or receipt.get("materialization_id") != request.get("materialization_id"):
        fail("stegbrowser_intr_materialization_not_admitted")
    print(json.dumps({
        "state":"INGRESS_ADMITTED",
        "goal_task_id":GOAL_TASK_ID,
        "cosv_task_vector":COSV,
        "invocation_request_nonce":NONCE,
        "materialization_id":request["materialization_id"],
        "request_hash":request["request_hash"],
        "node_id":receipt.get("node_id"),
        "interlock_id":receipt.get("interlock_id"),
        "consumer_dispatch_attempted":bool((receipt.get("dispatch") or {}).get("consumer_dispatch_attempted")),
        "authority_effect":"NONE_INGRESS_OBSERVATION_ONLY"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
