from __future__ import annotations

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


class FakeIngress:
    @staticmethod
    def profile(_tls: bool):
        return {
            "schema": "stegverse.universal-intr-profiled-ingress/v1",
            "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
            "protocol": "InTr",
            "profiles": ["CanonicalWork:Coordination"],
            "event_triggered": True,
            "always_on_application_receiver_required": False,
            "second_user_device_required": False,
            "execution_authority": "NONE",
            "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
        }


class StegBrowserRuntimeConnectionIngressConsumerTests(unittest.TestCase):
    def test_request_contract_is_non_authorizing_and_child_scoped(self):
        request = json.loads((ROOT / module.REQUEST_REL).read_text())
        module.validate_request(request)
        self.assertEqual(request["task_id"], module.TASK_ID)
        self.assertFalse(request["round_trip_1_payload_processing_allowed"])
        self.assertFalse(request["second_machine_required"])
        self.assertEqual(request["github_token_runtime_authority"], "NONE")

    def test_live_intr_profile_implies_callable(self):
        profile = FakeIngress.profile(False)
        callable_value = bool(
            profile.get("state") == "ACTIVE_SOVEREIGN_INTR_INGRESS"
            and profile.get("protocol") == "InTr"
            and profile.get("event_triggered") is True
            and "CanonicalWork:Coordination" in (profile.get("profiles") or [])
        )
        self.assertTrue(callable_value)

    def test_exact_manifest_protocol_resolution_requires_existing_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td)
            worker = source / module.MANIFEST_INGRESS_REL
            worker.parent.mkdir(parents=True)
            worker.write_text("# exact local adapter\n")
            self.assertTrue(module.exact_manifest_protocol_resolved(source, FakeIngress.profile(False)))
            worker.unlink()
            self.assertFalse(module.exact_manifest_protocol_resolved(source, FakeIngress.profile(False)))

    def test_refreshable_is_invocation_bound_not_persistent_source_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            definition = source / "source-bundles/reusable-task-registry.d/RT-SOVEREIGN-SOURCE-REFRESH-001.json"
            definition.parent.mkdir(parents=True)
            definition.write_text("{}\n")
            runtime.mkdir()
            self.assertTrue(module.refreshable_for_invocation(source, runtime, FakeIngress.profile(False)))
            self.assertFalse(module.refreshable_for_invocation(source, source, FakeIngress.profile(False)))

    def test_a1_resolution_selects_existing_tasks_only(self):
        resolver = module.resolve_module()
        observation = {
            "schema": module.OBS_SCHEMA,
            "task_id": module.TASK_ID,
            "parent_task_id": module.PARENT_TASK_ID,
            "cosv": module.COSV,
            "manifest_ref": module.MANIFEST_REF,
            "authority_owner": "Interlock/InTr",
            "authority_effect": "OBSERVATION_ONLY",
            "callable": True,
            "refreshable": True,
            "applicable_protocol_resolved": True,
        }
        result = resolver.resolve(observation)
        self.assertEqual(result["selected_reusable_tasks"], [module.SOURCE_REFRESH_RT])
        self.assertFalse(result["round_trip_1_payload_processing_allowed_by_this_resolution"])
        self.assertFalse(result["second_user_operated_device_required"])

    def test_a2_a4_delegate_to_existing_manifest_bound_reusable_runner(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            stegos = root / "StegOS"
            runner = source / module.MANIFEST_RUNNER_REL
            validator = stegos / "stegos/network_manifold.py"
            node_receipt = root / "node-genesis-receipt.json"
            runner.parent.mkdir(parents=True)
            validator.parent.mkdir(parents=True)
            runtime.mkdir(parents=True)
            runner.write_text("# canonical manifest-bound runner\n")
            validator.write_text("# canonical node validator\n")
            node_receipt.write_text("{}\n")
            completed = type("Completed", (), {
                "returncode": 0,
                "stdout": "runner-ok\n",
                "stderr": "",
            })()
            with patch.dict(module.os.environ, {"STEGVERSE_STEGOS_SOURCE_ROOT": str(stegos)}, clear=False):
                with patch.object(module.subprocess, "run", return_value=completed) as run:
                    result = module.run_canonical_node_bound_invocation(source, runtime, node_receipt)
            self.assertEqual(result["runner_returncode"], 0)
            cmd = run.call_args.args[0]
            self.assertEqual(Path(cmd[1]), runner)
            env = run.call_args.kwargs["env"]
            params = json.loads(env["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"])
            self.assertEqual(params["node_genesis_receipt"], str(node_receipt))
            self.assertEqual(params["runtime_root"], str(runtime))
            self.assertEqual(params["stegos_source_root"], str(stegos))
            self.assertNotIn(str(source / module.MANIFEST_INGRESS_REL), cmd)

    def test_missing_registered_node_is_retained_as_not_observed_not_a1(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('except RuntimeError as exc:', source)
        self.assertIn('node_resolution_error = str(exc)', source)
        self.assertIn('A1_NOT_OBSERVED_REGISTERED_NODE_RECEIPT_UNAVAILABLE', source)
        self.assertIn('"registered_stegverse_node_bound_to_invocation": a1_observed', source)
        self.assertNotIn('"A1_OBSERVED_NOT_CALLABLE"', source)


if __name__ == "__main__":
    unittest.main()
