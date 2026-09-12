#!/usr/bin/env python3
"""Materialize resident-local ERL shared-InTr submission input.

Consumes only an already-materialized ERL binding receipt plus an explicit
loopback Universal InTr ingress URL. It does not require, create, infer, or carry
a TVC relay authorization because this path is resident-local rather than a
sovereign relay EGRESS operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

TASK_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
INPUT_SCHEMA = "stegverse.erl-active-research-intr-resident-local-input/v1"
BINDING_RECEIPT_SCHEMA = "stegverse.erl-active-research.resident-consumption/v1"
BINDING_RECEIPT_REL = Path("receipts/sovereign-host/erl-active-research-intr-binding-consumption.latest.json")
OUTPUT_REL = Path("runtime-state/erl-active-research/intr-submission-input.json")
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


def sha_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


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
    require(path.read_text(encoding="utf-8") == rendered, "submission_input_readback_mismatch")


def validate_loopback(url: str) -> None:
    parsed = urlparse(url)
    require(parsed.scheme == "http", "ingress_url_must_be_loopback_http")
    require((parsed.hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}, "ingress_url_must_be_loopback")
    require(parsed.path == "/intr/materialization", "ingress_url_path_invalid")
    require(parsed.username is None and parsed.password is None, "ingress_url_credentials_forbidden")


def materialize(runtime_root: Path, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    require(not any(truthy(values.get(name)) for name in HOSTED), "hosted_environment_forbidden")
    runtime = runtime_root.expanduser().resolve()
    receipt_path = runtime / BINDING_RECEIPT_REL
    if not receipt_path.is_file():
        return {
            "schema": "stegverse.erl-active-research-intr-resident-local-input-materialization/v1",
            "state": "BINDING_NOT_MATERIALIZED",
            "task_id": TASK_ID,
            "input_materialized": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    receipt = load_json(receipt_path)
    require(receipt.get("schema") == BINDING_RECEIPT_SCHEMA, "binding_receipt_schema_invalid")
    require(receipt.get("task_id") == TASK_ID, "binding_receipt_task_mismatch")
    require(receipt.get("state") == "BINDING_MATERIALIZED_AWAITING_AUTHENTIC_INTR_SUBMISSION", "binding_receipt_state_not_ready")
    binding_ref = receipt.get("binding_ref")
    require(isinstance(binding_ref, str) and binding_ref.strip(), "binding_ref_required")
    binding_path = (runtime / binding_ref).resolve()
    require(runtime in binding_path.parents, "binding_ref_must_be_runtime_local")
    require(binding_path.is_file(), "binding_not_materialized")

    ingress_url = str(values.get(INGRESS_URL_ENV) or "").strip()
    if not ingress_url:
        return {
            "schema": "stegverse.erl-active-research-intr-resident-local-input-materialization/v1",
            "state": "INGRESS_NOT_MATERIALIZED",
            "task_id": TASK_ID,
            "missing_inputs": [INGRESS_URL_ENV],
            "input_materialized": False,
            "tvc_authorization_required": False,
            "tvc_authorization_created": False,
            "listener_created": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    validate_loopback(ingress_url)
    body = {
        "schema": INPUT_SCHEMA,
        "state": "READY",
        "task_id": TASK_ID,
        "binding_ref": binding_ref,
        "ingress_url": ingress_url,
        "transport_origin": TRANSPORT_ORIGIN,
        "transport_credential_required": False,
        "credential_authority": "TV/TVC",
        "request_grants_execution_authority": False,
        "provider_operation_authorized": False,
        "authority_effect": "NONE_INPUT_ONLY",
    }
    value = {**body, "input_hash": sha_uri(body)}
    write_atomic(runtime / OUTPUT_REL, value)
    return {
        "schema": "stegverse.erl-active-research-intr-resident-local-input-materialization/v1",
        "state": "INPUT_MATERIALIZED",
        "task_id": TASK_ID,
        "binding_ref": binding_ref,
        "input_ref": OUTPUT_REL.as_posix(),
        "input_hash": value["input_hash"],
        "input_materialized": True,
        "transport_origin": TRANSPORT_ORIGIN,
        "tvc_authorization_required": False,
        "tvc_authorization_created": False,
        "listener_created": False,
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
