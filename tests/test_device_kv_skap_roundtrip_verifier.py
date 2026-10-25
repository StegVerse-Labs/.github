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
    """Two-leg DEVICE_SYSTEM -> KV -> DEVICE_SYSTEM manifest with the in-KV SKAP gate exchange bound by its hash.

    Ruling (3) of StegVerse-org/.github#167 c6393224851 (PROVISIONAL_ON_RULING_C): KV<->SKAP is the in-KV gate,
    not an InTr leg.
    """
    previous=None; manifest={"schema":INPUT_SCHEMA,"task_id":TASK_ID,"current_device":True,"hosted_runtime_used":False,"second_user_operated_device_used":False}
    device_payload=b"device-request"
    intent=_intent(operation_id="ROUNDTRIP-1",payload_hash=sha_uri(device_payload),source="DEVICE_SYSTEM",destination="KV",prior=None)
    device_receipt=_receipt(intent,prior=None,source="DEVICE_SYSTEM",destination="KV",receipt_id="R-1")
    manifest["device_kv"]={"intent_path":_write(root,"device_kv/intent.json",intent),"payload_path":_write(root,"device_kv/payload.bin",device_payload,True),"receipt_path":_write(root,"device_kv/receipt.json",device_receipt)}
    exchange={"schema":"stegverse.kv-skap.gate-exchange/v1","kv_skap_path":"IN_KV_GATE","kv_skap_intr_hop":False,"operation_id":"ROUNDTRIP-1","credential_ref":"skap://APIs/coinbase/owner/1","canonical_device_kv_receipt_hash":device_receipt["receipt_hash"],"stored_object_sha256":"sha256:"+"a"*64,"exact_ciphertext_readback_verified":True,"secret_plaintext_present":False,"credential_material_present":False,"credential_authority":"TV/TVC","authority_effect":"NONE_EVIDENCE_ONLY"}
    raw_exchange=canonical(exchange); gate_hash=sha_uri(raw_exchange)
    manifest["kv_skap_gate_exchange"]={"path":_write(root,"gate/kv-skap-gate-exchange.json",raw_exchange,True),"kv_skap_gate_exchange_hash":gate_hash}
    returned=canonical({"schema":"stegverse.kv-skap.gate-return/v1","kv_skap_gate_exchange_hash":gate_hash,"device_kv_terminal_receipt_hash":device_receipt["receipt_hash"],"kv_skap_intr_hop":False})
    intent=_intent(operation_id="ROUNDTRIP-2",payload_hash=sha_uri(returned),source="KV",destination="DEVICE_SYSTEM",prior=device_receipt["receipt_hash"])
    receipt=_receipt(intent,prior=device_receipt["receipt_hash"],source="KV",destination="DEVICE_SYSTEM",receipt_id="R-2")
    manifest["kv_device"]={"intent_path":_write(root,"kv_device/intent.json",intent),"payload_path":_write(root,"kv_device/payload.bin",returned,True),"receipt_path":_write(root,"kv_device/receipt.json",receipt)}
    manifest["readback"]={"skap":{"observed":True,"exact_readback":True,"kv_skap_gate_exchange_hash":gate_hash,"object_sha256":"sha256:"+"a"*64,"credential_material_present":False},"kv":{"observed":True,"exact_readback":True,"kv_skap_gate_exchange_hash":gate_hash,"object_sha256":sha_uri(returned),"credential_material_present":False}}
    return manifest


def _legacy_leg(root, manifest, name):
    payload=b"retired-"+name.encode()
    intent=_intent(operation_id="RETIRED-"+name,payload_hash=sha_uri(payload),source="KV",destination="SKAP_VAULT",prior=None)
    receipt=_receipt(intent,prior=None,source="KV",destination="SKAP_VAULT",receipt_id="R-"+name)
    manifest[name]={"intent_path":_write(root,f"{name}/intent.json",intent),"payload_path":_write(root,f"{name}/payload.bin",payload,True),"receipt_path":_write(root,f"{name}/receipt.json",receipt)}


