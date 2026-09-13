#!/usr/bin/env python3
"""Fetch one bounded resident intent and dispatch an already-registered consumer.

This is the canonical resident-side implementation of RTC-RESIDENT-RENDEZVOUS-010.
The rendezvous is transport only: it creates no user verification, claim/fence,
Interlock/InTr admission, credential, scheduler, listener, or execution authority.
Each selected consumer keeps its own exact resident-request contract and downstream
authority checks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

DISPATCHER = Path("scripts/dispatch_resident_execution_requests.py")
DISPATCH_RECEIPT = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
RECEIPT_PATH = Path("receipts/sovereign-host/resident-rendezvous-consumption.latest.json")
SUPERSEDED_REQUEST_DIR = Path("receipts/sovereign-host/resident-rendezvous-superseded-requests")

RENDEZVOUS_REQUEST_SCHEMA = "stegverse.resident-rendezvous.request/v1"
FETCH_SCHEMA = "stegverse.resident-rendezvous.fetch-result/v1"
ACK_SCHEMA = "stegverse.resident-rendezvous.acknowledgement/v1"
ADVERTISEMENT_SCHEMA = "stegverse.resident-rendezvous.advertisement/v1"
RESIDENT_SCHEMA = "stegverse.resident-execution-request/v1"
ADVERTISEMENT_LEASE_SECONDS = 120

# Backward-compatible fixed-chain constants remain exported for existing callers/tests.
CONSUMER = "stegos_kv_intr_chain"
CURRENT_REQUEST_ID = "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003"
TASK_ID = "SHWP-STEGOS-KV-INTR-CHAIN-001"
MODE = "STEGOS_KV_INTR_CHAIN"
ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
STEPS = [
    "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
    "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
    "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
]
REQUEST_PATH = Path("control/resident-execution-request.d/stegos-kv-intr-chain-001.json")
CHAIN_RECEIPT = Path("receipts/sovereign-host/stegos-kv-intr-chain-consumption.latest.json")

GADI_CONSUMER = "gadi_runtime_observation"
GADI_REQUEST_PATH = Path("control/resident-execution-request.d/gadi-runtime-observation-001.json")
GADI_CHAIN_RECEIPT = Path("receipts/sovereign-host/gadi-runtime-observation-request-consumption.latest.json")
GADI_REQUEST_ID = "RESIDENT-OBSERVE-GADI-RUNTIME-001"
GADI_EXPECTED = {
    "schema": RESIDENT_SCHEMA,
    "request_id": GADI_REQUEST_ID,
    "state": "REQUESTED",
    "task_id": "GADI-RESIDENT-EXECUTION-001",
    "parent_task_id": "GADI-001",
    "mode": "GADI_RUNTIME_OBSERVATION",
    "entrypoint": "scripts/dispatch_gadi_resident_execution.py",
    "observation_steps": [
        "CURRENT_RETAINED_STEGBROWSER_STEGOS_NODE_DISCOVERY",
        "CURRENT_RETAINED_STEGBROWSER_STEGOS_CURRENT_IPHONE_RECEIPT_READBACK",
        "CURRENT_GADI_RUNTIME_BINDING",
    ],
    "credential_authority": "TV/TVC",
    "github_token_required": False,
    "github_token_runtime_authority": "NONE",
    "heartbeat_grants_execution_authority": False,
    "request_granted_authority": False,
    "network_source_fetch_allowed": False,
    "second_machine_required": False,
    "workercoordinator_may_be_visited_only_after_nonclaim_readiness": True,
    "authority_effect": "NONE_REQUEST_ONLY",
}

RESEAL_CONSUMER = "sdk_workspace_external_collab_client_secret_reseal"
RESEAL_REQUEST_PATH = Path("control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json")
RESEAL_CHAIN_RECEIPT = Path("receipts/sovereign-host/sdk-workspace-external-collab-client-secret-reseal.latest.json")
RESEAL_REQUEST_ID = "RESIDENT-EXEC-SDK-WORKSPACE-EXTCOLLAB-CLIENT-SECRET-RESEAL-001"
RESEAL_EXPECTED = {
    "schema": RESIDENT_SCHEMA,
    "request_id": RESEAL_REQUEST_ID,
    "state": "REQUESTED",
    "task_id": "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003",
    "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
    "selector": RESEAL_CONSUMER,
    "credential_authority": "TV/TVC",
    "github_token_required": False,
    "github_token_runtime_authority": "NONE",
    "heartbeat_grants_execution_authority": False,
    "second_machine_required": False,
    "network_source_fetch_allowed": False,
    "credential_material_allowed": False,
    "request_granted_authority": False,
    "tvc_root_locator_required": True,
    "tvc_reseal_script": "scripts/reseal_google_drive_external_collaboration_client_secret.py",
    "expected_tvc_reseal_script_git_blob": "fba3f668e08dba300cd994e85b3c70872fc1f8e6",
    "source_custody_receipt": "/var/lib/stegverse/skap/resident-sealed/google-drive-client-secret/custody-receipt.json",
    "target_custody_receipt": "/var/lib/stegverse/skap/resident-sealed/google-drive-external-collaboration-client-secret/custody-receipt.json",
    "resident_seal_activation_receipt": "/var/lib/stegverse/skap/resident-sealed/recipient-key.latest.json",
    "resident_private_key": "/run/stegverse/tv-tvc-credentials/SKAP_RESIDENT_SEAL_P256_PRIVATE.pem",
    "target_purpose": "google_drive.external_collaboration.client_secret",
    "personal_kv_source_purpose": "google_drive.personal_kv.client_secret",
    "target_existing_policy": "VALIDATE_PRESENCE_DO_NOT_OVERWRITE",
    "execution_requires_root": True,
    "authority_effect": "NONE_REQUEST_ONLY",
    "note": "One-time resident request to materialize the already-authorized external-collaboration Google OAuth client-secret ciphertext purpose from existing Personal-KV ciphertext using merged TVC PR #397. The request carries no credential material and grants no provider/runtime/governance authority.",
}

LISTENER_CONSUMER = "sdk_workspace_external_collab_consent_listener"
LISTENER_REQUEST_PATH = Path("control/resident-execution-request.d/sdk-workspace-external-collab-consent-listener-001.json")
LISTENER_CHAIN_RECEIPT = Path("receipts/sovereign-host/sdk-workspace-external-collab-consent-listener.latest.json")
LISTENER_REQUEST_ID = "RESIDENT-EXEC-SDK-WORKSPACE-EXTCOLLAB-CONSENT-LISTENER-001"
LISTENER_EXPECTED = {
    "schema": RESIDENT_SCHEMA,
    "state": "REQUESTED",
    "request_id": LISTENER_REQUEST_ID,
    "task_id": "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003",
    "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
    "selector": LISTENER_CONSUMER,
    "credential_authority": "TV/TVC",
    "github_token_required": False,
    "github_token_runtime_authority": "NONE",
    "heartbeat_grants_execution_authority": False,
    "second_machine_required": False,
    "network_source_fetch_allowed": False,
    "credential_material_allowed": False,
    "request_granted_authority": False,
    "execution_requires_root": True,
    "tvc_root_locator_required": True,
    "tvc_installer": "scripts/install_external_collab_google_drive_consent_service.py",
    "expected_tvc_installer_git_blob": "dae00dbec1a79d611a3184e185e04e6f29110348",
    "loopback_health_url": "http://127.0.0.1:8786/tvc/external-collaboration/google-drive/consent/health",
    "expected_client_secret_purpose": "google_drive.external_collaboration.client_secret",
    "required_nonsecret_environment": [
        "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID",
        "STEGVERSE_OWNER_BINDING_DIGEST",
        "STEGVERSE_STEGFIN_SOURCE_ROOT",
    ],
    "public_https_binding_allowed": False,
    "google_owner_consent_allowed": False,
    "provider_contact_allowed": False,
    "gateway_authority": False,
    "authority_effect": "NONE_REQUEST_ONLY",
}

CONSUMER_PROFILES: dict[str, dict[str, Any]] = {
    CONSUMER: {
        "request_path": REQUEST_PATH,
        "chain_receipt": CHAIN_RECEIPT,
        "current_request_id": CURRENT_REQUEST_ID,
        "validation": "stegos_kv_intr_chain",
    },
    GADI_CONSUMER: {
        "request_path": GADI_REQUEST_PATH,
        "chain_receipt": GADI_CHAIN_RECEIPT,
        "current_request_id": GADI_REQUEST_ID,
        "validation": "exact_gadi",
    },
    RESEAL_CONSUMER: {
        "request_path": RESEAL_REQUEST_PATH,
        "chain_receipt": RESEAL_CHAIN_RECEIPT,
        "current_request_id": RESEAL_REQUEST_ID,
        "validation": "exact_sdk_extcollab_reseal",
    },
    LISTENER_CONSUMER: {
        "request_path": LISTENER_REQUEST_PATH,
        "chain_receipt": LISTENER_CHAIN_RECEIPT,
        "current_request_id": LISTENER_REQUEST_ID,
        "validation": "exact_sdk_extcollab_listener",
    },
}

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


def _profile(consumer: str) -> dict[str, Any]:
    profile = CONSUMER_PROFILES.get(consumer)
    if profile is None:
        raise ResidentRendezvousConsumerError("consumer not registered for resident rendezvous")
    return profile


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
            if key.lower() in FORBIDDEN_FIELD_NAMES:
                raise ResidentRendezvousConsumerError(f"forbidden field at {path}.{key}")
            _reject_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_fields(child, f"{path}[{index}]")


def _validate_stegos_kv_request(value: Mapping[str, Any]) -> dict[str, Any]:
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


def validate_resident_request(value: Any, *, consumer: str = CONSUMER) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResidentRendezvousConsumerError("resident request must be an object")
    _reject_forbidden_fields(value)
    profile = _profile(consumer)
    rendered = dict(value)
    if profile["validation"] == "stegos_kv_intr_chain":
        return _validate_stegos_kv_request(value)
    if profile["validation"] == "exact_gadi":
        if rendered != GADI_EXPECTED:
            raise ResidentRendezvousConsumerError("GADI runtime-observation request contract mismatch")
        return rendered
    if profile["validation"] == "exact_sdk_extcollab_reseal":
        if rendered != RESEAL_EXPECTED:
            raise ResidentRendezvousConsumerError("SDK external-collaboration reseal request contract mismatch")
        return rendered
    if profile["validation"] == "exact_sdk_extcollab_listener":
        if rendered != LISTENER_EXPECTED:
            raise ResidentRendezvousConsumerError("SDK external-collaboration consent-listener request contract mismatch")
        return rendered
    raise ResidentRendezvousConsumerError("resident rendezvous validation profile unsupported")


def validate_fetch(
    value: Any,
    *,
    node_ref: str,
    now: datetime | None = None,
    consumer: str = CONSUMER,
) -> dict[str, Any] | None:
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
    if request.get("consumer") != consumer:
        raise ResidentRendezvousConsumerError("consumer mismatch")
    if request.get("authority_effect") != "NONE_REQUEST_ONLY":
        raise ResidentRendezvousConsumerError("request authority effect mismatch")
    resident = validate_resident_request(request.get("resident_request"), consumer=consumer)
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
        "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT", "STEGVERSE_RELAY_RUNTIME_BASE",
        "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID", "STEGVERSE_OWNER_BINDING_DIGEST",
        "STEGVERSE_STEGFIN_SOURCE_ROOT", "STEGVERSE_TVC_ROOT",
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


def _allowed_request_supersession(existing: Mapping[str, Any], current: Mapping[str, Any]) -> bool:
    legacy_steps = [
        "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
        "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
        "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
        "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001",
    ]
    same_contract_keys = (
        "schema", "state", "task_id", "mode", "entrypoint", "credential_authority",
        "github_token_required", "github_token_runtime_authority",
        "heartbeat_grants_execution_authority", "request_granted_authority",
        "network_source_fetch_allowed", "second_machine_required", "authority_effect",
    )
    existing_id = existing.get("request_id")
    current_id = current.get("request_id")
    if existing_id not in {
        "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-001",
        "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-002",
    }:
        return False
    if current_id != CURRENT_REQUEST_ID:
        return False
    if any(existing.get(key) != current.get(key) for key in same_contract_keys):
        return False
    if current.get("steps") != STEPS:
        return False
    return existing.get("steps") in (STEPS, legacy_steps)


def materialize_request(
    runtime_root: Path,
    resident_request: Mapping[str, Any],
    *,
    consumer: str = CONSUMER,
) -> Path:
    profile = _profile(consumer)
    path = runtime_root / profile["request_path"]
    validated = validate_resident_request(resident_request, consumer=consumer)
    if path.is_file():
        existing = load_json(path)
        if canonical_json(existing) == canonical_json(validated):
            return path
        if consumer != CONSUMER or not _allowed_request_supersession(existing, validated):
            raise ResidentRendezvousConsumerError("local resident request differs from rendezvous request")
        archive_hash = sha256_uri(existing)[7:]
        archive = runtime_root / SUPERSEDED_REQUEST_DIR / f"{archive_hash}.json"
        atomic_json(archive, existing)
        if load_json(archive) != existing:
            raise ResidentRendezvousConsumerError("superseded resident request archive verification failed")
        atomic_json(path, validated)
        if load_json(path) != validated:
            raise ResidentRendezvousConsumerError("resident request supersession verification failed")
        return path
    atomic_json(path, validated)
    return path


def _advertisement(
    *,
    node_ref: str,
    consumer: str = CONSUMER,
    now: datetime | None = None,
) -> dict[str, Any]:
    profile = _profile(consumer)
    advertised = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = advertised + timedelta(seconds=ADVERTISEMENT_LEASE_SECONDS)
    return {
        "schema": ADVERTISEMENT_SCHEMA,
        "target_node_ref": node_ref,
        "consumer": consumer,
        "current_resident_request_id": profile["current_request_id"],
        "advertised_at": advertised.isoformat(),
        "expires_at": expires.isoformat(),
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "advertisement_grants_authority": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }


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


def _consumer_outcome(consumer: str, chain: Mapping[str, Any]) -> tuple[str, bool]:
    state = str(chain.get("state") or "ATTEMPT_RECORDED")
    if consumer == CONSUMER:
        terminal = bool(chain.get("terminal_chain_observed") is True and state == "COMPLETED")
        if state not in {"ATTEMPT_RECORDED", "COMPLETED", "BLOCKED", "NO_REQUEST"}:
            state = "ATTEMPT_RECORDED"
        return state, terminal
    if consumer == GADI_CONSUMER:
        if state == "OBSERVATION_REQUEST_BLOCKED_FAIL_CLOSED":
            return "BLOCKED", False
        if state == "OBSERVATION_ATTEMPT_RECORDED":
            return "ATTEMPT_RECORDED", False
        return "ATTEMPT_RECORDED", False
    if consumer == RESEAL_CONSUMER:
        if state in {"COMPLETED", "TARGET_ALREADY_PRESENT"}:
            return "COMPLETED", True
        if state == "BLOCKED":
            return "BLOCKED", False
        return "ATTEMPT_RECORDED", False
    if consumer == LISTENER_CONSUMER:
        if state in {"COMPLETED", "SERVICE_ALREADY_HEALTHY"}:
            return "COMPLETED", True
        if state == "BLOCKED":
            return "BLOCKED", False
        return "ATTEMPT_RECORDED", False
    return "ATTEMPT_RECORDED", False


def consume(
    runtime_root: Path,
    *,
    base_url: str,
    node_ref: str,
    source_root: Path | None = None,
    consumer: str = CONSUMER,
    runner=subprocess.run,
    getter=http_get_json,
    poster=http_post_json,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    profile = _profile(consumer)
    runtime = runtime_root.expanduser().resolve()
    source = (source_root or runtime).expanduser().resolve()
    endpoint = validate_endpoint(base_url)
    safe = safe_env(env)
    advertisement = _advertisement(node_ref=node_ref, consumer=consumer)
    advertisement_result = poster(
        endpoint + "/api/resident-rendezvous/v1/advertisements",
        advertisement,
        node_ref=node_ref,
    )
    if not isinstance(advertisement_result, Mapping) or advertisement_result.get("state") != "ADVERTISED":
        raise ResidentRendezvousConsumerError("resident advertisement not accepted")
    if advertisement_result.get("gateway_execution_authority") != "NONE":
        raise ResidentRendezvousConsumerError("resident advertisement gateway authority mismatch")
    fetch_url = (
        endpoint
        + "/api/resident-rendezvous/v1/requests?target_node_ref="
        + quote(node_ref, safe="")
    )
    fetch = getter(fetch_url, node_ref=node_ref)
    request = validate_fetch(fetch, node_ref=node_ref, consumer=consumer)
    if request is None:
        receipt = {
            "schema": "stegverse.resident-rendezvous.local-consumption/v1",
            "state": "NO_REQUEST",
            "consumer": consumer,
            "target_node_ref": node_ref,
            "runtime_execution_attempted": False,
            "network_request_carrier_used": True,
            "network_source_fetch_performed": False,
            "resident_advertisement_state": advertisement_result.get("state"),
            "resident_advertisement_grants_authority": False,
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "user_verification_authority": "KV/SKAP Vault",
            "target_node_identity_role": "ROUTING_ONLY",
            "authority_effect": "NONE",
        }
        atomic_json(runtime / RECEIPT_PATH, receipt)
        return receipt

    materialize_request(runtime, request["resident_request"], consumer=consumer)
    dispatcher = runtime / DISPATCHER
    if not dispatcher.is_file():
        raise ResidentRendezvousConsumerError("resident dispatcher not materialized")
    completed = runner(
        [
            sys.executable,
            str(dispatcher),
            "--source-root", str(source),
            "--runtime-root", str(runtime),
            "--only-consumer", consumer,
        ],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=safe,
        timeout=1800,
    )
    dispatch = load_json(runtime / DISPATCH_RECEIPT) if (runtime / DISPATCH_RECEIPT).is_file() else {}
    chain_rel: Path = profile["chain_receipt"]
    chain = load_json(runtime / chain_rel) if (runtime / chain_rel).is_file() else {}
    local_state, terminal = _consumer_outcome(consumer, chain)
    refs = [str(DISPATCH_RECEIPT)]
    if (runtime / chain_rel).is_file():
        refs.append(str(chain_rel))
    ack = _ack(request=request, node_ref=node_ref, state=local_state, terminal=terminal, refs=refs)
    ack_result = poster(
        endpoint + "/api/resident-rendezvous/v1/acknowledgements",
        ack,
        node_ref=node_ref,
    )
    receipt_state = "COMPLETED" if terminal else ("BLOCKED" if local_state == "BLOCKED" else "ATTEMPT_RECORDED")
    receipt = {
        "schema": "stegverse.resident-rendezvous.local-consumption/v1",
        "state": receipt_state,
        "consumer": consumer,
        "rendezvous_request_id": request["request_id"],
        "resident_request_sha256": request["resident_request_sha256"],
        "target_node_ref": node_ref,
        "target_node_identity_role": "ROUTING_ONLY",
        "dispatcher_returncode": completed.returncode,
        "dispatch_state": dispatch.get("state"),
        "chain_state": chain.get("state"),
        "terminal_chain_observed": terminal,
        "acknowledgement_state": ack_result.get("state") if isinstance(ack_result, dict) else None,
        "resident_advertisement_state": advertisement_result.get("state"),
        "resident_advertisement_grants_authority": False,
        "runtime_execution_attempted": True,
        "network_request_carrier_used": True,
        "network_source_fetch_performed": False,
        "source_repository_mutated": False,
        "gateway_execution_authority": "NONE",
        "worker_coordinator_remains_execution_admission_authority": True,
        "credential_authority": "TV/TVC",
        "user_verification_authority": "KV/SKAP Vault",
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
    parser.add_argument(
        "--consumer",
        default=os.getenv("STEGVERSE_RESIDENT_RENDEZVOUS_CONSUMER", CONSUMER),
        choices=sorted(CONSUMER_PROFILES),
    )
    args = parser.parse_args()
    if not args.base_url or not args.node_ref:
        result = {
            "schema": "stegverse.resident-rendezvous.local-consumption/v1",
            "state": "NOT_CONFIGURED",
            "consumer": args.consumer,
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
        consumer=args.consumer,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST", "ATTEMPT_RECORDED", "COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
