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
        ):
            self.assertIn(f'"{state}"', source)
        self.assertIn('"request_dispatch_grants_authority": False', source)
        self.assertIn('"github_token_runtime_authority": "NONE"', source)


if __name__ == "__main__":
    unittest.main()
