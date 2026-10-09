from __future__ import annotations
import json, sys, tempfile, types, unittest
from pathlib import Path

from scripts import consume_kv_publisher_return_materialization_request as consumer
from workers import universal_intr_profiled_ingress as ingress


def _real_custody():
    """The real producer; appends go to the tmp Organization ledger root set in setUp."""
    import heartbeat_runtime.worker_runtime_legacy  # noqa: F401  (import order)
    from workers import canonical_state_transition_custody as real
    return real


def _recorded_rtc006(real) -> dict:
    """RTC-SDK-RETURN-006 as the real producer records it, projected the way the consumer returns it."""
    result=real.submit_state_receipt(real.build_state_receipt(
        transition_id="RTC-SDK-RETURN-006",transition_sequence=1,subject_or_correlation_id="RTC-FIXTURE",
        transition_outcome="EXECUTED",prior_state_ref_or_hash=None,resulting_state_ref_or_hash=None,
        governance_decision_ref_where_applicable=None,transition_evidence={"fixture":"rtc006"}))
    return {
      "state":result["state"],
      "organization_receipt_sha256":result["organization_receipt"]["receipt_sha256"],
      "reconstruction_status":result["reconstruction_status"],
      "required_evidence_validation_status":result["required_evidence_validation_status"],
      "receipt_sha256":result["receipt_sha256"],
      "reconstructed_receipt_sha256":None,
    }


def request(owner: str) -> dict:
    value={
      "schema":"stegverse.universal-intr-materialization-request/v1",
      "materialization_id":"INTR-MAT-"+"a"*24,
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
      "transport_schema":"stegverse.universal-intr-transport/v1",
      "transport_protocol":"InTr",
      "transport_intent_hash":"sha256:"+"1"*64,
      "operation_id":"publisher-transfer-001:return",
      "packet_id":"INTR-"+"2"*24,
      "payload_hash":"sha256:"+"3"*64,
      "payload_ref":"runtime://intr-payloads/publisher-artifact-transfer/x.return.bin",
      "destination":consumer.DESTINATION,
      "boundary_path":["STEGOS_ECOSYSTEM","DEVICE_SYSTEM","KV"],
      "downstream_owner_ref":owner,
      "event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,
      "interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,
      "transport_grants_execution_authority":False,"credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY",
    }
    body=dict(value); value["request_hash"]=consumer.sha(body)
    return value


def mir_return() -> dict:
    manifest={
      "schema":"stegverse.ingress-manifest/v1",
      "completion":{"direction":"SOUTH"},
    }
    capsule={
      "profile":consumer.SDK_COMPLETION_CAPSULE_PROFILE,
      "authority_effect":"NONE",
    }
    return {
      "schema":consumer.RETURN_SCHEMA,
      "roundtrip_binding":{
        "profile":consumer.MIR_ROUNDTRIP_BINDING_PROFILE,
        "publisher_transition_observed":True,
        "sdk_return_binding_observed":False,
        "final_stegverse_side_egress_transition_observed":False,
        "interlock_intr_egress_observed":False,
        "far_side_transition_observed":False,
        "authentic_external_mir_endpoint_substitution_observed":False,
        "communication_complete":False,
        "authority_effect":"NONE",
        "downstream_completion_capsule":capsule,
        "sdk_processor_state":{
          "state":"SDK_MANIFEST_SELECTED_PROCESSING_EXECUTED",
          "processor_result_observed":True,
          "manifest":manifest,
          "processor_result":{"manifest_receipt_id":"MR-"+"D"*64},
        },
      },
    }


