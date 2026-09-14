#!/usr/bin/env python3
"""Submit one exact SDK external-collaboration request through RTC-RESIDENT-RENDEZVOUS-010.

This is a non-authorizing request carrier. It discovers one currently advertised
established Node for an exact admitted consumer, binds the active Goal/COSV/static
invocation manifest into a transport-correlation reference, and stores the already-
canonical inner resident request at the existing Service Gateway rendezvous.

It does not establish a Node, verify a user, claim/fence work, grant InTr admission,
acquire credentials, contact a provider, or treat submission as execution evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004"
COSV = "71000000100110"
MANIFEST = Path("control/resident-rendezvous-invocation.d/sdk-workspace-extcollab-authentic-runtime-004.json")
RECEIPT = Path("receipts/sovereign-host/sdk-workspace-extcollab-rendezvous-submission.latest.json")
SCHEMA = "stegverse.resident-rendezvous.request/v1"
NODE_RE = re.compile(r"^SV-NODE-[0-9a-f]{24}$")
CONSUMERS = {
    "sdk_workspace_external_collab_client_secret_reseal": Path(
        "control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json"
    ),
    "sdk_workspace_external_collab_consent_listener": Path(
        "control/resident-execution-request.d/sdk-workspace-external-collab-consent-listener-001.json"
    ),
}


class RendezvousSubmissionError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RendezvousSubmissionError(f"expected JSON object: {path}")
    return value


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_endpoint(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RendezvousSubmissionError("rendezvous endpoint must use https or loopback http")
    return value.rstrip("/")


def http_get_json(url: str, *, timeout: int = 20) -> dict[str, Any]:
    request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "StegVerse-ExtCollab-Rendezvous-Submitter/1"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post_json(url: str, payload: Mapping[str, Any], *, authorization_ref: str, timeout: int = 20) -> dict[str, Any]:
    raw = json.dumps(dict(payload), separators=(",", ":")).encode("utf-8")
    request = Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-StegVerse-Authorization-Id": authorization_ref,
            "User-Agent": "StegVerse-ExtCollab-Rendezvous-Submitter/1",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def validate_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schema") != "stegverse.resident-rendezvous.goal-invocation-binding/v1":
        raise RendezvousSubmissionError("invocation binding schema mismatch")
    if value.get("task_id") != TASK_ID or value.get("cosv_task_vector") != COSV:
        raise RendezvousSubmissionError("Goal/COSV invocation binding mismatch")
    if value.get("component") != "RTC-RESIDENT-RENDEZVOUS-010":
        raise RendezvousSubmissionError("resident rendezvous component binding mismatch")
    if value.get("target_node_role") != "ROUTING_AND_RUNTIME_EVIDENCE_CORRELATION_ONLY":
        raise RendezvousSubmissionError("Node role mismatch")
    if value.get("physical_device_identity_gate") != "NONE_PROHIBITED":
        raise RendezvousSubmissionError("physical device identity gate must remain prohibited")
    if value.get("user_verification_authority") != "KV/SKAP Vault":
        raise RendezvousSubmissionError("KV/SKAP user-verification authority mismatch")
    if value.get("gateway_execution_authority") != "NONE":
        raise RendezvousSubmissionError("Gateway execution authority must remain NONE")
    if value.get("authority_effect") != "NONE_INVOCATION_BINDING_ONLY":
        raise RendezvousSubmissionError("invocation binding authority effect mismatch")
    admitted = value.get("allowed_consumers")
    if not isinstance(admitted, dict) or set(admitted) != set(CONSUMERS):
        raise RendezvousSubmissionError("invocation consumer allowlist mismatch")
    return dict(value)


def validate_inner_request(consumer: str, request: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    if consumer not in CONSUMERS:
        raise RendezvousSubmissionError("consumer not admitted")
    expected = manifest["allowed_consumers"][consumer]
    if request.get("schema") != "stegverse.resident-execution-request/v1":
        raise RendezvousSubmissionError("resident request schema mismatch")
    if request.get("state") != "REQUESTED" or request.get("mode") != "TARGETED_INDEPENDENT_TASK_CONTROL":
        raise RendezvousSubmissionError("resident request state/mode mismatch")
    if request.get("selector") != consumer or request.get("request_id") != expected.get("request_id"):
        raise RendezvousSubmissionError("resident request selector/id mismatch")
    if request.get("credential_authority") != "TV/TVC":
        raise RendezvousSubmissionError("credential authority mismatch")
    if request.get("request_granted_authority") is not False:
        raise RendezvousSubmissionError("resident request must not grant authority")
    if request.get("network_source_fetch_allowed") is not False:
        raise RendezvousSubmissionError("network source fetch must remain disabled")
    if request.get("second_machine_required") is not False:
        raise RendezvousSubmissionError("second-machine requirement prohibited")
    return dict(request)


def validate_discovery(value: Mapping[str, Any], consumer: str) -> str:
    if value.get("schema") != "stegverse.resident-rendezvous.discovery/v1":
        raise RendezvousSubmissionError("rendezvous discovery schema mismatch")
    if value.get("consumer") != consumer:
        raise RendezvousSubmissionError("rendezvous discovery consumer mismatch")
    if value.get("gateway_execution_authority") != "NONE" or value.get("discovery_grants_authority") is not False:
        raise RendezvousSubmissionError("rendezvous discovery authority boundary mismatch")
    state = value.get("state")
    if state != "AVAILABLE":
        raise RendezvousSubmissionError(f"established Node rendezvous unavailable: {state}")
    node_ref = str(value.get("target_node_ref") or "")
    if not NODE_RE.fullmatch(node_ref):
        raise RendezvousSubmissionError("canonical established Node ref required")
    return node_ref


def build_envelope(
    *,
    consumer: str,
    node_ref: str,
    resident_request: Mapping[str, Any],
    manifest: Mapping[str, Any],
    submitted_at: datetime,
    lease_seconds: int = 600,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if lease_seconds < 1 or lease_seconds > 3600:
        raise RendezvousSubmissionError("request lease must be between 1 and 3600 seconds")
    resident_digest = sha256_uri(resident_request)
    manifest_digest = sha256_uri(manifest)
    submitted = submitted_at.astimezone(timezone.utc)
    expires = submitted + timedelta(seconds=lease_seconds)
    correlation_context = {
        "schema": "stegverse.resident-rendezvous.transport-correlation-context/v1",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "component": "RTC-RESIDENT-RENDEZVOUS-010",
        "consumer": consumer,
        "target_node_ref": node_ref,
        "resident_request_sha256": resident_digest,
        "invocation_manifest_sha256": manifest_digest,
        "submitted_at": submitted.isoformat(),
        "node_identity_role": "ROUTING_AND_RUNTIME_EVIDENCE_CORRELATION_ONLY",
        "authority_effect": "NONE_CORRELATION_ONLY",
    }
    correlation = "transport-correlation:" + sha256_uri(correlation_context)
    request_suffix = hashlib.sha256(canonical_json(correlation_context).encode("utf-8")).hexdigest()[:16]
    envelope = {
        "schema": SCHEMA,
        "request_id": f"SDK-EXTCOLLAB-004-{request_suffix}",
        "target_node_ref": node_ref,
        "consumer": consumer,
        "resident_request": dict(resident_request),
        "resident_request_sha256": resident_digest,
        "submitted_at": submitted.isoformat(),
        "expires_at": expires.isoformat(),
        "submitter_authorization_ref": correlation,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return envelope, correlation_context


def submit(
    *,
    source_root: Path,
    base_url: str,
    consumer: str,
    now: datetime | None = None,
    getter=http_get_json,
    poster=http_post_json,
) -> dict[str, Any]:
    root = source_root.expanduser().resolve()
    manifest = validate_manifest(load_json(root / MANIFEST))
    configured = manifest["allowed_consumers"][consumer]
    expected_ref = str(configured.get("resident_request_ref") or "")
    if Path(expected_ref) != CONSUMERS[consumer]:
        raise RendezvousSubmissionError("resident request path binding mismatch")
    inner = validate_inner_request(consumer, load_json(root / CONSUMERS[consumer]), manifest)
    endpoint = validate_endpoint(base_url)
    discovery = getter(endpoint + "/api/resident-rendezvous/v1/discovery?consumer=" + quote(consumer, safe=""))
    node_ref = validate_discovery(discovery, consumer)
    submitted_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    envelope, correlation_context = build_envelope(
        consumer=consumer,
        node_ref=node_ref,
        resident_request=inner,
        manifest=manifest,
        submitted_at=submitted_at,
    )
    result = poster(
        endpoint + "/api/resident-rendezvous/v1/requests",
        envelope,
        authorization_ref=envelope["submitter_authorization_ref"],
    )
    if not isinstance(result, Mapping) or result.get("state") != "PENDING":
        raise RendezvousSubmissionError("Gateway did not retain rendezvous request as PENDING")
    if result.get("gateway_execution_authority") != "NONE" or result.get("authority_effect") != "NONE_REQUEST_ONLY":
        raise RendezvousSubmissionError("Gateway request-store authority boundary mismatch")
    receipt = {
        "schema": "stegverse.sdk-extcollab.rendezvous-submission-receipt/v1",
        "state": "REQUEST_STORED_PENDING_RESIDENT_CONSUMPTION",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "component": "RTC-RESIDENT-RENDEZVOUS-010",
        "consumer": consumer,
        "target_node_ref": node_ref,
        "target_node_identity_role": "ROUTING_AND_RUNTIME_EVIDENCE_CORRELATION_ONLY",
        "invocation_manifest_sha256": sha256_uri(manifest),
        "resident_request_sha256": envelope["resident_request_sha256"],
        "rendezvous_request_id": envelope["request_id"],
        "transport_correlation_ref": envelope["submitter_authorization_ref"],
        "transport_correlation_context_sha256": sha256_uri(correlation_context),
        "gateway_store_state": result.get("state"),
        "gateway_execution_authority": "NONE",
        "workercoordinator_claim_fence_observed": False,
        "intr_admission_observed": False,
        "resident_execution_observed": False,
        "provider_contact_observed": False,
        "authority_effect": "NONE_REQUEST_SUBMISSION_AND_CORRELATION_ONLY",
    }
    atomic_json(root / RECEIPT, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--consumer", required=True, choices=sorted(CONSUMERS))
    args = parser.parse_args()
    result = submit(source_root=args.source_root, base_url=args.base_url, consumer=args.consumer)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
