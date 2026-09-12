#!/usr/bin/env python3
"""Materialize bounded StegSocials shared-InTr input from authentic relay artifacts.

This helper creates no approval, TV/TVC authorization, listener, InTr admission,
provider action, or KV mutation. It only projects an already-materialized exact
Socials RECEIVED record plus an already-issued TV/TVC relay authorization whose
payload hash/size and next-hop endpoint bind that exact record and the existing
loopback /intr/materialization listener.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

TASK_ID = "SS-KV-SKAP-SOCIAL-RELEASE-001"
INPUT_SCHEMA = "stegverse.stegsocials-bounded-intr-admission-input/v1"
WORK_SCHEMA = "stegverse.universal-work-interlock/v1"
BINDING_SCHEMA = "stegos.sovereign_relay_egress_binding.v1"
AUTH_SCHEMA = "stegverse.tvc.sovereign-relay-egress-authorization/v1"
OUTPUT_REL = Path("runtime-state/stegsocials/bounded-intr-admission-input.json")
BINDING_ENV = "STEGVERSE_RELAY_EGRESS_BINDING"
AUTH_ENV = "STEGVERSE_RELAY_EGRESS_AUTHORIZATION"
PAYLOAD_ENV = "STEGVERSE_RELAY_EGRESS_PAYLOAD"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_hex(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(raw).hexdigest()


def sha_uri(value: Any) -> str:
    return "sha256:" + sha_hex(value)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    require(path.read_text(encoding="utf-8") == rendered, "input_readback_mismatch")


def resolve_file(values: Mapping[str, str], name: str) -> Path | None:
    raw = str(values.get(name) or "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    require(path.is_file(), f"runtime_artifact_missing:{name}")
    return path


def validate_loopback(url: str) -> None:
    parsed = urlparse(url)
    require(parsed.scheme == "http", "ingress_url_must_be_loopback_http")
    require((parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}, "ingress_url_must_be_loopback")
    require(parsed.path == "/intr/materialization", "ingress_url_path_invalid")
    require(parsed.username is None and parsed.password is None, "ingress_url_credentials_forbidden")


def validate_received(record: Mapping[str, Any]) -> None:
    require(record.get("schema") == WORK_SCHEMA, "received_schema_invalid")
    require(record.get("direction") == "INGRESS", "received_direction_invalid")
    require(record.get("state") == "RECEIVED", "received_state_invalid")
    require(record.get("next_owner") == "INTERLOCK_INTR", "received_next_owner_invalid")
    source = record.get("source")
    require(isinstance(source, Mapping), "received_source_required")
    require(source.get("identity") == TASK_ID, "received_task_identity_mismatch")
    intent = record.get("bounded_social_intent")
    require(isinstance(intent, Mapping), "bounded_social_intent_required")
    require(intent.get("task_id") == TASK_ID, "bounded_social_task_mismatch")
    require(record.get("admission_receipt_ref") is None, "received_may_not_carry_admission")
    require(record.get("runtime_admission_observed") is False, "received_may_not_claim_runtime_admission")
    authority = record.get("authority")
    require(isinstance(authority, Mapping), "received_authority_required")
    require(authority.get("credential_authority") == "TV/TVC", "received_credential_authority_invalid")
    require(authority.get("github_token_runtime_authority") == "NONE", "received_github_runtime_authority_invalid")
    require(authority.get("heartbeat_granted_authority") is False, "received_heartbeat_authority_invalid")
    require(authority.get("interlock_self_grants_authority") is False, "received_interlock_self_authority_invalid")
    require(authority.get("intr_self_grants_authority") is False, "received_intr_self_authority_invalid")
    require(authority.get("authority_effect") == "NONE_RECEIVED_INGRESS_RECORD_ONLY", "received_authority_effect_invalid")


def validate_binding_authorization(binding: Mapping[str, Any], authorization: Mapping[str, Any], payload_raw: bytes) -> tuple[str, str]:
    require(binding.get("schema") == BINDING_SCHEMA, "binding_schema_invalid")
    require(binding.get("route_admitted") is True, "binding_route_admission_required")
    require(binding.get("egress_authorized") is False, "binding_must_be_pre_authorization")
    require(binding.get("runtime_executed") is False, "binding_may_not_claim_runtime_execution")
    require(binding.get("credential_authority") == "TV/TVC", "binding_credential_authority_invalid")
    require(binding.get("credential_material_present") is False, "binding_credential_material_forbidden")

    require(authorization.get("schema") == AUTH_SCHEMA, "authorization_schema_invalid")
    require(authorization.get("decision") == "ALLOW_RELAY_EGRESS", "relay_egress_not_authorized")
    require(authorization.get("issuer_authority") == "TV/TVC", "authorization_issuer_invalid")
    require(authorization.get("credential_authority") == "TV/TVC", "authorization_credential_authority_invalid")
    require(authorization.get("credential_requirement") == "NONE", "authorization_credential_requirement_invalid")
    require(authorization.get("credential_material_present") is False, "authorization_credential_material_forbidden")
    require(authorization.get("route_admitted") is True, "authorization_route_admission_required")
    require(authorization.get("egress_authorized") is True, "authorization_egress_not_authorized")
    require(authorization.get("runtime_executed") is False, "authorization_may_not_claim_runtime_execution")
    require(authorization.get("payload_inspection_authority") is False, "authorization_payload_inspection_forbidden")
    require(authorization.get("canonical_transition_authority") is False, "authorization_transition_authority_forbidden")
    require(authorization.get("settlement_authority") is False, "authorization_settlement_authority_forbidden")
    require(authorization.get("authority_effect") == "BOUNDED_RELAY_EGRESS_AUTHORIZATION", "authorization_authority_effect_invalid")
    claimed_auth_hash = authorization.get("authorization_sha256")
    auth_material = dict(authorization)
    auth_material.pop("authorization_sha256", None)
    require(claimed_auth_hash == sha_hex(auth_material), "authorization_hash_mismatch")

    for field in ("binding_id", "route_receipt_hash", "route_candidate_hash", "route_id", "transport_id", "next_hop_transport_endpoint", "next_hop_identity_binding"):
        require(binding.get(field) == authorization.get(field), f"authorization_{field}_mismatch")
    payload_sha = hashlib.sha256(payload_raw).hexdigest()
    require(authorization.get("payload_sha256") == payload_sha, "authorization_payload_hash_mismatch")
    require(authorization.get("payload_size") == len(payload_raw), "authorization_payload_size_mismatch")
    ingress_url = str(authorization.get("next_hop_transport_endpoint") or "").strip()
    validate_loopback(ingress_url)
    authorization_id = str(authorization.get("authorization_id") or "").strip()
    require(bool(authorization_id), "authorization_id_required")
    return ingress_url, authorization_id


def materialize(runtime_root: Path, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    runtime = runtime_root.expanduser().resolve()
    binding_path = resolve_file(values, BINDING_ENV)
    authorization_path = resolve_file(values, AUTH_ENV)
    payload_path = resolve_file(values, PAYLOAD_ENV)
    missing = [name for name, path in ((BINDING_ENV, binding_path), (AUTH_ENV, authorization_path), (PAYLOAD_ENV, payload_path)) if path is None]
    if missing:
        return {
            "schema": "stegverse.stegsocials-bounded-intr-admission-input-materialization/v1",
            "state": "AUTHENTIC_RELAY_INPUT_NOT_MATERIALIZED",
            "task_id": TASK_ID,
            "missing_inputs": missing,
            "input_materialized": False,
            "tvc_authorization_created": False,
            "listener_created": False,
            "hosted_execution_attempted": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    require(not any(truthy(values.get(name)) for name in HOSTED), "hosted_environment_forbidden")
    assert binding_path is not None and authorization_path is not None and payload_path is not None
    payload_resolved = payload_path.resolve()
    require(runtime in payload_resolved.parents, "received_record_must_be_runtime_local")
    payload_raw = payload_resolved.read_bytes()
    received = json.loads(payload_raw.decode("utf-8"))
    require(isinstance(received, dict), "received_record_object_required")
    validate_received(received)
    binding = load_json(binding_path)
    authorization = load_json(authorization_path)
    ingress_url, authorization_id = validate_binding_authorization(binding, authorization, payload_raw)
    try:
        received_ref = payload_resolved.relative_to(runtime).as_posix()
    except ValueError:
        raise RuntimeError("received_record_must_be_runtime_local") from None
    body = {
        "schema": INPUT_SCHEMA,
        "state": "READY",
        "task_id": TASK_ID,
        "received_record_path": received_ref,
        "ingress_url": ingress_url,
        "tvc_relay_authorization_id": authorization_id,
        "transport_origin": "TVC_RELAY_EGRESS",
        "request_grants_execution_authority": False,
        "authority_effect": "NONE_INPUT_ONLY",
    }
    value = {**body, "input_hash": sha_uri(body)}
    output = runtime / OUTPUT_REL
    write_atomic(output, value)
    return {
        "schema": "stegverse.stegsocials-bounded-intr-admission-input-materialization/v1",
        "state": "INPUT_MATERIALIZED",
        "task_id": TASK_ID,
        "input_ref": OUTPUT_REL.as_posix(),
        "input_hash": value["input_hash"],
        "received_record_ref": received_ref,
        "relay_binding_ref": str(binding_path),
        "relay_authorization_ref": str(authorization_path),
        "input_materialized": True,
        "tvc_authorization_created": False,
        "listener_created": False,
        "intr_admission_created": False,
        "provider_operation_authorized": False,
        "authority_effect": "NONE_INPUT_MATERIALIZATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(materialize(args.runtime_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
