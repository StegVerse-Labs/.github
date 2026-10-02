#!/usr/bin/env python3
"""Deterministic verifier for synthetic Interlock/InTr protocol vectors.

Documentary/non-authorizing: this validates fixture semantics only. It does not
invoke Interlock/InTr, authenticate a node, or establish external conformance.
"""
import json
from pathlib import Path

VECTORS = Path(__file__).resolve().parents[1] / "test-vectors" / "interlock-intr-runtime-independent-protocol-v1.json"

FAIL_CLOSED_MUTATIONS = {
    "source_node_id=node:forged": "REGISTERED_NODE_IDENTITY_BOUND",
    "payload_sha256 differs from receipt": "PAYLOAD_COMMITMENT_BOUND",
    "state_binding=state:0000": "APPLICABLE_STATE_OR_PREDECESSOR_BOUND",
    "intent=DIFFERENT_INTENT": "MANIFEST_INTENT_BOUND",
    "requested_capability=unknown/v1": "REQUESTED_CAPABILITY_BOUND",
    "receipt manifest/payload commitment mismatch": "TRANSFER_RECEIPT_BOUND",
}

def evaluate(name, vector):
    mutation = vector.get("mutation")
    if name == "allow":
        return "ALLOW" if mutation is None else "FAIL_CLOSED"
    if name == "deny":
        return "DENY" if mutation == "policy_reject" else "FAIL_CLOSED"
    if name == "fail_closed":
        return "FAIL_CLOSED"
    if name.startswith("negative_"):
        if mutation not in FAIL_CLOSED_MUTATIONS:
            return "FAIL_CLOSED"
        if vector.get("predicate") != FAIL_CLOSED_MUTATIONS[mutation]:
            raise AssertionError(f"{name}: predicate does not match mutation")
        return "FAIL_CLOSED"
    if name == "master_records_checkpoint_profile":
        required = {
            "intent": "REPORT_MASTER_RECORDS_CHECKPOINT",
            "profile": "MasterRecordsCheckpoint/v1",
            "checkpoint_authority": "MASTER_RECORDS",
            "transport": "INTERLOCK_INTR",
            "external_conformance_claimed": False,
        }
        for key, expected in required.items():
            if vector.get(key) != expected:
                raise AssertionError(f"{name}: {key} mismatch")
        return "ALLOW_DENY_OR_FAIL_CLOSED"
    raise AssertionError(f"unrecognized vector {name}")

def main():
    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert doc["status"] == "SYNTHETIC_NON_AUTHORIZING"
    fixtures = doc["fixtures"]
    required = {
        "base","allow","deny","fail_closed","negative_node_identity","negative_payload",
        "negative_state","negative_manifest","negative_capability","negative_receipt",
        "master_records_checkpoint_profile",
    }
    assert required == set(fixtures), "fixture set changed"
    base = fixtures["base"]
    required_base = {
        "protocol": "stegverse.interlock-intr/v1",
        "source_node_id": "node:alpha",
        "destination_node_id": "node:beta",
        "intent": "TRANSFER_BOUND_PAYLOAD",
        "requested_capability": "example.echo/v1",
        "payload_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "state_binding": "state:0001",
    }
    assert base == required_base, "base fixture changed"
    results = {}
    for name in sorted(set(fixtures) - {"base"}):
        expected = fixtures[name]["expected"]
        actual = evaluate(name, fixtures[name])
        assert actual == expected, f"{name}: expected {expected}, got {actual}"
        results[name] = actual
    print(json.dumps({"schema":"stegverse.interlock-intr-vector-verification/v1","status":"PASS","results":results},sort_keys=True,separators=(",",":")))

if __name__ == "__main__":
    main()
