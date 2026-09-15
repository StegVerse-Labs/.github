from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


wrapper = load_module("stegbrowser_a1_wrapper", ROOT / "scripts/consume_stegbrowser_runtime_connection_ingress_request.py")
ingress = load_module("stegbrowser_mat_ingress", ROOT / "workers/stegbrowser_intr_materialization_ingress.py")
consumer = load_module("stegbrowser_mat_consumer", ROOT / "workers/stegbrowser_intr_materialization_consumer.py")
installer = load_module("stegbrowser_route_installer", ROOT / "scripts/install_stegbrowser_universal_intr_route.py")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def receipt_one(path: Path):
    body = {
        "schema": "stegos.node_handoff_receipt.v1",
        "receipt_number": 1,
        "transition": "NODE_REGISTERED",
        "prior_state": "UNREGISTERED",
        "resulting_state": "REGISTERED",
        "continuity_parent": "GENESIS",
        "node_id": "SV-NODE-0123456789abcdef01234567",
        "interlock_id": "SV-IL-0123456789abcdef01234567",
        "device_binding_sha256": "a" * 64,
        "authority_effect": "NONE",
        "heartbeat_authority": "StegVerse-Labs/.github",
        "credential_authority": "TV/TVC",
    }
    value = {**body, "receipt_sha256": hashlib.sha256(canonical(body)).hexdigest()}
    path.write_text(json.dumps(value))
    return value


class Completed:
    returncode = 0
    stdout = "ok\n"
    stderr = ""


class StegBrowserUniversalInTrMaterializationBindingTests(unittest.TestCase):
    def test_route_installer_reuses_existing_listener_and_is_idempotent(self):
        router = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text()
        transformed = installer.transform(router)
        self.assertIn("StegBrowser:ManifestIngress", transformed)
        self.assertIn("is_stegbrowser(payload)", transformed)
        self.assertIn("admit_stegbrowser", transformed)
        self.assertEqual(transformed.count("ThreadingHTTPServer"), router.count("ThreadingHTTPServer"))
        self.assertEqual(installer.transform(transformed), transformed)
        self.assertNotIn("WorkerCoordinator(", transformed)

    def test_node_trigger_unwrap_is_write_once_non_authorizing_contract(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            runtime.mkdir()
            rp = Path(td) / "receipt.json"
            node = receipt_one(rp)
            request, trigger = wrapper.build_materialization(ROOT, runtime, rp, node)
            extracted, source = ingress._request_from_payload(trigger, {
                "origin": ingress.transport_boundary.ORIGIN_NODE,
                "authorization_id": None,
                "payload_sha256": hashlib.sha256(canonical(trigger)).hexdigest(),
            })
            self.assertEqual(extracted["request_hash"], request["request_hash"])
            self.assertEqual(source["node_id"], node["node_id"])
            self.assertEqual(source["interlock_id"], node["interlock_id"])
            self.assertFalse(extracted["request_grants_execution_authority"])
            self.assertFalse(extracted["claim_or_fence_minted"])
            self.assertFalse(extracted["second_user_device_required"])

    def test_consumer_delegates_to_existing_manifest_runner_and_stops_before_round_trip_1(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            runtime.mkdir()
            rp = Path(td) / "receipt.json"
            node = receipt_one(rp)
            request, _trigger = wrapper.build_materialization(ROOT, runtime, rp, node)
            request_dir = runtime / "intr-materialization"
            request_dir.mkdir(parents=True)
            (request_dir / f"{request['materialization_id']}.json").write_text(json.dumps(request))
            ingress_dir = runtime / "receipts/sovereign-network/stegbrowser-intr-ingress"
            ingress_dir.mkdir(parents=True)
            ingress_receipt = {
                "schema": consumer.INGRESS_SCHEMA,
                "state": "INGRESS_ADMITTED",
                **{k: request[k] for k in (
                    "materialization_id", "request_hash", "transport_intent_hash", "payload_hash",
                    "operation_id", "packet_id", "node_id", "interlock_id",
                    "registration_receipt_sha256", "manifest_sha256",
                )},
                "claim_or_fence_minted": False,
                "credential_authority": "TV/TVC",
            }
            (ingress_dir / f"{request['materialization_id']}.json").write_text(json.dumps(ingress_receipt))

            def fake_runner(command, **kwargs):
                self.assertEqual(Path(command[1]).name, "run_stegbrowser_manifest_bound_runtime.py")
                params = json.loads(kwargs["env"]["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"])
                self.assertEqual(params["node_genesis_receipt"], str(rp.resolve()))
                boundary = runtime / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
                boundary.parent.mkdir(parents=True, exist_ok=True)
                boundary.write_text(json.dumps({
                    "runtime_ingress_projection": {
                        "workercoordinator_claim_fence_observed": True,
                        "organization_local_intr_ingress_receipt_verified": True,
                        "authentic_intr_ingress_observed": True,
                        "claim_ref": "CLAIM-G7",
                        "fence_ref": 7,
                        "lease_id": "LEASE-1",
                        "runtime_id": "RUNTIME-1",
                        "state_root_binding": "sha256:" + "b" * 64,
                    }
                }))
                return Completed()

            result = consumer.consume_one(ROOT, runtime, request["materialization_id"], runner=fake_runner, env={"PATH": "/usr/bin"})
            self.assertTrue(result["workercoordinator_claim_fence_observed"])
            self.assertTrue(result["organization_local_intr_ingress_receipt_verified"])
            self.assertTrue(result["authentic_intr_ingress_observed"])
            self.assertFalse(result["round_trip_1_started"])
            self.assertFalse(result["second_listener_created"])
            self.assertFalse(result["second_scheduler_created"])
            self.assertFalse(result["second_runtime_architecture_created"])
            self.assertFalse(result["second_user_device_required"])
            self.assertFalse(result["consumer_grants_execution_authority"])

    def test_adapter_and_consumer_define_no_server_or_scheduler_implementation(self):
        adapter_source = (ROOT / "workers/stegbrowser_intr_materialization_ingress.py").read_text()
        consumer_source = (ROOT / "workers/stegbrowser_intr_materialization_consumer.py").read_text()
        for text in (adapter_source, consumer_source):
            self.assertNotIn("ThreadingHTTPServer", text)
            self.assertNotIn("HTTPServer", text)
            self.assertNotIn("WorkerCoordinator(", text)
            self.assertNotIn("schedule.", text)
        self.assertIn("workers/universal_intr_profiled_ingress.py", (ROOT / "scripts/install_stegbrowser_universal_intr_route.py").read_text())


if __name__ == "__main__":
    unittest.main()
