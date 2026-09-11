#!/usr/bin/env python3
"""Consume Site publication Universal InTr materialization requests.

This consumer is deliberately non-authorizing. It validates one exact
SITE_PUBLICATION_EVENT request already admitted into the sovereign runtime queue
and emits a write-once candidate receipt for the existing canonical
EVENT_EPHEMERAL runtime lane. It does not claim public reachability, content
equivalence, DNS/TLS recovery, or final publication admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegOS:SitePublicationRuntime"}
DOWNSTREAM_OWNER = "StegVerse-Labs/StegOS:canonical-runtime-lane"
OPERATION_ID = "SITE_PUBLICATION_EVENT"
BOUNDARY_PATH = ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]
REQUEST_DIR = Path("intr-materialization")
RECEIPT_DIR = Path("receipts/sovereign-host/site-publication-intr-consumer")
LATEST = Path("receipts/sovereign-host/site-publication-intr-consumer.latest.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def scrubbed_env(env: dict[str, str] | None = None) -> dict[str, str]:
    child = dict(os.environ if env is None else env)
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "operation_id": OPERATION_ID,
        "destination": DESTINATION,
        "boundary_path": BOUNDARY_PATH,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        require(request.get(key) == value, f"request_{key}_mismatch")
    mid = request.get("materialization_id")
    require(isinstance(mid, str) and mid.startswith("INTR-MAT-") and len(mid) == 33, "materialization_id_invalid")
    require(all(ch in "0123456789abcdef" for ch in mid[9:]), "materialization_id_invalid")
    for key in ("transport_intent_hash", "payload_hash", "request_hash"):
        value = request.get(key)
        require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71, f"{key}_invalid")
    require(isinstance(request.get("packet_id"), str) and request["packet_id"].startswith("INTR-"), "packet_id_invalid")
    require(isinstance(request.get("payload_ref"), str) and request["payload_ref"].startswith("artifact://site-publication-manifest/"), "payload_ref_invalid")
    require(request["payload_ref"].split("/")[-1] == request["payload_hash"].removeprefix("sha256:"), "payload_ref_hash_mismatch")
    body = dict(request)
    claimed = body.pop("request_hash")
    require(claimed == sha_uri(body), "request_hash_mismatch")


def consume(runtime_root: Path, materialization_id: str) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_DIR / f"{materialization_id}.json"
    require(request_path.is_file(), f"request_missing:{request_path}")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    require(isinstance(request, dict), "request_object_required")
    validate_request(request)
    require(request["materialization_id"] == materialization_id, "materialization_path_binding_mismatch")

    receipt = {
        "schema": "stegverse.site-publication-intr-materialization-consumption/v1",
        "state": "VALIDATED_FOR_EVENT_EPHEMERAL_RUNTIME_MATERIALIZATION",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "artifact_manifest_sha256": request["payload_hash"],
        "payload_ref": request["payload_ref"],
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
        "runtime_class": "EVENT_EPHEMERAL",
        "persistent_node_identity_required": True,
        "persistent_host_required": False,
        "always_on_receiver_required": False,
        "second_user_operated_device_required": False,
        "hosted_provider_required": False,
        "render_allowed": False,
        "canonical_runtime_owner": DOWNSTREAM_OWNER,
        "runtime_materialization_attempted": False,
        "runtime_execution_observed": False,
        "public_https_profile_observed": False,
        "exact_http_readback_observed": False,
        "content_equivalence_observed": False,
        "lease_closure_observed": False,
        "final_publication_transition_admitted": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted_by_consumer": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_CANDIDATE_ONLY",
        "validated_at": now(),
    }
    receipt["receipt_hash"] = sha_uri(receipt)
    out = runtime / RECEIPT_DIR / f"{materialization_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if out.exists():
        require(out.read_text(encoding="utf-8") == raw, "write_once_collision")
    else:
        out.write_text(raw, encoding="utf-8")
    latest = runtime / LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    receipt = consume(args.runtime_root, args.materialization_id)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
