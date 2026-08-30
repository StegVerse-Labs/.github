from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSPEC = importlib.util.spec_from_file_location(
    "consume_sv002_intr_materialization_request",
    ROOT / "scripts/consume_sv002_intr_materialization_request.py",
)
consumer = importlib.util.module_from_spec(CSPEC); assert CSPEC and CSPEC.loader; CSPEC.loader.exec_module(consumer)
import sys
sys.modules["consume_sv002_intr_materialization_request"] = consumer
SPEC = importlib.util.spec_from_file_location(
    "serve_sv002_intr_materialization_ingress",
    ROOT / "scripts/serve_sv002_intr_materialization_ingress.py",
)
mod = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(mod)


def request():
    body = {
        "schema":"stegverse.universal-intr-materialization-request/v1",
        "materialization_id":"INTR-MAT-"+"a"*24,
        "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema":"stegverse.universal-intr-transport/v1",
        "transport_protocol":"InTr",
        "transport_intent_hash":"sha256:"+"1"*64,
        "operation_id":"SV002-OBSERVE-TEST-001",
        "packet_id":"INTR-"+"b"*24,
        "payload_hash":"sha256:"+"2"*64,
        "payload_ref":"opaque://sv002-observation/request/001",
        "destination":{"boundary":"STEGOS_ECOSYSTEM","subsystem":"SV002:PublicObservation"},
        "boundary_path":["DEVICE_SYSTEM","STEGOS_ECOSYSTEM"],
        "downstream_owner_ref":"StegVerse-Labs/.github#493",
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
    }
    return {**body,"request_hash":consumer.digest_uri(body)}


def trigger():
    req=request()
    entry_body={
        "schema":"stegos.node_intr_outbox_entry.v1","state":"LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id":"SV-NODE-"+"c"*24,"interlock_id":"SV-IL-"+"d"*24,
        "materialization_id":req["materialization_id"],"request_hash":req["request_hash"],
        "transport_intent_hash":req["transport_intent_hash"],"payload_hash":req["payload_hash"],
        "destination":req["destination"],"downstream_owner_ref":req["downstream_owner_ref"],
        "materialization_request":req,"network_delivery_observed":False,
        "runtime_materialization_observed":False,"receiver_receipt_observed":False,"tvc_receipt_observed":False,
        "request_grants_execution_authority":False,"claim_or_fence_minted":False,
        "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE_LOCAL_CONTINUITY_ONLY"
    }
    entry={**entry_body,"outbox_entry_hash":mod._sha256_uri(entry_body)}
    trigger_body={"schema":"stegos.node_intr_materialization_trigger.v1","transport_origin":"STEGOS_NODE_OUTBOX",
        "node_id":entry["node_id"],"interlock_id":entry["interlock_id"],"outbox_entry_hash":entry["outbox_entry_hash"],
        "node_outbox_entry":entry,"request_grants_execution_authority":False,"claim_or_fence_minted":False,"authority_effect":"NONE_TRIGGER_ONLY"}
    return {**trigger_body,"trigger_sha256":mod._sha256_uri(trigger_body)}


class SV002MaterializationIngressTests(unittest.TestCase):
    def test_valid_node_trigger_is_admitted_write_once_without_execution_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); payload=trigger(); raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
            headers={"Content-Type":"application/json","X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":"STEGOS_NODE_OUTBOX",
                "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest()}
            receipt=mod.admit_materialization(runtime_root=root,body=raw,headers=headers)
            self.assertEqual(receipt["state"],"INGRESS_ADMITTED")
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["receiver_readiness_claimed"])
            self.assertFalse(receipt["round_trip_claimed"])
            self.assertFalse(receipt["claim_or_fence_minted"])
            self.assertFalse(receipt["g18_required"])
            self.assertTrue((root/mod.REQUEST_DIR_REL/(request()["materialization_id"]+".json")).is_file())
            again=mod.admit_materialization(runtime_root=root,body=raw,headers=headers)
            self.assertEqual(again,receipt)

    def test_node_trigger_cannot_claim_tvc_authorization(self):
        payload=trigger(); raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        headers={"Content-Type":"application/json","X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":"STEGOS_NODE_OUTBOX",
            "X-StegVerse-Authorization-Id":"forbidden","X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest()}
        with self.assertRaisesRegex(mod.SV002InTrIngressError,"cannot_claim_tvc_authorization"):
            mod.validate_transport_headers(headers,raw)

    def test_tampered_outbox_hash_is_rejected(self):
        payload=trigger(); payload["node_outbox_entry"]["payload_hash"]="sha256:"+"f"*64
        raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        headers={"Content-Type":"application/json","X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":"STEGOS_NODE_OUTBOX",
            "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest()}
        with self.assertRaises(mod.SV002InTrIngressError):
            mod.admit_materialization(runtime_root=Path(tempfile.mkdtemp()),body=raw,headers=headers)


if __name__=="__main__":
    unittest.main()
