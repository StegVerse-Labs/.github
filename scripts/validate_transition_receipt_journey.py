#!/usr/bin/env python3
"""Validate one manifested InTr out-and-return receipt journey.

This is a source validator, not a runtime recorder. It consumes receipt JSON
objects already retained by an authorized custody surface and proves whether
four endpoint transitions describe one completed one-way-out / one-way-back
handoff.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED = ("journey_id","leg","direction","endpoint","counterparty","manifest_sha256")

def fail(code: str, detail: str) -> None:
    raise ValueError(f"{code}: {detail}")

def evidence(receipt: dict) -> dict:
    e=receipt.get("evidence")
    if not isinstance(e,dict): fail("JOURNEY_EVIDENCE_MISSING","receipt evidence must be an object")
    missing=[k for k in REQUIRED if not e.get(k)]
    if missing: fail("JOURNEY_CORRELATION_MISSING",",".join(missing))
    return e

def validate(receipts: list[dict]) -> dict:
    if len(receipts)!=4: fail("JOURNEY_INCOMPLETE",f"expected 4 endpoint receipts, observed {len(receipts)}")
    es=[evidence(r) for r in receipts]
    journey={e["journey_id"] for e in es}
    if len(journey)!=1: fail("JOURNEY_ID_MISMATCH","all endpoint receipts must share one journey_id")
    manifest={e["manifest_sha256"] for e in es}
    if len(manifest)!=1: fail("MANIFEST_HANDOFF_MISMATCH","manifest_sha256 changed across handoff")
    expected=[(1,"EGRESS"),(1,"INGRESS"),(2,"EGRESS"),(2,"INGRESS")]
    actual=[(e["leg"],e["direction"]) for e in es]
    if actual!=expected: fail("JOURNEY_SEQUENCE_INVALID",f"expected {expected!r}, observed {actual!r}")
    a,b,c,d=es
    if a["counterparty"]!=b["endpoint"] or b["counterparty"]!=a["endpoint"]:
        fail("OUTBOUND_HANDOFF_MISMATCH","leg 1 endpoint/counterparty pair does not close")
    if c["counterparty"]!=d["endpoint"] or d["counterparty"]!=c["endpoint"]:
        fail("RETURN_HANDOFF_MISMATCH","leg 2 endpoint/counterparty pair does not close")
    if a["endpoint"]!=d["endpoint"] or b["endpoint"]!=c["endpoint"]:
        fail("ROUNDTRIP_ENDPOINT_MISMATCH","return leg does not reverse the outbound endpoints")
    if b.get("custody")!="RETURN_WITH_MANIFEST" or c.get("custody")!="RETURN_WITH_MANIFEST":
        fail("EPHEMERAL_CUSTODY_INVALID","ephemeral endpoint receipts must return with the manifest, not require durable node custody")
    if d.get("returned_endpoint_receipts") is not True:
        fail("RETURN_EVIDENCE_MISSING","initiating endpoint ingress must attest returned endpoint receipts")
    return {
        "schema":"stegverse.transition-journey-validation/v1",
        "disposition":"ALLOW",
        "journey_id":a["journey_id"],
        "outbound_manifest_sha256":a["manifest_sha256"],\n        "return_manifest_sha256":c["manifest_sha256"],
        "legs":2,
        "endpoint_receipts":4,
        "ephemeral_durable_custody_required":False,
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("receipt_set",type=Path)
    a=p.parse_args()
    obj=json.loads(a.receipt_set.read_text())
    receipts=obj["receipts"] if isinstance(obj,dict) else obj
    try:
        print(json.dumps(validate(receipts),sort_keys=True))
    except ValueError as exc:
        print(json.dumps({"schema":"stegverse.transition-journey-validation/v1","disposition":"FAIL_CLOSED","failure":str(exc)},sort_keys=True))
        raise SystemExit(1)

if __name__=="__main__": main()
