#!/usr/bin/env python3
"""Validate one manifested InTr out-and-return endpoint receipt journey."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = ("journey_id", "leg", "direction", "endpoint", "counterparty", "manifest_sha256")


def fail(code: str, detail: str) -> None:
    raise ValueError(f"{code}: {detail}")


def evidence(receipt: dict) -> dict:
    value = receipt.get("evidence")
    if not isinstance(value, dict):
        fail("JOURNEY_EVIDENCE_MISSING", "receipt evidence must be an object")
    missing = [key for key in REQUIRED if value.get(key) in (None, "")]
    if missing:
        fail("JOURNEY_CORRELATION_MISSING", ",".join(missing))
    return value


def validate(receipts: list[dict]) -> dict:
    if len(receipts) != 4:
        fail("JOURNEY_INCOMPLETE", f"expected 4 endpoint receipts, observed {len(receipts)}")

    a, b, c, d = [evidence(receipt) for receipt in receipts]
    if len({a["journey_id"], b["journey_id"], c["journey_id"], d["journey_id"]}) != 1:
        fail("JOURNEY_ID_MISMATCH", "all endpoint receipts must share one journey_id")

    expected = [(1, "EGRESS"), (1, "INGRESS"), (2, "EGRESS"), (2, "INGRESS")]
    actual = [(item["leg"], item["direction"]) for item in (a, b, c, d)]
    if actual != expected:
        fail("JOURNEY_SEQUENCE_INVALID", f"expected {expected!r}, observed {actual!r}")

    if a["manifest_sha256"] != b["manifest_sha256"]:
        fail("OUTBOUND_MANIFEST_MISMATCH", "outbound egress/ingress must bind the same manifest")
    if c["manifest_sha256"] != d["manifest_sha256"]:
        fail("RETURN_MANIFEST_MISMATCH", "return egress/ingress must bind the same manifest")
    if (
        c.get("predecessor_manifest_sha256") != a["manifest_sha256"]
        or d.get("predecessor_manifest_sha256") != a["manifest_sha256"]
    ):
        fail("RETURN_MANIFEST_PREDECESSOR_MISSING", "return leg must predecessor-link to the outbound manifest")

    if a["counterparty"] != b["endpoint"] or b["counterparty"] != a["endpoint"]:
        fail("OUTBOUND_HANDOFF_MISMATCH", "leg 1 endpoint/counterparty pair does not close")
    if c["counterparty"] != d["endpoint"] or d["counterparty"] != c["endpoint"]:
        fail("RETURN_HANDOFF_MISMATCH", "leg 2 endpoint/counterparty pair does not close")
    if a["endpoint"] != d["endpoint"] or b["endpoint"] != c["endpoint"]:
        fail("ROUNDTRIP_ENDPOINT_MISMATCH", "return leg does not reverse the outbound endpoints")

    for endpoint_evidence in (b, c):
        if endpoint_evidence.get("manifest_read") is not True:
            fail("EPHEMERAL_MANIFEST_NOT_READ", "ephemeral endpoint must attest reading the admitted manifest")
        if endpoint_evidence.get("manifest_directed") is not True:
            fail("EPHEMERAL_ACTION_NOT_MANIFEST_DIRECTED", "ephemeral endpoint action/routing must be manifest-directed")
        if endpoint_evidence.get("receipt_appended") is not True:
            fail("EPHEMERAL_RECEIPT_NOT_APPENDED", "ephemeral endpoint must append its transition receipt")
        if endpoint_evidence.get("custody") != "RETURN_WITH_MANIFEST":
            fail("EPHEMERAL_CUSTODY_INVALID", "ephemeral endpoint receipts must return with the manifest")

    if c.get("next_leg_directed") is not True:
        fail("EPHEMERAL_NEXT_LEG_NOT_DIRECTED", "ephemeral egress must direct the separately manifested next leg")
    if d.get("returned_endpoint_receipts") is not True:
        fail("RETURN_EVIDENCE_MISSING", "initiating endpoint ingress must attest returned endpoint receipts")

    return {
        "schema": "stegverse.transition-journey-validation/v1",
        "disposition": "ALLOW",
        "journey_id": a["journey_id"],
        "outbound_manifest_sha256": a["manifest_sha256"],
        "return_manifest_sha256": c["manifest_sha256"],
        "legs": 2,
        "endpoint_receipts": 4,
        "ephemeral_durable_custody_required": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt_set", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.receipt_set.read_text())
    receipts = payload["receipts"] if isinstance(payload, dict) else payload
    try:
        print(json.dumps(validate(receipts), sort_keys=True))
    except ValueError as exc:
        print(json.dumps({
            "schema": "stegverse.transition-journey-validation/v1",
            "disposition": "FAIL_CLOSED",
            "failure": str(exc),
        }, sort_keys=True))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
