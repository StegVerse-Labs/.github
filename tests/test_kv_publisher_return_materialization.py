from __future__ import annotations
import base64, hashlib, json, tempfile, unittest
from pathlib import Path
from unittest import mock

from scripts import consume_kv_publisher_return_materialization_request as consumer
from workers import universal_intr_profiled_ingress as ingress

def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v):
    raw=v if isinstance(v,bytes) else canonical(v)
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def request(payload:bytes,intent:dict):
    body={
      "schema":"stegverse.universal-intr-materialization-request/v1",
      "materialization_id":"INTR-MAT-"+"c"*24,
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
      "transport_schema":"stegverse.universal-intr-transport/v1",
      "transport_protocol":"InTr",
      "transport_intent_hash":sha(intent),
      "operation_id":intent["operation_id"],
      "packet_id":intent["packet_id"],
      "payload_hash":sha(payload),
      "payload_ref":"runtime://publisher-return.bin",
      "destination":{"boundary":"KV","subsystem":"KnowledgeVault:DocumentImport"},
      "boundary_path":["STEGOS_ECOSYSTEM","DEVICE_SYSTEM","KV"],
      "downstream_owner_ref":"StegVerse-Labs/continuity-vault-kit",
      "event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,
      "interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,
      "transport_grants_execution_authority":False,"credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY"
    }
    body["request_hash"]=sha(body)
    return body

def intent(payload:bytes):
    return {
      "schema":"stegverse.universal-intr-transport/v1","protocol":"InTr",
      "operation_id":"publisher-transfer-001:return","packet_id":"INTR-"+"d"*24,
      "payload_hash":sha(payload),"prior_transport_receipt_hash":"sha256:"+"e"*64,
      "source":{"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Export"},
      "destination":{"boundary":"KV","subsystem":"KnowledgeVault:DocumentImport"},
      "boundary_path":["STEGOS_ECOSYSTEM","DEVICE_SYSTEM","KV"],
      "interlock_required":True,
      "transport_semantics":{"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,"receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION","exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False},
      "authority":{"authority_transfer":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC"},
      "receipt_chain":{"required":True,"receipt_schema":"stegverse.intr.hop_receipt/v1","payload_plaintext_in_receipts":False,"prior_hash_required_after_first_hop":True}
    }

class KVPublisherReturnMaterializationTests(unittest.TestCase):
    def test_request_is_event_first_non_authorizing(self):
        payload=b'{"schema":"stegverse.publisher.artifact-return/v1"}'
        it=intent(payload); req=request(payload,it)
        consumer.validate_request(req)
        self.assertFalse(req["always_on_receiver_required"])
        self.assertFalse(req["request_grants_execution_authority"])

    def test_ingress_persists_return_sidecars_before_dispatch(self):
        payload=b'{"schema":"stegverse.publisher.artifact-return/v1"}'
        it=intent(payload); req=request(payload,it)
        trigger={"schema":ingress.KV_PUBLISHER_RETURN_TRIGGER_SCHEMA,"materialization_request":req,
                 "transport_intent":it,"payload_base64":base64.b64encode(payload).decode(),
                 "reverse_receipts":[{"receipt_hash":"sha256:"+"1"*64}],
                 "request_grants_execution_authority":False,"claim_or_fence_minted":False,
                 "authority_effect":"NONE_TRIGGER_ONLY"}
        body=json.dumps(trigger,sort_keys=True).encode()
        headers={"X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":ingress.hil.ORIGIN_NODE,
                 "X-StegVerse-Payload-SHA256":hashlib.sha256(body).hexdigest(),"Content-Type":"application/json"}
        with tempfile.TemporaryDirectory() as td, mock.patch.object(ingress,"_dispatch_kv_publisher_return",return_value={"consumer_dispatch_attempted":True}):
            root=Path(td); rec=ingress.admit_kv_publisher_return(runtime_root=root,body=body,headers=headers)
            mid=req["materialization_id"]; base=root/ingress.KV_PUBLISHER_RETURN_PAYLOAD_DIR
            self.assertEqual((base/f"{mid}.bin").read_bytes(),payload)
            self.assertEqual(json.loads((base/f"{mid}.intent.json").read_text()),it)
            self.assertTrue(rec["exact_return_sidecars_persisted"])
            self.assertFalse(rec["claim_or_fence_minted"])

    def test_consumer_requires_private_source_bundle(self):
        payload=b'{"schema":"stegverse.publisher.artifact-return/v1","source_export_id":"export-1"}'
        it=intent(payload); req=request(payload,it); mid=req["materialization_id"]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/consumer.REQUEST_DIR).mkdir(parents=True)
            (root/consumer.REQUEST_DIR/f"{mid}.json").write_text(json.dumps(req))
            p=root/consumer.INGRESS_DIR; p.mkdir(parents=True)
            (p/f"{mid}.json").write_text(json.dumps({"schema":"stegverse.kv-publisher-return-materialization-ingress/v1","state":"INGRESS_ADMITTED","materialization_id":mid,"request_hash":req["request_hash"],"transport_intent_hash":req["transport_intent_hash"],"payload_hash":req["payload_hash"],"operation_id":req["operation_id"],"packet_id":req["packet_id"]}))
            side=root/consumer.PAYLOAD_DIR; side.mkdir(parents=True)
            (side/f"{mid}.bin").write_bytes(payload); (side/f"{mid}.intent.json").write_text(json.dumps(it)); (side/f"{mid}.receipts.json").write_text(json.dumps([{},{}]))
            with self.assertRaises(consumer.KVPublisherReturnError):
                consumer.consume(root,mid)

if __name__=="__main__": unittest.main()
