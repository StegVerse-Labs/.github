#!/usr/bin/env python3
"""Submit one exact private KV AI memory packet through the shared InTr ingress admission.

This helper reads the packet only from private resident bound state, admits it
in-process through the existing KV AI memory profile admission that the shared
Universal InTr listener routes to (kv_ai_memory_intr_transport.validate_headers
then kv_ai_memory_intr_profile.admit), validates the returned write-once
admission receipt against the exact packet, and writes only the compatible
admission artifact back into private bound state. No listener, socket, timeout
or receiver liveness is a predicate of the transition
(DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION); a configured loopback
endpoint is validated as destination identity only and never contacted. It
does not create an ALLOW result when the ingress admission refuses the packet,
and it projects INGRESS_ADMITTED only, never provider execution or KV writeback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

TASK_ID = "SV-KV-AI-PERSISTENCE-001"
PACKET_REL = Path("inputs/context-packet.json")
ADMISSION_REL = Path("inputs/memory-packet-admission.json")
SUBMISSION_SCHEMA = "stegverse.kv.ai-memory-intr-submission/v1"
RECEIPT_SCHEMA = "stegverse.kv.ai-memory-intr-admission/v1"
INGRESS_URL_ENV = "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"
TRANSPORT_ORIGIN = "STEGOS_RESIDENT_LOCAL"
# The write-once receipt location of workers/kv_ai_memory_intr_profile.py (RECEIPT_DIR).
INGRESS_RECEIPT_DIR = Path("receipts/sovereign-network/kv-ai-memory-intr")
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def packet_sha256(packet: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(dict(packet))).hexdigest()


def receipt_sha256(receipt_without_hash: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(dict(receipt_without_hash))).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def validate_loopback(url: str) -> None:
    parsed = urlparse(url)
    require(parsed.scheme == "http", "ingress_url_must_be_loopback_http")
    require((parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}, "ingress_url_must_be_loopback")
    require(parsed.path == "/intr/materialization", "ingress_url_path_invalid")
    require(parsed.username is None and parsed.password is None, "ingress_url_credentials_forbidden")


def _admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    """The shared listener's KV AI memory route, invoked in-process.

    A replay of the same exact packet returns the write-once receipt already
    admitted for it instead of re-admitting.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from workers import kv_ai_memory_intr_profile as profile
    from workers import kv_ai_memory_intr_transport as transport

    validated = transport.validate_headers(headers, body)
    payload = json.loads(body.decode("utf-8"))
    if profile.is_kv_ai_memory_submission(payload) and isinstance(payload.get("packet_id"), str):
        existing_path = runtime_root / profile.RECEIPT_DIR / f"{payload['packet_id']}.json"
        if existing_path.is_file():
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            if (
                existing.get("state") == "INGRESS_ADMITTED"
                and existing.get("packet_sha256") == payload.get("packet_sha256")
                and existing.get("transport_payload_sha256") == validated["payload_sha256_uri"]
            ):
                return existing
    return profile.admit(runtime_root=runtime_root, payload=payload, transport_payload_sha256=validated["payload_sha256_uri"])


def validate_receipt(packet: Mapping[str, Any], receipt: Mapping[str, Any]) -> str:
    packet_hash = packet_sha256(packet)
    require(receipt.get("schema") == RECEIPT_SCHEMA, "ingress_receipt_schema_invalid")
    require(receipt.get("state") == "INGRESS_ADMITTED" and receipt.get("disposition") == "ALLOW", "ingress_not_allowed")
    require(receipt.get("task_id") == TASK_ID, "ingress_task_mismatch")
    require(receipt.get("packet_id") == packet.get("packet_id"), "ingress_packet_id_mismatch")
    require(receipt.get("packet_sha256") == packet_hash, "ingress_packet_hash_mismatch")
    require(receipt.get("exact_packet_validated") is True, "ingress_exact_packet_validation_missing")
    require(receipt.get("private_packet_persisted_by_ingress") is False, "ingress_private_packet_persistence_forbidden")
    require(receipt.get("provider_request_materialized") is False, "ingress_provider_request_claim_forbidden")
    require(receipt.get("provider_ingress_admission_observed") is False, "ingress_provider_admission_claim_forbidden")
    require(receipt.get("provider_execution_observed") is False, "ingress_provider_execution_claim_forbidden")
    require(receipt.get("kv_writeback_observed") is False, "ingress_writeback_claim_forbidden")
    require(receipt.get("claim_or_fence_minted") is False, "ingress_claim_forbidden")
    require(receipt.get("credential_material_present") is False, "ingress_credentials_forbidden")
    require(receipt.get("heartbeat_grants_execution_authority") is False, "ingress_heartbeat_authority_forbidden")
    require(receipt.get("request_grants_execution_authority") is False, "ingress_execution_authority_forbidden")
    require(receipt.get("authority_effect") == "NONE_INGRESS_ADMISSION_ONLY", "ingress_authority_effect_invalid")
    claimed = receipt.get("receipt_hash")
    require(isinstance(claimed, str) and claimed.startswith("sha256:") and len(claimed) == 71, "ingress_receipt_hash_invalid")
    body = dict(receipt)
    body.pop("receipt_hash", None)
    require(receipt_sha256(body) == claimed, "ingress_receipt_hash_mismatch")
    return claimed