class SDKPublisherReturnIngressTests(unittest.TestCase):
    def setUp(self):
        # Ledger roots are supplied, never derived from the host.
        from unittest.mock import patch
        import os
        ledger=tempfile.TemporaryDirectory()
        self.addCleanup(ledger.cleanup)
        env=patch.dict(os.environ,{"STEGVERSE_ORG_LEDGER_ROOT":ledger.name})
        env.start()
        self.addCleanup(env.stop)

    def test_existing_discriminator_accepts_sdk_owner_without_new_ingress_plane(self):
        self.assertTrue(ingress._is_kv_publisher_return(request(consumer.SDK_DOWNSTREAM_OWNER)))
        self.assertTrue(ingress._is_kv_publisher_return(request(consumer.KV_DOWNSTREAM_OWNER)))

    def test_request_validator_accepts_only_known_return_owners(self):
        consumer.validate_request(request(consumer.SDK_DOWNSTREAM_OWNER))
        consumer.validate_request(request(consumer.KV_DOWNSTREAM_OWNER))
        bad=request("Unknown/Owner")
        with self.assertRaisesRegex(consumer.KVPublisherReturnError,"downstream_owner_ref"):
            consumer.validate_request(bad)

    def test_sdk_inputs_are_recovered_only_from_carried_verified_state(self):
        returned=mir_return()
        manifest,receipt_id,capsule=consumer.extract_sdk_materialization_inputs(returned)
        self.assertIs(manifest,returned["roundtrip_binding"]["sdk_processor_state"]["manifest"])
        self.assertEqual(receipt_id,"MR-"+"D"*64)
        self.assertIs(capsule,returned["roundtrip_binding"]["downstream_completion_capsule"])

    def test_sdk_input_extraction_fails_closed_without_original_receipt(self):
        returned=mir_return()
        del returned["roundtrip_binding"]["sdk_processor_state"]["processor_result"]["manifest_receipt_id"]
        with self.assertRaisesRegex(consumer.KVPublisherReturnError,"manifest_receipt_id"):
            consumer.extract_sdk_materialization_inputs(returned)

    def test_sdk_input_extraction_fails_closed_on_downstream_promotion(self):
        returned=mir_return(); returned["roundtrip_binding"]["interlock_intr_egress_observed"]=True
        with self.assertRaisesRegex(consumer.KVPublisherReturnError,"prematurely promoted"):
            consumer.extract_sdk_materialization_inputs(returned)

    def test_sdk_consumer_source_invokes_only_existing_sdk_materializer(self):
        source=open(consumer.__file__,encoding="utf-8").read()
        self.assertIn("from stegverse.publisher_return_materialization import materialize_publisher_return_binding",source)
        self.assertIn("sdk_return_binding_observed\":True",source)
        self.assertIn("successful_data_transport_round_trip_identified\":False",source)
        self.assertNotIn("communication_complete\":True",source)

    def test_sdk_return_binding_requires_organization_record_before_egress(self):
        captured={}
        real=_real_custody()
        fake=types.ModuleType("canonical_state_transition_custody")
        def build_state_receipt(**kwargs):
            captured.update(kwargs)
            return real.build_state_receipt(**kwargs)
        def submit_state_receipt(receipt):
            captured["submitted"]=receipt
            # Real producer: Organization ledger record, no Master Records reconstruction.
            captured["recorded"]=real.submit_state_receipt(receipt)
            return captured["recorded"]
        fake.build_state_receipt=build_state_receipt
        fake.submit_state_receipt=submit_state_receipt
        def require_predecessor_master_records_organization_record(receipt_sha256, *, successor_transition_id):
            self.assertEqual(receipt_sha256,"9"*64)
            self.assertEqual(successor_transition_id,"RTC-SDK-RETURN-006")
            closure={
              "transition_id":"RTC-PREDECESSOR",
              "state":"RECORDED",
              "reconstruction_status":"PASS",
              "required_evidence_validation_status":"PASS",
              "receipt_sha256":"9"*64,
              "reconstructed_receipt_sha256":"9"*64,
              "master_record_ref":"master-record:state-transition:sha256:"+"9"*64,
              "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
            }
            return "sha256:"+"9"*64,[{
              "evidence_id":"predecessor-master-records-organization-record:RTC-SDK-RETURN-006",
              "evidence_type":"PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD",
              "origin_transition_id":"RTC-SDK-RETURN-006",
              "encoding":"canonical-json",
              "sha256":consumer.sha(closure).split(":",1)[1],
              "content":closure,
            }]
        fake.require_predecessor_master_records_organization_record=require_predecessor_master_records_organization_record
        previous=sys.modules.get("canonical_state_transition_custody")
        sys.modules["canonical_state_transition_custody"]=fake
        try:
            with tempfile.TemporaryDirectory() as temp:
                runtime=Path(temp)
                output=runtime/consumer.SDK_BINDING_DIR/"sdk-return.json"
                output.parent.mkdir(parents=True)
                binding={"schema":"stegverse.sdk.publisher-return-binding/v1","sdk_return_binding_observed":True}
                output.write_text(json.dumps(binding,sort_keys=True,separators=(",",":")),encoding="utf-8")
                materialization={
                  "schema":"stegverse.sdk.publisher-return-materialization-receipt/v1",
                  "output_sha256":consumer.sha(binding),
                  "sdk_return_binding_observed":True,
                }
                req=request(consumer.SDK_DOWNSTREAM_OWNER)
                req["predecessor_master_records_receipt_sha256"]="9"*64
                result=consumer._record_sdk_return_binding_custody(
                    runtime,req["materialization_id"],req,"sha256:"+"7"*64,output,materialization
                )
            self.assertEqual(captured["transition_id"],"RTC-SDK-RETURN-006")
            self.assertEqual(captured["resulting_state_ref_or_hash"],consumer.sha(binding))
            self.assertEqual(captured["prior_state_ref_or_hash"],"sha256:"+"9"*64)
            self.assertEqual(len(captured["required_evidence_manifest"]),3)
            self.assertEqual(captured["required_evidence_manifest"][0]["evidence_type"],"PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD")
            self.assertEqual(captured["required_evidence_manifest"][0]["content"]["receipt_sha256"],"9"*64)
            self.assertEqual(captured["required_evidence_manifest"][1]["content"],binding)
            self.assertEqual(captured["required_evidence_manifest"][1]["evidence_type"],"SDK_PUBLISHER_RETURN_BINDING")
            self.assertEqual(captured["transition_evidence"]["return_transport_terminal_receipt_hash"],"sha256:"+"7"*64)
            self.assertEqual(result["state"],"RECORDED")
            self.assertEqual(result["organization_receipt_sha256"],captured["recorded"]["organization_receipt"]["receipt_sha256"])
            self.assertEqual(result["reconstruction_status"],"NOT_REQUESTED")
        finally:
            if previous is None:
                sys.modules.pop("canonical_state_transition_custody",None)
            else:
                sys.modules["canonical_state_transition_custody"]=previous

    def test_sdk_return_binding_blocks_when_organization_record_not_recorded(self):
        fake=types.ModuleType("canonical_state_transition_custody")
        fake.build_state_receipt=lambda **kwargs: {"schema":"stegverse.canonical-state-transition-receipt/v1"}
        fake.submit_state_receipt=lambda receipt: {"state":"BOUNDARY","reason":"not recorded"}
        recorded=[]
        def record_refusal(refusal, *, gated_transition_id, state_receipt_sha256=None, root=None):
            recorded.append((dict(refusal),gated_transition_id))
            return {**refusal,"refusal_recorded":True,"refusal_organization_receipt_sha256":"sha256:"+"5"*64}
        fake.record_organization_receipt_refusal=record_refusal
        fake.require_predecessor_master_records_organization_record=lambda receipt_sha256, *, successor_transition_id: (
            "sha256:"+"9"*64,
            [{
              "evidence_id":"predecessor-master-records-organization-record:RTC-SDK-RETURN-006",
              "evidence_type":"PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD",
              "origin_transition_id":"RTC-SDK-RETURN-006",
              "encoding":"canonical-json",
              "sha256":"8"*64,
              "content":{
                "transition_id":"RTC-PREDECESSOR",
                "state":"RECORDED",
                "reconstruction_status":"PASS",
                "required_evidence_validation_status":"PASS",
                "receipt_sha256":"9"*64,
                "reconstructed_receipt_sha256":"9"*64,
                "master_record_ref":"master-record:state-transition:sha256:"+"9"*64,
                "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
              },
            }],
        )
        previous=sys.modules.get("canonical_state_transition_custody")
        sys.modules["canonical_state_transition_custody"]=fake
        try:
            with tempfile.TemporaryDirectory() as temp:
                runtime=Path(temp)
                output=runtime/consumer.SDK_BINDING_DIR/"sdk-return.json"
                output.parent.mkdir(parents=True)
                binding={"schema":"stegverse.sdk.publisher-return-binding/v1","sdk_return_binding_observed":True}
                output.write_text(json.dumps(binding,sort_keys=True,separators=(",",":")),encoding="utf-8")
                materialization={
                  "schema":"stegverse.sdk.publisher-return-materialization-receipt/v1",
                  "output_sha256":consumer.sha(binding),
                  "sdk_return_binding_observed":True,
                }
                req=request(consumer.SDK_DOWNSTREAM_OWNER)
                req["predecessor_master_records_receipt_sha256"]="9"*64
                with self.assertRaisesRegex(consumer.KVPublisherReturnError,"SDK return binding Organization record not recorded") as caught:
                    consumer._record_sdk_return_binding_custody(
                        runtime,req["materialization_id"],req,"sha256:"+"9"*64,output,materialization
                    )
                # Inside the attempted transition: the typed refusal, with the
                # producer's reason, is appended as its non-ALLOW record.
                self.assertEqual(len(recorded),1)
                self.assertEqual(recorded[0][0]["failed_predicate"],"ORGANIZATION_RECORD_NOT_RECORDED")
                self.assertEqual(recorded[0][0]["detail"],"not recorded")
                self.assertFalse(caught.exception.refusal["consequence_committed"])
                self.assertTrue(caught.exception.refusal["refusal_recorded"])
        finally:
            if previous is None:
                sys.modules.pop("canonical_state_transition_custody",None)
            else:
                sys.modules["canonical_state_transition_custody"]=previous

    def test_rtc007_continuation_closes_master_records_before_rtc008_materialization(self):
        captured={}
        binding={
          "schema":"stegverse.sdk.publisher-return-binding/v1",
          "communication_state":"READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION",
          "authority_effect":"NONE",
          "communication_complete":False,
          "sdk_return_binding_observed":True,
          "final_stegverse_transition_observed":False,
          "interlock_intr_egress_observed":False,
          "far_side_transition_observed":False,
          "manifest_receipt_id":"MR-"+"D"*64,
          "egress":{"final_stegverse_transition_surface":"LLM_ADAPTER","transport":"INTERLOCK_INTR","destination_profile":"MIR","far_side_transition_required":True},
          "binding_sha256":"sha256:"+"b"*64,
        }
        llm_pkg=types.ModuleType("llm_adapter")
        llm=types.ModuleType("llm_adapter.southbound_sdk_return")
        def prepare_sdk_return_for_intr(binding_bytes,transition_id):
            self.assertEqual(json.loads(binding_bytes),binding)
            return {
              "schema":"stegverse.llm-adapter.southbound-final-transition/v1",
              "state":"FINAL_STEGVERSE_SIDE_TRANSITION_PREPARED",
              "transition_surface":"LLM_ADAPTER",
              "destination_profile":"MIR",
              "sdk_binding_sha256":consumer.sha(binding_bytes).split(":",1)[1],
              "final_stegverse_transition_surface_reached":True,
              "intr_handoff":{"schema":"stegverse.llm-adapter.southbound-intr-egress-handoff/v1","sdk_binding_sha256":consumer.sha(binding_bytes).split(":",1)[1]},
              "authority_effect":"NONE",
            }
        llm.prepare_sdk_return_for_intr=prepare_sdk_return_for_intr
        def admit_intr_egress(transition, *, disposition, egress_receipt_hash, admitted_sdk_binding_sha256):
            self.assertEqual(disposition,"ALLOW")
            self.assertEqual(egress_receipt_hash,"e"*64)
            self.assertEqual(admitted_sdk_binding_sha256,transition["intr_handoff"]["sdk_binding_sha256"])
            return {
              "schema":"stegverse.llm-adapter.southbound-intr-egress-admission/v1",
              "state":"EGRESS_ADMITTED",
              "sdk_binding_sha256":admitted_sdk_binding_sha256,
              "egress_receipt_hash":egress_receipt_hash,
              "far_side_transition_observed":False,
              "communication_complete":False,
              "transition_authority":"Interlock/InTr",
            }
        llm.admit_intr_egress=admit_intr_egress
        stegos_pkg=types.ModuleType("stegos")
        stegos=types.ModuleType("stegos.mir_southbound_intr_consumer")
        stegos.prepare_mir_southbound_materialization=lambda handoff,payload_ref: {
          "status":"MIR_SOUTHBOUND_INTR_MATERIALIZATION_READY",
          "materialization_request":{"schema":"stegverse.universal-intr-materialization-request/v1","state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"},
          "interlock_intr_admission_observed":False,
          "mir_destination_transition_observed":False,
          "authority_effect":"NONE_REQUEST_ONLY",
        }
        real=_real_custody()
        rtc006=_recorded_rtc006(real)
        custody=types.ModuleType("canonical_state_transition_custody")
        def build_state_receipt(**kwargs):
            captured.update(kwargs)
            return real.build_state_receipt(**kwargs)
        custody.build_state_receipt=build_state_receipt
        predecessor_closure={
          "transition_id":"RTC-SDK-RETURN-006",
          "state":"RECORDED",
          "reconstruction_status":"PASS",
          "required_evidence_validation_status":"PASS",
          "receipt_sha256":rtc006["receipt_sha256"],
          "reconstructed_receipt_sha256":rtc006["receipt_sha256"],
          "master_record_ref":"master-record:state-transition:sha256:"+rtc006["receipt_sha256"],
          "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }
        custody.require_predecessor_master_records_organization_record=lambda receipt_sha256, *, successor_transition_id: (
          "sha256:"+receipt_sha256,
          [{
            "evidence_id":"predecessor-master-records-organization-record:"+successor_transition_id,
            "evidence_type":"PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD",
            "origin_transition_id":successor_transition_id,
            "encoding":"canonical-json",
            "sha256":consumer.sha(predecessor_closure).split(":",1)[1],
            "content":predecessor_closure,
          }],
        )
        def submit_state_receipt(receipt):
            captured["recorded"]=real.submit_state_receipt(receipt)
            return captured["recorded"]
        custody.submit_state_receipt=submit_state_receipt
        previous={name:sys.modules.get(name) for name in (
          "llm_adapter","llm_adapter.southbound_sdk_return","stegos","stegos.mir_southbound_intr_consumer","canonical_state_transition_custody"
        )}
        sys.modules["llm_adapter"]=llm_pkg
        sys.modules["llm_adapter.southbound_sdk_return"]=llm
        sys.modules["stegos"]=stegos_pkg
        sys.modules["stegos.mir_southbound_intr_consumer"]=stegos
        sys.modules["canonical_state_transition_custody"]=custody
        original_source_root=consumer.source_root
        original_submit_rtc008=consumer._submit_rtc008_materialization
        consumer.source_root=lambda env_name,repo_name,required: Path("/tmp")
        consumer._submit_rtc008_materialization=lambda request, **kwargs: {
          "schema":consumer.MIR_RTC008_RECEIPT_SCHEMA,
          "state":"INGRESS_ADMITTED",
          "master_records_state":"RECORDED",
          "master_records_reconstruction_status":"PASS",
          "master_records_required_evidence_validation_status":"PASS",
          "master_records_receipt_sha256":"d"*64,
          "master_records_reconstructed_receipt_sha256":"d"*64,
          "intr_admission_receipt_sha256":"e"*64,
          "rtc008_evidence_complete":True,
          "far_side_transition_observed":False,
          "caller_consequence_observed":False,
        }
        try:
            with tempfile.TemporaryDirectory() as temp:
                runtime=Path(temp)
                output=runtime/consumer.SDK_BINDING_DIR/"sdk-return.json"
                output.parent.mkdir(parents=True)
                output.write_text(json.dumps(binding,sort_keys=True,separators=(",",":")),encoding="utf-8")
                req=request(consumer.SDK_DOWNSTREAM_OWNER)
                result=consumer._prepare_rtc007_continuation(
                  runtime,req["materialization_id"],req,output,consumer.sha(binding),
                  rtc006,
                )
            self.assertEqual(captured["transition_id"],"RTC-STEGVERSE-EGRESS-007")
            self.assertEqual(captured["transition_sequence"],2)
            self.assertEqual(captured["prior_state_ref_or_hash"],"sha256:"+rtc006["receipt_sha256"])
            self.assertEqual(len(captured["required_evidence_manifest"]),3)
            self.assertEqual(captured["required_evidence_manifest"][0]["evidence_type"],"PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD")
            self.assertEqual(captured["required_evidence_manifest"][0]["content"]["transition_id"],"RTC-SDK-RETURN-006")
            self.assertEqual(captured["required_evidence_manifest"][1]["evidence_type"],"RTC_STEGVERSE_EGRESS_007_TRANSITION")
            self.assertEqual(captured["required_evidence_manifest"][2]["content"],binding)
            self.assertEqual(result["rtc007_master_records"]["state"],"RECORDED")
            self.assertEqual(result["rtc007_master_records"]["organization_receipt_sha256"],captured["recorded"]["organization_receipt"]["receipt_sha256"])
            self.assertTrue(result["rtc008_admission_observed"])
            self.assertEqual(result["rtc008_llm_adapter_admission"]["state"],"EGRESS_ADMITTED")
            self.assertEqual(result["rtc008_llm_adapter_admission"]["egress_receipt_hash"],"e"*64)
            self.assertFalse(result["rtc009_far_side_transition_observed"])
            self.assertFalse(result["caller_consequence_observed"])
            self.assertFalse(result["communication_complete"])
        finally:
            consumer.source_root=original_source_root
            consumer._submit_rtc008_materialization=original_submit_rtc008
            for name,value in previous.items():
                if value is None: sys.modules.pop(name,None)
                else: sys.modules[name]=value

    def test_rtc007_reconstructs_rtc006_at_exact_emission_boundary(self):
        source=open(consumer.__file__,encoding="utf-8").read()
        self.assertIn('require_predecessor_master_records_organization_record(',source)
        self.assertIn('successor_transition_id="RTC-STEGVERSE-EGRESS-007"',source)
        self.assertIn('require_organization_recorded_predecessor(rtc006_master_records,predecessor_transition_id="RTC-SDK-RETURN-006",',source)
        self.assertIn('successor_transition_id="RTC-STEGVERSE-EGRESS-007")',source)
        self.assertIn('required_evidence=[\n      *predecessor_evidence,',source)
        self.assertIn('prior_state_ref_or_hash=prior_ref',source)

    def test_rtc007_rejects_predecessor_without_organization_receipt(self):
        binding={
          "schema":"stegverse.sdk.publisher-return-binding/v1",
          "communication_state":"READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION",
          "authority_effect":"NONE",
          "communication_complete":False,
          "sdk_return_binding_observed":True,
          "final_stegverse_transition_observed":False,
          "interlock_intr_egress_observed":False,
          "far_side_transition_observed":False,
          "manifest_receipt_id":"MR-"+"D"*64,
          "egress":{"final_stegverse_transition_surface":"LLM_ADAPTER","transport":"INTERLOCK_INTR","destination_profile":"MIR","far_side_transition_required":True},
          "binding_sha256":"sha256:"+"b"*64,
        }
        llm_pkg=types.ModuleType("llm_adapter")
        llm=types.ModuleType("llm_adapter.southbound_sdk_return")
        llm.prepare_sdk_return_for_intr=lambda binding_bytes,transition_id: {
          "schema":"stegverse.llm-adapter.southbound-final-transition/v1",
          "state":"FINAL_STEGVERSE_SIDE_TRANSITION_PREPARED",
          "transition_surface":"LLM_ADAPTER",
          "destination_profile":"MIR",
          "sdk_binding_sha256":consumer.sha(binding_bytes).split(":",1)[1],
          "final_stegverse_transition_surface_reached":True,
          "intr_handoff":{"schema":"stegverse.llm-adapter.southbound-intr-egress-handoff/v1"},
          "authority_effect":"NONE",
        }
        llm.admit_intr_egress=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("admission must not run before predecessor validation"))
        custody=types.ModuleType("canonical_state_transition_custody")
        custody.build_state_receipt=lambda **kwargs: kwargs
        custody.submit_state_receipt=lambda receipt: (_ for _ in ()).throw(AssertionError("submit must not run"))
        wrong={
          "transition_id":"SOME-OTHER-TRANSITION",
          "state":"RECORDED",
          "reconstruction_status":"PASS",
          "required_evidence_validation_status":"PASS",
          "receipt_sha256":"a"*64,
          "reconstructed_receipt_sha256":"a"*64,
        }
        custody.require_predecessor_master_records_organization_record=lambda receipt_sha256, *, successor_transition_id: (
          "sha256:"+receipt_sha256,
          [{
            "evidence_id":"predecessor-master-records-organization-record:"+successor_transition_id,
            "evidence_type":"PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD",
            "origin_transition_id":successor_transition_id,
            "encoding":"canonical-json",
            "sha256":consumer.sha(wrong).split(":",1)[1],
            "content":wrong,
          }],
        )
        previous={name:sys.modules.get(name) for name in (
          "llm_adapter","llm_adapter.southbound_sdk_return","canonical_state_transition_custody"
        )}
        sys.modules["llm_adapter"]=llm_pkg
        sys.modules["llm_adapter.southbound_sdk_return"]=llm
        sys.modules["canonical_state_transition_custody"]=custody
        original_source_root=consumer.source_root
        consumer.source_root=lambda env_name,repo_name,required: Path("/tmp")
        try:
            with tempfile.TemporaryDirectory() as temp:
                runtime=Path(temp)
                output=runtime/consumer.SDK_BINDING_DIR/"sdk-return.json"
                output.parent.mkdir(parents=True)
                output.write_text(json.dumps(binding,sort_keys=True,separators=(",",":")),encoding="utf-8")
                req=request(consumer.SDK_DOWNSTREAM_OWNER)
                # A reconstruction PASS without an Organization receipt does not
                # make the predecessor real; the successor is refused before submit.
                with self.assertRaisesRegex(consumer.KVOrganizationReceiptRefused,
                                            "predecessor Organization record refused:FAIL_CLOSED:ORGANIZATION_RECEIPT_SHA256_ABSENT"):
                    consumer._prepare_rtc007_continuation(
                      runtime,req["materialization_id"],req,output,consumer.sha(binding),
                      {
                        "state":"RECORDED",
                        "reconstruction_status":"PASS",
                        "required_evidence_validation_status":"PASS",
                        "receipt_sha256":"a"*64,
                        "reconstructed_receipt_sha256":"a"*64,
                      },
                    )
        finally:
            consumer.source_root=original_source_root
            for name,value in previous.items():
                if value is None: sys.modules.pop(name,None)
                else: sys.modules[name]=value

    def test_rtc007_continuation_fails_closed_without_recorded_organization_record(self):
        source=open(consumer.__file__,encoding="utf-8").read()
        self.assertIn('"RTC-STEGVERSE-EGRESS-007"',source)
        self.assertIn('"RTC_STEGVERSE_EGRESS_007_TRANSITION"',source)
        self.assertIn('organization_receipt_sha256=_organization_receipt_gate(\n        mr,transition_id="RTC-STEGVERSE-EGRESS-007"',source)
        self.assertIn("custody.verified_organization_record(",source)
        self.assertNotIn('mr.get("reconstruction_status")=="PASS"',source)
        self.assertIn('rtc008=_submit_rtc008_materialization(rtc008_request,runtime_root=runtime)',source)
        self.assertIn('"rtc008_admission_observed":True',source)
        self.assertIn('"rtc009_far_side_transition_observed":False',source)


    def test_rtc006_rejects_transport_terminal_hash_as_predecessor(self):
        fake=types.ModuleType("canonical_state_transition_custody")
        fake.build_state_receipt=lambda **kwargs: kwargs
        fake.submit_state_receipt=lambda receipt: (_ for _ in ()).throw(AssertionError("submit must not run without canonical predecessor"))
        fake.require_predecessor_master_records_organization_record=lambda receipt_sha256, *, successor_transition_id: (None,[])
        previous=sys.modules.get("canonical_state_transition_custody")
        sys.modules["canonical_state_transition_custody"]=fake
        try:
            with tempfile.TemporaryDirectory() as temp:
                runtime=Path(temp)
                output=runtime/consumer.SDK_BINDING_DIR/"sdk-return.json"
                output.parent.mkdir(parents=True)
                binding={"schema":"stegverse.sdk.publisher-return-binding/v1","sdk_return_binding_observed":True}
                output.write_text(json.dumps(binding,sort_keys=True,separators=(",",":")),encoding="utf-8")
                materialization={
                  "schema":"stegverse.sdk.publisher-return-materialization-receipt/v1",
                  "output_sha256":consumer.sha(binding),
                  "sdk_return_binding_observed":True,
                }
                req=request(consumer.SDK_DOWNSTREAM_OWNER)
                with self.assertRaisesRegex(consumer.KVPublisherReturnError,"canonical predecessor Master Records organization record required"):
                    consumer._record_sdk_return_binding_custody(
                        runtime,req["materialization_id"],req,"sha256:"+"7"*64,output,materialization
                    )
        finally:
            if previous is None:
                sys.modules.pop("canonical_state_transition_custody",None)
            else:
                sys.modules["canonical_state_transition_custody"]=previous

if __name__=="__main__": unittest.main()
