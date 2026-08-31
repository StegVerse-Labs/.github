import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/consume_kv_skap_custody_materialization_request.py"
INGRESS=ROOT/"workers/universal_intr_profiled_ingress.py"


def load_module():
    spec=importlib.util.spec_from_file_location("kv_skap_consumer",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KVSkapCustodyTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod=load_module()
        cls.ingress=INGRESS.read_text(encoding="utf-8")
        cls.dispatcher=(ROOT/"scripts/dispatch_kv_skap_custody_materialization.py").read_text(encoding="utf-8")

    def request(self):
        capsule={
            "schema":self.mod.CAPSULE_SCHEMA,
            "ingress_id":"ingress-1",
            "credential_ref":"skap://APIs/coinbase/owner/1",
            "credential_version":"1",
            "endpoint_origin":"https://api.coinbase.com",
            "purpose":"owner_authorized_provider_access",
            "sealed_material":{"recipient_key_id":"key-1","ciphertext_b64":"opaque"}
        }
        body={
            "schema":"stegverse.universal-intr-materialization-request/v1",
            "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
            "transport_schema":"stegverse.universal-intr-transport/v1",
            "transport_protocol":"InTr",
            "boundary_path":["KV","SKAP_VAULT"],
            "destination":self.mod.DESTINATION,
            "downstream_owner_ref":self.mod.DOWNSTREAM_OWNER,
            "event_triggered":True,
            "always_on_receiver_required":False,
            "second_user_device_required":False,
            "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
            "exact_packet_transport_retry_allowed":True,
            "blind_consequence_retry_allowed":False,
            "interlock_required":True,
            "request_grants_execution_authority":False,
            "claim_or_fence_minted":False,
            "transport_grants_execution_authority":False,
            "credential_authority":"TV/TVC",
            "github_token_runtime_authority":"NONE",
            "authority_transfer":False,
            "authority_effect":"NONE_REQUEST_ONLY",
            "materialization_id":"INTR-MAT-"+"1"*24,
            "operation_id":"ingress-1",
            "packet_id":"packet-1",
            "payload_ref":"inline://materialization_request.sealed_capsule",
            "transport_intent_hash":"sha256:"+"2"*64,
            "payload_hash":self.mod.sha_uri(capsule),
            "sealed_capsule":capsule,
            "device_kv_receipt":{"schema":"stegverse.intr.boundary_transition_receipt/v1","receipt_hash":"sha256:"+"3"*64}
        }
        body["request_hash"]=self.mod.sha_uri(body)
        return body

    def test_canonical_request_validates(self):
        self.mod.validate_request(self.request())

    def test_wrong_boundary_fails_closed(self):
        value=self.request()
        value["boundary_path"]=["DEVICE_SYSTEM","SKAP_VAULT"]
        value["request_hash"]=self.mod.sha_uri({k:v for k,v in value.items() if k!="request_hash"})
        with self.assertRaises(self.mod.KVSkapMaterializationError):
            self.mod.validate_request(value)

    def test_payload_hash_is_exact_sealed_capsule(self):
        value=self.request()
        value["sealed_capsule"]["purpose"]="tampered"
        with self.assertRaises(self.mod.KVSkapMaterializationError):
            self.mod.validate_request(value)

    def test_shared_ingress_routes_kv_skap_profile(self):
        for marker in (
            "KV:SKAPCiphertextCustody",
            "def _is_kv_skap(",
            "def admit_kv_skap(",
            "kv_skap_requires_tvc_relay_egress",
            "consume_kv_skap_custody_materialization_request.py",
            "KV_SKAP_RECEIPT_SCHEMA",
        ):
            self.assertIn(marker,self.ingress)

    def test_transport_does_not_grant_authority(self):
        source=SCRIPT.read_text(encoding="utf-8")
        for marker in (
            '"credential_authority": "TV/TVC"',
            '"github_token_runtime_authority": "NONE"',
            '"execution_authority": "NONE"',
            '"secret_plaintext_present": False',
            '"kv_decryption_authority": False',
            '"request_grants_authority": False',
            '"authority_effect": "NONE_CUSTODY_TRANSITION_ONLY"',
        ):
            self.assertIn(marker,source)



    def test_second_hop_has_canonical_event_ephemeral_sender(self):
        for marker in (
            'PROFILE_ID = "kv-skap-custody"',
            'stegos.universal_intr_transport',
            'stegos.universal_intr_materialization',
            'build_transport_intent(',
            'build_materialization_request(',
            'build_carrier_binding(',
            '"TVC_RELAY_EGRESS"',
            'admit_kv_skap(',
            '"NONE_TRANSPORT_DISPATCH_ONLY"',
        ):
            self.assertIn(marker,self.dispatcher)
        self.assertNotIn("requests.",self.dispatcher)
        self.assertNotIn("github.com",self.dispatcher)

if __name__=="__main__":
    unittest.main()
