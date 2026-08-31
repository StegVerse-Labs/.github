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
import hashlib
import json
import os
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import serve_hil_intr_materialization_ingress as hil  # noqa: E402
from consume_device_kv_intr_materialization_request import (  # noqa: E402
    DESTINATION as DEVICE_KV_DESTINATION,
    DOWNSTREAM_OWNER as DEVICE_KV_OWNER,
    scrubbed_env as device_kv_scrubbed_env,
    validate_request as validate_device_kv_request,
)
from workers.sv002_intr_materialization_consumer import (  # noqa: E402
    DESTINATION as SV002_DESTINATION,
    DOWNSTREAM_OWNER as SV002_OWNER,
    scrubbed_env as sv002_scrubbed_env,
    validate_request as validate_sv002_request,
)

PROFILE_PATH = "/intr/profile"
INGRESS_PATH = "/intr/materialization"
SV002_RECEIPT_SCHEMA = "stegverse.sv002-intr-materialization-ingress/v1"
SV002_RECEIPT_DIR = Path("receipts/sovereign-network/sv002-intr-ingress")
SV002_LATEST = Path("receipts/sovereign-network/sv002-intr-ingress.latest.json")
DEVICE_KV_RECEIPT_SCHEMA = "stegverse.device-kv-intr-materialization-ingress/v1"
DEVICE_KV_RECEIPT_DIR = Path("receipts/sovereign-network/device-kv-intr-ingress")
DEVICE_KV_LATEST = Path("receipts/sovereign-network/device-kv-intr-ingress.latest.json")
PUBLISHER_RECEIPT_SCHEMA = "stegverse.publisher-intr-materialization-ingress/v1"
PUBLISHER_RECEIPT_DIR = Path("receipts/sovereign-network/publisher-intr-ingress")
PUBLISHER_LATEST = Path("receipts/sovereign-network/publisher-intr-ingress.latest.json")
PUBLISHER_PAYLOAD_DIR = Path("intr-payload/publisher")
PUBLISHER_DESTINATION = {"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"}
PUBLISHER_OWNER = "GCAT-BCAT-Engine/Publisher"
PUBLISHER_TRIGGER_SCHEMA = "stegos.node_publisher_intr_trigger.v1"
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
    request_path=runtime_root/hil.REQUEST_DIR_REL/f"{materialization_id}.json"; request_raw=json.dumps(request,sort_keys=True,indent=2).encode("utf-8")+b"\n"; hil._write_once(request_path,request_raw)
    receipt_path=runtime_root/DEVICE_KV_RECEIPT_DIR/f"{materialization_id}.json"
    if receipt_path.exists():
        existing=json.loads(receipt_path.read_text(encoding="utf-8")); require(existing.get("request_hash")==request.get("request_hash") and existing.get("state")=="INGRESS_ADMITTED","write_once_collision"); return existing
    receipt={"schema":DEVICE_KV_RECEIPT_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":materialization_id,"request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],"payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],"transport_origin":source["transport_origin"],"transport_authorization_id":source["transport_authorization_id"],"node_id":source["node_id"],"interlock_id":source["interlock_id"],"outbox_entry_hash":source["outbox_entry_hash"],"transport_payload_sha256":transport["payload_sha256"],"queue_ref":str(request_path),"exact_request_validated":True,"write_once_persisted":True,"runtime_execution_attempted":False,"consumer_dispatch_attempted":False,"claim_or_fence_minted":False,"g18_required":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":AUTHORITY_EFFECT,"admitted_at":now()}
    raw=json.dumps(receipt,sort_keys=True,indent=2).encode("utf-8")+b"\n"; hil._write_once(receipt_path,raw); latest=runtime_root/DEVICE_KV_LATEST; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_bytes(raw)
    dispatch=_dispatch_device_kv_consumer(runtime_root=runtime_root,materialization_id=materialization_id)
    return {**receipt,"dispatch":dispatch}



def _validate_publisher_materialization_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema":"stegverse.universal-intr-materialization-request/v1",
        "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema":"stegverse.universal-intr-transport/v1",
        "transport_protocol":"InTr",
        "destination":PUBLISHER_DESTINATION,
        "downstream_owner_ref":PUBLISHER_OWNER,
        "event_triggered":True,
        "always_on_receiver_required":False,
        "second_user_device_required":False,
        "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed":True,
        "blind_consequence_retry_allowed":False,
        "interlock_required":True,
        "request_grants_execution_authority":False,
        "claim_or_fence_minted":False,
        "transport_grants_execution_authority":False,
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "authority_transfer":False,
        "authority_effect":"NONE_REQUEST_ONLY",
    }
    for key,value in expected.items():
        require(request.get(key)==value,"publisher_materialization_"+key+"_mismatch")
    require(request.get("boundary_path")==["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"],"publisher_materialization_boundary_path_invalid")
    mid=str(request.get("materialization_id") or "")
    safe_id(mid)
    for key in ("request_hash","transport_intent_hash","payload_hash"):
        require(isinstance(request.get(key),str) and len(request[key])==71 and request[key].startswith("sha256:"),"publisher_"+key+"_invalid")
    body=dict(request); claimed=body.pop("request_hash",None)
    require(claimed==sha_uri(body),"publisher_materialization_request_hash_mismatch")

