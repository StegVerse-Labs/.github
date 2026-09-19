from __future__ import annotations
import json, sys, tempfile, types, unittest
from pathlib import Path

from scripts import consume_kv_publisher_return_materialization_request as consumer
from workers import universal_intr_profiled_ingress as ingress


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

    def test_sdk_return_binding_requires_canonical_master_records_before_egress(self):
        captured={}
        fake=types.ModuleType("canonical_state_transition_custody")
        def build_state_receipt(**kwargs):
            captured.update(kwargs)
            return {"schema":"stegverse.canonical-state-transition-receipt/v1","transition_id":kwargs["transition_id"]}
        def submit_state_receipt(receipt):
            captured["submitted"]=receipt
            return {
              "state":"RECORDED",
              "reconstruction_status":"PASS",
              "required_evidence_validation_status":"PASS",
              "receipt_sha256":"a"*64,
              "reconstructed_receipt_sha256":"a"*64,
              "required_evidence_count":2,
            }
        fake.build_state_receipt=build_state_receipt
        fake.submit_state_receipt=submit_state_receipt
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
                result=consumer._record_sdk_return_binding_custody(
                    runtime,req["materialization_id"],req,"sha256:"+"9"*64,output,materialization
                )
            self.assertEqual(captured["transition_id"],"RTC-SDK-RETURN-006")
            self.assertEqual(captured["resulting_state_ref_or_hash"],consumer.sha(binding))
            self.assertEqual(len(captured["required_evidence_manifest"]),2)
            self.assertEqual(captured["required_evidence_manifest"][0]["content"],binding)
            self.assertEqual(captured["required_evidence_manifest"][0]["evidence_type"],"SDK_PUBLISHER_RETURN_BINDING")
            self.assertEqual(result["state"],"RECORDED")
            self.assertEqual(result["required_evidence_validation_status"],"PASS")
        finally:
            if previous is None:
                sys.modules.pop("canonical_state_transition_custody",None)
            else:
                sys.modules["canonical_state_transition_custody"]=previous

    def test_sdk_return_binding_blocks_when_master_records_does_not_close(self):
        fake=types.ModuleType("canonical_state_transition_custody")
        fake.build_state_receipt=lambda **kwargs: {"schema":"stegverse.canonical-state-transition-receipt/v1"}
        fake.submit_state_receipt=lambda receipt: {"state":"BOUNDARY","reason":"not recorded"}
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
                with self.assertRaisesRegex(consumer.KVPublisherReturnError,"Master Records custody not closed"):
                    consumer._record_sdk_return_binding_custody(
                        runtime,req["materialization_id"],req,"sha256:"+"9"*64,output,materialization
                    )
        finally:
            if previous is None:
                sys.modules.pop("canonical_state_transition_custody",None)
            else:
                sys.modules["canonical_state_transition_custody"]=previous

if __name__=="__main__": unittest.main()
