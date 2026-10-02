#!/usr/bin/env python3
"""Deterministic non-authorizing MasterRecordsCheckpoint/v1 verifier."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
construction=json.loads((ROOT/"test-vectors/master-records-checkpoint-construction-v1.json").read_text())
interop=json.loads((ROOT/"test-vectors/master-records-checkpoint-interoperability-v1.json").read_text())

def h(x): return hashlib.sha256(x).digest()
def leaf(c):
    assert c["state"]=="RECORDED"
    assert c["reconstruction_status"]=="PASS"
    assert c["required_evidence_validation_status"]=="PASS"
    assert c["receipt_sha256"]==c["reconstructed_receipt_sha256"]
    pre=b"stegverse-master-records-leaf/v1\n"+int(c["sequence"]).to_bytes(8,"big")+bytes.fromhex(c["receipt_sha256"])+bytes.fromhex(c["reconstructed_receipt_sha256"])
    return h(b"\x00"+pre)
def root(xs):
    if len(xs)==1:return xs[0]
    k=1 << ((len(xs)-1).bit_length()-1)
    return h(b"\x01"+root(xs[:k])+root(xs[k:]))
assert construction["status"]=="SYNTHETIC_NON_AUTHORIZING"
cs=construction["closures"]
assert [x["sequence"] for x in cs]==list(range(cs[0]["sequence"],cs[0]["sequence"]+len(cs)))
leaves=[leaf(x) for x in cs]; merkle=root(leaves).hex()
cp=construction["checkpoint"]
assert cp["tree_size"]==len(cs) and cp["first_sequence"]==cs[0]["sequence"] and cp["last_sequence"]==cs[-1]["sequence"]
assert cp["closure_receipt_sha256"]==cs[-1]["receipt_sha256"]
assert len(cp["predecessor_checkpoint_digest"])==64
assert interop["status"]=="SYNTHETIC_NON_AUTHORIZING"
b=interop["base"]
assert b["manifest"]["intent"]=="REPORT_MASTER_RECORDS_CHECKPOINT"
assert b["manifest"]["checkpoint_digest"]==b["payload_commitment"]["checkpoint_digest"]
assert b["transfer"]["transport"]=="INTERLOCK_INTR"
assert b["transfer"]["write_once_transfer_admission_receipt_required"] is True
assert b["transfer"]["participating_runtime_implementation_required"] is False
expected={"allow":"ALLOW","deny":"DENY","fail_closed":"FAIL_CLOSED","negative_node_identity":"FAIL_CLOSED","negative_checkpoint_digest":"FAIL_CLOSED","negative_manifest_intent":"FAIL_CLOSED","negative_receipt":"FAIL_CLOSED"}
assert {k:v["expected_disposition"] for k,v in interop["fixtures"].items()}==expected
assert interop["runtime_observation"]["required_for_documentary_validation"] is False
assert interop["claims"]=={"external_adoption":False,"external_conformance":False,"authentic_runtime_execution":False,"deployment":False}
print(json.dumps({"schema":"stegverse.master-records-checkpoint-verification/v1","status":"PASS","merkle_root":merkle,"closure_equality":"PASS","predecessor_continuity_binding":"PASS","interoperability_dispositions":expected,"runtime_observation_required":False,"authority_effect":"NONE_SYNTHETIC_NON_AUTHORIZING"},sort_keys=True))
