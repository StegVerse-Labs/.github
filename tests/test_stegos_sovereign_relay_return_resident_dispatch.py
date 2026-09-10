from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = ROOT / "scripts" / "dispatch_resident_execution_requests.py"
REFRESH_PATH = ROOT / "scripts" / "refresh_sovereign_worker_runtime_source.py"
CONSUMER_PATH = ROOT / "workers" / "stegos_sovereign_relay_return_path_request_consumer.py"
REQUEST_PATH = ROOT / "control" / "resident-execution-request.d" / "stegos-sovereign-relay-return-path-001.json"
HANDOFF_PATH = ROOT / "handoffs" / "SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001.json"
TASK_ID = "SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001"
SELECTOR = "stegos_sovereign_relay_return_path"
CONSUMER_REL = "workers/stegos_sovereign_relay_return_path_request_consumer.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RelayReturnResidentDispatchTests(unittest.TestCase):
    def test_request_is_exact_non_authorizing_targeted_task_control(self):
        request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(request["schema"], "stegverse.resident-execution-request/v1")
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["mode"], "TARGETED_INDEPENDENT_TASK_CONTROL")
        self.assertEqual(request["entrypoint"], "scripts/refresh_and_execute_resident_task.py")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertFalse(request["github_token_required"])
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["protected_material_allowed_in_request"])
        self.assertEqual(request["authority_effect"], "NONE_REQUEST_ONLY")

    def test_dispatcher_points_to_worker_tree_consumer(self):
        dispatcher = load_module(DISPATCHER_PATH, "relay_return_dispatcher_contract")
        by_name = dict(dispatcher.CONSUMERS)
        self.assertEqual(by_name[SELECTOR], CONSUMER_REL)
        self.assertTrue(CONSUMER_PATH.is_file())
        selected = dispatcher.select_consumers((SELECTOR,))
        self.assertEqual(selected, ((SELECTOR, CONSUMER_REL),))

    def test_normal_source_refresh_materializes_consumer_and_request(self):
        refresh = load_module(REFRESH_PATH, "relay_return_refresh_contract")
        self.assertIn(Path("workers"), refresh.STATIC_DIRS)
        self.assertIn(Path("control/resident-execution-request.d"), refresh.CONTROL_DIRS)
        self.assertTrue(CONSUMER_PATH.is_relative_to(ROOT / "workers"))
        self.assertTrue(REQUEST_PATH.is_relative_to(ROOT / "control" / "resident-execution-request.d"))

    def test_handoff_no_longer_requires_manual_artifact_locators(self):
        handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
        execution = handoff["execution"]
        self.assertEqual(execution["required_local_env"], [])
        self.assertEqual(
            execution["artifact_resolution"],
            "EXACT_LOCAL_SCHEMA_LINEAGE_HASH_AUTODISCOVERY_WITH_OPTIONAL_REVALIDATED_OVERRIDES",
        )
        for name in (
            "STEGVERSE_RELAY_EGRESS_BINDING",
            "STEGVERSE_RELAY_EGRESS_AUTHORIZATION",
            "STEGVERSE_RELAY_EGRESS_PAYLOAD",
        ):
            self.assertIn(name, execution["optional_local_env"])

    def test_dispatcher_forwards_optional_local_artifact_overrides_without_authority(self):
        dispatcher = load_module(DISPATCHER_PATH, "relay_return_dispatcher_env_contract")
        env = dispatcher.clean_exec_env({
            "PATH": "/bin",
            "HOME": "/tmp",
            "STEGVERSE_RELAY_EGRESS_BINDING": "/state/binding.json",
            "STEGVERSE_RELAY_EGRESS_AUTHORIZATION": "/state/authorization.json",
            "STEGVERSE_RELAY_EGRESS_PAYLOAD": "/state/payload.bin",
        })
        self.assertEqual(env["STEGVERSE_RELAY_EGRESS_BINDING"], "/state/binding.json")
        self.assertEqual(env["STEGVERSE_RELAY_EGRESS_AUTHORIZATION"], "/state/authorization.json")
        self.assertEqual(env["STEGVERSE_RELAY_EGRESS_PAYLOAD"], "/state/payload.bin")
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")

    def test_consumer_invokes_only_exact_existing_task_bridge(self):
        consumer = load_module(CONSUMER_PATH, "relay_return_request_consumer_contract")
        request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        consumer.validate_request(request)
        self.assertEqual(consumer.TARGET_TASK, TASK_ID)
        self.assertEqual(consumer.TARGET_ENTRYPOINT, "scripts/refresh_and_execute_resident_task.py")
        source = CONSUMER_PATH.read_text(encoding="utf-8")
        self.assertIn('"--task-id", TARGET_TASK', source)
        self.assertNotIn("git fetch", source)
        self.assertNotIn("git pull", source)
        self.assertNotIn("git clone", source)


if __name__ == "__main__":
    unittest.main()
