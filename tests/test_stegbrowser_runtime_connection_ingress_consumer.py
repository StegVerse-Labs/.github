from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "consume_stegbrowser_runtime_connection_ingress_request.py"
spec = importlib.util.spec_from_file_location("stegbrowser_a1_consumer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def node_receipt():
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
    return {**body, "receipt_sha256": hashlib.sha256(canonical(body)).hexdigest()}


class StegBrowserRuntimeConnectionIngressConsumerTests(unittest.TestCase):
    def test_request_contract_remains_non_authorizing_and_single_device(self):
        request = json.loads((ROOT / module.REQUEST_REL).read_text())
        module.validate_request(request)
        self.assertEqual(request["task_id"], module.TASK_ID)
        self.assertFalse(request["round_trip_1_payload_processing_allowed"])
        self.assertFalse(request["second_machine_required"])
        self.assertEqual(request["github_token_runtime_authority"], "NONE")

    def test_materialization_build_uses_existing_node_interlock_and_one_shot_nonce(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            runtime.mkdir()
            receipt_path = Path(td) / "receipt.json"
            receipt = node_receipt()
            receipt_path.write_text(json.dumps(receipt))
            request, trigger = module.build_materialization(ROOT, runtime, receipt_path, receipt)
            self.assertEqual(request["destination"]["subsystem"], "StegBrowser:ManifestIngress")
            self.assertEqual(request["node_id"], receipt["node_id"])
            self.assertEqual(request["interlock_id"], receipt["interlock_id"])
            self.assertEqual(request["registration_receipt_sha256"], receipt["receipt_sha256"])
            self.assertFalse(request["request_grants_execution_authority"])
            self.assertFalse(request["second_user_device_required"])
            self.assertEqual(trigger["schema"], "stegos.node_intr_materialization_trigger.v1")
            self.assertEqual(trigger["node_id"], receipt["node_id"])
            self.assertFalse(trigger["request_grants_execution_authority"])
            payload_path = runtime / "intr-payloads/stegbrowser-manifest" / f"{request['materialization_id']}.json"
            self.assertTrue(payload_path.is_file())

    def test_node_receipt_resolution_requires_existing_receipt_one(self):
        request = json.loads((ROOT / module.REQUEST_REL).read_text())
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "receipt.json"
            receipt = node_receipt()
            path.write_text(json.dumps(receipt))
            with patch.dict(module.os.environ, {module.NODE_PATH_ENV: str(path)}, clear=False):
                resolved, loaded = module.resolve_registered_node_receipt(request)
            self.assertEqual(resolved, path.resolve())
            self.assertEqual(loaded["receipt_number"], 1)
            self.assertEqual(loaded["node_id"], receipt["node_id"])

    def test_source_no_longer_uses_profile_polling_as_a1_gate(self):
        source = SCRIPT.read_text()
        self.assertNotIn("observe_live_profile", source)
        self.assertNotIn("/intr/profile", source)
        self.assertIn("stegos.node_intr_materialization_trigger.v1", source)
        self.assertIn("module.INGRESS_PATH", source)
        self.assertIn("VALIDATED_SV002_NODE_BOUND_WRITE_ONCE_UNIVERSAL_INTR_MATERIALIZATION_PATTERN", source)

    def test_post_uses_existing_shared_server_implementation(self):
        class FakeServer:
            def __init__(self, *_args):
                self.server_address = ("127.0.0.1", 12345)
            def handle_request(self):
                return None
            def server_close(self):
                return None
        fake_module = type("Shared", (), {"Server": FakeServer, "INGRESS_PATH": "/intr/materialization"})
        fake_response = type("Resp", (), {
            "status": 202,
            "read": lambda self: json.dumps({
                "schema": "stegverse.stegbrowser-intr-materialization-ingress/v1",
                "state": "INGRESS_ADMITTED",
            }).encode(),
            "__enter__": lambda self: self,
            "__exit__": lambda self, *_a: False,
        })()
        trigger = {"schema": "stegos.node_intr_materialization_trigger.v1"}
        with patch.object(module.urllib.request, "urlopen", return_value=fake_response):
            receipt = module.post_trigger(fake_module, Path("."), trigger)
        self.assertEqual(receipt["state"], "INGRESS_ADMITTED")


if __name__ == "__main__":
    unittest.main()