def submit(stage_root: Path, *, runtime_root: Path | None = None, env: Mapping[str, str] | None = None, admit=_admit) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    require(not any(truthy(values.get(name)) for name in HOSTED), "hosted_environment_forbidden")
    root = stage_root.expanduser().resolve()
    packet_path = root / PACKET_REL
    admission_path = root / ADMISSION_REL
    if not packet_path.is_file():
        return {
            "schema": "stegverse.kv.ai-memory-intr-submission-result/v1",
            "state": "PACKET_NOT_READY",
            "admission_written": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    ingress_url = str(values.get(INGRESS_URL_ENV) or "").strip()
    if ingress_url:
        # Destination identity only: validated, never contacted.
        validate_loopback(ingress_url)
    runtime = (runtime_root or root).expanduser().resolve()
    packet = load_object(packet_path)
    packet_hash = packet_sha256(packet)
    payload = {
        "schema": SUBMISSION_SCHEMA,
        "task_id": TASK_ID,
        "packet_id": packet.get("packet_id"),
        "packet_sha256": packet_hash,
        "packet": packet,
        "transport_origin": TRANSPORT_ORIGIN,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_material_present": False,
        "authority_effect": "NONE_SUBMISSION_ONLY",
    }
    body = canonical(payload)
    payload_hash = hashlib.sha256(body).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": TRANSPORT_ORIGIN,
        "X-StegVerse-Payload-SHA256": payload_hash,
    }
    try:
        receipt = admit(runtime_root=runtime, body=body, headers=headers)
    except ValueError as exc:
        raise RuntimeError("intr_admission_refused:" + str(exc)) from exc
    require(isinstance(receipt, dict), "ingress_receipt_object_required")
    receipt_hash = validate_receipt(packet, receipt)

    admission = {
        "schema": RECEIPT_SCHEMA,
        "disposition": "ALLOW",
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_hash,
        "receipt_hash": receipt_hash,
        "ingress_receipt": receipt,
        "authority_effect": "NONE_ADMISSION_EVIDENCE_ONLY",
    }
    admission_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(admission, indent=2, sort_keys=True) + "\n"
    if admission_path.exists():
        require(admission_path.read_text(encoding="utf-8") == rendered, "admission_write_once_collision")
    else:
        admission_path.write_text(rendered, encoding="utf-8")
    require(admission_path.read_text(encoding="utf-8") == rendered, "admission_readback_mismatch")
    return {
        "schema": "stegverse.kv.ai-memory-intr-submission-result/v1",
        "state": "AUTHENTIC_INGRESS_ADMISSION_WRITTEN",
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_hash,
        "receipt_hash": receipt_hash,
        "admission_ref": ADMISSION_REL.as_posix(),
        "admission_written": True,
        "ingress_state": receipt["state"],
        "ingress_receipt_ref": str(runtime / INGRESS_RECEIPT_DIR / f"{packet['packet_id']}.json"),
        "in_process_write_once_admission": True,
        "receiver_liveness_predicate": False,
        "provider_request_materialized": False,
        "provider_execution_observed": False,
        "kv_writeback_observed": False,
        "authority_effect": "NONE_ADMISSION_EVIDENCE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    result = submit(args.stage_root, runtime_root=args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"PACKET_NOT_READY", "AUTHENTIC_INGRESS_ADMISSION_WRITTEN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
