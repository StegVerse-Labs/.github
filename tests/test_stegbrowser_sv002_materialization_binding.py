from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


consumer = load_module("stegbrowser_materialization_consumer", "workers/stegbrowser_intr_materialization_consumer.py")
adapter = load_module("stegbrowser_materialization_ingress", "workers/stegbrowser_intr_materialization_ingress.py")
installer = load_module("stegbrowser_route_installer", "scripts/install_stegbrowser_universal_intr_route.py")


class StegBrowserSV002MaterializationBindingTests(unittest.TestCase):
    def request(self, receipt: Path) -> dict:
        body = {
            "schema": consumer.REQUEST_SCHEMA,
            "state": consumer.REQUEST_STATE,
            "materialization_id": "INTR-MAT-" + "a" * 24,
            "operation_id": "STEG-BROWSER-MANIFEST-A0-A4-001",
            "packet_id": "STEG-BROWSER-PACKET-001",
            "payload_ref": "runtime://stegbrowser/manifest-invocation.json",
            "payload_hash": "sha256:" + "1" * 64,
            "transport_schema": "stegverse.universal-intr-transport/v1",
            "transport_protocol": "InTr",
            "transport_intent_hash": "sha256:" + "2" * 64,
            "destination": dict(consumer.DESTINATION),
            "boundary_path": list(consumer.BOUNDARY_PATH),
            "downstream_owner_ref": consumer.DOWNSTREAM_OWNER,
            "event_triggered": True,
            "always_on_receiver_required": False,
            "second_user_device_required": False,
            "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
            "exact_packet_transport_retry_allowed": True,
            "blind_consequence_retry_allowed": False,
            "interlock_required": True,
            "request_grants_execution_authority": False,
            "claim_or_fence_minted": False,
            "transport_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_transfer": False,
            "authority_effect": "NONE_REQUEST_ONLY",
            "goal_task_id": consumer.GOAL,
            "cosv_task_vector": consumer.COSV,
            "manifest_ref": consumer.MANIFEST_REF,
            "node_genesis_receipt_ref": str(receipt),
        }
        body["request_hash"] = consumer.sha_uri(body)
        return body

    def trigger(self, request: dict) -> dict:
        boundary = load_module("hil_materialization_boundary", "scripts/serve_hil_intr_materialization_ingress.py")
        entry = {
            "schema": boundary.NODE_OUTBOX_SCHEMA,
            "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
            "node_id": "SV-NODE-TEST-001",
            "interlock_id": "SV-IL-TEST-001",
            "materialization_id": request["materialization_id"],
            "request_hash": request["request_hash"],
            "transport_intent_hash": request["transport_intent_hash"],
            "payload_hash": request["payload_hash"],
            "destination": request["destination"],
            "downstream_owner_ref": request["downstream_owner_ref"],
            "materialization_request": request,
            "network_delivery_observed": False,
            "runtime_materialization_observed": False,
            "receiver_receipt_observed": False,
            "tvc_receipt_observed": False,
            "request_grants_execution_authority": False,
            "claim_or_fence_minted": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
        }
        entry["outbox_entry_hash"] = boundary._sha256_uri(entry)
        trigger = {
            "schema": boundary.NODE_TRIGGER_SCHEMA,
            "transport_origin": boundary.ORIGIN_NODE,
            "node_id": entry["node_id"],
            "interlock_id": entry["interlock_id"],
            "outbox_entry_hash": entry["outbox_entry_hash"],
            "node_outbox_entry": entry,
            "request_grants_execution_authority": False,
            "claim_or_fence_minted": False,
            "authority_effect": "NONE_TRIGGER_ONLY",
        }
        trigger["trigger_sha256"] = boundary._sha256_uri(trigger)
        return trigger

    def test_request_contract_matches_sv002_authority_boundaries(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = Path(td) / "node.json"; receipt.write_text("{}\n")
            request = self.request(receipt)
            consumer.validate_request(request)
            self.assertFalse(request["request_grants_execution_authority"])
            self.assertFalse(request["claim_or_fence_minted"])
            self.assertFalse(request["second_user_device_required"])
            self.assertEqual(request["receiver_unavailable_disposition"], "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION")

    def test_adapter_accepts_only_node_bound_trigger_and_dispatches_non_authorizing_consumer(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); receipt = runtime / "node.json"; receipt.write_text("{}\n")
            request = self.request(receipt); trigger = self.trigger(request); raw = json.dumps(trigger, sort_keys=True, separators=(",", ":")).encode()
            boundary = load_module("hil_materialization_boundary_headers", "scripts/serve_hil_intr_materialization_ingress.py")
            headers = {"Content-Type":"application/json","X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":boundary.ORIGIN_NODE,"X-StegVerse-Payload-SHA256":__import__("hashlib").sha256(raw).hexdigest()}
            class Proc: pid = 123
            with patch.object(adapter.subprocess, "Popen", return_value=Proc()):
                result = adapter.admit(runtime_root=runtime, body=raw, headers=headers)
            self.assertEqual(result["state"], "INGRESS_ADMITTED")
            self.assertEqual(result["node_id"], "SV-NODE-TEST-001")
            self.assertEqual(result["interlock_id"], "SV-IL-TEST-001")
            self.assertFalse(result["claim_or_fence_minted"])
            self.assertFalse(result["ingress_grants_execution_authority"])
            self.assertFalse(result["second_listener_created"])
            self.assertFalse(result["second_scheduler_created"])

    def test_consumer_invokes_existing_manifest_runner_and_stops_before_round_trip_1(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); receipt = runtime / "node.json"; receipt.write_text("{}\n")
            request = self.request(receipt); mid=request["materialization_id"]
            q=runtime/"intr-materialization"; q.mkdir(); (q/f"{mid}.json").write_text(json.dumps(request))
            ingress_dir=runtime/"receipts/sovereign-network/stegbrowser-intr-ingress"; ingress_dir.mkdir(parents=True)
            ingress={"schema":consumer.INGRESS_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":mid,"request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],"payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],"node_id":"SV-NODE-TEST-001","interlock_id":"SV-IL-TEST-001","claim_or_fence_minted":False,"credential_authority":"TV/TVC"}
            (ingress_dir/f"{mid}.json").write_text(json.dumps(ingress))
            boundary=runtime/"receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"; boundary.parent.mkdir(parents=True); boundary.write_text(json.dumps({"workercoordinator_claim_fence_observed":True,"organization_local_intr_ingress_receipt_verified":True,"authentic_intr_ingress_observed":True,"claim_ref":"CLAIM-G1","fence_ref":1}))
            class Done: returncode=0; stdout=""; stderr=""
            calls=[]
            def runner(cmd, **kwargs): calls.append(cmd); return Done()
            result=consumer.consume_one(ROOT,runtime,mid,runner=runner,env={"PATH":"/usr/bin"})
            self.assertEqual(calls[0][1], str(ROOT/consumer.RUNNER))
            self.assertTrue(result["workercoordinator_claim_fence_observed"])
            self.assertTrue(result["authentic_intr_ingress_observed"])
            self.assertFalse(result["round_trip_1_started"])
            self.assertFalse(result["second_listener_created"])
            self.assertFalse(result["second_scheduler_created"])
            self.assertFalse(result["second_runtime_architecture_created"])

    def test_route_installer_extends_existing_shared_listener_only(self):
        source=(ROOT/"workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
        transformed=installer.transform(source)
        self.assertIn('"StegBrowser:ManifestIngress"', transformed)
        self.assertIn("is_stegbrowser(payload)", transformed)
        self.assertEqual(transformed.count("ThreadingHTTPServer"), source.count("ThreadingHTTPServer"))
        self.assertEqual(installer.transform(transformed), transformed)
        installer_source=(ROOT/"scripts/install_stegbrowser_universal_intr_route.py").read_text(encoding="utf-8")
        self.assertNotIn("ThreadingHTTPServer(", installer_source)


if __name__ == "__main__": unittest.main()