class DeviceKVSKAPRoundTripVerifierTests(unittest.TestCase):
    """Method names are kept from base (TEST_PRESENT_AT_BASE_RUNS_AT_HEAD). Bodies now cover the two-leg shape
    of #167 ruling (3), PROVISIONAL_ON_RULING_C."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_four_leg_manifest_verifies_as_one_roundtrip(self):
        """Name kept from base: the round trip now verifies as two InTr legs plus the hash-bound in-KV gate exchange."""
        m=build_manifest(self.root); proof=verify_manifest(m,runtime_root=self.root)
        self.assertEqual(proof["state"],"DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED"); self.assertTrue(proof["receipt_hash_chain_complete"]); self.assertTrue(proof["exact_packet_hashes_verified"]); self.assertEqual(proof["credential_authority"],"TV/TVC")
        self.assertEqual(proof["boundary_stack"],["DEVICE_SYSTEM","KV","DEVICE_SYSTEM"]); self.assertEqual(proof["kv_skap_path"],"IN_KV_GATE"); self.assertIs(proof["kv_skap_intr_hop"],False)
        self.assertEqual(sorted(proof["receipt_hashes"]),["device_kv","kv_device"])
        self.assertEqual(proof["kv_skap_gate_exchange_hash"],m["kv_skap_gate_exchange"]["kv_skap_gate_exchange_hash"])
    def test_detached_skap_return_fails_closed(self):
        """Name kept from base: a KV->DEVICE return detached from the DEVICE->KV receipt fails closed."""
        m=build_manifest(self.root); p=self.root/m["kv_device"]["intent_path"]; v=json.loads(p.read_text()); v["prior_transport_receipt_hash"]=None; p.write_text(json.dumps(v))
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_device_intent_prior_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_mutated_exact_packet_bytes_fail_closed(self):
        m=build_manifest(self.root); (self.root/m["kv_device"]["payload_path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_device_exact_packet_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_missing_exact_readback_fails_closed(self):
        m=build_manifest(self.root); m["readback"]["skap"]["exact_readback"]=False
        with self.assertRaisesRegex(RoundTripEvidenceError,"skap_exact_readback_not_observed"): verify_manifest(m,runtime_root=self.root)
    def test_wrong_credential_authority_fails_closed(self):
        m=build_manifest(self.root); p=self.root/m["device_kv"]["intent_path"]; v=json.loads(p.read_text()); v["authority"]["credential_authority"]="OTHER"; p.write_text(json.dumps(v))
        with self.assertRaisesRegex(RoundTripEvidenceError,"device_kv_credential_authority_invalid"): verify_manifest(m,runtime_root=self.root)
    def test_retired_kv_skap_intr_legs_fail_closed(self):
        for name in ("kv_skap","skap_kv"):
            m=build_manifest(self.root); _legacy_leg(self.root,m,name)
            with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_intr_leg_retired"): verify_manifest(m,runtime_root=self.root)
    def test_mutated_gate_exchange_bytes_fail_closed(self):
        m=build_manifest(self.root); p=self.root/m["kv_skap_gate_exchange"]["path"]; p.write_bytes(p.read_bytes().replace(b"coinbase",b"coinbasx"))
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_gate_exchange_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_gate_exchange_bound_to_other_device_receipt_fails_closed(self):
        m=build_manifest(self.root); p=self.root/m["kv_skap_gate_exchange"]["path"]; v=json.loads(p.read_bytes()); v["canonical_device_kv_receipt_hash"]="sha256:"+"c"*64
        raw=canonical(v); p.write_bytes(raw); m["kv_skap_gate_exchange"]["kv_skap_gate_exchange_hash"]=sha_uri(raw)
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_gate_not_bound_to_device_kv"): verify_manifest(m,runtime_root=self.root)
    def test_manifest_gate_hash_mismatch_fails_closed(self):
        m=build_manifest(self.root); m["kv_skap_gate_exchange"]["kv_skap_gate_exchange_hash"]="sha256:"+"d"*64
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_gate_exchange_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_gate_exchange_claiming_intr_hop_fails_closed(self):
        m=build_manifest(self.root); p=self.root/m["kv_skap_gate_exchange"]["path"]; v=json.loads(p.read_bytes()); v["kv_skap_intr_hop"]=True
        raw=canonical(v); p.write_bytes(raw); m["kv_skap_gate_exchange"]["kv_skap_gate_exchange_hash"]=sha_uri(raw)
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_gate_exchange_must_not_be_intr"): verify_manifest(m,runtime_root=self.root)


if __name__ == "__main__": unittest.main()
