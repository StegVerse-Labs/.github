from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json"
RUNNER = ROOT / "scripts/run_global_runtime_evidence_convergence.py"
BOOTSTRAP = ROOT / "scripts/install_and_run_canonical_work_event_bootstrap.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("global_runtime_evidence_convergence", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GlobalRuntimeEvidenceConvergenceExecutionTests(unittest.TestCase):
    def test_every_current_member_has_one_execution_routing_class(self):
        projection = json.loads(PROJECTION.read_text(encoding="utf-8"))
        module = load_runner()
        members = {row["task_id"] for row in projection["members"]}
        selector_tasks = set(module.TASK_SELECTORS) & members
        direct_tasks = set(module.DIRECT_CONSUMERS) & members
        canonical_work_tasks = set(module.CANONICAL_WORK_ONLY) & members
        unwired_tasks = set(module.NO_EXECUTION_PATH_REASON) & members
        self.assertEqual(18, len(members))
        self.assertEqual(members, selector_tasks | direct_tasks | canonical_work_tasks | unwired_tasks)
        classes = [selector_tasks, direct_tasks, canonical_work_tasks, unwired_tasks]
        for index, left in enumerate(classes):
            for right in classes[index + 1:]:
                self.assertFalse(left & right)

    def test_latent_existing_paths_are_reused(self):
        module = load_runner()
        self.assertEqual(("stegos_kv_intr_chain",), module.TASK_SELECTORS["SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001"])
        self.assertEqual(
            Path("control/resident-execution-request.d/consume-gadi-resident-execution.py"),
            module.DIRECT_CONSUMERS["GADI-RESIDENT-EXECUTION-001"],
        )
        self.assertNotIn("GADI-RESIDENT-EXECUTION-001", module.NO_EXECUTION_PATH_REASON)
        self.assertNotIn("SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001", module.NO_EXECUTION_PATH_REASON)

    def test_vacc_projection_uses_current_sovereign_task(self):
        projection = json.loads(PROJECTION.read_text(encoding="utf-8"))
        vacc = next(row for row in projection["members"] if row["lane"] == "VACC")
        self.assertEqual("VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023", vacc["task_id"])
        self.assertEqual("SOVEREIGN_VACC_REQUEST_EXECUTION", vacc["resume_stage"])

    def test_global_visitor_reuses_existing_dispatcher_and_does_not_recurse(self):
        module = load_runner()
        selected = {value for values in module.TASK_SELECTORS.values() for value in values}
        self.assertNotIn("canonical_work_coordination", selected)
        self.assertEqual(Path("scripts/dispatch_resident_execution_requests.py"), module.DISPATCHER_REL)
        self.assertIn("runtime_profile_map", selected)
        self.assertIn("hil", selected)
        self.assertIn("ecosystem_chat", selected)
        self.assertIn("stegos_kv_intr_chain", selected)
        self.assertIn("glm53_sovereign_lane", selected)

    def test_runtime_profile_map_bootstrap_triggers_global_visitor(self):
        text = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('RUNTIME_PROFILE_MAP_TASK_ID = "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"', text)
        self.assertIn("run_global_convergence_if_applicable(args.task_id)", text)
        self.assertIn("run_global_runtime_evidence_convergence.py", text)
        self.assertNotIn("systemd", text.lower())


if __name__ == "__main__":
    unittest.main()
