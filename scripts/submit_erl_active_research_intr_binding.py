#!/usr/bin/env python3
"""Submit one already-materialized ERL active-research binding to shared InTr.

This bridge is intentionally narrow. It requires a runtime-local binding sidecar,
a loopback-only shared Universal InTr endpoint, and an already-issued TVC relay
authorization identifier. It creates no TVC authorization, no listener, no
provider operation, and no hop receipt. Any returned runtime evidence must come
from the authentic shared ingress response.
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

TASK_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
INPUT_SCHEMA = "stegverse.erl-active-research-intr-submission-input/v1"
RECEIPT_SCHEMA = "stegverse.erl-active-research-intr-submission-consumption/v1"
BINDING_SCHEMA = "stegverse.erl.active-research-intr-binding/v1"
PATH = ["EXTERNAL_SYSTEM", "STEGOS_ECOSYSTEM", "DEVICE_SYSTEM", "KV"]
DEFAULT_INPUT_REL = Path("runtime-state/erl-active-research/intr-submission-input.json")
DEFAULT_RECEIPT_REL = Path("receipts/sovereign-host/erl-active-research-intr-submission.latest.json")
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(raw, encoding="utf-8")
    os.replace(tmp, path)


def validate_input(value: Mapping[str, Any], runtime_root: Path) -> tuple[Path, str, str]:
    expected = {
        "schema": INPUT_SCHEMA,
        "state": "READY",
        "task_id": TASK_ID,
        "transport_origin": "TVC_RELAY_EGRESS",
        "request_grants_execution_authority": False,
        "provider_operation_authorized": False,
        "authority_effect": "NONE_INPUT_ONLY",
    }
    for key, wanted in expected.items():
        require(value.get(key) == wanted, f"input_{key}_mismatch")
    body = dict(value)
    claimed = body.pop("input_hash", None)
    require(claimed == sha_uri(body), "input_hash_mismatch")

    binding_ref = value.get("binding_ref")
    require(isinstance(binding_ref, str) and binding_ref.strip(), "binding_ref_required")
    binding = Path(binding_ref).expanduser()
    if not binding.is_absolute():
        binding = runtime_root / binding
    binding = binding.resolve()
    runtime = runtime_root.resolve()
    require(binding == runtime or runtime in binding.parents, "binding_must_be_runtime_local")
    require(binding.is_file(), "binding_not_materialized")

    ingress_url = value.get("ingress_url")
    require(isinstance(ingress_url, str) and ingress_url, "ingress_url_required")
    parsed = urlparse(ingress_url)
    require(parsed.scheme == "http", "ingress_url_must_be_loopback_http")
    require((parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}, "ingress_url_must_be_loopback")
    require(parsed.path == "/intr/materialization", "ingress_url_path_invalid")
    require(parsed.username is None and parsed.password is None, "ingress_url_credentials_forbidden")

    authorization_id = value.get("tvc_relay_authorization_id")
    require(isinstance(authorization_id, str) and authorization_id.strip(), "tvc_relay_authorization_id_required")
    return binding, ingress_url, authorization_id


def validate_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    require(binding.get("schema") == BINDING_SCHEMA, "binding_schema_invalid")
    require(binding.get("expected_boundary_path") == PATH, "binding_boundary_path_invalid")
    require(binding.get("expected_runtime_receipt_count") == 3, "binding_receipt_count_invalid")
    require(binding.get("runtime_receipts_present") is False, "binding_runtime_receipts_must_be_absent_before_submission")
    require(binding.get("transport_execution_claimed") is False, "binding_transport_execution_preclaim_forbidden")
    body = dict(binding)
    claimed_binding_hash = body.pop("binding_hash", None)
    require(claimed_binding_hash == sha_uri(body), "binding_hash_mismatch")
    envelope = binding.get("acquisition_envelope")
    require(isinstance(envelope, dict), "binding_envelope_required")
    require(sha_uri(envelope) == binding.get("acquisition_envelope_sha256"), "binding_envelope_hash_mismatch")
    request = binding.get("materialization_request")
    require(isinstance(request, dict), "binding_materialization_request_required")
    expected = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "boundary_path": PATH,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        require(request.get(key) == wanted, f"materialization_{key}_mismatch")
    require(request.get("payload_hash") == binding.get("acquisition_envelope_sha256"), "binding_payload_hash_mismatch")
    return request


def post_exact(binding: Mapping[str, Any], ingress_url: str, authorization_id: str, *, opener=urlopen) -> dict[str, Any]:
    raw = canonical(binding)
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


def validate_admission(response: Mapping[str, Any], request: Mapping[str, Any], authorization_id: str) -> None:
    expected = {
        "state": "INGRESS_ADMITTED",
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": "TVC_RELAY_EGRESS",
        "transport_authorization_id": authorization_id,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }
    for key, wanted in expected.items():
        require(response.get(key) == wanted, f"admission_{key}_mismatch")
    schema = response.get("schema")
    require(schema in {"stegverse.erl-active-research-intr-ingress/v1", "stegverse.erl.active-research-intr-ingress/v1"}, "admission_schema_invalid")
    require(response.get("authority_effect") in {"NONE_INGRESS_ONLY", "INGRESS_TRANSITION_OBSERVED_ONLY"}, "admission_authority_effect_invalid")
    require(response.get("provider_operation_authorized") in {None, False}, "admission_provider_authority_forbidden")


def consume(runtime_root: Path, input_path: Path, *, opener=urlopen, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    require(not any(truthy(values.get(name)) for name in HOSTED), "hosted_environment_forbidden")
    runtime = runtime_root.expanduser().resolve()
    pointer = input_path if input_path.is_absolute() else runtime / input_path
    if not pointer.is_file():
        return {
            "schema": RECEIPT_SCHEMA,
            "state": "INPUT_NOT_MATERIALIZED",
            "task_id": TASK_ID,
            "runtime_execution_attempted": False,
            "transport_submission_attempted": False,
            "authority_effect": "NONE_WAITING_FOR_AUTHENTIC_INPUT",
        }
    input_value = load_json(pointer)
    binding_path, ingress_url, authorization_id = validate_input(input_value, runtime)
    binding = load_json(binding_path)
    request = validate_binding(binding)
    response = post_exact(binding, ingress_url, authorization_id, opener=opener)
    validate_admission(response, request, authorization_id)
    result = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "task_id": TASK_ID,
        "input_hash": input_value["input_hash"],
        "binding_ref": str(binding_path),
        "binding_hash": binding["binding_hash"],
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_submission_attempted": True,
        "authentic_shared_ingress_response_observed": True,
        "ingress_response": dict(response),
        "provider_operation_attempted": False,
        "runtime_receipts_fabricated": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "second_machine_required": False,
        "authority_effect": "INGRESS_TRANSITION_OBSERVED_ONLY",
    }
    write_atomic(runtime / DEFAULT_RECEIPT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_REL)
    args = parser.parse_args()
    result = consume(args.runtime_root, args.input)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
