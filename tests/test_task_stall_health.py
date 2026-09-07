from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_task_stall_health.py"
SPEC = importlib.util.spec_from_file_location("evaluate_task_stall_health", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TaskStallHealthTests(unittest.TestCase):
    def _record(self, root: Path, task_id: str, vector: str, **overrides):
        index_dir = root / "control" / "task-vector-index.d"
        record_dir = root / "data" / "canonical-task-records"
        index_dir.mkdir(parents=True, exist_ok=True)
        record_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "task_id": task_id,
            "coordination_state": "ACTIVE",
            "blockers": [],
            "dependencies": [],
            "next_admissible_work": {"kind": "TEST_WORK"},
            **overrides,
        }
        record_path = record_dir / f"{task_id}.json"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        (index_dir / f"{task_id}.json").write_text(
            json.dumps({
                "task_id": task_id,
                "vector": vector,
                "registry_ref": str(record_path.relative_to(root)),
                "source_state_vector_ref": f"control/task-vectors/{task_id}.json",
            }),
            encoding="utf-8",
        )

    def _evaluate(self, task_id: str, vector: str, **overrides):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self._record(root, task_id, vector, **overrides)
        old_root = MODULE.ROOT
        old_index_dir = MODULE.SHARDED_INDEX_DIR
        old_index = MODULE.MONOLITHIC_INDEX_PATH
        old_registry = MODULE.MONOLITHIC_REGISTRY_PATH
        old_contract = MODULE.CONTRACT_PATH
        try:
            MODULE.ROOT = root
            MODULE.SHARDED_INDEX_DIR = root / "control" / "task-vector-index.d"
            MODULE.MONOLITHIC_INDEX_PATH = root / "control" / "task-vector-index.json"
            MODULE.MONOLITHIC_REGISTRY_PATH = root / "data" / "canonical-task-registry.json"
            MODULE.CONTRACT_PATH = root / "data" / "task-stall-detection-contract.json"
            MODULE.CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
            MODULE.CONTRACT_PATH.write_text(json.dumps({
                "defaults": {
                    "attempts_without_progress_to_stall": 3,
                    "same_resolution_count_to_stall": 3,
                    "wall_clock_stall_seconds": None,
                }
            }), encoding="utf-8")
            return MODULE.evaluate_task_health(task_id, vector)
        finally:
            MODULE.ROOT = old_root
            MODULE.SHARDED_INDEX_DIR = old_index_dir
            MODULE.MONOLITHIC_INDEX_PATH = old_index
            MODULE.MONOLITHIC_REGISTRY_PATH = old_registry
            MODULE.CONTRACT_PATH = old_contract

    def test_progressing_when_next_work_exists(self):
        result = self._evaluate("TASK-1", "20010000100000")
        self.assertEqual(result["health"], "PROGRESSING")

    def test_stalled_after_repeated_attempts_without_progress(self):
        result = self._evaluate(
            "TASK-2",
            "20010000100000",
            task_health={"continuation_attempts_since_progress": 3},
        )
        self.assertEqual(result["health"], "STALLED")

    def test_stuck_when_no_next_work_or_explanation(self):
        result = self._evaluate("TASK-3", "20010000100000", next_admissible_work=None)
        self.assertEqual(result["health"], "STUCK")

    def test_waiting_is_not_stalled(self):
        result = self._evaluate(
            "TASK-4",
            "20010000100000",
            waiting_condition={"predicate": "EXTERNAL_EVENT"},
            next_admissible_work=None,
        )
        self.assertEqual(result["health"], "WAITING")

    def test_blocked_is_not_stalled(self):
        result = self._evaluate(
            "TASK-5",
            "20010000100000",
            blockers=[{"id": "B-1"}],
            next_admissible_work=None,
        )
        self.assertEqual(result["health"], "BLOCKED")

    def test_retired_is_terminal(self):
        result = self._evaluate(
            "TASK-6",
            "70000000100000",
            coordination_state="RETIRED",
            next_admissible_work=None,
        )
        self.assertEqual(result["health"], "TERMINAL")


if __name__ == "__main__":
    unittest.main()
