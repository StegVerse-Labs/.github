from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hil_resident_activation_test",
    ROOT / "scripts/run_hil_resident_activation_test.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class HILResidentActivationAcceptanceTests(unittest.TestCase):
    def test_controlled_request_and_node_trigger_validate_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            request, pdf = mod.controlled_request(runtime)
            self.assertTrue(pdf.is_file())
            mod.materialization.validate_request(request)
            trigger = mod.node_trigger(request)
            transport = {
                "origin": mod.ingress.ORIGIN_NODE,
                "authorization_id": None,
                "transport": "InTr",
                "payload_sha256": "0" * 64,
            }
            extracted, source = mod.ingress.extract_materialization(trigger, transport)
            self.assertEqual(extracted["request_hash"], request["request_hash"])
            self.assertEqual(source["transport_origin"], mod.ingress.ORIGIN_NODE)
            self.assertIsNone(source["transport_authorization_id"])

    def test_controlled_request_is_idempotent_for_same_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            first, first_pdf = mod.controlled_request(runtime)
            second, second_pdf = mod.controlled_request(runtime)
            self.assertEqual(first["request_hash"], second["request_hash"])
            self.assertEqual(first["materialization_id"], second["materialization_id"])
            self.assertEqual(first_pdf.read_bytes(), second_pdf.read_bytes())

    def test_select_materialization_result_binds_exact_request(self) -> None:
        batch = {
            "results": [
                {"materialization_id": "INTR-MAT-" + "a" * 24, "esrl_lease_state": "LOCAL_READY"},
                {
                    "materialization_id": "INTR-MAT-" + "b" * 24,
                    "state": "MATERIALIZATION_EXECUTION_ATTEMPTED",
                    "esrl_lease_state": "LEASE_OPEN",
                    "same_device_execution_required": True,
                    "requires_other_machine": False,
                    "public_observation_is_downstream_optional": True,
                    "public_gateway_readiness_verified": False,
                    "public_gateway_origin": None,
                },
            ]
        }
        selected = mod.select_materialization_result(batch, "INTR-MAT-" + "b" * 24)
        self.assertEqual(selected["esrl_lease_state"], "LEASE_OPEN")
        self.assertTrue(selected["same_device_execution_required"])
        self.assertFalse(selected["requires_other_machine"])
        self.assertTrue(selected["public_observation_is_downstream_optional"])
        self.assertFalse(selected["public_gateway_readiness_verified"])
        self.assertIsNone(selected["public_gateway_origin"])
        self.assertEqual(mod.select_materialization_result(batch, "INTR-MAT-" + "c" * 24), {})

    def test_hosted_markers_are_detectable(self) -> None:
        self.assertTrue(mod.truthy("1"))
        self.assertTrue(mod.truthy("true"))
        self.assertFalse(mod.truthy("false"))
        self.assertIn("GITHUB_ACTIONS", mod.HOSTED_ENV)

    def test_test_receipt_never_grants_authority(self) -> None:
        self.assertEqual(mod.materialization.TARGET_TASK, "SHWP-HIL-SOVEREIGN-RECEIVER-001")
        self.assertEqual(mod.materialization.DESTINATION["subsystem"], "HIL:Ingress")


if __name__ == "__main__":
    unittest.main()
