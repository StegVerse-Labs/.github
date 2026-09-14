#!/usr/bin/env python3
"""Submit one exact private KV AI memory packet to the shared loopback InTr ingress.

This helper reads the packet only from private resident bound state, submits it to
an explicitly configured loopback Universal InTr endpoint, validates the returned
admission against the exact packet, and writes only the compatible admission
artifact back into private bound state. It does not create an ALLOW result when
the ingress is unavailable or rejects the packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TASK_ID = "SV-KV-AI-PERSISTENCE-001"
PACKET_REL = Path("inputs/context-packet.json")
ADMISSION_REL = Path("inputs/memory-packet-admission.json")
SUBMISSION_SCHEMA = "stegverse.kv.ai-memory-intr-submission/v1"
RECEIPT_SCHEMA = "stegverse.kv.ai-memory-intr-admission/v1"
INGRESS_URL_ENV = "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"
TRANSPORT_ORIGIN = "STEGOS_RESIDENT_LOCAL"
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


def _open(request: Request, *, timeout: float) -> tuple[int, bytes]:
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback URL is validated
        return int(response.status), response.read()


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


def submit(stage_root: Path, *, env: Mapping[str, str] | None = None, opener=_open, timeout: float = 10.0) -> dict[str, Any]:
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
    if not ingress_url:
        return {
            "schema": "stegverse.kv.ai-memory-intr-submission-result/v1",
            "state": "INGRESS_NOT_READY",
            "missing_inputs": [INGRESS_URL_ENV],
            "admission_written": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    validate_loopback(ingress_url)
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
    request = Request(
        ingress_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": TRANSPORT_ORIGIN,
            "X-StegVerse-Payload-SHA256": payload_hash,
        },
    )
    status, raw = opener(request, timeout=timeout)
    require(status == 202, f"ingress_status_invalid:{status}")
    receipt = json.loads(raw.decode("utf-8"))
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
        "provider_request_materialized": False,
        "provider_execution_observed": False,
        "kv_writeback_observed": False,
        "authority_effect": "NONE_ADMISSION_EVIDENCE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    result = submit(args.stage_root, timeout=args.timeout)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"PACKET_NOT_READY", "INGRESS_NOT_READY", "AUTHENTIC_INGRESS_ADMISSION_WRITTEN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
