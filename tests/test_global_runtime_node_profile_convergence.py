from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "control/runtime-node-profiles.json"
WRAPPER = ROOT / "scripts/run_global_runtime_node_profile_convergence.py"
BOOTSTRAP = ROOT / "scripts/install_and_run_canonical_work_event_bootstrap.py"
STEGBROWSER_OBSERVABILITY = ROOT / "control/runtime-observability-consumers/stegbrowser-ephemeral-runtime-binding-001.json"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("global_runtime_node_profile_convergence", WRAPPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GlobalRuntimeNodeProfileConvergenceTests(unittest.TestCase):
    def test_all_18_runtime_lanes_have_one_hb32_retained_node_profile(self):
        data = json.loads(PROFILES.read_text(encoding="utf-8"))
        self.assertEqual("stegverse.runtime-node-profiles/v1", data["schema"])
        self.assertEqual("GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001", data["goal_task_id"])
        self.assertEqual("HB32", data["profile_policy"]["hb_protocol"])
        self.assertEqual("RETAINED_STEGOS_NODE", data["profile_policy"]["node_state_class"])
        self.assertEqual("EPHEMERAL_OR_BOUNDED_RUNTIME_LEASE", data["profile_policy"]["execution_session_class"])
        self.assertTrue(data["profile_policy"]["node_identity_survives_session_teardown"])
        self.assertFalse(data["profile_policy"]["session_credentials_survive_teardown"])
        self.assertFalse(data["profile_policy"]["session_cookies_survive_teardown"])
        self.assertTrue(data["profile_policy"]["hb_is_observability_only"])
        self.assertFalse(data["profile_policy"]["hb_grants_execution_authority"])
        self.assertEqual(18, len(data["profiles"]))
        self.assertEqual(18, len({row["task_id"] for row in data["profiles"]}))
        self.assertEqual(18, len({row["profile_id"] for row in data["profiles"]}))

    def test_stegbrowser_is_the_retained_node_lifecycle_reference(self):
        data = json.loads(PROFILES.read_text(encoding="utf-8"))
        row = next(item for item in data["profiles"] if item["task_id"] == "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001")
        self.assertEqual("STEGBROWSER_RESIDENT", row["node_origin"])
        self.assertEqual("stegbrowser.resident-node-state/v1", row["node_state_schema"])
        self.assertIn("node_ref", row["retained_state"])
        self.assertIn("state_commitment", row["retained_state"])
        self.assertIn("cookies", row["ephemeral_state"])
        self.assertIn("credential_material", row["ephemeral_state"])
        obs = json.loads(STEGBROWSER_OBSERVABILITY.read_text(encoding="utf-8"))
        self.assertEqual("HB32", obs["hb_profile"]["protocol"])
        self.assertEqual("STEGBROWSER_RESIDENT", obs["hb_profile"]["node_state_origin"])
        self.assertTrue(obs["predicate_map"]["retained_node_source_implemented"]["observed"])
        self.assertFalse(obs["predicate_map"]["resident_process_alive_supervised"]["observed"])

    def test_previously_unwired_lanes_now_have_profile_bound_resolution_classes(self):
        data = json.loads(PROFILES.read_text(encoding="utf-8"))
        by_task = {row["task_id"]: row for row in data["profiles"]}
        self.assertEqual("EXTERNAL_RUNTIME_PROFILE_BRIDGE", by_task["VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023"]["execution_binding"]["type"])
        self.assertEqual("OBSERVABILITY_BOUND_EXTERNAL_RUNTIME", by_task["DATA-CONTINUATION-STEGCLAW-P4"]["execution_binding"]["type"])
        self.assertEqual("EXACT_PARENT_REBIND_PROFILE", by_task["DECISION-ENVELOPE-DE006"]["execution_binding"]["type"])

    def test_wrapper_replaces_unwired_class_without_inventing_runtime_success(self):
        module = load_wrapper()
        profile_data = json.loads(PROFILES.read_text(encoding="utf-8"))
        outcomes = []
        for row in profile_data["profiles"]:
            state = "NO_REGISTERED_SELECTOR" if row["task_id"] in {
                "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023",
                "DATA-CONTINUATION-STEGCLAW-P4",
                "DECISION-ENVELOPE-DE006",
            } else "WAITING_FOR_REQUEST"
            path = "UNWIRED_CHILD_RUNTIME" if state == "NO_REGISTERED_SELECTOR" else "REGISTERED_RESIDENT_SELECTOR"
            outcomes.append({"lane": row["lane"], "task_id": row["task_id"], "state": state, "execution_path": path, "resume_stage": row["resume_stage"]})

        def fake_base(_source: Path, _runtime: Path):
            return {"schema": "stegverse.global-runtime-evidence-convergence/v1", "state": "CONVERGENCE_VISIT_COMPLETE", "lane_outcomes": outcomes}

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            (runtime / "control/runtime-observability-consumers").mkdir(parents=True)
            source_de006 = ROOT / "control/runtime-observability-consumers/decision-envelope-de006.json"
            (runtime / "control/runtime-observability-consumers/decision-envelope-de006.json").write_bytes(source_de006.read_bytes())
            result = module.execute(ROOT, runtime, base_executor=fake_base)
            self.assertEqual(18, result["member_count"])
            self.assertEqual(0, result["unwired_member_count"])
            self.assertFalse(any(row["execution_path"] == "UNWIRED_CHILD_RUNTIME" for row in result["lane_outcomes"]))
            by_task = {row["task_id"]: row for row in result["lane_outcomes"]}
            self.assertEqual("PROFILE_BOUND_EXTERNAL_RUNTIME_NOT_MATERIALIZED", by_task["VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023"]["state"])
            self.assertEqual("PROFILE_BOUND_RESIDENT_MATERIALIZATION_PENDING", by_task["DATA-CONTINUATION-STEGCLAW-P4"]["state"])
            self.assertEqual("PROFILE_BOUND_PARENT_REBIND_REQUIRED", by_task["DECISION-ENVELOPE-DE006"]["state"])

    def test_runtime_profile_map_bootstrap_uses_profiled_wrapper_and_materializes_profile_registry(self):
        text = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('GLOBAL_HELPER_REL = Path("scripts/run_global_runtime_node_profile_convergence.py")', text)
        self.assertIn('GLOBAL_BASE_HELPER_REL = Path("scripts/run_global_runtime_evidence_convergence.py")', text)
        self.assertIn('GLOBAL_NODE_PROFILES_REL = Path("control/runtime-node-profiles.json")', text)
        self.assertIn("materialize_exact(source_root, GLOBAL_NODE_PROFILES_REL)", text)
        self.assertNotIn("systemd", text.lower())


if __name__ == "__main__":
    unittest.main()
