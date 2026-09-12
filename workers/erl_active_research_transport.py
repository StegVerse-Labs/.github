#!/usr/bin/env python3
"""Transport-header validator for resident-local ERL active-research InTr admission.

This profile is intentionally scoped to ERL bindings intercepted by the existing
shared Universal InTr listener. It is not a generic HIL transport origin and it
cannot mint or claim TVC relay authorization. The logical ERL boundary path
remains EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV; this module
only describes how an already-materialized resident binding reaches the shared
loopback ingress.
"""
from __future__ import annotations

import hashlib
from typing import Mapping

ORIGIN = "STEGOS_RESIDENT_LOCAL"
MAX_REQUEST_BYTES = 512 * 1024


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_headers(headers: Mapping[str, str], body: bytes) -> dict[str, str | None]:
    require(len(body) <= MAX_REQUEST_BYTES, "request_body_too_large")
    transport = str(headers.get("X-StegVerse-Transport", ""))
    origin = str(headers.get("X-StegVerse-Transport-Origin", ""))
    authorization_id = str(headers.get("X-StegVerse-Authorization-Id", "")) or None
    supplied_hash = str(headers.get("X-StegVerse-Payload-SHA256", "")).lower()
    content_type = str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
    require(transport == "InTr", "transport_header_mismatch")
    require(origin == ORIGIN, "transport_origin_header_invalid")
    require(authorization_id is None, "resident_local_cannot_claim_tvc_relay_authorization")
    require(content_type == "application/json", "content_type_not_supported")
    require(len(supplied_hash) == 64 and all(ch in "0123456789abcdef" for ch in supplied_hash), "payload_sha256_header_invalid")
    actual = hashlib.sha256(body).hexdigest()
    require(supplied_hash == actual, "payload_sha256_header_mismatch")
    return {
        "transport": transport,
        "origin": origin,
        "authorization_id": None,
        "payload_sha256": supplied_hash,
        "payload_sha256_uri": "sha256:" + supplied_hash,
    }
