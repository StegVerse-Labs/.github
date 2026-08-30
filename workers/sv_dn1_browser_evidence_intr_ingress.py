#!/usr/bin/env python3
"""Validate and materialize an authentic SV-DN-1 browser observation bundle.

This module is called by the shared profiled Universal InTr ingress. It performs
write-once local evidence materialization and may dispatch the already-admitted
sv_dn1 resident consumer. It grants no execution, SDK, governance, repository,
publication, credential, or certification authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Mapping

from workers import sv_dn1_sdk_browser_evidence_adapter as adapter

PROFILE = "SV-DN1:BrowserObservation"
ORIGIN = "STEGOS_WEB_BOOTSTRAP_EGRESS"
TRANSPORT_SCHEMA = "stegverse.sv-dn1.browser-observation-transport/v1"
INTERLOCK_SCHEMA = "stegverse.sv-dn1.browser-observation-interlock-receipt/v1"
INGRESS_RECEIPT_SCHEMA = "stegverse.sv-dn1.browser-observation-ingress-receipt/v1"
POLICY_ID = "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001"
TRANSPORT_PROFILE = "stegverse.universal-intr.adjacent-hop/v1"
BUNDLE_SCHEMA = "stegverse.sv-dn1.browser-resident-observation-bundle/v3"
BOUNDARY_FROM = "DEVICE_SYSTEM"
BOUNDARY_TO = "STEGOS_ECOSYSTEM"
EVIDENCE_REL = Path("evidence/sv-dn1-browser-observation")
LOCATOR_REL = Path("control/sv-dn1-browser-observation-locator.json")
INGRESS_RECEIPTS_REL = Path("receipts/sovereign-network/sv-dn1-browser-evidence-ingress")
INGRESS_LATEST_REL = Path("receipts/sovereign-network/sv-dn1-browser-evidence-ingress.latest.json")
DISPATCHER_REL = Path("scripts/dispatch_resident_execution_requests.py")
AUTHORITY_EFFECT = "NONE_INGRESS_ONLY"

FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AZURE_CLIENT_SECRET", "OAUTH_TOKEN",
)
SAFE_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_SV_DN1_SOURCE_ROOT", "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT", "STEGVERSE_SV_DN1_INTR_STATE_ROOT",
    "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_SDK_SOURCE_ROOT", "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _materialization_id(bundle_sha256: str) -> str:
    require(isinstance(bundle_sha256, str) and bundle_sha256.startswith("sha256:") and len(bundle_sha256) == 71, "bundle_sha256_invalid")
    digest = bundle_sha256[7:]
    require(all(ch in "0123456789abcdef" for ch in digest), "bundle_sha256_invalid")
    return "INTR-MAT-" + digest[:24]


def _validate_zero_authority(payload: Mapping[str, Any]) -> None:
    required_false = (
        "request_grants_execution_authority", "claim_or_fence_minted", "credential_used",
        "sdk_admitted", "governance_decision_made", "repository_writeback_performed",
        "deployment_performed", "publication_decision_made", "certification_claimed",
    )
    for field in required_false:
        require(payload.get(field) is False, field + "_must_be_false")
    require(payload.get("credential_authority") == "TV/TVC", "credential_authority_invalid")
    require(payload.get("github_token_runtime_authority") == "NONE", "github_token_runtime_authority_invalid")
    require(payload.get("authority_effect") == "NONE_TRANSPORT_ONLY", "authority_effect_invalid")


def _validate_interlock(receipt: Mapping[str, Any], *, materialization_id: str, bundle_sha256: str, node_id: str, device_id: str, journal_tail: str) -> str:
    require(receipt.get("schema") == INTERLOCK_SCHEMA, "source_interlock_schema_invalid")
    body = dict(receipt)
    claimed = body.pop("receipt_hash", None)
    require(isinstance(claimed, str) and claimed == sha_uri(body), "source_interlock_receipt_hash_mismatch")
    expected = {
        "role": "SOURCE_EGRESS_INTERLOCK",
        "materialization_id": materialization_id,
        "profile_id": "SV-DN-1",
        "node_id": node_id,
        "device_continuity_id": device_id,
        "bundle_sha256": bundle_sha256,
        "journal_tail_sha256": "sha256:" + journal_tail,
        "prior_receipt_hash": "sha256:" + journal_tail,
        "boundary_from": BOUNDARY_FROM,
        "boundary_to": BOUNDARY_TO,
        "transport_profile": TRANSPORT_PROFILE,
        "universal_intr_policy_id": POLICY_ID,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "authority_effect": "NONE",
    }
    for key, wanted in expected.items():
        require(receipt.get(key) == wanted, "source_interlock_binding_mismatch:" + key)
    return claimed


def validate_transport(payload: Mapping[str, Any]) -> dict[str, Any]:
    require(payload.get("schema") == TRANSPORT_SCHEMA, "transport_schema_invalid")
    require(payload.get("profile") == PROFILE, "transport_profile_name_invalid")
    require(payload.get("profile_id") == "SV-DN-1", "profile_id_invalid")
    require(payload.get("universal_intr_policy_id") == POLICY_ID, "universal_intr_policy_invalid")
    require(payload.get("transport_profile") == TRANSPORT_PROFILE, "transport_profile_invalid")
    require(payload.get("boundary_from") == BOUNDARY_FROM and payload.get("boundary_to") == BOUNDARY_TO, "transport_boundary_invalid")
    _validate_zero_authority(payload)

    bundle = payload.get("bundle")
    require(isinstance(bundle, dict), "browser_bundle_object_required")
    require(bundle.get("schema") == BUNDLE_SCHEMA, "browser_bundle_schema_invalid")
    require(bundle.get("state") == "OBSERVED", "browser_bundle_not_observed")
    require(bundle.get("observation_class") == "AUTHENTIC_ESTABLISHED_STEGVERSE_WEB_NODE", "browser_bundle_observation_class_invalid")

    # Reuse the canonical SDK-side validator so ingress and SDK admission cannot
    # diverge about journal replay, source digest, exchange identity, InTr policy,
    # destination validation, or claim/terminal/reconstruction lineage.
    adapter.validate(dict(bundle))

    registration = bundle.get("node_registration") or {}
    node_id = str(registration.get("node_id") or "")
    device_id = str(registration.get("device_continuity_id") or "")
    require(node_id.startswith("stegnode-web-") and len(node_id) > len("stegnode-web-"), "established_node_id_invalid")
    require(device_id.startswith("stegdevice-") and len(device_id) > len("stegdevice-"), "device_continuity_id_invalid")
    require(registration.get("state") == "ESTABLISHED" and registration.get("credential_authority") == "TV/TVC", "node_registration_invalid")
    require(payload.get("node_id") == node_id and payload.get("device_continuity_id") == device_id, "transport_node_device_binding_mismatch")

    bundle_sha256 = sha_uri(bundle)
    require(payload.get("bundle_sha256") == bundle_sha256, "bundle_sha256_mismatch")
    materialization_id = _materialization_id(bundle_sha256)
    require(payload.get("materialization_id") == materialization_id, "materialization_id_mismatch")

    replay = bundle.get("journal_replay") or {}
    journal_tail = str(replay.get("tail_sha256") or "")
    require(len(journal_tail) == 64 and all(ch in "0123456789abcdef" for ch in journal_tail), "journal_tail_invalid")
    source_interlock = payload.get("source_interlock_receipt")
    require(isinstance(source_interlock, dict), "source_interlock_receipt_required")
    interlock_hash = _validate_interlock(source_interlock, materialization_id=materialization_id, bundle_sha256=bundle_sha256, node_id=node_id, device_id=device_id, journal_tail=journal_tail)
    require(payload.get("previous_receipt_hash") == interlock_hash, "transport_previous_receipt_hash_mismatch")

    return {
        "materialization_id": materialization_id,
        "bundle": dict(bundle),
        "bundle_sha256": bundle_sha256,
        "node_id": node_id,
        "device_continuity_id": device_id,
        "journal_tail_sha256": journal_tail,
        "source_interlock_receipt_hash": interlock_hash,
    }


def _write_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == raw, "write_once_collision")
        return
    path.write_bytes(raw)
    require(path.read_bytes() == raw, "persistence_verification_failed")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    temp.write_text(json.dumps(dict(value), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def scrubbed_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    env = {name: source[name] for name in SAFE_ENV if source.get(name)}
    for name in FORBIDDEN_CREDENTIAL_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def dispatch_consumer(runtime_root: Path) -> dict[str, Any]:
    dispatcher = runtime_root / DISPATCHER_REL
    if not dispatcher.is_file():
        return {
            "consumer_dispatch_attempted": False,
            "consumer_dispatch_reason": "RUNTIME_DISPATCHER_NOT_MATERIALIZED",
            "consumer_execution_authority": False,
            "claim_or_fence_minted_by_ingress": False,
            "authority_effect": "NONE",
        }
    command = [
        sys.executable,
        str(dispatcher),
        "--source-root", str(runtime_root),
        "--runtime-root", str(runtime_root),
        "--only-consumer", "sv_dn1",
    ]
    process = subprocess.Popen(
        command,
        cwd=str(runtime_root),
        env=scrubbed_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return {
        "consumer_dispatch_attempted": True,
        "consumer_pid": process.pid,
        "consumer_execution_authority": False,
        "claim_or_fence_minted_by_ingress": False,
        "authority_effect": "NONE_DISPATCH_ONLY",
    }


def admit(*, runtime_root: Path, payload: Mapping[str, Any], transport_payload_sha256: str) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    validated = validate_transport(payload)
    materialization_id = validated["materialization_id"]
    bundle_path = runtime / EVIDENCE_REL / materialization_id / "bundle.json"
    bundle_raw = json.dumps(validated["bundle"], sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    _write_once(bundle_path, bundle_raw)

    locator = {
        "schema": "stegverse.sv-dn1.browser-observation-locator/v1",
        "state": "AVAILABLE_LOCAL_ONLY",
        "bundle_path": str(bundle_path),
        "bundle_sha256": validated["bundle_sha256"],
        "materialization_id": materialization_id,
        "credential_material_included": False,
        "network_fetch_performed": False,
        "authority_effect": "NONE_LOCAL_EVIDENCE_LOCATOR_ONLY",
    }
    _atomic_json(runtime / LOCATOR_REL, locator)

    receipt_path = runtime / INGRESS_RECEIPTS_REL / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("bundle_sha256") == validated["bundle_sha256"] and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return dict(existing)

    receipt = {
        "schema": INGRESS_RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "profile": PROFILE,
        "profile_id": "SV-DN-1",
        "materialization_id": materialization_id,
        "bundle_sha256": validated["bundle_sha256"],
        "node_id": validated["node_id"],
        "device_continuity_id": validated["device_continuity_id"],
        "journal_tail_sha256": validated["journal_tail_sha256"],
        "source_interlock_receipt_hash": validated["source_interlock_receipt_hash"],
        "previous_receipt_hash": validated["source_interlock_receipt_hash"],
        "transport_payload_sha256": transport_payload_sha256,
        "universal_intr_policy_id": POLICY_ID,
        "transport_profile": TRANSPORT_PROFILE,
        "boundary_from": BOUNDARY_FROM,
        "boundary_to": BOUNDARY_TO,
        "exact_bundle_validated": True,
        "journal_replay_validated": True,
        "source_interlock_validated": True,
        "destination_validation": "PASS",
        "lineage_verified": True,
        "write_once_persisted": True,
        "bundle_path": str(bundle_path),
        "locator_path": str(runtime / LOCATOR_REL),
        "locator_persisted": True,
        "consumer_dispatch_attempted": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "sdk_admitted": False,
        "governance_decision_made": False,
        "repository_writeback_performed": False,
        "deployment_performed": False,
        "publication_decision_made": False,
        "certification_claimed": False,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "github_token_runtime_authority": "NONE",
        "authority_effect": AUTHORITY_EFFECT,
        "admitted_at": now(),
    }
    _write_once(receipt_path, json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    latest = runtime / INGRESS_LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    dispatch = dispatch_consumer(runtime)
    return {**receipt, "dispatch": dispatch, "consumer_dispatch_attempted": bool(dispatch.get("consumer_dispatch_attempted"))}
