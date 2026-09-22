from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class StegBrowserResidentDispatchRegistrationTests(unittest.TestCase):
    def test_native_dispatcher_registers_a1_a4_consumer(self):
        dispatcher = load("resident_dispatch", "scripts/dispatch_resident_execution_requests.py")
        mapping = dict(dispatcher.CONSUMERS)
        self.assertEqual(
            mapping.get("stegbrowser_runtime_connection_ingress"),
            "scripts/consume_stegbrowser_runtime_connection_ingress_request.py",
        )
        selected = dispatcher.select_consumers(("stegbrowser_runtime_connection_ingress",))
        self.assertEqual(selected, (("stegbrowser_runtime_connection_ingress", "scripts/consume_stegbrowser_runtime_connection_ingress_request.py"),))

    def test_dispatcher_preserves_canonical_node_receipt_locator_without_credential_authority(self):
        dispatcher = load("resident_dispatch_node_locator", "scripts/dispatch_resident_execution_requests.py")
        env = dispatcher.clean_exec_env({
            "PATH": "/usr/bin",
            "STEGVERSE_NODE_GENESIS_RECEIPT": "/state/stegverse/node-receipt-1.json",
            "GITHUB_TOKEN": "must-not-propagate",
        })
        self.assertEqual(env["STEGVERSE_NODE_GENESIS_RECEIPT"], "/state/stegverse/node-receipt-1.json")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")

    def test_local_source_refresh_materializes_consumer_and_resolver(self):
        refresh = load("resident_refresh", "scripts/refresh_sovereign_worker_runtime_source.py")
        required = {
            Path("scripts/consume_stegbrowser_runtime_connection_ingress_request.py"),
            Path("scripts/resolve_stegbrowser_runtime_connection_transition.py"),
            Path("scripts/refresh_sovereign_worker_runtime_source_reusable.py"),
            Path("scripts/dispatch_resident_execution_requests.py"),
        }
        self.assertTrue(required.issubset(set(refresh.STATIC_FILES)))
        self.assertIn(Path("workers"), refresh.STATIC_DIRS)
        self.assertIn(Path("control/resident-execution-request.d"), refresh.CONTROL_DIRS)

    def test_dispatch_accepts_bounded_child_states_without_granting_authority(self):
        source = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
        for state in (
            "A1_A2_A3_A4_OBSERVED",
            "A1_A2_OBSERVED_A3_A4_PENDING",
            "A1_OBSERVED_NOT_MATERIALIZED",
            "A1_A2_A2_1_A2_2_A3_A4_OBSERVED",
            "A1_OBSERVED_CANONICAL_INVOCATION_PENDING_OR_BOUNDARY",
            "A1_NOT_OBSERVED_REGISTERED_NODE_RECEIPT_UNAVAILABLE",
            "A1_NOT_OBSERVED_CANONICAL_INVOCATION_NOT_RETAINED",
            "A1_NOT_OBSERVED_NOT_CALLABLE",
        ):
            self.assertIn(f'"{state}"', source)
        self.assertIn('"request_dispatch_grants_authority": False', source)
        self.assertIn('"github_token_runtime_authority": "NONE"', source)


if __name__ == "__main__":
    unittest.main()
