from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import universal_intr_profiled_ingress as ingress
from scripts import consume_publisher_intr_materialization_request as consumer


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def sha_uri(value):
    raw=value if isinstance(value,bytes) else canonical(value).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()


def packet():
    exact=b'{"schema":"stegverse.publisher.artifact-transfer/v1","test":"exact"}'
    intent={
      "schema":"stegverse.universal-intr-transport/v1","protocol":"InTr",
      "operation_id":"publisher-transfer-test-001","packet_id":"INTR-"+"1"*24,
      "payload_hash":sha_uri(exact),"prior_transport_receipt_hash":None,
      "source":{"boundary":"KV","subsystem":"KnowledgeVault:DocumentExport"},
      "destination":{"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"},
      "boundary_path":["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"],"interlock_required":True,
      "transport_semantics":{"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,
        "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False},
      "authority":{"authority_transfer":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC"},
      "receipt_chain":{"required":True,"receipt_schema":"stegverse.intr.hop_receipt/v1","payload_plaintext_in_receipts":False,"prior_hash_required_after_first_hop":True}
    }
    req_body={
      "schema":"stegverse.universal-intr-materialization-request/v1","materialization_id":"INTR-MAT-"+"2"*24,
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION","transport_schema":"stegverse.universal-intr-transport/v1",
      "transport_protocol":"InTr","transport_intent_hash":sha_uri(intent),"operation_id":intent["operation_id"],
      "packet_id":intent["packet_id"],"payload_hash":intent["payload_hash"],
      "payload_ref":"runtime://intr-payload/publisher/INTR-MAT-"+"2"*24+".bin",
      "destination":intent["destination"],"boundary_path":intent["boundary_path"],
      "downstream_owner_ref":"GCAT-BCAT-Engine/Publisher","event_triggered":True,
      "always_on_receiver_required":False,"second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,
      "interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,
      "transport_grants_execution_authority":False,"credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY"
    }
    request={**req_body,"request_hash":sha_uri(req_body)}
    trigger_body={
      "schema":"stegos.node_publisher_intr_trigger.v1","transport_origin":"STEGOS_NODE_OUTBOX",
      "node_id":"SV-NODE-"+"3"*24,"interlock_id":"SV-IL-"+"4"*24,
      "materialization_request":request,"transport_intent":intent,
      "exact_payload_base64":base64.b64encode(exact).decode(),
      "request_grants_execution_authority":False,"claim_or_fence_minted":False,
      "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE_TRIGGER_ONLY"
    }
    trigger={**trigger_body,"trigger_sha256":sha_uri(trigger_body)}
    raw=canonical(trigger).encode()
    headers={"X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":"STEGOS_NODE_OUTBOX",
      "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest(),"Content-Type":"application/json"}
    return exact,intent,request,trigger,raw,headers


class PublisherInTrMaterializationTests(unittest.TestCase):
    def test_ingress_persists_exact_payload_before_dispatch(self):
        exact,_intent,request,_trigger,raw,headers=packet()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with mock.patch.object(ingress,"_dispatch_publisher_consumer",return_value={"consumer_dispatch_attempted":True,"authority_effect":"NONE_DISPATCH_ONLY"}) as dispatch:
                receipt=ingress.admit_publisher(runtime_root=root,body=raw,headers=headers)
            mid=request["materialization_id"]
            self.assertEqual((root/"intr-payload/publisher"/f"{mid}.bin").read_bytes(),exact)
            self.assertTrue(receipt["exact_payload_materialized"])
            self.assertEqual(receipt["payload_hash"],sha_uri(exact))
            dispatch.assert_called_once()

    def test_exact_retry_does_not_repeat_completed_consequence(self):
        _exact,_intent,request,_trigger,raw,headers=packet()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with mock.patch.object(ingress,"_dispatch_publisher_consumer",return_value={"consumer_dispatch_attempted":True}):
                ingress.admit_publisher(runtime_root=root,body=raw,headers=headers)
            mid=request["materialization_id"]
            ret=root/"intr-return/publisher"/f"{mid}.json"; ret.parent.mkdir(parents=True)
            ret.write_text("{}")
            with mock.patch.object(ingress,"_dispatch_publisher_consumer") as dispatch:
                receipt=ingress.admit_publisher(runtime_root=root,body=raw,headers=headers)
            self.assertFalse(receipt["dispatch"]["consumer_dispatch_attempted"])
            self.assertEqual(receipt["dispatch"]["consumer_result"]["state"],"ALREADY_STAGED")
            dispatch.assert_not_called()

    def test_payload_tamper_fails_before_persistence(self):
        _exact,_intent,_request,trigger,_raw,headers=packet()
        trigger["exact_payload_base64"]=base64.b64encode(b"tampered").decode()
        body=dict(trigger); body.pop("trigger_sha256",None); trigger["trigger_sha256"]=sha_uri(body)
        raw=canonical(trigger).encode(); headers=dict(headers); headers["X-StegVerse-Payload-SHA256"]=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ingress.admit_publisher(runtime_root=Path(td),body=raw,headers=headers)

    def test_consumer_reuses_already_staged_result(self):
        _exact,_intent,request,_trigger,_raw,_headers=packet(); mid=request["materialization_id"]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            reqdir=root/"intr-materialization"; reqdir.mkdir(parents=True); (reqdir/f"{mid}.json").write_text(json.dumps(request))
            ingdir=root/"receipts/sovereign-network/publisher-intr-ingress"; ingdir.mkdir(parents=True)
            (ingdir/f"{mid}.json").write_text(json.dumps({"state":"INGRESS_ADMITTED","exact_payload_materialized":True}))
            taskdir=root/"receipts/publisher-artifact-transfer"; taskdir.mkdir(parents=True)
            (taskdir/f"{consumer.TASK_ID}.json").write_text(json.dumps({"state":"RETURN_STAGED_TO_DEVICE","materialization_id":mid,"return_meta_ref":"intr-return/publisher/x.json"}))
            with mock.patch("subprocess.run") as run:
                result=consumer.consume(root,root,mid)
            self.assertEqual(result["state"],"ALREADY_STAGED")
            self.assertFalse(result["runtime_execution_attempted"])
            run.assert_not_called()

    def test_runtime_materialization_lists_include_publisher_consumer(self):
        root=Path(__file__).resolve().parents[1]
        for path in ("scripts/install_sovereign_heartbeat_service.py","scripts/bootstrap_sovereign_runtime.py","scripts/refresh_sovereign_worker_runtime_source.py"):
            self.assertIn("consume_publisher_intr_materialization_request.py",(root/path).read_text())
        bridge=(root/"scripts/refresh_and_execute_resident_task.py").read_text()
        self.assertIn('"STEGVERSE_PUBLISHER_ROOT"',bridge)
        self.assertIn('"STEGVERSE_PUBLISHER_INTR_MATERIALIZATION_ID"',bridge)

if __name__=="__main__":
    unittest.main()
