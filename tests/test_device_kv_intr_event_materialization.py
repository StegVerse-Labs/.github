from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from unittest import mock
from scripts import consume_device_kv_intr_materialization_request as consumer
from workers import device_kv_intr_observation_worker as worker
from workers import universal_intr_profiled_ingress as ingress

def materialization():
    body={
      "schema":"stegverse.universal-intr-materialization-request/v1",
      "materialization_id":"INTR-MAT-"+"a"*24,
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
      "transport_schema":"stegverse.universal-intr-transport/v1",
      "transport_protocol":"InTr",
      "transport_intent_hash":"sha256:"+"1"*64,
      "operation_id":"op-1",
      "packet_id":"INTR-"+"2"*24,
      "payload_hash":"sha256:"+"3"*64,
      "payload_ref":"queue://device-kv/op-1",
      "destination":{"boundary":"KV","subsystem":"KnowledgeVault:Interlock"},
      "boundary_path":["DEVICE_SYSTEM","KV"],
      "downstream_owner_ref":"StegVerse-Labs/continuity-vault-kit#79",
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
      "authority_effect":"NONE_REQUEST_ONLY"
    }
    body["request_hash"]=consumer.sha(body)
    return body

class DeviceKVEventMaterializationTests(unittest.TestCase):
    def test_request_validator_accepts_canonical_device_kv(self):
        consumer.validate_request(materialization())

    def test_shared_ingress_classifies_device_kv(self):
        self.assertTrue(ingress._is_device_kv(materialization()))

    def test_worker_accepts_event_ingress_basis_without_parent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            req=materialization()
            mid=req["materialization_id"]
            req_dir=root/"intr-materialization"
            req_dir.mkdir(parents=True)
            (req_dir/f"{mid}.json").write_text(json.dumps(req),encoding="utf-8")
            receipt={
              "schema":"stegverse.device-kv-intr-materialization-ingress/v1",
              "state":"INGRESS_ADMITTED",
              "materialization_id":mid,
              "request_hash":req["request_hash"],
              "transport_intent_hash":req["transport_intent_hash"],
              "payload_hash":req["payload_hash"],
              "operation_id":req["operation_id"],
              "packet_id":req["packet_id"],
              "node_id":"SV-NODE-"+"4"*24,
              "interlock_id":"SV-IL-"+"5"*24,
              "claim_or_fence_minted":False,
              "credential_authority":"TV/TVC"
            }
            ing_dir=root/"receipts/sovereign-network/device-kv-intr-ingress"
            ing_dir.mkdir(parents=True)
            (ing_dir/f"{mid}.json").write_text(json.dumps(receipt),encoding="utf-8")
            with mock.patch.object(worker,"EVENT_REQUEST_DIR",req_dir),                  mock.patch.object(worker,"EVENT_INGRESS_DIR",ing_dir),                  mock.patch.dict(worker.os.environ,{worker.EVENT_MATERIALIZATION_ENV:mid},clear=False):
                basis=worker.event_materialization_basis()
            self.assertIsNotNone(basis)
            self.assertEqual(basis["mode"],"EVENT_MATERIALIZATION_INGRESS")
            self.assertEqual(basis["transport_intent_hash"],req["transport_intent_hash"])

    def test_registry_does_not_require_relay_parent_for_claim(self):
        root=Path(__file__).resolve().parents[1]
        reg=json.loads((root/"control/worker-registry.d/device-kv-intr-observation-001.json").read_text())
        adm=reg["tasks"][0]["admission"]
        self.assertNotIn("parent_terminal_transition_required",adm)
        self.assertEqual(adm["admitted_predecessor_rule"],"AUTHENTIC_RELAY_CONTINUITY_OR_VERIFIED_DEVICE_KV_EVENT_MATERIALIZATION")
        self.assertFalse(adm["event_materialization_grants_authority"])

    def test_consumer_scrubs_hosted_and_github_authority(self):
        env=consumer.scrubbed_env({
            "PATH":"/bin",
            "HOME":"/tmp",
            "GITHUB_ACTIONS":"true",
            "GITHUB_TOKEN":"secret",
            "STEGVERSE_GITHUB_TOKEN":"secret2"
        })
        self.assertNotIn("GITHUB_ACTIONS",env)
        self.assertNotIn("GITHUB_TOKEN",env)
        self.assertNotIn("STEGVERSE_GITHUB_TOKEN",env)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"],"TV/TVC")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"],"NONE")

if __name__=="__main__":
    unittest.main()
