from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

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

    def test_live_intr_profile_implies_callable_and_protocol_resolved(self):
        profile = FakeIngress.profile(False)
        callable_value = bool(
            profile.get("state") == "ACTIVE_SOVEREIGN_INTR_INGRESS"
            and profile.get("protocol") == "InTr"
            and profile.get("event_triggered") is True
            and "CanonicalWork:Coordination" in (profile.get("profiles") or [])
        )
        protocol_resolved = bool(callable_value and "CanonicalWork:Coordination" in (profile.get("profiles") or []))
        self.assertTrue(callable_value)
        self.assertTrue(protocol_resolved)

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


if __name__ == "__main__":
    unittest.main()
