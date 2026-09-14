#!/usr/bin/env python3
"""Submit one staged KV AI memory packet to the existing loopback Universal InTr ingress.

This is a resident-local transport client only. It does not create an InTr
admission, WorkerCoordinator claim/fence, provider request, credential, model
operation, or KV write. It validates the returned exact-packet admission before
writing the admission artifact into the existing fenced bound-state slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TASK_ID = "SV-KV-AI-PERSISTENCE-001"
SUBMISSION_SCHEMA = "stegverse.kv.ai-memory-intr-submission/v1"
PACKET_SCHEMA = "stegverse.kv.ai-memory-context-packet/v1"
RECEIPT_SCHEMA = "stegverse.kv.ai-memory-intr-admission/v1"
PACKET_REL = Path("inputs/context-packet.json")
ADMISSION_REL = Path("inputs/memory-packet-admission.json")
SUBMISSION_RECEIPT_REL = Path("receipts/memory-packet-intr-submission.json")
INGRESS_URL_ENV = "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"
TRANSPORT_ORIGIN = "STEGOS_RESIDENT_LOCAL"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def packet_sha256(packet: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(dict(packet))).hexdigest()


def receipt_hash(body: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(dict(body))).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    require(path.read_text(encoding="utf-8") == rendered, "write_readback_mismatch")


def validate_loopback(url: str) -> None:
    parsed = urlparse(url)
    require(parsed.scheme == "http", "ingress_url_must_be_loopback_http")
    require((parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}, "ingress_url_must_be_loopback")
    require(parsed.path == "/intr/materialization", "ingress_url_path_invalid")
    require(parsed.username is None and parsed.password is None, "ingress_url_credentials_forbidden")


def validate_packet(packet: Mapping[str, Any]) -> None:
    require(packet.get("schema") == PACKET_SCHEMA, "memory_packet_schema_invalid")
    require(packet.get("kv_class") == "PERSONAL_KV", "memory_packet_kv_class_invalid")
    require(packet.get("authority_domain") == "PERSON", "memory_packet_authority_domain_invalid")
    require(packet.get("consumer_ai_role") == "PERSONAL_ASSISTANT_AI", "memory_packet_consumer_role_invalid")
    require(packet.get("intr_admission_required") is True, "memory_packet_intr_required")
    require(packet.get("secret_material_included") is False, "memory_packet_secret_material_forbidden")
    require(packet.get("cross_authority_content_included") is False, "memory_packet_cross_authority_forbidden")
    require(packet.get("model_is_authority") is False, "memory_packet_model_authority_forbidden")
    require(packet.get("context_transfers_authority") is False, "memory_packet_authority_transfer_forbidden")
    require(packet.get("authority_effect") == "NONE_CONTEXT_ONLY", "memory_packet_authority_effect_invalid")
    require(isinstance(packet.get("packet_id"), str) and packet["packet_id"].startswith("KVMEM-"), "memory_packet_id_invalid")


def build_submission(packet: Mapping[str, Any]) -> dict[str, Any]:
    validate_packet(packet)
    return {
        "schema": SUBMISSION_SCHEMA,
        "task_id": TASK_ID,
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "packet": dict(packet),
        "transport_origin": TRANSPORT_ORIGIN,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_material_present": False,
        "authority_effect": "NONE_SUBMISSION_ONLY",
    }


def validate_admission(packet: Mapping[str, Any], admission: Mapping[str, Any]) -> None:
    require(admission.get("schema") == RECEIPT_SCHEMA, "memory_admission_schema_invalid")
    require(admission.get("state") == "INGRESS_ADMITTED", "memory_admission_state_invalid")
    require(admission.get("disposition") == "ALLOW", "memory_admission_not_allow")
    require(admission.get("task_id") == TASK_ID, "memory_admission_task_invalid")
    require(admission.get("packet_id") == packet.get("packet_id"), "memory_admission_packet_id_mismatch")
    require(admission.get("packet_sha256") == packet_sha256(packet), "memory_admission_packet_hash_mismatch")
    require(admission.get("exact_packet_validated") is True, "memory_admission_exact_packet_not_validated")
    require(admission.get("private_packet_persisted_by_ingress") is False, "memory_admission_private_packet_persistence_forbidden")
    require(admission.get("provider_request_materialized") is False, "memory_admission_provider_request_claim_forbidden")
    require(admission.get("provider_execution_observed") is False, "memory_admission_provider_execution_claim_forbidden")
    require(admission.get("kv_writeback_observed") is False, "memory_admission_writeback_claim_forbidden")
    require(admission.get("claim_or_fence_minted") is False, "memory_admission_claim_forbidden")
    require(admission.get("credential_material_present") is False, "memory_admission_credentials_forbidden")
    require(admission.get("request_grants_execution_authority") is False, "memory_admission_execution_authority_forbidden")
    claimed = admission.get("receipt_hash")
    require(isinstance(claimed, str) and claimed.startswith("sha256:") and len(claimed) == 71, "memory_admission_receipt_hash_invalid")
    body = dict(admission)
    body.pop("receipt_hash", None)
    require(claimed == receipt_hash(body), "memory_admission_receipt_hash_mismatch")


def submit(stage_root: Path, *, env: Mapping[str, str] | None = None, opener=urlopen) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    require(not any(truthy(values.get(name)) for name in HOSTED_ENV), "hosted_environment_forbidden")
    root = stage_root.expanduser().resolve()
    packet_path = root / PACKET_REL
    require(packet_path.is_file(), "context_packet_not_staged")
    packet = load_object(packet_path)
    submission = build_submission(packet)

    ingress_url = str(values.get(INGRESS_URL_ENV) or "").strip()
    require(bool(ingress_url), "universal_intr_ingress_url_required")
    validate_loopback(ingress_url)

    body = canonical(submission)
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": TRANSPORT_ORIGIN,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }
    request = Request(ingress_url, data=body, headers=headers, method="POST")
    try:
        response = opener(request, timeout=15)
        raw = response.read()
        status = int(getattr(response, "status", 0) or response.getcode())
    except HTTPError as exc:
        raise RuntimeError(f"intr_http_error:{exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("intr_unreachable") from exc
    require(status == 202, f"intr_unexpected_status:{status}")
    admission = json.loads(raw.decode("utf-8"))
    require(isinstance(admission, dict), "memory_admission_object_required")
    validate_admission(packet, admission)

    admission_path = root / ADMISSION_REL
    if admission_path.exists():
        existing = load_object(admission_path)
        require(existing == admission, "memory_admission_write_once_collision")
    else:
        write_atomic(admission_path, admission)

    result = {
        "schema": "stegverse.kv.ai-memory-intr-local-submission/v1",
        "state": "AUTHENTIC_INGRESS_ADMISSION_STAGED",
        "task_id": TASK_ID,
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "admission_ref": ADMISSION_REL.as_posix(),
        "admission_receipt_hash": admission["receipt_hash"],
        "transport_origin": TRANSPORT_ORIGIN,
        "tvc_authorization_required": False,
        "tvc_authorization_created": False,
        "worker_claim_or_fence_minted": False,
        "provider_execution_observed": False,
        "kv_writeback_observed": False,
        "authority_effect": "NONE_TRANSPORT_AND_STAGING_ONLY",
    }
    write_atomic(root / SUBMISSION_RECEIPT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(submit(args.stage_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
