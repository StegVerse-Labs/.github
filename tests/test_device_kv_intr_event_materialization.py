from __future__ import annotations
import hashlib, json, subprocess, tempfile, unittest
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
                "\"credential_authority\":\"TV/TVC\"}\n"
                "def promote_portable_direct_source(request, staging_receipt, *, kv_data_root):\n"
                "    return {\"admission_receipt\":{"
                "\"schema\":\"stegverse.kv.portable-direct-source-canonical-admission/v1\","
                "\"state\":\"CANONICAL_ADMITTED\",\"receipt_sha256\":\"sha256:"
                + "b"*64
                + "\",\"canonical_batch_path\":\"04_Media/Pictures/test\","
                "\"canonical_kv_persistence_observed\":True,"
                "\"exact_canonical_readback_verified\":True,"
                "\"trusted_semantic_admission\":True,"
                "\"provider_session_required\":False,"
                "\"provider_operation_authorized\":False,"
                "\"credential_authority\":\"TV/TVC\","
                "\"authority_effect\":\"NONE\"},"
                "\"connection_health\":{"
                "\"compatibility_state\":\"VERIFIED\","
                "\"credential_material_present\":False,"
                "\"provider_operation_authorized\":False,"
                "\"authority_effect\":\"NONE\"}}\n",
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
                    "STEGVERSE_KV_ROOT":str(kv_data),
                },
            )
            self.assertEqual(result["state"],"MATERIALIZATION_EXECUTION_ATTEMPTED")
            self.assertTrue(result["portable_payload_present"])
            self.assertTrue(result["portable_kv_staging_attempted"])
            self.assertEqual(result["portable_kv_staging_state"],"STAGED_UNTRUSTED")
            self.assertTrue(result["portable_kv_exact_readback_verified"])
            self.assertTrue(result["portable_kv_canonical_admission_attempted"])
            self.assertEqual(result["portable_kv_canonical_admission_state"],"CANONICAL_ADMITTED")
            self.assertEqual(result["portable_kv_canonical_batch_path"],"04_Media/Pictures/test")
            self.assertTrue(result["portable_kv_exact_canonical_readback_verified"])
            self.assertEqual(result["portable_kv_connection_health_state"],"VERIFIED")
            self.assertTrue(result["trusted_semantic_admission"])

    def test_portable_canonical_admission_failure_blocks_consumption(self):
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
            (kv_source/"runtime/portable_direct_source_ingress.py").write_text(
                "def admit_portable_direct_source(request, ingress_receipt, *, kv_data_root):\n"
                "    return {\"schema\":\"stegverse.kv.portable-direct-source-admission/v1\","
                "\"state\":\"STAGED_UNTRUSTED\",\"receipt_sha256\":\"sha256:"+"a"*64+"\","
                "\"staging_path\":\"00_Inbox/DirectSource/pictures/test\","
                "\"exact_readback_verified\":True,\"trusted_semantic_admission\":False,"
                "\"credential_authority\":\"TV/TVC\"}\n"
                "def promote_portable_direct_source(request, staging_receipt, *, kv_data_root):\n"
                "    raise ValueError(\"canonical readback failed\")\n",
                encoding="utf-8",
            )
            def runner(*args,**kwargs):
                return subprocess.CompletedProcess(args[0],0,stdout='{"state":"COMPLETED"}\n',stderr="")
            result=consumer.consume_one(
                source,runtime,mid,runner=runner,
                env={"PATH":"/bin","HOME":str(base),"STEGVERSE_KV_SOURCE_ROOT":str(kv_source),"STEGVERSE_KV_ROOT":str(kv_data)},
            )
            self.assertEqual(result["state"],"MATERIALIZATION_EXECUTION_BLOCKED")
            self.assertEqual(result["portable_kv_canonical_admission_state"],"BLOCKED")
            self.assertIn("portable_kv_canonical_admission_failed",result["portable_kv_canonical_admission_error"])
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

    def test_bounded_kv_query_projects_directory_and_materializes_hb_response(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"
            source=base/"source"
            kv_source=base/"cvk"
            kv_data=base/"KnowledgeVault"
            heartbeat=base/"heartbeat"
            (runtime/consumer.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime/consumer.INGRESS_DIR_REL).mkdir(parents=True)
            (kv_source/"runtime").mkdir(parents=True)
            (kv_data/"00_Inbox").mkdir(parents=True)
            query={
                "schema_version":"kv.interlock.request.v1",
                "operation":"REQUEST",
                "request_id":"site-kv-query-1",
                "requester":{"module":"Site","component":"MyKVDirectory"},
                "purpose":"List the selected owner KnowledgeVault directory.",
                "record_class":"MY_KV_DIRECTORY_PROJECTION",
                "requested_scope":["entries","connection_health"],
                "minimum_necessary_justification":"Render only admitted file metadata and connection health.",
                "authority_ref":"stegos-node://SV-NODE-"+"4"*24,
                "disclosure_mode":"BOUNDED_CONTEXT",
                "selector":{"directory_id":"pictures","canonical_path":"04_Media/Pictures"},
            }
            req=materialization()
            req["payload_ref"]="inline://materialization_request.kv_request"
            req["kv_request"]=query
            req["payload_hash"]=consumer.sha(query)
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
                "transport_origin":"STEGOS_NODE_OUTBOX",
                "node_id":"SV-NODE-"+"4"*24,
                "interlock_id":"SV-IL-"+"5"*24,
                "claim_or_fence_minted":False,
                "credential_authority":"TV/TVC",
                "github_token_runtime_authority":"NONE",
            }
            (runtime/consumer.INGRESS_DIR_REL/f"{mid}.json").write_text(json.dumps(ing),encoding="utf-8")
            (kv_source/"runtime/portable_directory_projection.py").write_text(
                "def list_admitted_directory(*, kv_data_root, directory_id, canonical_path):\n"
                "    return {\"schema\":\"stegverse.kv.portable-directory-projection/v1\","
                "\"state\":\"KV_LISTED\",\"directory_id\":directory_id,"
                "\"canonical_path\":canonical_path,\"entries\":[{\"name\":\"one.bin\",\"kind\":\"file\"}],"
                "\"connection_health\":{\"compatibility_state\":\"VERIFIED\"},"
                "\"credential_material_present\":False,\"provider_operation_authorized\":False,"
                "\"authority_effect\":\"NONE\"}\n"
                "def get_directory_health(*, kv_data_root, directory_id, canonical_path):\n"
                "    return {\"canonical_path\":canonical_path,\"compatibility_state\":\"VERIFIED\","
                "\"credential_material_present\":False,\"provider_operation_authorized\":False,"
                "\"authority_effect\":\"NONE\"}\n"
                "def get_installation_status(*, kv_data_root):\n"
                "    return {\"schema\":\"stegverse.kv.installation-status-projection/v1\","
                "\"state\":\"KV_INSTALLATION_VERIFIED\",\"resident_kv_root_observed\":True,"
                "\"installation_receipt_present\":True,\"source_tree_sha\":\""
                + "a"*40
                + "\",\"receipt_sha256\":\"sha256:"
                + "b"*64
                + "\",\"receipt_verified_utc\":\"2026-08-31T20:00:00Z\","
                "\"full_template_parity\":\"VALIDATED\","
                "\"source_census\":{\"files\":133,\"directories\":53},"
                "\"destination_kind\":\"owner-storage\","
                "\"current_cloud_provider_observation\":False,"
                "\"credential_material_present\":False,\"provider_operation_authorized\":False,"
                "\"authority_effect\":\"NONE\"}\n",
                encoding="utf-8",
            )
            def runner(*args,**kwargs):
                return subprocess.CompletedProcess(args[0],0,stdout='{"state":"COMPLETED"}\n',stderr="")
            env={
                "PATH":"/bin","HOME":str(base),
                "STEGVERSE_KV_SOURCE_ROOT":str(kv_source),
                "STEGVERSE_KV_ROOT":str(kv_data),
                "STEGVERSE_HEARTBEAT_ROOT":str(heartbeat),
            }
            result=consumer.consume_one(source,runtime,mid,runner=runner,env=env)
            self.assertEqual(result["state"],"MATERIALIZATION_EXECUTION_ATTEMPTED")
            self.assertTrue(result["kv_query_present"])
            self.assertTrue(result["kv_query_attempted"])
            self.assertEqual(result["kv_query_state"],"QUERY_COMPLETE")
            self.assertTrue(result["kv_query_response_transported_on_hb_derived_carrier"])
            self.assertTrue(result["kv_query_exact_response_packet_recovered"])
            persisted=json.loads((runtime/consumer.QUERY_RESPONSE_DIR_REL/f"{mid}.json").read_text())
            self.assertEqual(persisted["response"]["projection"]["entries"][0]["name"],"one.bin")
            self.assertTrue((heartbeat/persisted["response_shared_hb_signal_ref"]).is_file())

            lookup={
                "schema":"stegverse.device-kv.query-result-request/v1",
                "materialization_id":mid,
                "request_hash":req["request_hash"],
                "node_id":ing["node_id"],
                "authority_effect":"NONE_RESULT_LOOKUP_ONLY",
            }
            raw=json.dumps(lookup,sort_keys=True,separators=(",",":")).encode()
            headers={
                "Content-Type":"application/json",
                "X-StegVerse-Transport":"InTr",
                "X-StegVerse-Transport-Origin":"STEGOS_NODE_OUTBOX",
                "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest(),
            }
            with mock.patch.dict(consumer.os.environ,{"STEGVERSE_HEARTBEAT_ROOT":str(heartbeat)},clear=False):
                delivered=ingress.retrieve_device_kv_query_result(runtime_root=runtime,body=raw,headers=headers)
            self.assertEqual(delivered["state"],"RESULT_AVAILABLE")
            self.assertEqual(delivered["response"]["projection"]["entries"][0]["name"],"one.bin")
            self.assertTrue(delivered["response_transported_on_hb_derived_carrier"])
            self.assertEqual(delivered["response_carrier_signal"]["authority"]["authority_effect"],"NONE_CARRIER_ONLY")


    def test_bounded_kv_installation_status_query_uses_same_hb_return_path(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"
            source=base/"source"
            kv_source=base/"cvk"
            kv_data=base/"KnowledgeVault"
            heartbeat=base/"heartbeat"
            (runtime/consumer.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime/consumer.INGRESS_DIR_REL).mkdir(parents=True)
            (kv_source/"runtime").mkdir(parents=True)
            (kv_data/"_System").mkdir(parents=True)

            query={
                "schema_version":"kv.interlock.request.v1",
                "operation":"REQUEST",
                "request_id":"site-kv-installation-query-1",
                "requester":{"module":"Site","component":"MyKVOnboarding"},
                "purpose":"Determine whether the current resident KnowledgeVault is a validated canonical installation.",
                "record_class":"MY_KV_INSTALLATION_STATUS",
                "requested_scope":["installation_status"],
                "minimum_necessary_justification":"Return only bounded installation status needed for My KV Step 2.",
                "authority_ref":"stegos-node://SV-NODE-"+"4"*24,
                "disclosure_mode":"BOUNDED_CONTEXT",
                "selector":{"receipt_path":"_System/installation.receipt.json"},
            }
            req=materialization()
            req["payload_ref"]="inline://materialization_request.kv_request"
            req["kv_request"]=query
            req["payload_hash"]=consumer.sha(query)
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
                "transport_origin":"STEGOS_NODE_OUTBOX",
                "node_id":"SV-NODE-"+"4"*24,
                "interlock_id":"SV-IL-"+"5"*24,
                "claim_or_fence_minted":False,
                "credential_authority":"TV/TVC",
                "github_token_runtime_authority":"NONE",
            }
            (runtime/consumer.INGRESS_DIR_REL/f"{mid}.json").write_text(json.dumps(ing),encoding="utf-8")
            (kv_source/"runtime/portable_directory_projection.py").write_text(
                "def list_admitted_directory(*, kv_data_root, directory_id, canonical_path):\n"
                "    raise AssertionError('directory projection should not run')\n"
                "def get_directory_health(*, kv_data_root, directory_id, canonical_path):\n"
                "    raise AssertionError('health projection should not run')\n"
                "def get_installation_status(*, kv_data_root):\n"
                "    return {\"schema\":\"stegverse.kv.installation-status-projection/v1\","
                "\"state\":\"KV_INSTALLATION_VERIFIED\","
                "\"resident_kv_root_observed\":True,"
                "\"installation_receipt_present\":True,"
                "\"source_tree_sha\":\""+"a"*40+"\","
                "\"receipt_sha256\":\"sha256:"+"b"*64+"\","
                "\"receipt_verified_utc\":\"2026-08-31T20:00:00Z\","
                "\"full_template_parity\":\"VALIDATED\","
                "\"source_census\":{\"files\":133,\"directories\":53},"
                "\"destination_kind\":\"owner-storage\","
                "\"current_cloud_provider_observation\":False,"
                "\"credential_material_present\":False,"
                "\"provider_operation_authorized\":False,"
                "\"authority_effect\":\"NONE\"}\n",
                encoding="utf-8",
            )
            env={
                "PATH":"/bin","HOME":str(base),
                "STEGVERSE_KV_SOURCE_ROOT":str(kv_source),
                "STEGVERSE_KV_ROOT":str(kv_data),
                "STEGVERSE_HEARTBEAT_ROOT":str(heartbeat),
            }
            result=consumer.consume_one(source,runtime,mid,env=env)
            self.assertEqual(result["state"],"MATERIALIZATION_EXECUTION_ATTEMPTED")
            persisted=json.loads((runtime/consumer.QUERY_RESPONSE_DIR_REL/f"{mid}.json").read_text())
            response=persisted["response"]
            self.assertEqual(response["record_class"],"MY_KV_INSTALLATION_STATUS")
            self.assertEqual(response["selector"],{"receipt_path":"_System/installation.receipt.json"})
            self.assertIsNone(response["directory_id"])
            self.assertEqual(response["receipt_path"],"_System/installation.receipt.json")
            self.assertEqual(response["projection"]["state"],"KV_INSTALLATION_VERIFIED")
            self.assertTrue(response["projection"]["resident_kv_root_observed"])
            self.assertFalse(response["projection"]["current_cloud_provider_observation"])
            self.assertTrue(persisted["response_transported_on_hb_derived_carrier"])
            self.assertTrue(persisted["exact_response_packet_recovered"])

    def test_installation_status_query_rejects_directory_requester_and_wrong_selector(self):
        query={
            "schema_version":"kv.interlock.request.v1","operation":"REQUEST","request_id":"q-install",
            "requester":{"module":"Site","component":"MyKVDirectory"},"purpose":"read",
            "record_class":"MY_KV_INSTALLATION_STATUS","requested_scope":["installation_status"],
            "minimum_necessary_justification":"minimum","authority_ref":"stegos-node://SV-NODE-"+"4"*24,
            "disclosure_mode":"BOUNDED_CONTEXT",
            "selector":{"receipt_path":"_System/installation.receipt.json"},
        }
        req=materialization()
        req["payload_ref"]="inline://materialization_request.kv_request"; req["kv_request"]=query
        req["payload_hash"]=consumer.sha(query)
        body=dict(req); body.pop("request_hash",None); req["request_hash"]=consumer.sha(body)
        ing={"transport_origin":"STEGOS_NODE_OUTBOX","node_id":"SV-NODE-"+"4"*24}
        with self.assertRaisesRegex(consumer.DeviceKVMaterializationError,"requester_invalid"):
            consumer.validate_kv_query(req,ing)
        query["requester"]={"module":"Site","component":"MyKVOnboarding"}
        query["selector"]={"receipt_path":"../installation.receipt.json"}
        req["kv_request"]=query; req["payload_hash"]=consumer.sha(query)
        body=dict(req); body.pop("request_hash",None); req["request_hash"]=consumer.sha(body)
        with self.assertRaisesRegex(consumer.DeviceKVMaterializationError,"installation_query_selector_invalid"):
            consumer.validate_kv_query(req,ing)

    def test_kv_query_node_binding_mismatch_blocks_projection(self):
        query={
            "schema_version":"kv.interlock.request.v1","operation":"REQUEST","request_id":"q",
            "requester":{"module":"Site","component":"MyKVDirectory"},"purpose":"read",
            "record_class":"MY_KV_CONNECTION_HEALTH","requested_scope":["connection_health"],
            "minimum_necessary_justification":"minimum","authority_ref":"stegos-node://SV-NODE-"+"9"*24,
            "disclosure_mode":"BOUNDED_CONTEXT",
            "selector":{"directory_id":"pictures","canonical_path":"04_Media/Pictures"},
        }
        req=materialization()
        req["payload_ref"]="inline://materialization_request.kv_request"; req["kv_request"]=query
        req["payload_hash"]=consumer.sha(query)
        body=dict(req); body.pop("request_hash",None); req["request_hash"]=consumer.sha(body)
        ing={"transport_origin":"STEGOS_NODE_OUTBOX","node_id":"SV-NODE-"+"4"*24}
        with self.assertRaisesRegex(consumer.DeviceKVMaterializationError,"node_authority_binding"):
            consumer.validate_kv_query(req,ing)

    def test_profile_advertises_device_kv_result_path(self):
        p=ingress.profile(False)
        self.assertEqual(p["device_kv_result_path"],"/intr/device-kv/result")
        self.assertIn("KV:KnowledgeVaultInterlock",p["profiles"])

    def test_kv_data_root_is_forwarded_by_all_resident_boundaries(self):
        root=Path(__file__).resolve().parents[1]
        for rel in (
            "scripts/refresh_and_execute_resident_task.py",
            "scripts/consume_stegos_kv_intr_chain_request.py",
            "scripts/consume_resident_rendezvous.py",
        ):
            self.assertIn("STEGVERSE_KV_ROOT",(root/rel).read_text())

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
