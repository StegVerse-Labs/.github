#!/usr/bin/env python3
"""Fetch one bounded resident intent from the StegVerse Service Gateway and dispatch it locally."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

REQUEST_PATH = Path("control/resident-execution-request.d/stegos-kv-intr-chain-001.json")
DISPATCHER = Path("scripts/dispatch_resident_execution_requests.py")
CHAIN_RECEIPT = Path("receipts/sovereign-host/stegos-kv-intr-chain-consumption.latest.json")
DISPATCH_RECEIPT = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
RECEIPT_PATH = Path("receipts/sovereign-host/resident-rendezvous-consumption.latest.json")

RENDEZVOUS_REQUEST_SCHEMA = "stegverse.resident-rendezvous.request/v1"
FETCH_SCHEMA = "stegverse.resident-rendezvous.fetch-result/v1"
ACK_SCHEMA = "stegverse.resident-rendezvous.acknowledgement/v1"
RESIDENT_SCHEMA = "stegverse.resident-execution-request/v1"
CONSUMER = "stegos_kv_intr_chain"
TASK_ID = "SHWP-STEGOS-KV-INTR-CHAIN-001"
MODE = "STEGOS_KV_INTR_CHAIN"
ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
STEPS = [
    "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
    "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
    "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
]
HOSTED = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN",
)
FORBIDDEN_FIELD_NAMES = {
    "password", "secret", "credential", "credential_value", "private_key",
    "private_key_material", "token", "access_token", "refresh_token", "cookie",
    "mnemonic", "seed", "raw_biometric", "shell", "command", "argv",
}


class ResidentRendezvousConsumerError(RuntimeError):
    pass


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ResidentRendezvousConsumerError(f"expected JSON object: {path}")
    return value


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ResidentRendezvousConsumerError("timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ResidentRendezvousConsumerError("invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ResidentRendezvousConsumerError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _reject_forbidden_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ResidentRendezvousConsumerError(f"non-string field at {path}")
            lowered = key.lower()
            if lowered in FORBIDDEN_FIELD_NAMES:
                raise ResidentRendezvousConsumerError(f"forbidden field at {path}.{key}")
            _reject_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_fields(child, f"{path}[{index}]")


def validate_resident_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentRendezvousConsumerError("resident request must be an object")
    _reject_forbidden_fields(value)
    expected = {
        "schema": RESIDENT_SCHEMA,
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": ENTRYPOINT,
        "steps": STEPS,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ResidentRendezvousConsumerError(f"resident request {key} mismatch")
    if not isinstance(value.get("request_id"), str) or not value["request_id"]:
        raise ResidentRendezvousConsumerError("resident request id required")
    allowed = set(expected) | {"request_id", "note"}
    if set(value) - allowed:
        raise ResidentRendezvousConsumerError("resident request fields invalid")
    return dict(value)


def validate_fetch(value: Any, *, node_ref: str, now: datetime | None = None) -> dict[str, Any] | None:
    if not isinstance(value, Mapping) or value.get("schema") != FETCH_SCHEMA:
        raise ResidentRendezvousConsumerError("fetch response schema invalid")
    state = value.get("state")
    if state == "NO_REQUEST":
        return None
    if state != "REQUEST_AVAILABLE":
        raise ResidentRendezvousConsumerError("fetch response state invalid")
    if value.get("gateway_execution_authority") != "NONE":
        raise ResidentRendezvousConsumerError("gateway execution authority mismatch")
    if value.get("authority_effect") != "NONE_REQUEST_ONLY":
        raise ResidentRendezvousConsumerError("gateway authority effect mismatch")
    request = value.get("request")
    if not isinstance(request, Mapping):
        raise ResidentRendezvousConsumerError("rendezvous request missing")
    _reject_forbidden_fields(request)
    if request.get("schema") != RENDEZVOUS_REQUEST_SCHEMA:
        raise ResidentRendezvousConsumerError("rendezvous request schema invalid")
    if request.get("target_node_ref") != node_ref:
        raise ResidentRendezvousConsumerError("target node mismatch")
    if request.get("consumer") != CONSUMER:
        raise ResidentRendezvousConsumerError("consumer mismatch")
    if request.get("authority_effect") != "NONE_REQUEST_ONLY":
        raise ResidentRendezvousConsumerError("request authority effect mismatch")
    resident = validate_resident_request(request.get("resident_request"))
    if request.get("resident_request_sha256") != sha256_uri(resident):
        raise ResidentRendezvousConsumerError("resident request digest mismatch")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if _parse_time(request.get("expires_at")) <= current:
        raise ResidentRendezvousConsumerError("rendezvous request expired")
    return dict(request)


def safe_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    if hosted:
        raise ResidentRendezvousConsumerError(
            "hosted environment may not consume sovereign resident rendezvous"
        )
    credentialed = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(values.get(name))]
    if credentialed:
        raise ResidentRendezvousConsumerError(
            "credential-bearing environment forbidden for resident rendezvous"
        )
    allowed = (
        "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
        "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
        "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
        "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_STEGOS_ROOT",
        "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_DATA_ROOT", "STEGVERSE_RELAY_RUNTIME_BASE",
    )
    env = {name: values[name] for name in allowed if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_endpoint(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https":
        if parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ResidentRendezvousConsumerError("rendezvous endpoint must use https")
    return value.rstrip("/")


def http_get_json(url: str, *, node_ref: str, timeout: int = 20) -> dict[str, Any]:
    req = Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-StegVerse-Node-Ref": node_ref,
            "User-Agent": "StegVerse-Sovereign-Resident-Rendezvous/1",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post_json(url: str, payload: Mapping[str, Any], *, node_ref: str, timeout: int = 20) -> dict[str, Any]:
    raw = json.dumps(dict(payload), separators=(",", ":")).encode("utf-8")
    req = Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-StegVerse-Node-Ref": node_ref,
            "User-Agent": "StegVerse-Sovereign-Resident-Rendezvous/1",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def materialize_request(runtime_root: Path, resident_request: Mapping[str, Any]) -> Path:
    path = runtime_root / REQUEST_PATH
    validated = validate_resident_request(resident_request)
    if path.is_file():
        existing = load_json(path)
        if canonical_json(existing) == canonical_json(validated):
            return path
        # This v1 lane owns one exact resident request. A different local request
        # at the same canonical path is an ambiguity and must not be overwritten.
        raise ResidentRendezvousConsumerError("local resident request differs from rendezvous request")
    atomic_json(path, validated)
    return path


def _ack(
    *,
    request: Mapping[str, Any],
    node_ref: str,
    state: str,
    terminal: bool,
    refs: list[str],
) -> dict[str, Any]:
    return {
        "schema": ACK_SCHEMA,
        "request_id": request["request_id"],
        "target_node_ref": node_ref,
        "resident_request_sha256": request["resident_request_sha256"],
        "resident_consumption_state": state,
        "local_receipt_refs": refs,
        "terminal_chain_observed": terminal,
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
    }


def consume(
    runtime_root: Path,
    *,
    base_url: str,
    node_ref: str,
    source_root: Path | None = None,
    runner=subprocess.run,
    getter=http_get_json,
    poster=http_post_json,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    source = (source_root or runtime).expanduser().resolve()
    endpoint = validate_endpoint(base_url)
    safe = safe_env(env)
    fetch_url = (
        endpoint
        + "/api/resident-rendezvous/v1/requests?target_node_ref="
        + quote(node_ref, safe="")
    )
    fetch = getter(fetch_url, node_ref=node_ref)
    request = validate_fetch(fetch, node_ref=node_ref)
    if request is None:
        receipt = {
            "schema": "stegverse.resident-rendezvous.local-consumption/v1",
            "state": "NO_REQUEST",
            "target_node_ref": node_ref,
            "runtime_execution_attempted": False,
            "network_request_carrier_used": True,
            "network_source_fetch_performed": False,
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE",
        }
        atomic_json(runtime / RECEIPT_PATH, receipt)
        return receipt

    materialize_request(runtime, request["resident_request"])
    dispatcher = runtime / DISPATCHER
    if not dispatcher.is_file():
        raise ResidentRendezvousConsumerError("resident dispatcher not materialized")
    completed = runner(
        [
            sys.executable,
            str(dispatcher),
            "--source-root", str(source),
            "--runtime-root", str(runtime),
            "--only-consumer", CONSUMER,
        ],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=safe,
        timeout=1800,
    )
    dispatch = load_json(runtime / DISPATCH_RECEIPT) if (runtime / DISPATCH_RECEIPT).is_file() else {}
    chain = load_json(runtime / CHAIN_RECEIPT) if (runtime / CHAIN_RECEIPT).is_file() else {}
    terminal = bool(chain.get("terminal_chain_observed") is True and chain.get("state") == "COMPLETED")
    local_state = str(chain.get("state") or "ATTEMPT_RECORDED")
    if local_state not in {"ATTEMPT_RECORDED", "COMPLETED", "BLOCKED", "NO_REQUEST"}:
        local_state = "ATTEMPT_RECORDED"
    refs = [str(DISPATCH_RECEIPT)]
    if (runtime / CHAIN_RECEIPT).is_file():
        refs.append(str(CHAIN_RECEIPT))
    ack = _ack(request=request, node_ref=node_ref, state=local_state, terminal=terminal, refs=refs)
    ack_result = poster(
        endpoint + "/api/resident-rendezvous/v1/acknowledgements",
        ack,
        node_ref=node_ref,
    )
    receipt = {
        "schema": "stegverse.resident-rendezvous.local-consumption/v1",
        "state": "COMPLETED" if terminal else "ATTEMPT_RECORDED",
        "rendezvous_request_id": request["request_id"],
        "resident_request_sha256": request["resident_request_sha256"],
        "target_node_ref": node_ref,
        "dispatcher_returncode": completed.returncode,
        "dispatch_state": dispatch.get("state"),
        "chain_state": chain.get("state"),
        "terminal_chain_observed": terminal,
        "acknowledgement_state": ack_result.get("state") if isinstance(ack_result, dict) else None,
        "runtime_execution_attempted": True,
        "network_request_carrier_used": True,
        "network_source_fetch_performed": False,
        "source_repository_mutated": False,
        "gateway_execution_authority": "NONE",
        "worker_coordinator_remains_execution_admission_authority": True,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_REQUEST_CARRIER_AND_OBSERVATION_ONLY",
    }
    atomic_json(runtime / RECEIPT_PATH, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--base-url", default=os.getenv("STEGVERSE_RESIDENT_RENDEZVOUS_URL", ""))
    parser.add_argument("--node-ref", default=os.getenv("STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF", ""))
    args = parser.parse_args()
    if not args.base_url or not args.node_ref:
        result = {
            "schema": "stegverse.resident-rendezvous.local-consumption/v1",
            "state": "NOT_CONFIGURED",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 0
    result = consume(
        args.runtime_root,
        base_url=args.base_url,
        node_ref=args.node_ref,
        source_root=args.source_root,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST", "ATTEMPT_RECORDED", "COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
