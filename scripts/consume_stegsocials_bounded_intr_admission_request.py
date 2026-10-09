#!/usr/bin/env python3
"""Consume one already-local bounded StegSocials RECEIVED object through shared InTr.

This consumer is non-authorizing. It never creates participant approval, InTr
admission, TV/TVC authorization, SKAP/session authority, provider authority,
publication evidence, or KV evidence. If its hash-bound runtime input pointer is
absent, it may invoke the resident non-authorizing input materializer, which can
only bind already-materialized authentic relay artifacts.

The exact request is admitted in-process through the existing StegSocials
profile ingress (workers/stegsocials_bounded_intr_ingress.py admit, with the
shared HIL transport-header validator the listener uses for this profile),
which persists it write-once into the durable queue. No listener, socket,
timeout or receiver liveness is a predicate of this transition
(DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION). The input's loopback
ingress_url is validated as the manifested destination identity only; it is
never contacted. The receipt projects INGRESS_ADMITTED and never claims
downstream execution.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

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


def load_admission(source_root: Path):
    """The existing in-process StegSocials profile admission, bound to the listener's validator."""
    for path in (source_root, source_root / "scripts"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    ingress = load_module(
        source_root,
        "workers/stegsocials_bounded_intr_ingress.py",
        "stegsocials_bounded_intr_ingress",
        "stegsocials_bounded_intr_ingress_missing",
    )
    hil = load_module(
        source_root,
        "scripts/serve_hil_intr_materialization_ingress.py",
        "serve_hil_intr_materialization_ingress",
        "shared_intr_transport_validator_missing",
    )

    def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
        return ingress.admit(runtime_root=runtime_root, body=body, headers=headers, transport_validator=hil.validate_transport_headers)

    return admit


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


def admit_exact(request_value: Mapping[str, Any], runtime_root: Path, authorization_id: str, *, admit) -> dict[str, Any]:
    """Admit the exact request write-once in-process; a refusal is typed and commits nothing."""
    raw = canonical(request_value)
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
        "X-StegVerse-Authorization-Id": authorization_id,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
    }
    try:
        value = admit(runtime_root=runtime_root, body=raw, headers=headers)
    except ValueError as exc:
        raise RuntimeError("intr_admission_refused:" + str(exc)) from exc
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


def consume(source_root: Path, runtime_root: Path, input_path: Path, *, admit=None) -> dict[str, Any]:
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
    received, _destination_url, authorization_id = validate_input(input_value, runtime)
    input_hash = str(input_value["input_hash"])
    receipt_path = runtime / DEFAULT_RECEIPT_REL
    if receipt_path.is_file():
        previous = load_json(receipt_path)
        if previous.get("state") in {"INGRESS_ADMITTED", "COMPLETED"} and previous.get("input_hash") == input_hash:
            return {**previous, "state": "ALREADY_CONSUMED"}
    builder = load_builder(source)
    payload, request_value, payload_path = materialize_request(builder, received, runtime)
    if admit is None:
        admit = load_admission(source)
    response = admit_exact(request_value, runtime, authorization_id, admit=admit)
    validate_admission(response, request_value, payload, authorization_id)
    require(response.get("write_once_persisted") is True, "admission_write_once_receipt_missing")
    result = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
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
        "ingress_queue_ref": response.get("queue_ref"),
        "ingress_write_once_persisted": True,
        "work_id": payload["work_id"],
        "correlation_id": payload["correlation_id"],
        "group_id": payload["group_id"],
        "use_index": payload["use_index"],
        "runtime_execution_attempted": False,
        "in_process_write_once_admission": True,
        "receiver_liveness_predicate": False,
        "downstream_execution_observed": False,
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
