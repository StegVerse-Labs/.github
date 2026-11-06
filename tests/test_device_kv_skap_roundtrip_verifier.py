import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import importlib.util

from workers.device_kv_skap_roundtrip_verifier import INPUT_SCHEMA, LEG_ORDER, TASK_ID, Layer2BindingRefused, RoundTripEvidenceError, canonical, sha_uri, verify_manifest

_spec = importlib.util.spec_from_file_location("kv_skap_layer_receipts", Path(__file__).resolve().parent / "kv_skap_layer_receipts.py")
LAYERS = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LAYERS)
ROOT = Path(__file__).resolve().parents[1]
SIX_FIELDS = ["BLOCKS", "CLASS", "CODE", "EXPECTED", "NEXT", "OBSERVED"]


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


def build_manifest(root, *, kv_access=None, skap_access=None):
    """Two-leg DEVICE_SYSTEM -> KV -> DEVICE_SYSTEM manifest. The in-KV SKAP gate exchange is the cvk layer-2
    SKAP-access receipt, chained to the layer-1 KV-access receipt of the device_kv hop, bound by its exact-byte hash.

    Ruling C of StegVerse-org/.github#167 (accepted with conditions C1-C3, c6393756343): KV<->SKAP is the in-KV
    gate, not an InTr leg.
    """
    previous=None; manifest={"schema":INPUT_SCHEMA,"task_id":TASK_ID,"current_device":True,"hosted_runtime_used":False,"second_user_operated_device_used":False}
    device_payload=b"device-request"
    intent=_intent(operation_id="ROUNDTRIP-1",payload_hash=sha_uri(device_payload),source="DEVICE_SYSTEM",destination="KV",prior=None)
    device_receipt=_receipt(intent,prior=None,source="DEVICE_SYSTEM",destination="KV",receipt_id="R-1")
    manifest["device_kv"]={"intent_path":_write(root,"device_kv/intent.json",intent),"payload_path":_write(root,"device_kv/payload.bin",device_payload,True),"receipt_path":_write(root,"device_kv/receipt.json",device_receipt)}
    default_l1, default_l2 = LAYERS.pair(device_receipt["receipt_hash"])
    kv_access = kv_access or default_l1; skap_access = skap_access or default_l2
    raw_exchange=canonical(skap_access); gate_hash=sha_uri(raw_exchange)
    manifest["kv_skap_gate_exchange"]={"path":_write(root,"gate/kv-skap-gate-exchange.json",raw_exchange,True),"kv_skap_gate_exchange_hash":gate_hash,"kv_access_receipt_path":_write(root,"gate/kv-access-receipt.json",kv_access)}
    returned=canonical({"schema":"stegverse.kv-skap.gate-return/v1","kv_skap_gate_exchange_hash":gate_hash,"device_kv_terminal_receipt_hash":device_receipt["receipt_hash"],"kv_access_receipt_hash":kv_access["receipt_hash"],"skap_access_receipt_hash":skap_access["receipt_hash"],"stored_object_sha256":"sha256:"+"a"*64,"kv_skap_intr_hop":False})
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
    of #167 ruling C, accepted with conditions C1-C3 (c6393756343)."""
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
    def _device_terminal(self, m):
        return json.loads((self.root/m["device_kv"]["receipt_path"]).read_text())["receipt_hash"]
    def _refused(self, m, cause):
        with self.assertRaisesRegex(Layer2BindingRefused, cause) as ctx: verify_manifest(m,runtime_root=self.root)
        self.assertEqual(sorted(ctx.exception.fail_closed), SIX_FIELDS); self.assertEqual(ctx.exception.fail_closed["CODE"], "KV_SKAP_LAYER2_ACCESS_RECEIPT_BINDING_REFUSED")
        return ctx.exception.fail_closed
    def test_gate_exchange_bound_to_other_device_receipt_fails_closed(self):
        """C2: a layer-1 receipt for another DEVICE->KV hop (and a layer-2 receipt chained to it) fails closed."""
        other=LAYERS.layer1("sha256:"+"c"*64)
        m=build_manifest(self.root,kv_access=other,skap_access=LAYERS.layer2(other))
        self._refused(m,"layer1_not_for_this_device_kv_hop")
    def test_manifest_gate_hash_mismatch_fails_closed(self):
        m=build_manifest(self.root); m["kv_skap_gate_exchange"]["kv_skap_gate_exchange_hash"]="sha256:"+"d"*64
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_gate_exchange_hash_mismatch"): verify_manifest(m,runtime_root=self.root)
    def test_gate_exchange_claiming_intr_hop_fails_closed(self):
        """C1: a gate exchange claiming an InTr boundary is not a KV_INTERNAL_SKAP_GATE layer-2 receipt."""
        m=build_manifest(self.root); terminal=self._device_terminal(m); l1=LAYERS.layer1(terminal)
        l2=LAYERS.seal({**LAYERS.layer2(l1),"boundary":"InTr"})
        m=build_manifest(self.root,kv_access=l1,skap_access=l2)
        self._refused(m,"layer2_skap_access_receipt_invalid")

    def test_c1_gate_exchange_is_the_rederived_cvk_layer2_receipt(self):
        m=build_manifest(self.root); proof=verify_manifest(m,runtime_root=self.root)
        raw=(self.root/m["kv_skap_gate_exchange"]["path"]).read_bytes(); l2=json.loads(raw)
        self.assertEqual(l2["schema"],"stegverse.skap-access-receipt/v1"); self.assertEqual(l2["boundary"],"KV_INTERNAL_SKAP_GATE"); self.assertEqual(l2["minted_by"],"SkapLayer2Gate.admit"); self.assertEqual(l2["from_role"],"KV")
        self.assertEqual(proof["kv_skap_gate_exchange_hash"],sha_uri(raw)); self.assertEqual(proof["skap_access_receipt_hash"],l2["receipt_hash"]); self.assertEqual(proof["kv_skap_gate"],"KV_INTERNAL_SKAP_GATE")
    def test_c1_caller_asserted_layer2_receipt_hash_fails_closed(self):
        """C1: an edited layer-2 receipt that keeps its old receipt_hash does not re-derive, even with a matching manifest hash."""
        m=build_manifest(self.root); l1=LAYERS.layer1(self._device_terminal(m)); l2={**LAYERS.layer2(l1),"operation":"SKAP_READ"}
        m=build_manifest(self.root,kv_access=l1,skap_access=l2)
        self._refused(m,"layer2_skap_access_receipt_not_rederived")
    def test_c1_layer2_receipt_not_minted_by_the_gate_fails_closed(self):
        m=build_manifest(self.root); l1=LAYERS.layer1(self._device_terminal(m))
        for change in ({"minted_by":"caller"},{"from_role":"DEVICE_SYSTEM"},{"schema":"stegverse.kv-skap.gate-exchange/v1"}):
            self._refused(build_manifest(self.root,kv_access=l1,skap_access=LAYERS.seal({**LAYERS.layer2(l1),**change})),"layer2_skap_access_receipt_invalid")
    def test_c2_layer2_receipt_must_chain_to_the_layer1_receipt(self):
        m=build_manifest(self.root); l1=LAYERS.layer1(self._device_terminal(m))
        l2=LAYERS.seal({**LAYERS.layer2(l1),"prior_receipt_hash":"sha256:"+"e"*64})
        fc=self._refused(build_manifest(self.root,kv_access=l1,skap_access=l2),"layer2_not_chained_to_layer1")
        self.assertIn(l1["receipt_hash"],fc["EXPECTED"])
    def test_c2_layer1_receipt_must_be_minted_by_kv_interlock_runtime(self):
        m=build_manifest(self.root); terminal=self._device_terminal(m)
        for change,cause in (({"minted_by":"caller"},"layer1_kv_access_receipt_invalid"),({"boundary":"KV_INTERNAL_SKAP_GATE"},"layer1_kv_access_receipt_invalid"),({"healthy_node_receipt":{"healthy_node_established":False}},"layer1_healthy_node_not_established")):
            l1=LAYERS.seal({**LAYERS.layer1(terminal),**change})
            self._refused(build_manifest(self.root,kv_access=l1,skap_access=LAYERS.layer2(l1)),cause)
        l1=LAYERS.layer1(terminal); l1={**l1,"requester_node_ref":"node://other"}
        self._refused(build_manifest(self.root,kv_access=l1,skap_access=LAYERS.layer2(LAYERS.layer1(terminal))),"layer1_kv_access_receipt_not_rederived")
    def test_c2_mismatch_never_falls_back_to_the_four_leg_path(self):
        """A refused layer-2 binding is not rescued by also supplying the retired kv_skap/skap_kv legs."""
        other=LAYERS.layer1("sha256:"+"c"*64); m=build_manifest(self.root,kv_access=other,skap_access=LAYERS.layer2(other))
        _legacy_leg(self.root,m,"kv_skap"); _legacy_leg(self.root,m,"skap_kv")
        with self.assertRaisesRegex(RoundTripEvidenceError,"kv_skap_intr_leg_retired"): verify_manifest(m,runtime_root=self.root)
    def test_c3_two_leg_order_with_no_kv_skap_alias(self):
        self.assertEqual([leg[0] for leg in LEG_ORDER],["device_kv","kv_device"])
        self.assertFalse(any("SKAP_VAULT" in leg for leg in LEG_ORDER))
        cont=(ROOT/"scripts/continue_device_kv_skap_from_tvc_custody.py").read_text(encoding="utf-8")
        for marker in ('"kv-skap"',"connector_from_registry","kv_skap_connector","skap_kv","prepare_response(","connector.prepare(","SKAP_TO_KV","hop_index=1"):self.assertNotIn(marker,cont)
        ret=(ROOT/"scripts/materialize_kv_device_from_skap_return.py").read_text(encoding="utf-8")
        for marker in ("skap_kv","SKAP->KV InTr intent","skap_kv_intent","skap_kv_receipt","gate_exchange_bytes"):self.assertNotIn(marker,ret)
        found=[]
        for path in sorted((ROOT/"scripts").glob("*.py"))+sorted((ROOT/"workers").glob("*.py")):
            for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
                if ('("kv_skap", "KV", "SKAP_VAULT")' in line) or ('("skap_kv", "SKAP_VAULT", "KV")' in line):found.append(f"{path.name}:{n}")
        self.assertEqual(found,[])

if __name__ == "__main__": unittest.main()
