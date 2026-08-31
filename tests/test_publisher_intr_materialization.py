from __future__ import annotations
import base64, hashlib, json, tempfile, unittest
from pathlib import Path
from unittest import mock

from scripts import consume_publisher_intr_materialization_request as consumer
from workers import universal_intr_profiled_ingress as ingress

def canon(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v):
    raw=v if isinstance(v,bytes) else canon(v)
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def request(payload: bytes):
    body={
      "schema":"stegverse.universal-intr-materialization-request/v1",
      "materialization_id":"INTR-MAT-"+"b"*24,
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
      "transport_schema":"stegverse.universal-intr-transport/v1",
      "transport_protocol":"InTr",
      "transport_intent_hash":"sha256:"+"1"*64,
      "operation_id":"publisher-transfer-001",
      "packet_id":"INTR-"+"2"*24,
      "payload_hash":sha(payload),
      "payload_ref":"runtime://intr-payloads/publisher-artifact-transfer/INTR-MAT-"+"b"*24+".bin",
      "destination":{"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"},
      "boundary_path":["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"],
      "downstream_owner_ref":"GCAT-BCAT-Engine/Publisher",
      "event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,
      "interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,
      "transport_grants_execution_authority":False,"credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY"
    }
    body["request_hash"]=sha(body)
    return body

class PublisherInTrMaterializationTests(unittest.TestCase):
    def test_ingress_persists_exact_sidecars_before_dispatch(self):
        payload=b'{"authority_effect":"NONE","schema":"stegverse.publisher.artifact-transfer/v1"}'
        req=request(payload)
        trigger={"schema":ingress.PUBLISHER_TRIGGER_SCHEMA,"materialization_request":req,
                 "payload_base64":base64.b64encode(payload).decode(),
                 "forward_receipts":[{"receipt_hash":"sha256:"+"3"*64}],
                 "request_grants_execution_authority":False,"claim_or_fence_minted":False,
                 "authority_effect":"NONE_TRIGGER_ONLY"}
        body=json.dumps(trigger,sort_keys=True).encode()
        headers={"X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":ingress.hil.ORIGIN_NODE,
                 "X-StegVerse-Payload-SHA256":hashlib.sha256(body).hexdigest(),"Content-Type":"application/json"}
        with tempfile.TemporaryDirectory() as td, mock.patch.object(ingress,"_dispatch_publisher_consumer",return_value={"consumer_dispatch_attempted":True}):
            root=Path(td)
            receipt=ingress.admit_publisher(runtime_root=root,body=body,headers=headers)
            mid=req["materialization_id"]
            self.assertEqual((root/ingress.PUBLISHER_PAYLOAD_DIR/f"{mid}.bin").read_bytes(),payload)
            saved=json.loads((root/ingress.PUBLISHER_PAYLOAD_DIR/f"{mid}.forward-receipts.json").read_text())
            self.assertEqual(saved,trigger["forward_receipts"])
            self.assertTrue(receipt["exact_payload_sidecar_persisted"])
            self.assertTrue(receipt["forward_receipt_chain_sidecar_persisted"])
            self.assertFalse(receipt["claim_or_fence_minted"])

    def test_consumer_fails_closed_without_forward_receipts(self):
        payload=b"{}"; req=request(payload); mid=req["materialization_id"]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/consumer.REQUEST_DIR).mkdir(parents=True)
            (root/consumer.REQUEST_DIR/f"{mid}.json").write_text(json.dumps(req))
            ing=root/consumer.INGRESS_DIR; ing.mkdir(parents=True)
            receipt={"schema":"stegverse.publisher-intr-materialization-ingress/v1","state":"INGRESS_ADMITTED",
                     "materialization_id":mid,"request_hash":req["request_hash"],"transport_intent_hash":req["transport_intent_hash"],
                     "payload_hash":req["payload_hash"],"operation_id":req["operation_id"],"packet_id":req["packet_id"]}
            (ing/f"{mid}.json").write_text(json.dumps(receipt))
            p=root/consumer.PAYLOAD_DIR; p.mkdir(parents=True); (p/f"{mid}.bin").write_bytes(payload)
            with self.assertRaisesRegex(consumer.PublisherInTrConsumerError,"forward_receipt_chain_missing"):
                consumer.consume(root,mid)

    def test_request_is_non_authorizing(self):
        req=request(b"{}")
        consumer.validate_request(req)
        self.assertFalse(req["request_grants_execution_authority"])
        self.assertFalse(req["transport_grants_execution_authority"])
        self.assertEqual(req["credential_authority"],"TV/TVC")

    def test_payload_ref_must_bind_runtime_exact_sidecar(self):
        req=request(b"{}")
        req["payload_ref"]="runtime://wrong/path.bin"
        body=dict(req); body.pop("request_hash",None); req["request_hash"]=sha(body)
        with self.assertRaisesRegex(consumer.PublisherInTrConsumerError,"payload_ref_mismatch"):
            consumer.validate_request(req)

    def test_exact_retry_redispatches_only_until_return_packet_exists(self):
        payload=b'{"authority_effect":"NONE","schema":"stegverse.publisher.artifact-transfer/v1"}'
        req=request(payload)
        trigger={"schema":ingress.PUBLISHER_TRIGGER_SCHEMA,"materialization_request":req,
                 "payload_base64":base64.b64encode(payload).decode(),
                 "forward_receipts":[{"receipt_hash":"sha256:"+"3"*64}],
                 "request_grants_execution_authority":False,"claim_or_fence_minted":False,
                 "authority_effect":"NONE_TRIGGER_ONLY"}
        body=json.dumps(trigger,sort_keys=True).encode()
        headers={"X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":ingress.hil.ORIGIN_NODE,
                 "X-StegVerse-Payload-SHA256":hashlib.sha256(body).hexdigest(),"Content-Type":"application/json"}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); mid=req["materialization_id"]
            with mock.patch.object(ingress,"_dispatch_publisher_consumer",return_value={"consumer_dispatch_attempted":True}) as dispatch:
                ingress.admit_publisher(runtime_root=root,body=body,headers=headers)
                ingress.admit_publisher(runtime_root=root,body=body,headers=headers)
                self.assertEqual(dispatch.call_count,2)
            result_dir=root/"receipts/sovereign-host/publisher-artifact-transfer"; result_dir.mkdir(parents=True)
            (result_dir/f"{mid}.json").write_text(json.dumps({"state":"RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED","materialization_id":mid,"request_hash":req["request_hash"]}))
            with mock.patch.object(ingress,"_dispatch_publisher_consumer") as dispatch:
                result=ingress.admit_publisher(runtime_root=root,body=body,headers=headers)
                dispatch.assert_not_called()
                self.assertEqual(result["dispatch"]["consumer_result_state"],"ALREADY_RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED")

    def test_render_success_queues_reverse_materialization_source(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/consume_publisher_intr_materialization_request.py").read_text()
        self.assertIn("build_materialization_request(response.intent",source)
        self.assertIn("build_carrier_binding(",source)
        self.assertIn('return_request["carrier_binding"]=carrier_binding',source)
        self.assertIn('return_request["request_hash"]=sha(return_request_body)',source)
        self.assertIn('"return_carrier_binding_sha256":carrier_binding["binding_sha256"]',source)
        self.assertIn('"return_carrier_grants_authority":False',source)
        self.assertIn("RETURN_MATERIALIZATION_QUEUED_NOT_TRANSPORTED",source)
        self.assertIn("StegVerse-Labs/continuity-vault-kit",source)

if __name__=="__main__":
    unittest.main()
