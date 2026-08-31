from __future__ import annotations
import json, subprocess, tempfile, unittest
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

    def test_portable_payload_stages_through_current_cvk_source(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"
            source=base/"source"
            kv_source=base/"cvk"
            kv_data=base/"KnowledgeVault"
            (runtime/consumer.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime/consumer.INGRESS_DIR_REL).mkdir(parents=True)
            (kv_source/"runtime").mkdir(parents=True)
            kv_data.mkdir(parents=True)

            req=materialization()
            req["payload_ref"]="inline://materialization_request.portable_payload"
            req["portable_payload"]={
                "schema":"stegverse.kv.portable-direct-source-inline-payload/v1",
                "directory_id":"pictures",
                "canonical_path":"04_Media/Pictures",
                "source_class":"OWNER_CONTROLLED_FILE",
                "credential_requirement":"NONE",
                "total_bytes":3,
                "files":[],
                "authority_effect":"NONE",
            }
            req["payload_hash"]=consumer.sha(req["portable_payload"])
            body=dict(req); body.pop("request_hash",None); req["request_hash"]=consumer.sha(body)
            mid=req["materialization_id"]
            (runtime/consumer.REQUEST_DIR_REL/f"{mid}.json").write_text(json.dumps(req),encoding="utf-8")
            ing={
                "schema":"stegverse.device-kv-intr-materialization-ingress/v1",
                "state":"INGRESS_ADMITTED",
                "materialization_id":mid,
                "request_hash":req["request_hash"],
                "transport_intent_hash":req["transport_intent_hash"],
                "payload_hash":req["payload_hash"],
                "operation_id":req["operation_id"],
                "packet_id":req["packet_id"],
                "claim_or_fence_minted":False,
                "credential_authority":"TV/TVC",
                "github_token_runtime_authority":"NONE",
            }
            (runtime/consumer.INGRESS_DIR_REL/f"{mid}.json").write_text(json.dumps(ing),encoding="utf-8")
            (kv_source/"runtime/portable_direct_source_ingress.py").write_text(
                "def admit_portable_direct_source(request, ingress_receipt, *, kv_data_root):\n"
                "    return {\"schema\":\"stegverse.kv.portable-direct-source-admission/v1\","
                "\"state\":\"STAGED_UNTRUSTED\",\"receipt_sha256\":\"sha256:"
                + "a"*64
                + "\",\"staging_path\":\"00_Inbox/DirectSource/pictures/test\","
                "\"exact_readback_verified\":True,\"trusted_semantic_admission\":False,"
                "\"credential_authority\":\"TV/TVC\"}\n",
                encoding="utf-8",
            )
            def runner(*args,**kwargs):
                return subprocess.CompletedProcess(args[0],0,stdout='{"state":"COMPLETED"}\n',stderr="")
            result=consumer.consume_one(
                source,runtime,mid,runner=runner,
                env={
                    "PATH":"/bin",
                    "HOME":str(base),
                    "STEGVERSE_KV_SOURCE_ROOT":str(kv_source),
                    "STEGVERSE_KV_DATA_ROOT":str(kv_data),
                },
            )
            self.assertEqual(result["state"],"MATERIALIZATION_EXECUTION_ATTEMPTED")
            self.assertTrue(result["portable_payload_present"])
            self.assertTrue(result["portable_kv_staging_attempted"])
            self.assertEqual(result["portable_kv_staging_state"],"STAGED_UNTRUSTED")
            self.assertTrue(result["portable_kv_exact_readback_verified"])
            self.assertFalse(result["trusted_semantic_admission"])

    def test_portable_payload_missing_data_root_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"
            source=base/"source"
            kv_source=base/"cvk"
            (runtime/consumer.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime/consumer.INGRESS_DIR_REL).mkdir(parents=True)
            (kv_source/"runtime").mkdir(parents=True)
            req=materialization()
            req["payload_ref"]="inline://materialization_request.portable_payload"
            req["portable_payload"]={
                "schema":"stegverse.kv.portable-direct-source-inline-payload/v1",
                "directory_id":"pictures","canonical_path":"04_Media/Pictures",
                "source_class":"OWNER_CONTROLLED_FILE","credential_requirement":"NONE",
                "total_bytes":1,"files":[],"authority_effect":"NONE",
            }
            req["payload_hash"]=consumer.sha(req["portable_payload"])
            body=dict(req); body.pop("request_hash",None); req["request_hash"]=consumer.sha(body)
            mid=req["materialization_id"]
            (runtime/consumer.REQUEST_DIR_REL/f"{mid}.json").write_text(json.dumps(req),encoding="utf-8")
            ing={"schema":"stegverse.device-kv-intr-materialization-ingress/v1","state":"INGRESS_ADMITTED",
                 "materialization_id":mid,"request_hash":req["request_hash"],
                 "transport_intent_hash":req["transport_intent_hash"],"payload_hash":req["payload_hash"],
                 "operation_id":req["operation_id"],"packet_id":req["packet_id"],
                 "claim_or_fence_minted":False,"credential_authority":"TV/TVC"}
            (runtime/consumer.INGRESS_DIR_REL/f"{mid}.json").write_text(json.dumps(ing),encoding="utf-8")
            def runner(*args,**kwargs):
                return subprocess.CompletedProcess(args[0],0,stdout='{"state":"COMPLETED"}\n',stderr="")
            result=consumer.consume_one(
                source,runtime,mid,runner=runner,
                env={"PATH":"/bin","HOME":str(base),"STEGVERSE_KV_SOURCE_ROOT":str(kv_source)},
            )
            self.assertEqual(result["state"],"MATERIALIZATION_EXECUTION_BLOCKED")
            self.assertEqual(result["portable_kv_staging_state"],"BLOCKED")
            self.assertIn("portable_kv_data_root_missing",result["portable_kv_staging_error"])

    def test_kv_data_root_is_forwarded_by_all_resident_boundaries(self):
        root=Path(__file__).resolve().parents[1]
        for rel in (
            "scripts/refresh_and_execute_resident_task.py",
            "scripts/consume_stegos_kv_intr_chain_request.py",
            "scripts/consume_resident_rendezvous.py",
        ):
            self.assertIn("STEGVERSE_KV_DATA_ROOT",(root/rel).read_text())

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
