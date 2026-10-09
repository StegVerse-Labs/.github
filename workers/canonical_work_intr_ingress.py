#!/usr/bin/env python3
"""Reusable Canonical Work admission adapter for the existing Universal InTr ingress.

This module does not start a server. The existing Universal InTr ingress owns the
network listener. This adapter validates one CanonicalWork request, persists its
write-once ingress receipt, and dispatches the non-authorizing coordination
consumer. HB32 carrier data is validated as reference/transport evidence only.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import serve_hil_intr_materialization_ingress as transport_boundary  # noqa: E402
from consume_canonical_work_intr_materialization_request import (  # noqa: E402
    DESTINATION,
    DOWNSTREAM_OWNER,
    validate_request,
)


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


# The A4 contract, byte-identical to StegVerse-org/.github@f791799. It asks the
# TV/TVC credential authority and reads its receipt; it holds no key and no
# verification algorithm, and neither does this worker.
origin_attestation = _load("origin_attestation", "org-boundary/runtime/origin_attestation.py")

INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"
RECEIPT_DIR_REL = Path("receipts/sovereign-network/canonical-work-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/canonical-work-intr-ingress.latest.json")
REQUEST_DIR_REL = Path("intr-materialization")
# TVC_RELAY_EGRESS is admitted only on a TV/TVC receipt for this statement.
A4_VERIFIER_PREDICATE = "A4_TV_TVC_ORIGIN_VERIFIER_PRESENT_AT_CUSTODY_OWNER"
RETRY_ENTRYPOINT = "workers/canonical_work_intr_ingress.py::admit"
FAIL_CLOSED_SCHEMA = "stegverse.canonical-work-intr-ingress-fail-closed/v1"
DESTINATION_ORGANIZATION = "StegVerse-Labs"
DESTINATION_SERVICE = DESTINATION["subsystem"]
ORIGIN_ORGANIZATION_HEADER = "X-StegVerse-Origin-Organization"
ORIGIN_ATTESTATION_HEADER = "X-StegVerse-Origin-Attestation"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_canonical_work_request(value: Any) -> bool:
    return isinstance(value, dict) and value.get("destination") == DESTINATION and value.get("downstream_owner_ref") == DOWNSTREAM_OWNER


def _envelope_request(payload: Any) -> Any:
    entry = payload.get("node_outbox_entry") if isinstance(payload, dict) else None
    return entry.get("materialization_request") if isinstance(entry, dict) else None


def is_canonical_work(payload: Any) -> bool:
    """Route predicate: an exact CanonicalWork request or a node envelope carrying one."""
    return _is_canonical_work_request(payload) or _is_canonical_work_request(_envelope_request(payload))


def scrubbed_env() -> dict[str, str]:
    import os
    child = dict(os.environ)
    for key in ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS", "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


class OriginAttestationFailClosed(ValueError):
    """A relay origin this ingress will not admit, carrying its no-effect record."""

    def __init__(self, failed_predicate: str, reason: str) -> None:
        super().__init__(failed_predicate)
        self.failed_predicate = failed_predicate
        self.record = {
            "schema": FAIL_CLOSED_SCHEMA,
            "state": "FAIL_CLOSED",
            "disposition": "FAIL_CLOSED",
            "transport_origin": transport_boundary.ORIGIN_RELAY,
            "failed_predicate": failed_predicate,
            "detail": reason,
            "retry_entrypoint": RETRY_ENTRYPOINT,
            "admission_attempted": True,
            "queue_written": False,
            "receipt_written": False,
            "origin_attestation": origin_attestation.refusal_record(failed_predicate, reason),
            "authority_effect": "NONE_NO_EFFECT",
        }


def relay_statement(request: Mapping[str, Any], *, origin_organization: str | None, request_sha256: str) -> dict[str, Any]:
    """The A4 statement for one relayed request, rebuilt by this receiver.

    Nothing of it travels beside the signature: the origin is the one the relay
    declared, the destination is this ingress, the packet is the request id and
    the payload is the digest of the exact request body.
    """
    return origin_attestation.statement(
        origin_organization=origin_organization,
        destination_organization=DESTINATION_ORGANIZATION,
        destination_service=DESTINATION_SERVICE,
        packet_id=request.get("materialization_id"),
        payload_sha256=request_sha256,
        transport_profile=transport_boundary.ORIGIN_RELAY,
    )


def _carried_signature(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def require_relay_origin_attestation(request: Mapping[str, Any], transport: Mapping[str, str | None],
                                     origin_verifier: Callable[..., Mapping[str, Any]] | None) -> dict[str, Any]:
    """Admit TVC_RELAY_EGRESS only on TV/TVC's own receipt that it signed this statement.

    The verifier is the custody owner's TV/TVC surface, injected by the caller or
    materializer. There is no default and no environment fallback: an absent
    verifier is a hold, never a pass, and a refusal carries the attestation's own
    predicate. Either is FAIL_CLOSED before any queue entry or receipt exists.
    """
    if origin_verifier is None:
        raise OriginAttestationFailClosed(
            A4_VERIFIER_PREDICATE,
            "no " + origin_attestation.VERIFY_OPERATION + " surface was supplied to this ingress")
    try:
        declared = relay_statement(request, origin_organization=transport.get("origin_organization"),
                                   request_sha256=str(transport.get("payload_sha256") or ""))
        receipt = origin_attestation.verify(declared, _carried_signature(transport.get("origin_attestation")), origin_verifier)
    except origin_attestation.AttestationRefused as refused:
        raise OriginAttestationFailClosed(refused.failed_predicate, refused.reason) from None
    return origin_attestation.record(declared, _carried_signature(transport.get("origin_attestation")), receipt)


def bound_request(payload: Any, transport: Mapping[str, str | None], *,
                  origin_verifier: Callable[..., Mapping[str, Any]] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply the origin-specific checks that must hold before ALLOW.

    Node origin: the payload must be a node-trigger/outbox envelope that passes the
    HIL ingress's own envelope validator. Relay origin: the exact request, its
    digest, and TV/TVC's verification receipt for the A4 statement binding both.
    A carrier binding is never origin.
    """
    origin = transport.get("origin")
    if origin == transport_boundary.ORIGIN_NODE:
        require(_is_canonical_work_request(_envelope_request(payload)), "node_outbox_canonical_work_envelope_required")
        return transport_boundary.extract_materialization(payload, transport, request_validator=validate_request)
    require(origin == transport_boundary.ORIGIN_RELAY, "transport_origin_header_invalid")
    require(isinstance(payload, dict), "request_object_required")
    require(_is_canonical_work_request(payload), "canonical_work_destination_mismatch")
    validate_request(payload)
    require(len(str(transport.get("payload_sha256") or "")) == 64, "relay_exact_request_digest_invalid")
    attested = require_relay_origin_attestation(payload, transport, origin_verifier)
    request, source = transport_boundary.extract_materialization(payload, transport, request_validator=validate_request)
    return request, {**source, "origin_attestation": attested}


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str],
          origin_verifier: Callable[..., Mapping[str, Any]] | None = None) -> dict[str, Any]:
    transport = transport_boundary.validate_transport_headers(headers, body)
    if transport.get("origin") == transport_boundary.ORIGIN_RELAY:
        transport = {**transport,
                     "origin_organization": str(headers.get(ORIGIN_ORGANIZATION_HEADER, "")) or None,
                     "origin_attestation": str(headers.get(ORIGIN_ATTESTATION_HEADER, "")) or None}
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    request, source = bound_request(payload, transport, origin_verifier=origin_verifier)

    materialization_id = str(request["materialization_id"])
    request_path = runtime_root / REQUEST_DIR_REL / f"{materialization_id}.json"
    request_raw = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(request_path, request_raw)

    receipt_path = runtime_root / RECEIPT_DIR_REL / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED"
                and existing.get("transport_origin") == source["transport_origin"] and existing.get("outbox_entry_hash") == source["outbox_entry_hash"], "write_once_collision")
        return existing

    receipt = {
        "schema": INGRESS_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "disposition": "ALLOW",
        "disposition_authority": "INTERLOCK_INTR",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": source["transport_origin"],
        "transport_authorization_id": source["transport_authorization_id"],
        "node_id": source["node_id"],
        "interlock_id": source["interlock_id"],
        "outbox_entry_hash": source["outbox_entry_hash"],
        "transport_payload_sha256": transport.get("payload_sha256"),
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "carrier_binding_present": request.get("carrier_binding") is not None,
        "carrier_binding_grants_authority": False,
        "runtime_execution_attempted": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "INGRESS_TRANSITION_ONLY",
        "admitted_at": now()
    }
    if source["transport_origin"] == transport_boundary.ORIGIN_RELAY:
        receipt["origin_attestation"] = source["origin_attestation"]
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(receipt_path, raw)
    latest = runtime_root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)

    process = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "consume_canonical_work_intr_materialization_request.py"),
            "--runtime-root",
            str(runtime_root),
            "--materialization-id",
            materialization_id,
        ],
        cwd=str(ROOT),
        env=scrubbed_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return {
        **receipt,
        "dispatch": {
            "consumer_dispatch_attempted": True,
            "consumer_pid": process.pid,
            "consumer_execution_authority": False,
            "consumer_claim_or_fence_minted_by_ingress": False,
            "authority_effect": "NONE_DISPATCH_ONLY"
        }
    }


__all__ = ["A4_VERIFIER_PREDICATE", "DESTINATION", "DOWNSTREAM_OWNER", "INGRESS_SCHEMA", "OriginAttestationFailClosed", "is_canonical_work", "bound_request", "relay_statement", "admit"]
