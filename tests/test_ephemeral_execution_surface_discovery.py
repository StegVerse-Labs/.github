import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "list_stegverse_execution_surfaces.py"
SPEC = importlib.util.spec_from_file_location("surface_discovery", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class EphemeralExecutionSurfaceDiscoveryTests(unittest.TestCase):
    def test_connected_empty_does_not_block_runtime(self):
        result = MOD.discover("connected", [])
        self.assertEqual(result["connected_count"], 0)
        self.assertFalse(result["zero_connected_devices_is_runtime_blocker"])
        self.assertEqual(result["surfaces"], [])

    def test_ephemeral_exposes_node_and_stegbrowser(self):
        result = MOD.discover("ephemeral", [])
        self.assertEqual(result["connected_count"], 0)
        self.assertEqual(result["ephemeral_count"], 2)
        by_name = {x["surface"]: x for x in result["surfaces"]}
        self.assertEqual(set(by_name), {"StegVerseNode", "StegBrowser"})
        for surface in by_name.values():
            self.assertEqual(surface["class"], "ephemeral")
            self.assertEqual(surface["availability"], "AVAILABLE_TO_INVOKE")
            self.assertEqual(surface["instance_state"], "NOT_MATERIALIZED")
            self.assertEqual(surface["runtime_class"], "EVENT_EPHEMERAL")
            self.assertEqual(surface["materialization"], "ON_INVOCATION")
            self.assertFalse(surface["persistent_connection_required"])
            self.assertFalse(surface["second_user_operated_device_required"])
            self.assertEqual(surface["authority_effect"], "NONE_DISCOVERY_ONLY")

        node = by_name["StegVerseNode"]
        self.assertEqual(node["callable_task"], "STEGVERSE-002-EXPERIMENT-RERUN-001")
        self.assertEqual(node["execution_owner"], "StegVerse-002/.github")
        self.assertEqual(node["operation"], "REQUEST_SELF_CHARACTERIZATION")
        self.assertNotEqual(node["callable_task"], "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001")

        browser = by_name["StegBrowser"]
        self.assertEqual(browser["callable_task"], "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001")
        self.assertEqual(browser["execution_owner"], "StegVerse-Labs/.github")
        self.assertEqual(browser["operation"], "STEGBROWSER_MANIFEST_DEFINED_INTR_INGRESS")

    def test_all_preserves_connected_and_adds_ephemeral(self):
        connected = [{"device_id": "phone-1", "state": "CONNECTED"}]
        result = MOD.discover("all", connected)
        self.assertEqual(result["connected_count"], 1)
        self.assertEqual(result["ephemeral_count"], 2)
        self.assertEqual(len(result["surfaces"]), 3)
        self.assertEqual(result["surfaces"][0]["class"], "connected")

    def test_invalid_class_fails_closed(self):
        with self.assertRaises(ValueError):
            MOD.discover("standing", [])

    def test_connected_json_must_be_array(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "connected.json"
            path.write_text(json.dumps({"device_id": "bad"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                MOD._load_connected(str(path))


if __name__ == "__main__":
    unittest.main()
