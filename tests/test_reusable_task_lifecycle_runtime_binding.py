from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_lifecycle():
    path = ROOT / "workers/reusable_task_lifecycle.py"
    spec = importlib.util.spec_from_file_location("reusable_lifecycle_binding", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReusableTaskLifecycleRuntimeBindingTests(unittest.TestCase):
    def test_ece_identity_uses_existing_real_runner(self):
        registry = json.loads((ROOT / "data/reusable-task-registry.json").read_text(encoding="utf-8"))
        rows = [row for row in registry["tasks"] if row.get("reusable_task_id") == "RT-ECOSYSTEM-CONTINUITY-EVALUATION-001"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["runner_templates"], ["scripts/run_ecosystem_continuity_reusable_task.py"])
        self.assertIn("EXACT_EVALUATION_BYTES_CUSTODIED_AND_RECONSTRUCTED_BEFORE_DOWNSTREAM_PROJECTION", row["completion_predicates"])

    def test_ece_runner_writes_standard_result_only_after_complete_cycle(self):
        source = (ROOT / "scripts/run_ecosystem_continuity_reusable_task.py").read_text(encoding="utf-8")
        self.assertIn("STEGVERSE_REUSABLE_TASK_RESULT_PATH", source)
        self.assertIn('value.get("state") != "COMPLETE"', source)
        self.assertIn("stegverse.reusable-task-runner-result/v1", source)

    def test_trigger_retains_old_boundary_without_standard_result_and_advances_master_records_when_available(self):
        source = (ROOT / "scripts/trigger_reusable_task.py").read_text(encoding="utf-8")
        self.assertIn("if not result_path.is_file()", source)
        self.assertIn("COMPLETION_PREDICATES_REQUIRE_EVIDENCE_RECONCILIATION", source)
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_REQUIRED", source)
        self.assertIn("reusable_task_master_records_roundtrip", source)
        self.assertIn("ENTROPY_RECOVERY_RECORDED", source)
        self.assertIn("NONE_FOR_THIS_INVOCATION", source)

    def test_custody_request_targets_existing_ece_master_records_root(self):
        lifecycle = load_lifecycle()
        manifest = {"invocation_id":"i","reusable_task_id":"r","manifest_hash":"a"*64}
        request = lifecycle.build_custody_request(manifest=manifest, trigger_receipt={}, runner_result={}, runner_expiry={}, residual_recording={})
        self.assertEqual(request["destination"], "master-records/orchestration")
        self.assertFalse(request["destination_custody_accepted"])

    def test_lifecycle_workers_are_on_existing_resident_propagation_surface(self):
        refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        self.assertIn('Path("workers")', refresh)
        self.assertTrue((ROOT / "workers/reusable_task_lifecycle.py").is_file())
        self.assertTrue((ROOT / "workers/reusable_task_master_records_roundtrip.py").is_file())
        self.assertTrue((ROOT / "workers/finalize_reusable_task_entropy.py").is_file())


if __name__ == "__main__":
    unittest.main()
