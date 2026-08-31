#!/usr/bin/env python3
"""Build and dispatch one canonical KV -> SKAP Vault InTr custody event.

This is the organization transport egress side of kv-skap-custody. It consumes
an already-sealed capsule and an already-issued DEVICE->KV Interlock receipt,
builds the canonical StegOS transport/materialization request, attaches the
non-authorizing HB-derived carrier binding, and invokes the shared profiled
ingress event-ephemerally. TVC remains the admission/custody authority.
"""
from __future__ import annotations

import argparse
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
PROFILE_ID = "kv-skap-custody"
PROFILE_REGISTRY_REL = Path("specs/universal-intr-connector-profiles.v1.json")
TRANSPORT_REL = Path("stegos/universal_intr_transport.py")
MATERIALIZATION_REL = Path("stegos/universal_intr_materialization.py")
EGRESS_DIR_REL = Path("receipts/sovereign-network/kv-skap-custody-egress")
LATEST_REL = Path("receipts/sovereign-network/kv-skap-custody-egress.latest.json")


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
        "materialization_extension_fields": ["sealed_capsule", "device_kv_receipt"],
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise KVSkapDispatchError("canonical_profile_mismatch:" + key)
    return profile


def build_request(*, stegos_root: Path, capsule: dict[str, Any], device_kv_receipt: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile(stegos_root)
    if capsule.get("schema") != CAPSULE_SCHEMA:
        raise KVSkapDispatchError("sealed_capsule_schema_invalid")
    ingress_id = str(capsule.get("ingress_id") or "")
    if not ingress_id:
        raise KVSkapDispatchError("sealed_capsule_ingress_id_required")
    if not isinstance(device_kv_receipt, dict) or device_kv_receipt.get("schema") != "stegverse.intr.boundary_transition_receipt/v1":
        raise KVSkapDispatchError("device_kv_receipt_invalid")

    root_text = str(stegos_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    transport = importlib.import_module("stegos.universal_intr_transport")
    materialization = importlib.import_module("stegos.universal_intr_materialization")
    for module, rel in ((transport, TRANSPORT_REL), (materialization, MATERIALIZATION_REL)):
        module_file = Path(str(getattr(module, "__file__", ""))).resolve()
        if module_file != (stegos_root / rel).resolve():
            raise KVSkapDispatchError("canonical_stegos_module_root_mismatch:" + rel.as_posix())
    payload_hash = sha_uri(capsule)
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
        payload_ref="inline://materialization_request.sealed_capsule",
        downstream_owner_ref=profile["downstream_owner_ref"],
    )
    body = dict(base)
    body.pop("request_hash", None)
    body["sealed_capsule"] = capsule
    body["device_kv_receipt"] = device_kv_receipt
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
    capsule: dict[str, Any],
    device_kv_receipt: dict[str, Any],
    authorization_id: str,
) -> dict[str, Any]:
    if not authorization_id:
        raise KVSkapDispatchError("tvc_relay_authorization_id_required")
    request = build_request(stegos_root=stegos_root, capsule=capsule, device_kv_receipt=device_kv_receipt)
    raw = canonical(request)
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
        "X-StegVerse-Authorization-Id": authorization_id,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
    }
    admitted = admit_kv_skap(runtime_root=runtime_root.expanduser().resolve(), body=raw, headers=headers)
    if admitted.get("state") != "INGRESS_ADMITTED":
        raise KVSkapDispatchError("kv_skap_ingress_not_admitted")
    receipt_body = {
        "schema": "stegverse.kv-skap-custody-egress-dispatch/v1",
        "state": "DISPATCHED_TO_PROFILED_INGRESS",
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "device_kv_receipt_hash": device_kv_receipt["receipt_hash"],
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
    parser.add_argument("--sealed-capsule", type=Path, required=True)
    parser.add_argument("--device-kv-receipt", type=Path, required=True)
    parser.add_argument("--authorization-id")
    args = parser.parse_args()
    stegos_root = (args.stegos_root or (Path(os.environ[STEGOS_ROOT_ENV]) if os.environ.get(STEGOS_ROOT_ENV) else None))
    if stegos_root is None:
        print(json.dumps({"state": "BLOCKED", "reason": "STEGVERSE_STEGOS_ROOT_required", "authority_effect": "NONE"}, sort_keys=True))
        return 1
    authorization_id = args.authorization_id or os.environ.get(TVC_AUTHORIZATION_ID_ENV, "")
    try:
        result = dispatch(
            runtime_root=args.runtime_root,
            stegos_root=stegos_root.expanduser().resolve(),
            capsule=load_json(args.sealed_capsule),
            device_kv_receipt=load_json(args.device_kv_receipt),
            authorization_id=authorization_id,
        )
    except Exception as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc), "authority_effect": "NONE"}, sort_keys=True))
        return 1
    print(json.dumps(result["egress_receipt"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
