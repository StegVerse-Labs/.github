#!/usr/bin/env python3
"""Consume admitted exact-byte KV -> SKAP Vault Universal InTr custody requests.

The .github organization boundary owns transport admission/dispatch only.
TVC remains the double-Interlock and credential/custody authority. Original
browser packet bytes are preserved exactly through the second hop.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_DIR_REL = Path("receipts/sovereign-network/kv-skap-custody-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/kv-skap-custody")
LATEST_REL = Path("receipts/sovereign-host/kv-skap-custody-consumption.latest.json")
DESTINATION = {"boundary": "SKAP_VAULT", "subsystem": "SKAP:Vault"}
SOURCE = {"boundary": "KV", "subsystem": "KnowledgeVault:SKAPClient"}
DOWNSTREAM_OWNER = "StegVerse-Labs/TVC"
CAPSULE_SCHEMA = "stegverse.skap.browser_ingress/p256-ecdh-hkdf-sha256-aes256gcm/v1"
BOUNDARY_RECEIPT_SCHEMA = "stegverse.intr.boundary_transition_receipt/v1"
TVC_ROOT_ENV = "STEGVERSE_TVC_ROOT"
KV_ROOT_ENV = "STEGVERSE_KV_ROOT"
MAX_PACKET_BYTES = 64 * 1024
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "STEGVERSE_GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")


class KVSkapMaterializationError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise KVSkapMaterializationError("object_required")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def scrubbed_env(env: dict[str, str] | None = None) -> dict[str, str]:
    child = dict(os.environ if env is None else env)
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def _require_sha(value: Any, reason: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise KVSkapMaterializationError(reason)
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise KVSkapMaterializationError(reason) from exc
    return value


def decode_raw_packet(request: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    encoded = request.get("sealed_capsule_raw_b64")
    if not isinstance(encoded, str) or not encoded:
        raise KVSkapMaterializationError("sealed_capsule_raw_b64_required")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise KVSkapMaterializationError("sealed_capsule_raw_b64_invalid") from exc
    if not raw or len(raw) > MAX_PACKET_BYTES:
        raise KVSkapMaterializationError("sealed_capsule_raw_size_invalid")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise KVSkapMaterializationError("sealed_capsule_raw_json_invalid") from exc
    if not isinstance(parsed, dict) or parsed.get("schema") != CAPSULE_SCHEMA:
        raise KVSkapMaterializationError("sealed_capsule_raw_schema_invalid")
    supplied = request.get("sealed_capsule")
    if not isinstance(supplied, dict) or supplied.get("schema") != CAPSULE_SCHEMA:
        raise KVSkapMaterializationError("sealed_capsule_invalid")
    if canonical(parsed) != canonical(supplied):
        raise KVSkapMaterializationError("sealed_capsule_raw_semantic_mismatch")
    return raw, parsed


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
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
        if request.get(key) != value:
            raise KVSkapMaterializationError("materialization_" + key + "_mismatch")
    if request.get("boundary_path") != ["KV", "SKAP_VAULT"]:
        raise KVSkapMaterializationError("boundary_path_invalid")
    for key in ("materialization_id", "operation_id", "packet_id", "payload_ref"):
        if not isinstance(request.get(key), str) or not request[key]:
            raise KVSkapMaterializationError(key + "_required")
    for key in ("transport_intent_hash", "payload_hash", "request_hash", "stage_receipt_digest"):
        _require_sha(request.get(key), key + "_invalid")
    if request.get("payload_ref") != "inline://materialization_request.sealed_capsule_raw_b64":
        raise KVSkapMaterializationError("payload_ref_invalid")
    raw, capsule = decode_raw_packet(request)
    if request.get("payload_hash") != sha_uri(raw):
        raise KVSkapMaterializationError("sealed_capsule_raw_payload_hash_mismatch")
    first_receipt = request.get("device_kv_receipt")
    if not isinstance(first_receipt, dict) or first_receipt.get("schema") != BOUNDARY_RECEIPT_SCHEMA:
        raise KVSkapMaterializationError("device_kv_receipt_required")
    if first_receipt.get("connector") != "InTr" or first_receipt.get("from_boundary") != "DEVICE" or first_receipt.get("to_boundary") != "KV":
        raise KVSkapMaterializationError("device_kv_receipt_boundary_invalid")
    if first_receipt.get("credential_ref") != capsule.get("credential_ref"):
        raise KVSkapMaterializationError("device_kv_credential_ref_mismatch")
    if first_receipt.get("operation_id") != request.get("operation_id") or request.get("operation_id") != capsule.get("ingress_id"):
        raise KVSkapMaterializationError("device_kv_operation_binding_mismatch")
    if first_receipt.get("raw_body_digest") != sha_uri(raw):
        raise KVSkapMaterializationError("device_kv_raw_body_digest_mismatch")
    body = dict(request)
    claimed = body.pop("request_hash")
    if claimed != sha_uri(body):
        raise KVSkapMaterializationError("request_hash_mismatch")


def _load_tvc(tvc_root: Path):
    tvc = tvc_root.expanduser().resolve()
    required = (
        tvc / "tools" / "skap_vault_interlock_gate.py",
        tvc / "tools" / "skap_vault_store.py",
        tvc / "tools" / "validate_coinbase_browser_skap_admission.py",
    )
    if not all(path.is_file() for path in required):
        raise KVSkapMaterializationError("current_tvc_skap_source_missing")
    if str(tvc) not in sys.path:
        sys.path.insert(0, str(tvc))
    from tools.skap_vault_interlock_gate import (
        digest as gate_digest,
        validate_double_interlock,
        validate_receipt as validate_boundary_receipt,
    )
    from tools.skap_vault_store import persist_coinbase_ciphertext
    from tools.validate_coinbase_browser_skap_admission import (
        CUSTODY_FORMAT,
        build_transition_receipt,
        digest,
        validate_browser_packet,
    )
    return (
        gate_digest,
        validate_double_interlock,
        validate_boundary_receipt,
        persist_coinbase_ciphertext,
        CUSTODY_FORMAT,
        build_transition_receipt,
        digest,
        validate_browser_packet,
    )


def consume_one(source_root: Path, runtime_root: Path, materialization_id: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_DIR_REL / f"{materialization_id}.json"
    ingress_path = runtime / INGRESS_DIR_REL / f"{materialization_id}.json"
    if not request_path.is_file() or not ingress_path.is_file():
        raise KVSkapMaterializationError("admitted_kv_skap_materialization_missing")
    request = load(request_path)
    ingress = load(ingress_path)
    validate_request(request)
    if ingress.get("state") != "INGRESS_ADMITTED" or ingress.get("request_hash") != request["request_hash"]:
        raise KVSkapMaterializationError("kv_skap_ingress_receipt_binding_invalid")
    safe = scrubbed_env(env)
    tvc_value = safe.get(TVC_ROOT_ENV)
    kv_value = safe.get(KV_ROOT_ENV)
    if not tvc_value:
        raise KVSkapMaterializationError("STEGVERSE_TVC_ROOT_required")
    if not kv_value:
        raise KVSkapMaterializationError("STEGVERSE_KV_ROOT_required")
    kv_root = Path(kv_value).expanduser().resolve()
    kv_root.mkdir(parents=True, exist_ok=True)

    (
        gate_digest,
        validate_double_interlock,
        validate_boundary_receipt,
        persist_ciphertext,
        custody_format,
        build_transition,
        packet_digest,
        validate_packet,
    ) = _load_tvc(Path(tvc_value))

    raw_packet, capsule = decode_raw_packet(request)
    findings = validate_packet(capsule)
    if findings:
        raise KVSkapMaterializationError("sealed_capsule_denied:" + ",".join(findings))

    device_kv = request["device_kv_receipt"]
    try:
        validate_boundary_receipt(device_kv, expected_from="DEVICE", expected_to="KV")
    except Exception as exc:
        raise KVSkapMaterializationError("device_kv_receipt_invalid:" + str(exc)) from exc
    if device_kv.get("browser_ingress_digest") != packet_digest(capsule):
        raise KVSkapMaterializationError("device_kv_browser_ingress_digest_mismatch")
    if device_kv.get("raw_body_digest") != sha_uri(raw_packet):
        raise KVSkapMaterializationError("device_kv_raw_body_digest_mismatch")

    credential_ref = str(capsule.get("credential_ref") or "")
    operation_id = str(request["operation_id"])
    if not credential_ref:
        raise KVSkapMaterializationError("credential_ref_required")
    if operation_id != str(capsule.get("ingress_id") or ""):
        raise KVSkapMaterializationError("operation_ingress_binding_mismatch")

    kv_skap_body = {
        "schema": BOUNDARY_RECEIPT_SCHEMA,
        "connector": "InTr",
        "from_boundary": "KV",
        "to_boundary": "SKAP_VAULT",
        "credential_ref": credential_ref,
        "operation_id": operation_id,
        "prior_boundary_receipt_hash": device_kv.get("receipt_hash"),
        "stage_receipt_digest": request["stage_receipt_digest"],
        "materialization_request_hash": request["request_hash"],
        "secret_plaintext_present": False,
        "authority_transfer": False,
    }
    kv_skap_receipt = {**kv_skap_body, "receipt_hash": gate_digest(kv_skap_body)}
    double_gate = validate_double_interlock(
        device_kv_receipt=device_kv,
        kv_skap_receipt=kv_skap_receipt,
        credential_ref=credential_ref,
        operation_id=operation_id,
    )

    sealed = capsule["sealed_material"]
    credential_path = kv_root / "_Vault" / "SKAP" / "Credentials" / "coinbase" / f"{operation_id}.json"
    custody_record = {
        "format": custody_format,
        "ingress_id": operation_id,
        "object_id": credential_ref,
        "credential_version": capsule["credential_version"],
        "purpose": capsule["purpose"],
        "endpoint_ref": capsule["endpoint_origin"],
        "recipient_key_id": sealed["recipient_key_id"],
        "browser_sealed_digest": packet_digest(sealed),
        "browser_ingress_digest": packet_digest(capsule),
        "raw_body_digest": sha_uri(raw_packet),
        "stage_receipt_digest": request["stage_receipt_digest"],
        "sealed_material_ref": str(credential_path) + "#/sealed_material",
        "skap_vault_path": str(credential_path),
        "device_kv_interlock_receipt_hash": device_kv["receipt_hash"],
        "kv_skap_interlock_receipt_hash": kv_skap_receipt["receipt_hash"],
        "double_interlock_gate_receipt_hash": double_gate["gate_receipt_hash"],
        "sealed_material_persisted_unchanged": True,
        "endpoint_verification_required_before_decryption": True,
        "decryption_performed": False,
        "rewrap_performed": False,
        "plaintext_persisted": False,
        "kv_decryption_authority": False,
        "authority_transfer": False,
    }
    transition = build_transition(capsule, custody_record)
    interlock_record = {
        "device_kv_interlock_receipt": device_kv,
        "kv_skap_interlock_receipt": kv_skap_receipt,
        "double_interlock_gate_receipt": double_gate,
    }
    persisted = persist_ciphertext(
        kv_root=kv_root,
        ingress_id=operation_id,
        credential_ref=credential_ref,
        raw_packet=raw_packet,
        custody_record=custody_record,
        transition_receipt=transition,
        interlock_record=interlock_record,
        double_interlock_gate=double_gate,
    )
    if persisted.get("backend_id") != "KV_SKAP_INTR_FILESYSTEM":
        raise KVSkapMaterializationError("resident_kv_skap_backend_identity_invalid")

    exact_readback = Path(persisted["credential_path"]).read_bytes() == raw_packet
    if not exact_readback:
        raise KVSkapMaterializationError("exact_ciphertext_readback_mismatch")
    result_body = {
        "schema": "stegverse.kv-skap-custody.materialization-consumption/v1",
        "state": "ADMITTED_TO_SKAP_VAULT",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "raw_body_digest": sha_uri(raw_packet),
        "stage_receipt_digest": request["stage_receipt_digest"],
        "operation_id": operation_id,
        "credential_ref": credential_ref,
        "device_kv_interlock_receipt_hash": device_kv["receipt_hash"],
        "kv_skap_interlock_receipt_hash": kv_skap_receipt["receipt_hash"],
        "double_interlock_gate_receipt_hash": double_gate["gate_receipt_hash"],
        "skap_vault_storage_connector": "KV_SKAP_INTR_ONLY",
        "skap_vault_storage_backend": persisted["backend_id"],
        "credential_persistence_ref": persisted["credential_path"],
        "custody_receipt_ref": persisted["custody_receipt_path"],
        "transition_receipt_ref": persisted["transition_receipt_path"],
        "interlock_receipt_ref": persisted["interlock_receipt_path"],
        "exact_ciphertext_persisted": True,
        "exact_ciphertext_readback_verified": True,
        "secret_plaintext_present": False,
        "kv_decryption_authority": False,
        "device_durable_secret_custody": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "request_grants_authority": False,
        "authority_effect": "NONE_CUSTODY_TRANSITION_ONLY",
        "consumed_at": now(),
    }
    result = {**result_body, "result_hash": sha_uri(result_body)}
    target = runtime / RECEIPT_DIR_REL / f"{materialization_id}.json"
    if target.exists():
        existing = load(target)
        if existing != result:
            raise KVSkapMaterializationError("kv_skap_consumption_replay_collision")
        return existing
    atomic_json(target, result)
    atomic_json(runtime / LATEST_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    try:
        result = consume_one(args.source_root, args.runtime_root, args.materialization_id)
    except Exception as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc), "authority_effect": "NONE"}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") == "ADMITTED_TO_SKAP_VAULT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
