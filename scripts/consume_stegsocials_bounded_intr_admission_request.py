#!/usr/bin/env python3
"""Consume one already-local bounded StegSocials RECEIVED object through shared InTr.

This consumer is non-authorizing. It never creates participant approval, InTr
admission, TV/TVC authorization, SKAP/session authority, provider authority,
publication evidence, or KV evidence. If its hash-bound runtime input pointer is
absent, it may invoke the resident non-authorizing input materializer, which can
only bind already-materialized authentic relay artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TASK_ID = "SS-KV-SKAP-SOCIAL-RELEASE-001"
INPUT_SCHEMA = "stegverse.stegsocials-bounded-intr-admission-input/v1"
RECEIPT_SCHEMA = "stegverse.stegsocials-bounded-intr-admission-consumption/v1"
DEFAULT_INPUT_REL = Path("runtime-state/stegsocials/bounded-intr-admission-input.json")
DEFAULT_RECEIPT_REL = Path("receipts/sovereign-host/stegsocials-bounded-intr-admission-request-consumption.latest.json")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(dict(value), sort_keys=True, indent=2) + "\n"
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(raw, encoding="utf-8")
    tmp.replace(path)


def load_module(source_root: Path, rel: str, name: str, missing_reason: str):
    path = source_root / rel
    require(path.is_file(), missing_reason)
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"{name}_load_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_builder(source_root: Path):
    return load_module(
        source_root,
        "scripts/build_stegsocials_bounded_intr_materialization.py",
        "stegsocials_materialization_builder",
        "stegsocials_materialization_builder_missing",
    )


def load_input_materializer(source_root: Path):
    return load_module(
        source_root,
        "scripts/materialize_stegsocials_bounded_intr_admission_input.py",
        "stegsocials_input_materializer",
        "stegsocials_input_materializer_missing",
    )


def validate_input(value: Mapping[str, Any], runtime_root: Path) -> tuple[Path, str, str]:
    expected = {
        "schema": INPUT_SCHEMA,
        "state": "READY",
        "task_id": TASK_ID,
        "transport_origin": "TVC_RELAY_EGRESS",
        "request_grants_execution_authority": False,
        "authority_effect": "NONE_INPUT_ONLY",
    }
    for key, wanted in expected.items():
        require(value.get(key) == wanted, f"input_{key}_mismatch")
    body = dict(value)
    claimed = body.pop("input_hash", None)
    require(claimed == sha_uri(body), "input_hash_mismatch")
    received_ref = value.get("received_record_path")
    require(isinstance(received_ref, str) and received_ref.strip(), "received_record_path_required")
    received = Path(received_ref).expanduser()
    if not received.is_absolute():
        received = runtime_root / received
    received = received.resolve()
    runtime = runtime_root.resolve()
    require(received == runtime or runtime in received.parents, "received_record_must_be_runtime_local")
    require(received.is_file(), "received_record_not_materialized")
    ingress_url = value.get("ingress_url")
    require(isinstance(ingress_url, str) and ingress_url, "ingress_url_required")
    parsed = urlparse(ingress_url)
    require(parsed.scheme == "http", "ingress_url_must_be_loopback_http")
    require((parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}, "ingress_url_must_be_loopback")
    require(parsed.path == "/intr/materialization", "ingress_url_path_invalid")
    require(parsed.username is None and parsed.password is None, "ingress_url_credentials_forbidden")
    authorization_id = value.get("tvc_relay_authorization_id")
    require(isinstance(authorization_id, str) and authorization_id.strip(), "tvc_relay_authorization_id_required")
    return received, ingress_url, authorization_id


def materialize_request(builder, received: Path, runtime_root: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    record = load_json(received)
    payload, request = builder.build(record)
    payload_path = runtime_root / "intr-payloads/stegsocials-bounded-social" / f"{request['materialization_id']}.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if payload_path.exists():
        require(payload_path.read_text(encoding="utf-8") == payload_raw, "payload_write_once_collision")
    else:
        payload_path.write_text(payload_raw, encoding="utf-8")
    return payload, request, payload_path


def post_exact(request_value: Mapping[str, Any], ingress_url: str, authorization_id: str, *, opener=urlopen) -> dict[str, Any]:
    raw = canonical(request_value)
    req = Request(
        ingress_url,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
            "X-StegVerse-Authorization-Id": authorization_id,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        },
    )
    with opener(req, timeout=10.0) as response:
        body = response.read()
    value = json.loads(body.decode("utf-8"))
    require(isinstance(value, dict), "ingress_response_object_required")
    return value


def validate_admission(response: Mapping[str, Any], request_value: Mapping[str, Any], payload: Mapping[str, Any], authorization_id: str) -> None:
    expected = {
        "schema": "stegverse.stegsocials-bounded-intr-materialization-ingress/v1",
        "state": "INGRESS_ADMITTED",
        "materialization_id": request_value["materialization_id"],
        "request_hash": request_value["request_hash"],
        "payload_hash": request_value["payload_hash"],
        "transport_intent_hash": request_value["transport_intent_hash"],
        "work_id": payload["work_id"],
        "correlation_id": payload["correlation_id"],
        "group_id": payload["group_id"],
        "use_index": payload["use_index"],
        "content_hash": payload["content_hash"],
        "transport_origin": "TVC_RELAY_EGRESS",
        "transport_authorization_id": authorization_id,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "admission_grants_publication_authority": False,
        "next_owner": "TV/TVC_SKAP_SESSION_MATERIALIZATION",
    }
    for key, wanted in expected.items():
        require(response.get(key) == wanted, f"admission_{key}_mismatch")
    require(response.get("runtime_execution_attempted") is False, "admission_runtime_execution_claim_forbidden")
    require(response.get("provider_operation_authorized") is False, "admission_provider_authority_forbidden")
    require(response.get("credential_material_present") is False, "admission_credential_material_forbidden")


def consume(source_root: Path, runtime_root: Path, input_path: Path, *, opener=urlopen) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    pointer = input_path if input_path.is_absolute() else runtime / input_path
    input_materialization = None
    if not pointer.is_file():
        materializer = load_input_materializer(source)
        input_materialization = materializer.materialize(runtime)
        if input_materialization.get("input_materialized") is not True:
            return {
                "schema": RECEIPT_SCHEMA,
                "state": "INPUT_NOT_MATERIALIZED",
                "task_id": TASK_ID,
                "input_ref": str(pointer),
                "input_materialization": input_materialization,
                "runtime_execution_attempted": False,
                "authority_effect": "NONE_WAITING_FOR_AUTHENTIC_INPUT",
            }
    input_value = load_json(pointer)
    received, ingress_url, authorization_id = validate_input(input_value, runtime)
    input_hash = str(input_value["input_hash"])
    receipt_path = runtime / DEFAULT_RECEIPT_REL
    if receipt_path.is_file():
        previous = load_json(receipt_path)
        if previous.get("state") == "COMPLETED" and previous.get("input_hash") == input_hash:
            return {**previous, "state": "ALREADY_CONSUMED"}
    builder = load_builder(source)
    payload, request_value, payload_path = materialize_request(builder, received, runtime)
    response = post_exact(request_value, ingress_url, authorization_id, opener=opener)
    validate_admission(response, request_value, payload, authorization_id)
    result = {
        "schema": RECEIPT_SCHEMA,
        "state": "COMPLETED",
        "task_id": TASK_ID,
        "input_hash": input_hash,
        "input_ref": str(pointer),
        "input_materialization": input_materialization,
        "received_record_ref": str(received),
        "received_record_hash": sha_uri(load_json(received)),
        "materialization_id": request_value["materialization_id"],
        "request_hash": request_value["request_hash"],
        "payload_hash": request_value["payload_hash"],
        "payload_ref": str(payload_path),
        "ingress_receipt_hash": response.get("receipt_hash"),
        "ingress_receipt_ref": str(runtime / "receipts/sovereign-network/stegsocials-bounded-intr-ingress" / f"{request_value['materialization_id']}.json"),
        "work_id": payload["work_id"],
        "correlation_id": payload["correlation_id"],
        "group_id": payload["group_id"],
        "use_index": payload["use_index"],
        "runtime_execution_attempted": True,
        "authentic_shared_ingress_response_observed": True,
        "publication_authority_granted": False,
        "provider_execution_attempted": False,
        "credential_material_present": False,
        "next_owner": "TV/TVC_SKAP_SESSION_MATERIALIZATION",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "INGRESS_TRANSITION_OBSERVED_ONLY",
    }
    result["receipt_hash"] = sha_uri(result)
    write_atomic(receipt_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_REL)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root, args.input)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
