import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/consume_kv_skap_custody_materialization_request.py"
INGRESS=ROOT/"workers/universal_intr_profiled_ingress.py"
RETURN=ROOT/"scripts/materialize_kv_skap_canonical_return.py"

def load_module():
    spec=importlib.util.spec_from_file_location("kv_skap_consumer",SCRIPT);module=importlib.util.module_from_spec(spec);assert spec.loader is not None;spec.loader.exec_module(module);return module

RETIRED_PROFILE_TOKENS=('"kv-skap"','"kv-skap-custody"','"kv-skap-account-metadata"')

def load_dispatcher():
    spec=importlib.util.spec_from_file_location("kv_skap_gate_dispatcher",ROOT/"scripts/dispatch_kv_skap_custody_materialization.py");module=importlib.util.module_from_spec(spec);assert spec.loader is not None;spec.loader.exec_module(module);return module

class KVSkapCustodyTransportTests(unittest.TestCase):
    """Method names are kept from base (TEST_PRESENT_AT_BASE_RUNS_AT_HEAD). Under #167 ruling (3) c6393224851
    (PROVISIONAL_ON_RULING_C), KV->SKAP is the in-KV SKAP gate, not an InTr hop, so the bodies now assert the
    gate request and the two-leg DEVICE->KV->DEVICE return."""
    @classmethod
    def setUpClass(cls):
        cls.mod=load_module();cls.ingress=INGRESS.read_text(encoding="utf-8");cls.dispatcher=(ROOT/"scripts/dispatch_kv_skap_custody_materialization.py").read_text(encoding="utf-8");cls.returner=RETURN.read_text(encoding="utf-8")

    def capsule(self):
        return {"schema":self.mod.CAPSULE_SCHEMA,"ingress_id":"ingress-1","credential_ref":"skap://APIs/coinbase/owner/1","credential_version":"1","endpoint_origin":"https://api.coinbase.com","purpose":"owner_authorized_provider_access","sealed_material":{"recipient_key_id":"key-1","ciphertext_b64":"opaque"}}
    def canonical_receipt(self):
        canonical_body={"schema":"stegverse.intr.hop_receipt/v1","receipt_id":"device-kv-1","packet_id":"packet-device","hop_index":1,"direction":"FORWARD","from_role":"DEVICE_SYSTEM","to_role":"KV","operation_hash":"sha256:"+"4"*64,"payload_hash":"sha256:"+"5"*64,"prior_receipt_hash":None,"boundary_identity_ref":"kv://test","boundary_verification":"VERIFIED","transition_state":"RECEIVED","secret_plaintext_present":False,"authority_transfer":False,"recorded_at":"2026-09-10T19:00:00Z"}
        return {**canonical_body,"receipt_hash":self.mod.sha_uri(canonical_body)}
    def request(self):
        return load_dispatcher().build_request(capsule=self.capsule(),device_kv_receipt={"schema":"stegverse.intr.boundary_transition_receipt/v1","receipt_hash":"sha256:"+"3"*64},canonical_device_kv_receipt=self.canonical_receipt())
    def reseal(self,value):
        value["request_hash"]=self.mod.sha_uri({k:v for k,v in value.items() if k!="request_hash"});return value

    def test_canonical_request_validates(self):
        value=self.request();self.mod.validate_request(value)
        self.assertEqual(value["schema"],self.mod.GATE_REQUEST_SCHEMA);self.assertEqual(value["kv_skap_path"],"IN_KV_GATE");self.assertIs(value["kv_skap_intr_hop"],False)
    def test_missing_canonical_device_receipt_fails_closed(self):
        value=self.request();value.pop("canonical_device_kv_receipt");self.reseal(value)
        with self.assertRaises(self.mod.KVSkapMaterializationError):self.mod.validate_request(value)
    def test_wrong_boundary_fails_closed(self):
        """A request still carrying a KV->SKAP InTr boundary path is retired and fails closed."""
        value=self.request();value["boundary_path"]=["KV","SKAP_VAULT"];self.reseal(value)
        with self.assertRaisesRegex(self.mod.KVSkapMaterializationError,"kv_skap_intr_request_retired"):self.mod.validate_request(value)
        value=self.request();value.pop("boundary_path",None);value["gate"]={"boundary":"SKAP_VAULT","from_subsystem":"x","to_subsystem":"y"};self.reseal(value)
        with self.assertRaisesRegex(self.mod.KVSkapMaterializationError,"gate_request_gate_mismatch"):self.mod.validate_request(value)
    def test_payload_hash_is_exact_sealed_capsule(self):
        value=self.request();value["sealed_capsule"]["purpose"]="tampered"
        with self.assertRaises(self.mod.KVSkapMaterializationError):self.mod.validate_request(value)
    def test_shared_ingress_routes_kv_skap_profile(self):
        """The shared InTr ingress no longer routes a KV->SKAP profile: the step is the in-KV gate."""
        for marker in ("KV:SKAPCiphertextCustody","def _is_kv_skap(","def admit_kv_skap(","kv_skap_requires_tvc_relay_egress","consume_kv_skap_custody_materialization_request","KV_SKAP_RECEIPT_SCHEMA"):self.assertNotIn(marker,self.ingress)
    def test_transport_does_not_grant_authority(self):
        source=SCRIPT.read_text(encoding="utf-8")
        for marker in ('"credential_authority":"TV/TVC"','"github_token_runtime_authority":"NONE"','"execution_authority":"NONE"','"secret_plaintext_present":False','"kv_decryption_authority":False','"request_grants_authority":False','"authority_effect":"NONE_CUSTODY_TRANSITION_ONLY"'):self.assertIn(marker,source)
    def test_second_hop_has_canonical_event_ephemeral_sender(self):
        """The KV->SKAP step has no InTr sender: the dispatcher hands the gate request to the in-KV gate admission."""
        for marker in ('PROFILE_ID=','stegos.universal_intr_transport','stegos.universal_intr_materialization','build_transport_intent(','build_materialization_request(','build_carrier_binding(','"TVC_RELAY_EGRESS"','admit_kv_skap(','X-StegVerse-Transport'):self.assertNotIn(marker,self.dispatcher)
        for marker in ('.admit(runtime_root=','"NONE_GATE_DISPATCH_ONLY"','canonical_device_kv_receipt','"kv_skap_intr_hop":False'):self.assertIn(marker,self.dispatcher)
        self.assertNotIn("requests.",self.dispatcher);self.assertNotIn("github.com",self.dispatcher)
    def test_canonical_return_uses_backbone_and_exact_readback(self):
        """The return requires the exact SKAP readback, binds the gate exchange by hash and emits only the device-kv leg."""
        for marker in ('PROFILE_ID = "device-kv"','skap_exact_readback_mismatch','build_gate_exchange(','device_return.materialize(','KV_TO_DEVICE_RETURN_PERSISTED','"kv_skap_intr_hop": False'):
            self.assertIn(marker,self.returner)
        for marker in ('connector.prepare(','connector.prepare_response(','boundary_identity_ref="tvc://SKAP_VAULT"','SKAP_TO_KV_RETURN_PERSISTED'):self.assertNotIn(marker,self.returner)
        self.assertNotIn("requests.",self.returner)
        device=(ROOT/"scripts/materialize_kv_device_from_skap_return.py").read_text(encoding="utf-8")
        for marker in ('connector.accept_hop(','connector.validate_complete(','prior_transport_receipt_hash=terminal','GATE_EXCHANGE_FIELD: gate_hash','kv_exact_readback_mismatch'):self.assertIn(marker,device)

    def test_gate_admission_is_write_once_and_not_intr(self):
        with tempfile.TemporaryDirectory() as tmp:
            request=self.request();first=self.mod.admit(runtime_root=Path(tmp),request=request,dispatch=False)
            self.assertEqual(first["state"],"GATE_ADMITTED");self.assertIs(first["kv_skap_intr_hop"],False);self.assertEqual(first["canonical_device_kv_receipt_hash"],request["canonical_device_kv_receipt"]["receipt_hash"])
            again=self.mod.admit(runtime_root=Path(tmp),request=request,dispatch=False);self.assertEqual(again["receipt_hash"],first["receipt_hash"])
            other=self.request();other["operation_id"]="ingress-2";self.reseal(other)
            with self.assertRaises(self.mod.KVSkapMaterializationError):self.mod.admit(runtime_root=Path(tmp),request=other,dispatch=False)

    def test_gate_exchange_binds_device_receipt_by_hash(self):
        spec=importlib.util.spec_from_file_location("kv_device_return",ROOT/"scripts/materialize_kv_device_from_skap_return.py");mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        receipt=self.canonical_receipt();terminal=mod.validate_device_kv_receipt(receipt)
        raw=mod.build_gate_exchange(operation_id="ingress-1",credential_ref="skap://APIs/coinbase/owner/1",device_kv_terminal=terminal,stored_object_sha256="sha256:"+"a"*64,custody_evidence={})
        exchange=json.loads(raw);self.assertEqual(exchange["canonical_device_kv_receipt_hash"],terminal);self.assertIs(exchange["kv_skap_intr_hop"],False)
        with self.assertRaisesRegex(mod.KVDeviceReturnError,"kv_skap_gate_not_bound_to_device_kv"):mod.validate_gate_exchange(raw,device_kv_terminal="sha256:"+"0"*64)

    def test_no_labs_source_resolves_a_retired_kv_skap_profile(self):
        found=[]
        for path in sorted((ROOT/"scripts").glob("*.py"))+sorted((ROOT/"workers").glob("*.py")):
            text=path.read_text(encoding="utf-8")
            for line in text.splitlines():
                if ("PROFILE_ID" in line or "connector_from_registry" in line) and any(token in line for token in RETIRED_PROFILE_TOKENS):found.append(f"{path.relative_to(ROOT)}:{line.strip()}")
        self.assertEqual(found,[])

if __name__=="__main__":unittest.main()