def _validate_publisher_intent(intent: Mapping[str, Any], request: Mapping[str, Any], payload: bytes) -> None:
    require(intent.get("schema")=="stegverse.universal-intr-transport/v1","publisher_intent_schema_invalid")
    require(intent.get("protocol")=="InTr","publisher_intent_protocol_invalid")
    require(intent.get("operation_id")==request.get("operation_id"),"publisher_intent_operation_id_mismatch")
    require(intent.get("packet_id")==request.get("packet_id"),"publisher_intent_packet_id_mismatch")
    require(intent.get("payload_hash")==request.get("payload_hash"),"publisher_intent_payload_hash_mismatch")
    require(intent.get("source")=={"boundary":"KV","subsystem":"KnowledgeVault:DocumentExport"},"publisher_intent_source_invalid")
    require(intent.get("destination")==PUBLISHER_DESTINATION,"publisher_intent_destination_invalid")
    require(intent.get("boundary_path")==["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"],"publisher_intent_boundary_path_invalid")
    semantics=intent.get("transport_semantics") or {}
    require(semantics.get("event_triggered") is True and semantics.get("always_on_receiver_required") is False and semantics.get("second_user_device_required") is False,"publisher_intent_availability_invalid")
    authority=intent.get("authority") or {}
    require(authority.get("authority_transfer") is False and authority.get("transport_grants_execution_authority") is False and authority.get("credential_authority")=="TV/TVC","publisher_intent_authority_invalid")
    require(sha_uri(intent)==request.get("transport_intent_hash"),"publisher_transport_intent_hash_mismatch")
    require("sha256:"+hashlib.sha256(payload).hexdigest()==request.get("payload_hash"),"publisher_exact_payload_hash_mismatch")

def _is_publisher(payload: Any) -> bool:
    return isinstance(payload,dict) and payload.get("schema")==PUBLISHER_TRIGGER_SCHEMA

def _publisher_trigger(payload: Any) -> tuple[dict[str,Any],dict[str,Any],bytes,dict[str,Any]]:
    require(isinstance(payload,dict) and payload.get("schema")==PUBLISHER_TRIGGER_SCHEMA,"publisher_trigger_schema_invalid")
    require(payload.get("transport_origin")==hil.ORIGIN_NODE,"publisher_trigger_origin_invalid")
    require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False,"publisher_trigger_authority_forbidden")
    require(payload.get("credential_authority")=="TV/TVC" and payload.get("github_token_runtime_authority")=="NONE" and payload.get("authority_effect")=="NONE_TRIGGER_ONLY","publisher_trigger_credential_boundary_invalid")
    request=payload.get("materialization_request"); intent=payload.get("transport_intent")
    require(isinstance(request,dict) and isinstance(intent,dict),"publisher_trigger_transport_objects_required")
    _validate_publisher_materialization_request(request)
    node_id=str(payload.get("node_id") or ""); interlock_id=str(payload.get("interlock_id") or "")
    require(node_id.startswith("SV-NODE-") and interlock_id.startswith("SV-IL-"),"publisher_trigger_node_binding_invalid")
    encoded=payload.get("exact_payload_base64")
    require(isinstance(encoded,str) and encoded,"publisher_exact_payload_required")
    import base64
    try: exact=base64.b64decode(encoded,validate=True)
    except Exception as exc: raise ValueError("publisher_exact_payload_base64_invalid") from exc
    _validate_publisher_intent(intent,request,exact)
    body=dict(payload); claimed=body.pop("trigger_sha256",None)
    require(claimed==sha_uri(body),"publisher_trigger_hash_mismatch")
    return dict(request),dict(intent),exact,{"node_id":node_id,"interlock_id":interlock_id,"trigger_sha256":claimed}

