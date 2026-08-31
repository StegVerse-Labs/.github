#!/usr/bin/env python3
"""Build and dispatch one exact-byte KV -> SKAP Vault InTr custody event.

Inputs are the original staged browser packet bytes and the Gateway STAGED_FOR_TVC
receipt. The dispatcher validates their binding, constructs the canonical
StegOS kv-skap-custody request, attaches the non-authorizing HB carrier binding,
and invokes the shared profiled ingress event-ephemerally.

Transport grants no credential, execution, routing, transition, receiving, or
provider authority. TV/TVC remains the credential and SKAP custody authority.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.intr_carrier_profile import build_carrier_binding
from workers.universal_intr_profiled_ingress import admit_kv_skap

STEGOS_ROOT_ENV = "STEGVERSE_STEGOS_ROOT"
TVC_AUTHORIZATION_ID_ENV = "STEGVERSE_TVC_RELAY_AUTHORIZATION_ID"
CAPSULE_SCHEMA = "stegverse.skap.browser_ingress/p256-ecdh-hkdf-sha256-aes256gcm/v1"
STAGE_SCHEMA = "stegverse.service_gateway.coinbase_skap_stage_receipt/v1"
BOUNDARY_RECEIPT_SCHEMA = "stegverse.intr.boundary_transition_receipt/v1"
PROFILE_ID = "kv-skap-custody"
PROFILE_REGISTRY_REL = Path("specs/universal-intr-connector-profiles.v1.json")
TRANSPORT_REL = Path("stegos/universal_intr_transport.py")
MATERIALIZATION_REL = Path("stegos/universal_intr_materialization.py")
EGRESS_DIR_REL = Path("receipts/sovereign-network/kv-skap-custody-egress")
LATEST_REL = Path("receipts/sovereign-network/kv-skap-custody-egress.latest.json")
MAX_PACKET_BYTES = 64 * 1024


class KVSkapDispatchError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise KVSkapDispatchError("object_required:" + str(path))
    return value


def load_packet(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_PACKET_BYTES:
        raise KVSkapDispatchError("sealed_capsule_raw_size_invalid")
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise KVSkapDispatchError("sealed_capsule_raw_json_invalid") from exc
    if not isinstance(value, dict) or value.get("schema") != CAPSULE_SCHEMA:
        raise KVSkapDispatchError("sealed_capsule_schema_invalid")
    return raw, value


def validate_stage_binding(*, stage_receipt: dict[str, Any], raw_packet: bytes, capsule: dict[str, Any]) -> dict[str, Any]:
    if stage_receipt.get("schema") != STAGE_SCHEMA or stage_receipt.get("decision") != "STAGED_FOR_TVC":
        raise KVSkapDispatchError("stage_receipt_state_invalid")
    if stage_receipt.get("credential_authority") != "TV/TVC":
        raise KVSkapDispatchError("stage_receipt_credential_authority_invalid")
    if stage_receipt.get("next_required_transition") != "KV_SKAP_VAULT_INTERLOCK_ADMISSION":
        raise KVSkapDispatchError("stage_receipt_next_transition_invalid")
    body = {k: v for k, v in stage_receipt.items() if k != "receipt_digest"}
    if stage_receipt.get("receipt_digest") != sha_uri(body):
        raise KVSkapDispatchError("stage_receipt_digest_invalid")
    if stage_receipt.get("raw_body_digest") != sha_uri(raw_packet):
        raise KVSkapDispatchError("stage_raw_body_digest_mismatch")
    if stage_receipt.get("browser_ingress_digest") != sha_uri(capsule):
        raise KVSkapDispatchError("stage_browser_ingress_digest_mismatch")
    if stage_receipt.get("ingress_id") != capsule.get("ingress_id"):
        raise KVSkapDispatchError("stage_ingress_id_mismatch")
    device_kv = stage_receipt.get("device_kv_interlock_receipt")
    if not isinstance(device_kv, dict) or device_kv.get("schema") != BOUNDARY_RECEIPT_SCHEMA:
        raise KVSkapDispatchError("device_kv_receipt_invalid")
    if device_kv.get("from_boundary") != "DEVICE" or device_kv.get("to_boundary") != "KV" or device_kv.get("connector") != "InTr":
        raise KVSkapDispatchError("device_kv_boundary_invalid")
    if device_kv.get("credential_ref") != capsule.get("credential_ref") or device_kv.get("operation_id") != capsule.get("ingress_id"):
        raise KVSkapDispatchError("device_kv_capsule_binding_mismatch")
    if device_kv.get("raw_body_digest") != sha_uri(raw_packet) or device_kv.get("browser_ingress_digest") != sha_uri(capsule):
        raise KVSkapDispatchError("device_kv_exact_packet_binding_mismatch")
    return device_kv


def load_profile(stegos_root: Path) -> dict[str, Any]:
    registry = load_json(stegos_root / PROFILE_REGISTRY_REL)
    profiles = [p for p in registry.get("profiles", []) if isinstance(p, dict) and p.get("profile_id") == PROFILE_ID]
    if len(profiles) != 1:
        raise KVSkapDispatchError("canonical_kv_skap_profile_missing_or_ambiguous")
    profile = profiles[0]
    expected = {
        "request_class": "KV_SKAP_CIPHERTEXT_CUSTODY",
        "payload_schema": CAPSULE_SCHEMA,
        "operations": ["ADMIT_CIPHERTEXT"],
        "source": {"boundary": "KV", "subsystem": "KnowledgeVault:SKAPClient"},
        "destination": {"boundary": "SKAP_VAULT", "subsystem": "SKAP:Vault"},
        "downstream_owner_ref": "StegVerse-Labs/TVC",
        "custody_mode": "EXACT_BYTES",
        "authorization_required": True,
        "authority_effect": "NONE",
        "materialization_extension_fields": [
            "sealed_capsule",
            "sealed_capsule_raw_b64",
            "device_kv_receipt",
            "stage_receipt_digest",
        ],
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise KVSkapDispatchError("canonical_profile_mismatch:" + key)
    return profile


def build_request(
    *,
    stegos_root: Path,
    raw_packet: bytes,
    capsule: dict[str, Any],
    stage_receipt: dict[str, Any],
) -> dict[str, Any]:
    profile = load_profile(stegos_root)
    device_kv_receipt = validate_stage_binding(stage_receipt=stage_receipt, raw_packet=raw_packet, capsule=capsule)
    ingress_id = str(capsule.get("ingress_id") or "")
    if not ingress_id:
        raise KVSkapDispatchError("sealed_capsule_ingress_id_required")

    root_text = str(stegos_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    transport = importlib.import_module("stegos.universal_intr_transport")
    materialization = importlib.import_module("stegos.universal_intr_materialization")
    for module, rel in ((transport, TRANSPORT_REL), (materialization, MATERIALIZATION_REL)):
        module_file = Path(str(getattr(module, "__file__", ""))).resolve()
        if module_file != (stegos_root / rel).resolve():
            raise KVSkapDispatchError("canonical_stegos_module_root_mismatch:" + rel.as_posix())

    payload_hash = sha_uri(raw_packet)
    intent = transport.build_transport_intent(
        operation_id=ingress_id,
        payload_hash=payload_hash,
        source_boundary=profile["source"]["boundary"],
        source_subsystem=profile["source"]["subsystem"],
        destination_boundary=profile["destination"]["boundary"],
        destination_subsystem=profile["destination"]["subsystem"],
        prior_transport_receipt_hash=device_kv_receipt.get("receipt_hash"),
    )
    base = materialization.build_materialization_request(
        intent,
        payload_ref="inline://materialization_request.sealed_capsule_raw_b64",
        downstream_owner_ref=profile["downstream_owner_ref"],
    )
    body = dict(base)
    body.pop("request_hash", None)
    body["sealed_capsule"] = capsule
    body["sealed_capsule_raw_b64"] = base64.b64encode(raw_packet).decode("ascii")
    body["device_kv_receipt"] = device_kv_receipt
    body["stage_receipt_digest"] = stage_receipt["receipt_digest"]
    body["carrier_binding"] = build_carrier_binding(
        packet_id=body["packet_id"],
        payload_hash=body["payload_hash"],
        sampled_unix_ms=int(time.time() * 1000),
    )
    return {**body, "request_hash": sha_uri(body)}


def dispatch(
    *,
    runtime_root: Path,
    stegos_root: Path,
    raw_packet: bytes,
    capsule: dict[str, Any],
    stage_receipt: dict[str, Any],
    authorization_id: str,
) -> dict[str, Any]:
    if not authorization_id:
        raise KVSkapDispatchError("tvc_relay_authorization_id_required")
    request = build_request(
        stegos_root=stegos_root,
        raw_packet=raw_packet,
        capsule=capsule,
        stage_receipt=stage_receipt,
    )
    request_bytes = canonical(request)
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
        "X-StegVerse-Authorization-Id": authorization_id,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(request_bytes).hexdigest(),
    }
    admitted = admit_kv_skap(runtime_root=runtime_root.expanduser().resolve(), body=request_bytes, headers=headers)
    if admitted.get("state") != "INGRESS_ADMITTED":
        raise KVSkapDispatchError("kv_skap_ingress_not_admitted")
    receipt_body = {
        "schema": "stegverse.kv-skap-custody-egress-dispatch/v1",
        "state": "DISPATCHED_TO_PROFILED_INGRESS",
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "raw_body_digest": sha_uri(raw_packet),
        "stage_receipt_digest": stage_receipt["receipt_digest"],
        "device_kv_receipt_hash": request["device_kv_receipt"]["receipt_hash"],
        "carrier_binding_sha256": request["carrier_binding"]["binding_sha256"],
        "ingress_receipt_state": admitted["state"],
        "ingress_authority_effect": admitted["authority_effect"],
        "consumer_dispatch_attempted": bool((admitted.get("dispatch") or {}).get("consumer_dispatch_attempted")),
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "transport_grants_execution_authority": False,
        "authority_effect": "NONE_TRANSPORT_DISPATCH_ONLY",
    }
    receipt = {**receipt_body, "receipt_hash": sha_uri(receipt_body)}
    target = runtime_root.expanduser().resolve() / EGRESS_DIR_REL / f"{request['materialization_id']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != serialized:
        raise KVSkapDispatchError("kv_skap_egress_receipt_collision")
    target.write_text(serialized, encoding="utf-8")
    latest = runtime_root.expanduser().resolve() / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(serialized, encoding="utf-8")
    return {"request": request, "ingress": admitted, "egress_receipt": receipt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--stegos-root", type=Path)
    parser.add_argument("--sealed-capsule", type=Path, required=True, help="Original staged browser packet bytes")
    parser.add_argument("--stage-receipt", type=Path, required=True)
    parser.add_argument("--authorization-id")
    args = parser.parse_args()
    stegos_root = args.stegos_root or (Path(os.environ[STEGOS_ROOT_ENV]) if os.environ.get(STEGOS_ROOT_ENV) else None)
    if stegos_root is None:
        print(json.dumps({"state": "BLOCKED", "reason": "STEGVERSE_STEGOS_ROOT_required", "authority_effect": "NONE"}, sort_keys=True))
        return 1
    authorization_id = args.authorization_id or os.environ.get(TVC_AUTHORIZATION_ID_ENV, "")
    try:
        raw_packet, capsule = load_packet(args.sealed_capsule)
        result = dispatch(
            runtime_root=args.runtime_root,
            stegos_root=stegos_root.expanduser().resolve(),
            raw_packet=raw_packet,
            capsule=capsule,
            stage_receipt=load_json(args.stage_receipt),
            authorization_id=authorization_id,
        )
    except Exception as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc), "authority_effect": "NONE"}, sort_keys=True))
        return 1
    print(json.dumps(result["egress_receipt"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
