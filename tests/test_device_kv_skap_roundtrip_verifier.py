import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workers.device_kv_skap_roundtrip_verifier import INPUT_SCHEMA, TASK_ID, RoundTripEvidenceError, canonical, sha_uri, verify_manifest


def _intent(*, operation_id, payload_hash, source, destination, prior):
    basis={"operation_id":operation_id,"payload_hash":payload_hash,"source_boundary":source,"source_subsystem":source+":test","destination_boundary":destination,"destination_subsystem":destination+":test","boundary_path":[source,destination]}
    packet_id="INTR-"+hashlib.sha256(canonical(basis)).hexdigest()[:24]
    return {"schema":"stegverse.universal-intr-transport/v1","protocol":"InTr","operation_id":operation_id,"packet_id":packet_id,"payload_hash":payload_hash,"prior_transport_receipt_hash":prior,"source":{"boundary":source,"subsystem":source+":test"},"destination":{"boundary":destination,"subsystem":destination+":test"},"boundary_path":[source,destination],"interlock_required":True,"transport_semantics":{"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,"receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION","exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False},"authority":{"authority_transfer":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC"},"receipt_chain":{"required":True,"receipt_schema":"stegverse.intr.hop_receipt/v1","payload_plaintext_in_receipts":False,"prior_hash_required_after_first_hop":True}}


def _receipt(intent, *, prior, source, destination, receipt_id):
    operation_hash=sha_uri({"operation_id":intent["operation_id"],"packet_id":intent["packet_id"],"payload_hash":intent["payload_hash"]})
    body={"schema":"stegverse.intr.hop_receipt/v1","receipt_id":receipt_id,"packet_id":intent["packet_id"],"hop_index":1,"direction":"FORWARD","from_role":source,"to_role":destination,"operation_hash":operation_hash,"payload_hash":intent["payload_hash"],"prior_receipt_hash":prior,"boundary_identity_ref":"tvc://boundary/runtime-test","boundary_verification":"VERIFIED","transition_state":"RECEIVED","secret_plaintext_present":False,"authority_transfer":False,"recorded_at":"2026-09-10T19:05:00Z"}
    return {**body,"receipt_hash":sha_uri(body)}


def _write(root, name, value, binary=False):
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value) if binary else path.write_text(json.dumps(value,sort_keys=True),encoding="utf-8")
    return str(path.relative_to(root))


def build_manifest(root):
    spec=[("device_kv","DEVICE_SYSTEM","KV",b"device-request"),("kv_skap","KV","SKAP_VAULT",b"sealed-skap-ciphertext"),("skap_kv","SKAP_VAULT","KV",b"skap-result-reference"),("kv_device","KV","DEVICE_SYSTEM",b"device-result-reference")]
    previous=None; receipts={}; manifest={"schema":INPUT_SCHEMA,"task_id":TASK_ID,"current_device":True,"hosted_runtime_used":False,"second_user_operated_device_used":False}
    for i,(name,source,destination,payload) in enumerate(spec,1):
        intent=_intent(operation_id=f"ROUNDTRIP-{i}",payload_hash=sha_uri(payload),source=source,destination=destination,prior=previous)
        receipt=_receipt(intent,prior=previous,source=source,destination=destination,receipt_id=f"R-{i}")
        manifest[name]={"intent_path":_write(root,f"{name}/intent.json",intent),"payload_path":_write(root,f"{name}/payload.bin",payload,True),"receipt_path":_write(root,f"{name}/receipt.json",receipt)}
        receipts[name]=receipt; previous=receipt["receipt_hash"]
    manifest["readback"]={"skap":{"observed":True,"exact_readback":True,"source_receipt_hash":receipts["kv_skap"]["receipt_hash"],"object_sha256":"sha256:"+"a"*64,"credential_material_present":False},"kv":{"observed":True,"exact_readback":True,"source_receipt_hash":receipts["skap_kv"]["receipt_hash"],"object_sha256":"sha256:"+"b"*64,"credential_material_present":False}}
    return manifest


class DeviceKVSKAPRoundTripVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_four_leg_manifest_verifies_as_one_roundtrip(self):
        proof=verify_manifest(build_manifest(self.root),runtime_root=self.root)
        self.assertEqual(proof["state"],"DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED"); self.assertTrue(proof["receipt_hash_chain_complete"]); self.assertTrue(proof["exact_packet_hashes_verified"]); self.assertEqual(proof["credential_authority"],"TV/TVC")
    def test_detached_skap_return_fails_closed(self):
        m=build_manifest(self.root); p=self.root/m["skap_kv"]["intent_path"]; v=json.loads(p.read_text()); v["prior_transport_receipt_hash"]=None; p.write_text(json.dumps(v))
        with self.assertRaisesRegex(RoundTripEvidenceError,"skap_kv_intent_prior_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_mutated_exact_packet_bytes_fail_closed(self):
        m=build_manifest(self.root); (self.root/m["kv_skap"]["payload_path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_exact_packet_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_missing_exact_readback_fails_closed(self):
        m=build_manifest(self.root); m["readback"]["skap"]["exact_readback"]=False
        with self.assertRaisesRegex(RoundTripEvidenceError,"skap_exact_readback_not_observed"): verify_manifest(m,runtime_root=self.root)
    def test_wrong_credential_authority_fails_closed(self):
        m=build_manifest(self.root); p=self.root/m["device_kv"]["intent_path"]; v=json.loads(p.read_text()); v["authority"]["credential_authority"]="OTHER"; p.write_text(json.dumps(v))
        with self.assertRaisesRegex(RoundTripEvidenceError,"device_kv_credential_authority_invalid"): verify_manifest(m,runtime_root=self.root)


if __name__ == "__main__": unittest.main()