def _dispatch_publisher_consumer(*,runtime_root:Path,materialization_id:str) -> dict[str,Any]:
    env={k:v for k,v in os.environ.items() if k not in {"GITHUB_TOKEN","GH_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN","GITHUB_ACTIONS","RENDER","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS"}}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"; env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    command=[sys.executable,str(ROOT/"scripts/consume_publisher_intr_materialization_request.py"),"--source-root",str(ROOT),"--runtime-root",str(runtime_root),"--materialization-id",materialization_id]
    completed=subprocess.run(command,cwd=str(ROOT),env=env,capture_output=True,text=True,check=False,timeout=300)
    result=None
    for line in reversed([x.strip() for x in completed.stdout.splitlines() if x.strip()]):
        try:
            candidate=json.loads(line)
            if isinstance(candidate,dict): result=candidate; break
        except Exception: pass
    return {"consumer_dispatch_attempted":True,"consumer_returncode":completed.returncode,"consumer_result":result,"consumer_execution_authority":False,"consumer_claim_or_fence_minted_by_ingress":False,"authority_effect":"NONE_DISPATCH_ONLY"}

def admit_publisher(*,runtime_root:Path,body:bytes,headers:Mapping[str,str]) -> dict[str,Any]:
    transport=hil.validate_transport_headers(headers,body)
    require(transport["origin"]==hil.ORIGIN_NODE,"publisher_materialization_requires_node_origin")
    try: payload=json.loads(body.decode("utf-8"))
    except Exception as exc: raise ValueError("publisher_trigger_json_invalid") from exc
    request,intent,exact,source=_publisher_trigger(payload)
    mid=safe_id(str(request["materialization_id"]))
    request_path=runtime_root/hil.REQUEST_DIR_REL/f"{mid}.json"
    payload_path=runtime_root/PUBLISHER_PAYLOAD_DIR/f"{mid}.bin"
    hil._write_once(request_path,json.dumps(request,sort_keys=True,indent=2).encode()+b"\n")
    hil._write_once(payload_path,exact)
    receipt_path=runtime_root/PUBLISHER_RECEIPT_DIR/f"{mid}.json"
    base_receipt={
      "schema":PUBLISHER_RECEIPT_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":mid,
      "request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],
      "payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],
      "node_id":source["node_id"],"interlock_id":source["interlock_id"],"trigger_sha256":source["trigger_sha256"],
      "transport_payload_sha256":transport["payload_sha256"],"queue_ref":str(request_path),"payload_ref":str(payload_path),
      "exact_request_validated":True,"exact_payload_materialized":True,"write_once_persisted":True,
      "runtime_execution_attempted":False,"return_staged":False,"claim_or_fence_minted":False,
      "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":AUTHORITY_EFFECT,
    }
    if receipt_path.exists():
        existing=json.loads(receipt_path.read_text(encoding="utf-8"))
        for key in ("materialization_id","request_hash","transport_intent_hash","payload_hash","node_id","interlock_id","trigger_sha256"):
            require(existing.get(key)==base_receipt.get(key),"publisher_ingress_write_once_collision:"+key)
        return_meta=runtime_root/"intr-return/publisher"/f"{mid}.json"
        if return_meta.is_file():
            return {**existing,"dispatch":{"consumer_dispatch_attempted":False,"consumer_result":{"state":"ALREADY_STAGED"},"consumer_execution_authority":False,"consumer_claim_or_fence_minted_by_ingress":False,"authority_effect":"NONE_DISPATCH_ONLY"}}
        dispatch=_dispatch_publisher_consumer(runtime_root=runtime_root,materialization_id=mid)
        return {**existing,"dispatch":dispatch}
    receipt={**base_receipt,"admitted_at":now()}
    raw=json.dumps(receipt,sort_keys=True,indent=2).encode()+b"\n"; hil._write_once(receipt_path,raw)
    latest=runtime_root/PUBLISHER_LATEST; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_bytes(raw)
    dispatch=_dispatch_publisher_consumer(runtime_root=runtime_root,materialization_id=mid)
    return {**receipt,"dispatch":dispatch}

def profile(tls_enabled: bool) -> dict[str, Any]:
    return {
        "schema": "stegverse.universal-intr-profiled-ingress/v1",
        "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
        "protocol": "InTr",
        "profile_path": PROFILE_PATH,
        "materialization_path": INGRESS_PATH,
        "profiles": ["HIL:Ingress", "SV002:PublicObservation", "KV:KnowledgeVaultInterlock", "Publisher:Ingress"],
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
        if self.path != INGRESS_PATH:
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
            payload = json.loads(body.decode("utf-8"))
            receipt = admit_publisher(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_publisher(payload) else (admit_device_kv(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_device_kv(payload) else (admit_sv002(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_sv002(payload) else hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)))
        except Exception as exc:
            self.send_json(400, {"state": "REJECTED", "reason": str(exc), "authority_effect": AUTHORITY_EFFECT})
            return
        self.server.handled_requests += 1
        self.send_json(202, receipt)


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
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
