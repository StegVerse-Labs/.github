#!/usr/bin/env python3
"""Shared profiled Universal InTr materialization ingress.

HIL requests delegate to the already-validated HIL ingress unchanged. SV002
public-observation requests use a distinct validator/receipt namespace and,
after write-once admission, launch a credential-scrubbed non-authorizing
consumer. That consumer may ask the existing WorkerCoordinator to execute only
the already-admitted SV002 observation task under its own claim/fence authority.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import serve_hil_intr_materialization_ingress as hil  # noqa: E402
from heartbeat_runtime.intr_carrier_profile import (  # noqa: E402
    carrier_profile as hb_intr_carrier_profile,
    validate_carrier_binding,
)
from consume_kv_publisher_return_materialization_request import (  # noqa: E402
    DESTINATION as KV_PUBLISHER_RETURN_DESTINATION,
    DOWNSTREAM_OWNER as KV_PUBLISHER_RETURN_OWNER,
    scrubbed_env as kv_publisher_return_scrubbed_env,
    validate_request as validate_kv_publisher_return_request,
)
from consume_publisher_intr_materialization_request import (  # noqa: E402
    DESTINATION as PUBLISHER_DESTINATION,
    DOWNSTREAM_OWNER as PUBLISHER_OWNER,
    scrubbed_env as publisher_scrubbed_env,
    validate_request as validate_publisher_request,
)
from consume_device_kv_intr_materialization_request import (  # noqa: E402
    DESTINATION as DEVICE_KV_DESTINATION,
    DOWNSTREAM_OWNER as DEVICE_KV_OWNER,
    QUERY_RESPONSE_DIR_REL as DEVICE_KV_QUERY_RESPONSE_DIR_REL,
    scrubbed_env as device_kv_scrubbed_env,
    validate_request as validate_device_kv_request,
)
from heartbeat_runtime.intr_subsignal_runtime import (  # noqa: E402
    default_heartbeat_runtime_root,
    recover_local_intr_subsignal,
)
from workers.sv002_intr_materialization_consumer import (  # noqa: E402
    DESTINATION as SV002_DESTINATION,
    DOWNSTREAM_OWNER as SV002_OWNER,
    scrubbed_env as sv002_scrubbed_env,
    validate_request as validate_sv002_request,
)

PROFILE_PATH = "/intr/profile"
INGRESS_PATH = "/intr/materialization"
DEVICE_KV_RESULT_PATH = "/intr/device-kv/result"
SV002_RECEIPT_SCHEMA = "stegverse.sv002-intr-materialization-ingress/v1"
SV002_RECEIPT_DIR = Path("receipts/sovereign-network/sv002-intr-ingress")
SV002_LATEST = Path("receipts/sovereign-network/sv002-intr-ingress.latest.json")
DEVICE_KV_RECEIPT_SCHEMA = "stegverse.device-kv-intr-materialization-ingress/v1"
DEVICE_KV_RECEIPT_DIR = Path("receipts/sovereign-network/device-kv-intr-ingress")
DEVICE_KV_LATEST = Path("receipts/sovereign-network/device-kv-intr-ingress.latest.json")
PUBLISHER_RECEIPT_SCHEMA = "stegverse.publisher-intr-materialization-ingress/v1"
PUBLISHER_RECEIPT_DIR = Path("receipts/sovereign-network/publisher-intr-ingress")
PUBLISHER_LATEST = Path("receipts/sovereign-network/publisher-intr-ingress.latest.json")
PUBLISHER_PAYLOAD_DIR = Path("intr-payloads/publisher-artifact-transfer")
PUBLISHER_TRIGGER_SCHEMA = "stegverse.publisher-intr-materialization-trigger/v1"
KV_PUBLISHER_RETURN_RECEIPT_SCHEMA = "stegverse.kv-publisher-return-materialization-ingress/v1"
KV_PUBLISHER_RETURN_RECEIPT_DIR = Path("receipts/sovereign-network/kv-publisher-return-ingress")
KV_PUBLISHER_RETURN_LATEST = Path("receipts/sovereign-network/kv-publisher-return-ingress.latest.json")
KV_PUBLISHER_RETURN_PAYLOAD_DIR = Path("intr-payloads/kv-publisher-return")
KV_PUBLISHER_RETURN_TRIGGER_SCHEMA = "stegverse.kv-publisher-return-materialization-trigger/v1"
AUTHORITY_EFFECT = "NONE_INGRESS_ONLY"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_id(value: str) -> str:
    require(value.startswith("INTR-MAT-") and len(value) == 33 and all(ch in "0123456789abcdef" for ch in value[9:]), "materialization_id_invalid")
    return value


def carrier_binding_evidence(request: Mapping[str, Any]) -> dict[str, Any]:
    binding = request.get("carrier_binding")
    if binding is None:
        return {
            "carrier_binding_present": False,
            "carrier_binding_validated": False,
            "carrier_profile": "stegverse.intr.hb-derived-carrier-profile/v1",
            "heartbeat_reference_epoch": None,
            "heartbeat_reference_id": None,
            "carrier_channel_id": None,
            "carrier_binding_sha256": None,
            "carrier_binding_grants_authority": False,
        }
    validated = validate_carrier_binding(
        binding,
        packet_id=str(request.get("packet_id") or ""),
        payload_hash=str(request.get("payload_hash") or ""),
    )
    reference = validated["heartbeat_reference"]
    channel = validated["channel"]
    return {
        "carrier_binding_present": True,
        "carrier_binding_validated": True,
        "carrier_profile": validated["carrier_profile"],
        "heartbeat_reference_epoch": reference["heartbeat_epoch"],
        "heartbeat_reference_id": reference["heartbeat_id"],
        "carrier_channel_id": channel["channel_id"],
        "carrier_binding_sha256": validated["binding_sha256"],
        "carrier_binding_grants_authority": False,
    }


def _sv002_request_from_payload(payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    origin = transport["origin"]
    if origin == hil.ORIGIN_RELAY:
        require(isinstance(payload, dict), "request_object_required")
        validate_sv002_request(payload)
        return dict(payload), {
            "transport_origin": origin,
            "transport_authorization_id": transport["authorization_id"],
            "node_id": None,
            "interlock_id": None,
            "outbox_entry_hash": None,
        }
    require(isinstance(payload, dict) and payload.get("schema") == hil.NODE_TRIGGER_SCHEMA, "node_trigger_schema_invalid")
    require(payload.get("transport_origin") == hil.ORIGIN_NODE, "node_trigger_origin_invalid")
    require(payload.get("authority_effect") == "NONE_TRIGGER_ONLY", "node_trigger_authority_effect_invalid")
    require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False, "node_trigger_authority_forbidden")
    entry = payload.get("node_outbox_entry")
    require(isinstance(entry, dict), "node_outbox_entry_required")
    require(entry.get("schema") == hil.NODE_OUTBOX_SCHEMA and entry.get("state") == "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY", "node_outbox_state_invalid")
    require(entry.get("network_delivery_observed") is False and entry.get("runtime_materialization_observed") is False and entry.get("receiver_receipt_observed") is False and entry.get("tvc_receipt_observed") is False, "node_outbox_promoted_evidence_forbidden")
    require(entry.get("request_grants_execution_authority") is False and entry.get("claim_or_fence_minted") is False, "node_outbox_authority_forbidden")
    require(entry.get("credential_authority") == "TV/TVC" and entry.get("github_token_runtime_authority") == "NONE" and entry.get("authority_effect") == "NONE_LOCAL_CONTINUITY_ONLY", "node_outbox_credential_boundary_invalid")
    body = dict(entry)
    claimed = body.pop("outbox_entry_hash", None)
    require(claimed == sha_uri(body), "node_outbox_entry_hash_mismatch")
    request = entry.get("materialization_request")
    require(isinstance(request, dict), "node_outbox_materialization_request_required")
    validate_sv002_request(request)
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "destination", "downstream_owner_ref"):
        require(entry.get(key) == request.get(key), "node_outbox_binding_mismatch:" + key)
    require(payload.get("node_id") == entry.get("node_id") and payload.get("interlock_id") == entry.get("interlock_id") and payload.get("outbox_entry_hash") == entry.get("outbox_entry_hash"), "node_trigger_binding_mismatch")
    trigger = dict(payload)
    trigger_claim = trigger.pop("trigger_sha256", None)
    require(trigger_claim == sha_uri(trigger), "node_trigger_hash_mismatch")
    return dict(request), {
        "transport_origin": origin,
        "transport_authorization_id": None,
        "node_id": entry.get("node_id"),
        "interlock_id": entry.get("interlock_id"),
        "outbox_entry_hash": entry.get("outbox_entry_hash"),
    }


def _is_sv002(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("destination") == SV002_DESTINATION and payload.get("downstream_owner_ref") == SV002_OWNER:
        return True
    if isinstance(payload, dict):
        entry = payload.get("node_outbox_entry")
        if isinstance(entry, dict):
            request = entry.get("materialization_request")
            return isinstance(request, dict) and request.get("destination") == SV002_DESTINATION and request.get("downstream_owner_ref") == SV002_OWNER
    return False


def _dispatch_sv002_consumer(*, runtime_root: Path, materialization_id: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "workers.sv002_intr_materialization_consumer",
        "--source-root",
        str(ROOT),
        "--runtime-root",
        str(runtime_root),
        "--materialization-id",
        materialization_id,
    ]
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=sv002_scrubbed_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return {
        "consumer_dispatch_attempted": True,
        "consumer_pid": process.pid,
        "consumer_execution_authority": False,
        "consumer_claim_or_fence_minted_by_ingress": False,
        "authority_effect": "NONE_DISPATCH_ONLY",
    }


def admit_sv002(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = hil.validate_transport_headers(headers, body)
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    request, source = _sv002_request_from_payload(payload, transport)
    materialization_id = safe_id(str(request["materialization_id"]))
    carrier = carrier_binding_evidence(request)
    request_path = runtime_root / hil.REQUEST_DIR_REL / f"{materialization_id}.json"
    request_raw = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    hil._write_once(request_path, request_raw)
    receipt_path = runtime_root / SV002_RECEIPT_DIR / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return existing
    receipt = {
        "schema": SV002_RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": source["transport_origin"],
        "transport_authorization_id": source["transport_authorization_id"],
        "node_id": source["node_id"],
        "interlock_id": source["interlock_id"],
        "outbox_entry_hash": source["outbox_entry_hash"],
        "transport_payload_sha256": transport["payload_sha256"],
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_execution_attempted": False,
        "consumer_dispatch_attempted": False,
        "receiver_readiness_claimed": False,
        "round_trip_claimed": False,
        "observation_round_trip_claimed": False,
        "observer_direct_relation_to_stegverse_002": False,
        "claim_or_fence_minted": False,
        "g18_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        **carrier,
        "authority_effect": AUTHORITY_EFFECT,
        "admitted_at": now(),
    }
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    hil._write_once(receipt_path, raw)
    latest = runtime_root / SV002_LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)
    dispatch = _dispatch_sv002_consumer(runtime_root=runtime_root, materialization_id=materialization_id)
    return {**receipt, "dispatch": dispatch}


def _device_kv_request_from_payload(payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    origin = transport["origin"]
    if origin == hil.ORIGIN_RELAY:
        require(isinstance(payload, dict), "request_object_required")
        validate_device_kv_request(payload)
        return dict(payload), {"transport_origin":origin,"transport_authorization_id":transport["authorization_id"],"node_id":None,"interlock_id":None,"outbox_entry_hash":None}
    require(isinstance(payload, dict) and payload.get("schema") == hil.NODE_TRIGGER_SCHEMA, "node_trigger_schema_invalid")
    require(payload.get("transport_origin") == hil.ORIGIN_NODE and payload.get("authority_effect") == "NONE_TRIGGER_ONLY", "node_trigger_invalid")
    require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False, "node_trigger_authority_forbidden")
    entry=payload.get("node_outbox_entry"); require(isinstance(entry,dict), "node_outbox_entry_required")
    require(entry.get("schema")==hil.NODE_OUTBOX_SCHEMA and entry.get("state")=="LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY", "node_outbox_state_invalid")
    require(entry.get("request_grants_execution_authority") is False and entry.get("claim_or_fence_minted") is False, "node_outbox_authority_forbidden")
    require(entry.get("credential_authority")=="TV/TVC" and entry.get("github_token_runtime_authority")=="NONE" and entry.get("authority_effect")=="NONE_LOCAL_CONTINUITY_ONLY", "node_outbox_credential_boundary_invalid")
    body=dict(entry); claimed=body.pop("outbox_entry_hash",None); require(claimed==sha_uri(body), "node_outbox_entry_hash_mismatch")
    request=entry.get("materialization_request"); require(isinstance(request,dict), "node_outbox_materialization_request_required"); validate_device_kv_request(request)
    for key in ("materialization_id","request_hash","transport_intent_hash","payload_hash","destination","downstream_owner_ref"):
        require(entry.get(key)==request.get(key), "node_outbox_binding_mismatch:"+key)
    require(payload.get("node_id")==entry.get("node_id") and payload.get("interlock_id")==entry.get("interlock_id") and payload.get("outbox_entry_hash")==entry.get("outbox_entry_hash"), "node_trigger_binding_mismatch")
    trigger=dict(payload); trigger_claim=trigger.pop("trigger_sha256",None); require(trigger_claim==sha_uri(trigger), "node_trigger_hash_mismatch")
    return dict(request), {"transport_origin":origin,"transport_authorization_id":None,"node_id":entry.get("node_id"),"interlock_id":entry.get("interlock_id"),"outbox_entry_hash":entry.get("outbox_entry_hash")}

def _is_device_kv(payload: Any) -> bool:
    if isinstance(payload,dict) and payload.get("destination")==DEVICE_KV_DESTINATION and payload.get("downstream_owner_ref")==DEVICE_KV_OWNER: return True
    if isinstance(payload,dict):
        entry=payload.get("node_outbox_entry")
        if isinstance(entry,dict):
            request=entry.get("materialization_request")
            return isinstance(request,dict) and request.get("destination")==DEVICE_KV_DESTINATION and request.get("downstream_owner_ref")==DEVICE_KV_OWNER
    return False

def _dispatch_device_kv_consumer(*, runtime_root: Path, materialization_id: str) -> dict[str, Any]:
    command=[sys.executable,str(ROOT/"scripts/consume_device_kv_intr_materialization_request.py"),"--source-root",str(ROOT),"--runtime-root",str(runtime_root),"--materialization-id",materialization_id]
    process=subprocess.Popen(command,cwd=str(ROOT),env=device_kv_scrubbed_env(),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    return {"consumer_dispatch_attempted":True,"consumer_pid":process.pid,"consumer_execution_authority":False,"consumer_claim_or_fence_minted_by_ingress":False,"authority_effect":"NONE_DISPATCH_ONLY"}

def admit_device_kv(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport=hil.validate_transport_headers(headers,body)
    try: payload=json.loads(body.decode("utf-8"))
    except Exception as exc: raise ValueError("request_json_invalid") from exc
    request,source=_device_kv_request_from_payload(payload,transport); materialization_id=safe_id(str(request["materialization_id"]))
    carrier=carrier_binding_evidence(request)
    request_path=runtime_root/hil.REQUEST_DIR_REL/f"{materialization_id}.json"; request_raw=json.dumps(request,sort_keys=True,indent=2).encode("utf-8")+b"\n"; hil._write_once(request_path,request_raw)
    receipt_path=runtime_root/DEVICE_KV_RECEIPT_DIR/f"{materialization_id}.json"
    if receipt_path.exists():
        existing=json.loads(receipt_path.read_text(encoding="utf-8")); require(existing.get("request_hash")==request.get("request_hash") and existing.get("state")=="INGRESS_ADMITTED","write_once_collision"); return existing
    receipt={"schema":DEVICE_KV_RECEIPT_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":materialization_id,"request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],"payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],"transport_origin":source["transport_origin"],"transport_authorization_id":source["transport_authorization_id"],"node_id":source["node_id"],"interlock_id":source["interlock_id"],"outbox_entry_hash":source["outbox_entry_hash"],"transport_payload_sha256":transport["payload_sha256"],"queue_ref":str(request_path),"exact_request_validated":True,"write_once_persisted":True,"runtime_execution_attempted":False,"consumer_dispatch_attempted":False,"claim_or_fence_minted":False,"g18_required":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE",**carrier,"authority_effect":AUTHORITY_EFFECT,"admitted_at":now()}
    raw=json.dumps(receipt,sort_keys=True,indent=2).encode("utf-8")+b"\n"; hil._write_once(receipt_path,raw); latest=runtime_root/DEVICE_KV_LATEST; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_bytes(raw)
    dispatch=_dispatch_device_kv_consumer(runtime_root=runtime_root,materialization_id=materialization_id)
    return {**receipt,"dispatch":dispatch}


def retrieve_device_kv_query_result(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport=hil.validate_transport_headers(headers,body)
    require(transport["origin"]==hil.ORIGIN_NODE and transport["authorization_id"] is None,"device_kv_result_requires_node_origin")
    try:
        payload=json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("device_kv_result_request_json_invalid") from exc
    require(isinstance(payload,dict),"device_kv_result_request_object_required")
    require(set(payload)=={"schema","materialization_id","request_hash","node_id","authority_effect"},"device_kv_result_request_field_set_invalid")
    require(payload.get("schema")=="stegverse.device-kv.query-result-request/v1","device_kv_result_request_schema_invalid")
    require(payload.get("authority_effect")=="NONE_RESULT_LOOKUP_ONLY","device_kv_result_request_authority_invalid")
    materialization_id=safe_id(str(payload.get("materialization_id") or ""))
    request_hash=payload.get("request_hash")
    node_id=payload.get("node_id")
    require(isinstance(request_hash,str) and len(request_hash)==71 and request_hash.startswith("sha256:"),"device_kv_result_request_hash_invalid")
    require(isinstance(node_id,str) and node_id.startswith("SV-NODE-"),"device_kv_result_node_id_invalid")

    ingress_path=runtime_root/DEVICE_KV_RECEIPT_DIR/f"{materialization_id}.json"
    result_path=runtime_root/DEVICE_KV_QUERY_RESPONSE_DIR_REL/f"{materialization_id}.json"
    require(ingress_path.is_file(),"device_kv_result_ingress_missing")
    require(result_path.is_file(),"device_kv_result_not_ready")
    ingress=json.loads(ingress_path.read_text(encoding="utf-8"))
    result=json.loads(result_path.read_text(encoding="utf-8"))
    require(ingress.get("state")=="INGRESS_ADMITTED","device_kv_result_ingress_not_admitted")
    require(ingress.get("request_hash")==request_hash and ingress.get("node_id")==node_id,"device_kv_result_ingress_binding_mismatch")
    require(result.get("state")=="RESPONSE_PERSISTED","device_kv_result_state_invalid")
    require(result.get("materialization_id")==materialization_id and result.get("request_hash")==request_hash and result.get("node_id")==node_id,"device_kv_result_response_binding_mismatch")
    require(result.get("response_transported_on_hb_derived_carrier") is True and result.get("exact_response_packet_recovered") is True,"device_kv_result_carrier_evidence_missing")
    signal_ref=result.get("response_shared_hb_signal_ref")
    signal_sha=result.get("response_shared_hb_signal_sha256")
    require(isinstance(signal_ref,str) and signal_ref and isinstance(signal_sha,str) and len(signal_sha)==64,"device_kv_result_signal_binding_invalid")
    heartbeat_root=default_heartbeat_runtime_root()
    recovered=recover_local_intr_subsignal(root=heartbeat_root,signal_ref=signal_ref)
    require(sha_uri(recovered)==result.get("response_payload_hash"),"device_kv_result_recovered_payload_hash_mismatch")
    require(recovered==canonical(result.get("response")),"device_kv_result_recovered_response_mismatch")
    signal_path=(heartbeat_root/signal_ref).resolve()
    try:
        signal_path.relative_to(heartbeat_root)
    except ValueError as exc:
        raise ValueError("device_kv_result_signal_ref_outside_runtime") from exc
    require(signal_path.is_file(),"device_kv_result_signal_missing")
    signal=json.loads(signal_path.read_text(encoding="utf-8"))
    require(sha_uri(signal)[7:]==signal_sha,"device_kv_result_signal_sha256_mismatch")
    return {
        "schema":"stegverse.device-kv.query-result-delivery/v1",
        "state":"RESULT_AVAILABLE",
        "materialization_id":materialization_id,
        "request_hash":request_hash,
        "node_id":node_id,
        "response":result["response"],
        "response_receipt_hash":result["receipt_hash"],
        "response_payload_hash":result["response_payload_hash"],
        "response_carrier_signal":signal,
        "response_shared_hb_signal_ref":signal_ref,
        "response_shared_hb_signal_sha256":signal_sha,
        "response_transported_on_hb_derived_carrier":True,
        "exact_response_packet_recovered":True,
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "credential_material_present":False,
        "provider_operation_authorized":False,
        "result_lookup_grants_authority":False,
        "authority_effect":"NONE_RESULT_DELIVERY_ONLY",
    }


def _is_publisher(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("destination") == PUBLISHER_DESTINATION and payload.get("downstream_owner_ref") == PUBLISHER_OWNER:
        return True
    if isinstance(payload, dict) and payload.get("schema") == PUBLISHER_TRIGGER_SCHEMA:
        request = payload.get("materialization_request")
        return isinstance(request, dict) and request.get("destination") == PUBLISHER_DESTINATION and request.get("downstream_owner_ref") == PUBLISHER_OWNER
    return False

def _publisher_request_from_payload(*, runtime_root: Path, payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(payload, dict) and payload.get("schema") == PUBLISHER_TRIGGER_SCHEMA:
        require(payload.get("authority_effect") == "NONE_TRIGGER_ONLY", "publisher_trigger_authority_effect_invalid")
        require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False, "publisher_trigger_authority_forbidden")
        request = payload.get("materialization_request")
        require(isinstance(request, dict), "publisher_materialization_request_required")
        validate_publisher_request(request)
        raw_b64 = payload.get("payload_base64")
        receipts = payload.get("forward_receipts")
        require(isinstance(raw_b64, str) and raw_b64, "publisher_payload_base64_required")
        require(isinstance(receipts, list) and receipts, "publisher_forward_receipts_required")
        try:
            raw = base64.b64decode(raw_b64, validate=True)
        except Exception as exc:
            raise ValueError("publisher_payload_base64_invalid") from exc
        require(sha_uri(raw) == request.get("payload_hash"), "publisher_payload_hash_mismatch")
        mid = safe_id(str(request["materialization_id"]))
        payload_path = runtime_root / PUBLISHER_PAYLOAD_DIR / f"{mid}.bin"
        receipts_path = runtime_root / PUBLISHER_PAYLOAD_DIR / f"{mid}.forward-receipts.json"
        hil._write_once(payload_path, raw)
        hil._write_once(receipts_path, json.dumps(receipts, sort_keys=True, indent=2).encode("utf-8") + b"\n")
        return dict(request), {
            "transport_origin": transport["origin"],
            "transport_authorization_id": transport["authorization_id"],
            "publisher_payload_sidecar_persisted": True,
            "publisher_forward_receipts_sidecar_persisted": True,
        }
    require(isinstance(payload, dict), "publisher_request_object_required")
    validate_publisher_request(payload)
    return dict(payload), {
        "transport_origin": transport["origin"],
        "transport_authorization_id": transport["authorization_id"],
        "publisher_payload_sidecar_persisted": False,
        "publisher_forward_receipts_sidecar_persisted": False,
    }

def _dispatch_publisher_consumer(*, runtime_root: Path, materialization_id: str) -> dict[str, Any]:
    command=[sys.executable,str(ROOT/"scripts/consume_publisher_intr_materialization_request.py"),"--runtime-root",str(runtime_root),"--materialization-id",materialization_id]
    process=subprocess.Popen(command,cwd=str(ROOT),env=publisher_scrubbed_env(),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    return {"consumer_dispatch_attempted":True,"consumer_pid":process.pid,"consumer_execution_authority":False,"consumer_claim_or_fence_minted_by_ingress":False,"authority_effect":"NONE_DISPATCH_ONLY"}

def admit_publisher(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = hil.validate_transport_headers(headers, body)
    try:
        payload=json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("publisher_request_json_invalid") from exc
    request, source = _publisher_request_from_payload(runtime_root=runtime_root, payload=payload, transport=transport)
    carrier = carrier_binding_evidence(request)
    carrier=carrier_binding_evidence(request)
    mid=safe_id(str(request["materialization_id"]))
    request_path=runtime_root/hil.REQUEST_DIR_REL/f"{mid}.json"
    hil._write_once(request_path,json.dumps(request,sort_keys=True,indent=2).encode("utf-8")+b"\n")
    receipt_path=runtime_root/PUBLISHER_RECEIPT_DIR/f"{mid}.json"
    if receipt_path.exists():
        existing=json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash")==request.get("request_hash") and existing.get("state")=="INGRESS_ADMITTED","write_once_collision")
        result_path=runtime_root/Path("receipts/sovereign-host/publisher-artifact-transfer")/f"{mid}.json"
        if result_path.is_file():
            result=json.loads(result_path.read_text(encoding="utf-8"))
            if result.get("state")=="RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED" and result.get("materialization_id")==mid and result.get("request_hash")==request.get("request_hash"):
                return {**existing,"dispatch":{"consumer_dispatch_attempted":False,"consumer_result_state":"ALREADY_RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED","consumer_execution_authority":False,"consumer_claim_or_fence_minted_by_ingress":False,"authority_effect":"NONE_DISPATCH_ONLY"}}
        dispatch=_dispatch_publisher_consumer(runtime_root=runtime_root,materialization_id=mid)
        return {**existing,"dispatch":dispatch}
    receipt={
        "schema":PUBLISHER_RECEIPT_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":mid,
        "request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],
        "payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],
        "transport_origin":source["transport_origin"],"transport_authorization_id":source["transport_authorization_id"],
        "exact_payload_sidecar_persisted":source["publisher_payload_sidecar_persisted"],
        "forward_receipt_chain_sidecar_persisted":source["publisher_forward_receipts_sidecar_persisted"],
        "runtime_execution_attempted":False,"claim_or_fence_minted":False,"credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",**carrier,"authority_effect":AUTHORITY_EFFECT,"admitted_at":now()
    }
    raw=json.dumps(receipt,sort_keys=True,indent=2).encode("utf-8")+b"\n"
    hil._write_once(receipt_path,raw)
    latest=runtime_root/PUBLISHER_LATEST; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_bytes(raw)
    dispatch=_dispatch_publisher_consumer(runtime_root=runtime_root,materialization_id=mid)
    return {**receipt,"dispatch":dispatch}


def _is_kv_publisher_return(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("destination") == KV_PUBLISHER_RETURN_DESTINATION and payload.get("downstream_owner_ref") == KV_PUBLISHER_RETURN_OWNER:
        return True
    if isinstance(payload, dict) and payload.get("schema") == KV_PUBLISHER_RETURN_TRIGGER_SCHEMA:
        request=payload.get("materialization_request")
        return isinstance(request,dict) and request.get("destination")==KV_PUBLISHER_RETURN_DESTINATION and request.get("downstream_owner_ref")==KV_PUBLISHER_RETURN_OWNER
    return False

def _dispatch_kv_publisher_return(*,runtime_root:Path,materialization_id:str)->dict[str,Any]:
    command=[sys.executable,str(ROOT/"scripts/consume_kv_publisher_return_materialization_request.py"),"--runtime-root",str(runtime_root),"--materialization-id",materialization_id]
    process=subprocess.Popen(command,cwd=str(ROOT),env=kv_publisher_return_scrubbed_env(),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    return {"consumer_dispatch_attempted":True,"consumer_pid":process.pid,"consumer_execution_authority":False,"consumer_claim_or_fence_minted_by_ingress":False,"authority_effect":"NONE_DISPATCH_ONLY"}

def admit_kv_publisher_return(*,runtime_root:Path,body:bytes,headers:Mapping[str,str])->dict[str,Any]:
    transport=hil.validate_transport_headers(headers,body)
    try: payload=json.loads(body.decode("utf-8"))
    except Exception as exc: raise ValueError("kv_publisher_return_json_invalid") from exc
    require(isinstance(payload,dict),"kv_publisher_return_object_required")
    if payload.get("schema")==KV_PUBLISHER_RETURN_TRIGGER_SCHEMA:
        require(payload.get("authority_effect")=="NONE_TRIGGER_ONLY","kv_publisher_return_trigger_authority_invalid")
        require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False,"kv_publisher_return_trigger_grant_forbidden")
        request=payload.get("materialization_request"); intent=payload.get("transport_intent"); receipts=payload.get("reverse_receipts"); raw_b64=payload.get("payload_base64")
        require(isinstance(request,dict) and isinstance(intent,dict) and isinstance(receipts,list) and receipts and isinstance(raw_b64,str) and raw_b64,"kv_publisher_return_trigger_content_missing")
        validate_kv_publisher_return_request(request)
        try: raw=base64.b64decode(raw_b64,validate=True)
        except Exception as exc: raise ValueError("kv_publisher_return_payload_base64_invalid") from exc
        require(sha_uri(raw)==request.get("payload_hash"),"kv_publisher_return_payload_hash_mismatch")
        require(sha_uri(intent)==request.get("transport_intent_hash"),"kv_publisher_return_intent_hash_mismatch")
    else:
        request=payload; validate_kv_publisher_return_request(request); intent=None; receipts=None; raw=None
    carrier=carrier_binding_evidence(request)
    mid=safe_id(str(request["materialization_id"]))
    request_path=runtime_root/hil.REQUEST_DIR_REL/f"{mid}.json"
    hil._write_once(request_path,json.dumps(request,sort_keys=True,indent=2).encode("utf-8")+b"\n")
    exact=False
    if raw is not None:
        payload_dir=runtime_root/KV_PUBLISHER_RETURN_PAYLOAD_DIR
        hil._write_once(payload_dir/f"{mid}.bin",raw)
        hil._write_once(payload_dir/f"{mid}.intent.json",json.dumps(intent,sort_keys=True,indent=2).encode("utf-8")+b"\n")
        hil._write_once(payload_dir/f"{mid}.receipts.json",json.dumps(receipts,sort_keys=True,indent=2).encode("utf-8")+b"\n")
        exact=True
    receipt_path=runtime_root/KV_PUBLISHER_RETURN_RECEIPT_DIR/f"{mid}.json"
    if receipt_path.exists():
        existing=json.loads(receipt_path.read_text(encoding="utf-8")); require(existing.get("request_hash")==request.get("request_hash") and existing.get("state")=="INGRESS_ADMITTED","write_once_collision"); return existing
    receipt={"schema":KV_PUBLISHER_RETURN_RECEIPT_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":mid,"request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],"payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],"transport_origin":transport["origin"],"transport_authorization_id":transport["authorization_id"],"exact_return_sidecars_persisted":exact,"runtime_execution_attempted":False,"claim_or_fence_minted":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE",**carrier,"authority_effect":AUTHORITY_EFFECT,"admitted_at":now()}
    raw_receipt=json.dumps(receipt,sort_keys=True,indent=2).encode("utf-8")+b"\n"; hil._write_once(receipt_path,raw_receipt)
    latest=runtime_root/KV_PUBLISHER_RETURN_LATEST; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_bytes(raw_receipt)
    dispatch=_dispatch_kv_publisher_return(runtime_root=runtime_root,materialization_id=mid)
    return {**receipt,"dispatch":dispatch}


def profile(tls_enabled: bool) -> dict[str, Any]:
    return {
        "schema": "stegverse.universal-intr-profiled-ingress/v1",
        "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
        "protocol": "InTr",
        "profile_path": PROFILE_PATH,
        "materialization_path": INGRESS_PATH,
        "device_kv_result_path": DEVICE_KV_RESULT_PATH,
        "profiles": ["HIL:Ingress", "SV002:PublicObservation", "KV:KnowledgeVaultInterlock", "Publisher:ArtifactTransfer", "KV:PublisherArtifactImport"],
        "heartbeat_derived_carrier": hb_intr_carrier_profile(),
        "supported_origins": [hil.ORIGIN_NODE, hil.ORIGIN_RELAY],
        "event_triggered": True,
        "always_on_application_receiver_required": False,
        "second_user_device_required": False,
        "g18_required": False,
        "tls_enabled": tls_enabled,
        "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }


class Handler(BaseHTTPRequestHandler):
    server: "Server"

    def log_message(self, _fmt: str, *_args: object) -> None:
        return

    def send_json(self, status: int, value: Mapping[str, Any]) -> None:
        raw = json.dumps(dict(value), sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != PROFILE_PATH:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": "NONE"})
            return
        self.send_json(200, profile(self.server.tls_enabled))

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {INGRESS_PATH, DEVICE_KV_RESULT_PATH}:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": AUTHORITY_EFFECT})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_json(411, {"state": "REJECTED", "reason": "content_length_invalid", "authority_effect": AUTHORITY_EFFECT})
            return
        if length < 0 or length > hil.MAX_REQUEST_BYTES:
            self.send_json(413, {"state": "REJECTED", "reason": "request_body_too_large", "authority_effect": AUTHORITY_EFFECT})
            return
        body = self.rfile.read(length)
        try:
            if self.path == DEVICE_KV_RESULT_PATH:
                receipt = retrieve_device_kv_query_result(runtime_root=self.server.runtime_root, body=body, headers=self.headers)
                status = 200
            else:
                payload = json.loads(body.decode("utf-8"))
                receipt = admit_kv_publisher_return(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_kv_publisher_return(payload) else (admit_publisher(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_publisher(payload) else (admit_device_kv(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_device_kv(payload) else (admit_sv002(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_sv002(payload) else hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers))))
                status = 202
        except Exception as exc:
            self.send_json(400, {"state": "REJECTED", "reason": str(exc), "authority_effect": AUTHORITY_EFFECT})
            return
        self.server.handled_requests += 1
        self.send_json(status, receipt)


class Server(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], runtime_root: Path, max_requests: int):
        super().__init__(address, Handler)
        self.runtime_root = runtime_root
        self.max_requests = max_requests
        self.handled_requests = 0
        self.tls_enabled = False


def serve(*, runtime_root: Path, bind_host: str, bind_port: int, max_requests: int, tls_cert: Path | None = None, tls_key: Path | None = None) -> tuple[str, int]:
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    server = Server((bind_host, bind_port), runtime, max_requests)
    if tls_cert or tls_key:
        require(tls_cert is not None and tls_key is not None, "tls_cert_and_key_required_together")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(tls_cert), str(tls_key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
        server.tls_enabled = True
    elif bind_host not in {"127.0.0.1", "::1", "localhost"}:
        server.server_close()
        raise ValueError("non_loopback_ingress_requires_tls")
    bound = server.server_address
    try:
        while not max_requests or server.handled_requests < max_requests:
            server.handle_request()
    finally:
        server.server_close()
    return str(bound[0]), int(bound[1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve shared profiled Universal InTr materialization ingress.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bind-host", default="127.0.0.1")
    parser.add_argument("--bind-port", type=int, default=0)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    args = parser.parse_args()
    host, port = serve(runtime_root=args.runtime_root, bind_host=args.bind_host, bind_port=args.bind_port, max_requests=args.max_requests, tls_cert=args.tls_cert, tls_key=args.tls_key)
    print(json.dumps({
        "schema": "stegverse.universal-intr-profiled-ingress-listener/v1",
        "state": "STOPPED_AFTER_BOUND",
        "bound_host": host,
        "bound_port": port,
        "profile_path": PROFILE_PATH,
        "materialization_path": INGRESS_PATH,
        "device_kv_result_path": DEVICE_KV_RESULT_PATH,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
