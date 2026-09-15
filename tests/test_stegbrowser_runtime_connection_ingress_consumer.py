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

    def test_a3_a4_reuses_existing_manifest_ingress_worker(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            runtime = Path(td) / "runtime"
            worker = source / module.MANIFEST_INGRESS_REL
            worker.parent.mkdir(parents=True)
            worker.write_text("# worker\n")
            runtime.mkdir()
            completed = type("Completed", (), {
                "returncode": 0,
                "stdout": json.dumps({
                    "state": "AUTHENTIC_INTR_INGRESS_OBSERVED",
                    "claim_id": "SHWP-ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001-G23",
                    "fencing_token": 23,
                    "workercoordinator_claim_fence_observed": True,
                    "manifest_defined_path": True,
                }) + "\n",
                "stderr": "",
            })()
            with patch.object(module.subprocess, "run", return_value=completed) as run:
                result = module.run_existing_manifest_ingress(source, runtime)
            self.assertEqual(result["state"], "AUTHENTIC_INTR_INGRESS_OBSERVED")
            self.assertEqual(result["fencing_token"], 23)
            cmd = run.call_args.args[0]
            self.assertEqual(Path(cmd[1]), worker)
            self.assertIn("--source-root", cmd)
            self.assertIn("--runtime-root", cmd)


if __name__ == "__main__":
    unittest.main()
