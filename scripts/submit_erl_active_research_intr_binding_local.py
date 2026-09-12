#!/usr/bin/env python3
"""Submit one resident-local ERL active-research binding to shared InTr.

This is the active resident path for ERL. It reuses the already-validated binding
and admission validators but uses the profile-specific STEGOS_RESIDENT_LOCAL
transport origin. No TVC relay authorization header is accepted or emitted.
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

import submit_erl_active_research_intr_binding as legacy

TASK_ID = legacy.TASK_ID
INPUT_SCHEMA = "stegverse.erl-active-research-intr-resident-local-input/v1"
RECEIPT_SCHEMA = "stegverse.erl-active-research-intr-resident-local-submission-consumption/v1"
TRANSPORT_ORIGIN = "STEGOS_RESIDENT_LOCAL"
DEFAULT_INPUT_REL = legacy.DEFAULT_INPUT_REL
DEFAULT_RECEIPT_REL = Path("receipts/sovereign-host/erl-active-research-intr-resident-local-submission.latest.json")
HOSTED = legacy.HOSTED


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical(value: Any) -> bytes:
    return legacy.canonical(value)


def sha_uri(value: Any) -> str:
    return legacy.sha_uri(value)


def load_json(path: Path) -> dict[str, Any]:
    return legacy.load_json(path)


def write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    legacy.write_atomic(path, value)


def validate_input(value: Mapping[str, Any], runtime_root: Path) -> tuple[Path, str]:
    expected = {
        "schema": INPUT_SCHEMA,
        "state": "READY",
        "task_id": TASK_ID,
        "transport_origin": TRANSPORT_ORIGIN,
        "transport_credential_required": False,
        "credential_authority": "TV/TVC",
        "request_grants_execution_authority": False,
        "provider_operation_authorized": False,
        "authority_effect": "NONE_INPUT_ONLY",
    }
    for key, wanted in expected.items():
        require(value.get(key) == wanted, f"input_{key}_mismatch")
    require("tvc_relay_authorization_id" not in value, "resident_local_tvc_relay_authorization_forbidden")
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
    return binding, ingress_url


def post_exact(binding: Mapping[str, Any], ingress_url: str, *, opener=urlopen) -> dict[str, Any]:
    raw = canonical(binding)
    req = Request(
        ingress_url,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": TRANSPORT_ORIGIN,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        },
    )
    with opener(req, timeout=10.0) as response:
        body = response.read()
    value = json.loads(body.decode("utf-8"))
    require(isinstance(value, dict), "ingress_response_object_required")
    return value


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
    binding_path, ingress_url = validate_input(input_value, runtime)
    binding = load_json(binding_path)
    request = legacy.validate_binding(binding)
    response = post_exact(binding, ingress_url, opener=opener)
    legacy.validate_admission(response, request, binding)
    result = {
        "schema": RECEIPT_SCHEMA,
        "state": "PROFILE_ADMITTED_TERMINAL_MATERIALIZATION_PENDING",
        "task_id": TASK_ID,
        "input_hash": input_value["input_hash"],
        "binding_ref": str(binding_path),
        "binding_hash": binding["binding_hash"],
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": TRANSPORT_ORIGIN,
        "transport_credential_required": False,
        "transport_submission_attempted": True,
        "authentic_shared_ingress_response_observed": True,
        "upstream_hop_receipts": response["hop_receipts"],
        "terminal_materialization_request": response["terminal_materialization_request"],
        "terminal_runtime_receipt_present": False,
        "provider_operation_attempted": False,
        "runtime_receipts_fabricated": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "second_machine_required": False,
        "authority_effect": "INGRESS_TRANSITIONS_OBSERVED_TERMINAL_PENDING",
    }
    write_atomic(runtime / DEFAULT_RECEIPT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_REL)
    args = parser.parse_args()
    print(json.dumps(consume(args.runtime_root, args.input), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
