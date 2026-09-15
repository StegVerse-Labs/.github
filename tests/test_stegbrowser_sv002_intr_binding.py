from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


consumer = load("stegbrowser_intr_consumer", "scripts/consume_stegbrowser_intr_materialization_request.py")
ingress = load("stegbrowser_intr_ingress", "workers/stegbrowser_intr_ingress.py")
installer = load("stegbrowser_intr_installer", "scripts/install_stegbrowser_universal_intr_route.py")


def request() -> dict:
    body = {
        "schema": consumer.REQUEST_SCHEMA,
        "materialization_id": "INTR-MAT-" + "a" * 24,
        "state": consumer.REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": consumer.GOAL_TASK_ID + ":" + consumer.NONCE,
        "packet_id": "INTR-" + "2" * 24,
        "payload_hash": "sha256:" + "3" * 64,
        "payload_ref": "/tmp/stegbrowser-manifest.json",
        "destination": dict(consumer.DESTINATION),
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
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
    }
    body["request_hash"] = consumer.sha_uri(body)
    return body


def trigger(req: dict) -> dict:
    entry = {
        "schema": "stegos.node_intr_outbox_entry.v1",
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": "SV-NODE-test",
        "interlock_id": "SV-IL-test",
        "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"],
        "transport_intent_hash": req["transport_intent_hash"],
        "payload_hash": req["payload_hash"],
        "destination": req["destination"],
        "downstream_owner_ref": req["downstream_owner_ref"],
        "materialization_request": req,
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
    entry["outbox_entry_hash"] = ingress.transport_boundary.digest_uri(entry)
    value = {
        "schema": ingress.transport_boundary.NODE_TRIGGER_SCHEMA,
        "transport_origin": ingress.transport_boundary.ORIGIN_NODE,
        "node_id": entry["node_id"],
        "interlock_id": entry["interlock_id"],
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    value["trigger_sha256"] = ingress.transport_boundary.digest_uri(value)
    return value


class StegBrowserSV002InTrBindingTests(unittest.TestCase):
    def test_request_contract_is_non_authorizing_and_nonce_bound(self):
        value = request()
        consumer.validate_request(value)
        self.assertEqual(value["destination"], consumer.DESTINATION)
        self.assertEqual(value["downstream_owner_ref"], consumer.GOAL_TASK_ID)
        self.assertIn(consumer.NONCE, value["operation_id"])
        self.assertFalse(value["request_grants_execution_authority"])
        self.assertFalse(value["claim_or_fence_minted"])

    def test_ingress_admits_node_trigger_and_dispatches_without_authority(self):
        req = request()
        payload = trigger(req)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        headers = {
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": ingress.transport_boundary.ORIGIN_NODE,
            "X-StegVerse-Payload-SHA256": ingress.transport_boundary.hashlib.sha256(raw).hexdigest(),
            "Content-Type": "application/json",
        }
        with tempfile.TemporaryDirectory() as td, patch.object(ingress.subprocess, "Popen") as popen:
            popen.return_value.pid = 101
            receipt = ingress.admit(runtime_root=Path(td), body=raw, headers=headers)
            self.assertEqual(receipt["schema"], consumer.INGRESS_SCHEMA)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["node_id"], "SV-NODE-test")
            self.assertEqual(receipt["interlock_id"], "SV-IL-test")
            self.assertFalse(receipt["claim_or_fence_minted"])
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertTrue(receipt["dispatch"]["consumer_dispatch_attempted"])
            popen.assert_called_once()

    def test_consumer_requires_ingress_and_dispatches_existing_manifest_runner(self):
        req = request()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            source = Path(td) / "source"
            (source / "scripts").mkdir(parents=True)
            (source / consumer.TARGET_ENTRYPOINT).write_text("# fixture\n", encoding="utf-8")
            req_path = runtime / consumer.REQUEST_DIR_REL / f"{req['materialization_id']}.json"
            req_path.parent.mkdir(parents=True)
            req_path.write_text(json.dumps(req), encoding="utf-8")
            ir = {
                "schema": consumer.INGRESS_SCHEMA,
                "state": "INGRESS_ADMITTED",
                "materialization_id": req["materialization_id"],
                "request_hash": req["request_hash"],
                "transport_intent_hash": req["transport_intent_hash"],
                "payload_hash": req["payload_hash"],
                "operation_id": req["operation_id"],
                "packet_id": req["packet_id"],
                "node_id": "SV-NODE-test",
                "interlock_id": "SV-IL-test",
                "claim_or_fence_minted": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
            }
            ir_path = runtime / consumer.INGRESS_DIR_REL / f"{req['materialization_id']}.json"
            ir_path.parent.mkdir(parents=True)
            ir_path.write_text(json.dumps(ir), encoding="utf-8")

            calls = []
            def fake_runner(command, **kwargs):
                calls.append((command, kwargs))
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            result = consumer.consume_one(source, runtime, req["materialization_id"], runner=fake_runner, env={"STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON": "{}"})
            self.assertEqual(result["state"], "MATERIALIZATION_EXECUTION_ATTEMPTED")
            self.assertEqual(Path(calls[0][0][1]).name, "run_stegbrowser_manifest_bound_runtime.py")
            self.assertEqual(calls[0][1]["env"]["STEGVERSE_STEGBROWSER_INTR_ADMITTED"], "1")
            self.assertFalse(result["consumer_claim_or_fence_minted"])

    def test_shared_router_install_is_idempotent_and_reuses_listener(self):
        source = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
        once = installer.transform(source)
        twice = installer.transform(once)
        self.assertEqual(once, twice)
        self.assertIn('"StegBrowser:ManifestExecution"', once)
        self.assertIn("is_stegbrowser(payload)", once)
        self.assertIn("admit_stegbrowser", once)
        self.assertEqual(once.count("class Server(ThreadingHTTPServer)"), source.count("class Server(ThreadingHTTPServer)"))

    def test_manifest_runner_has_pre_and_post_admission_modes(self):
        text = (ROOT / "scripts/run_stegbrowser_manifest_bound_runtime.py").read_text(encoding="utf-8")
        self.assertIn("STEGVERSE_STEGBROWSER_INTR_ADMITTED", text)
        self.assertIn("build_transport_intent", text)
        self.assertIn("build_materialization_request", text)
        self.assertIn("stegos.node_intr_outbox_entry.v1", text)
        self.assertIn("ingress.admit", text)
        self.assertNotIn("control-plane source-package", text)


if __name__ == "__main__":
    unittest.main()
