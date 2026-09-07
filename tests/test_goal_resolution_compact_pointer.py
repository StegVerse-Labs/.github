from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_goal_resolution_continuation.py"
SPEC = importlib.util.spec_from_file_location("evaluate_goal_resolution_continuation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CompactPointerContinuationTests(unittest.TestCase):
    def _canonical_files(self) -> tuple[Path, Path, TemporaryDirectory[str]]:
        tmp = TemporaryDirectory()
        root = Path(tmp.name)
        index = root / "control" / "task-vector-index.json"
        registry = root / "data" / "canonical-task-registry.json"
        index.parent.mkdir(parents=True, exist_ok=True)
        registry.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "task_id": "TASK-001",
                            "vector": "10100000100000",
                            "registry_ref": "data/canonical-task-registry.json",
                            "source_state_vector_ref": "control/task-vectors/TASK-001.json",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        registry.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "task_id": "TASK-001",
                            "root_correlation_id": "GOAL-001",
                            "coordination_state": "ACTIVE",
                            "source_refs": [
                                "docs/TASK_001_MIRROR_HANDOFF.md",
                                "control/resident-execution-request.d/task-001.json",
                                "scripts/run_task.py",
                            ],
                            "dependency_refs": ["TASK-DEP"],
                            "adjacent_task_refs": ["TASK-ADJ"],
                            "existing_evidence_refs": ["receipts/preflight/TASK-001.json"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return index, registry, tmp

    def test_task_id_and_cosv_resolve_full_canonical_context(self) -> None:
        index, registry, tmp = self._canonical_files()
        self.addCleanup(tmp.cleanup)
        resolved = MODULE.resolve_compact_task_pointer(
            "TASK-001",
            "10100000100000",
            task_index_path=index,
            task_registry_path=registry,
        )
        self.assertTrue(resolved["pointer_binding_verified"])
        self.assertEqual(resolved["root_correlation_id"], "GOAL-001")
        self.assertEqual(resolved["handoff"], "docs/TASK_001_MIRROR_HANDOFF.md")
        self.assertEqual(resolved["dependencies"], ["TASK-DEP"])
        self.assertEqual(resolved["adjacent_tasks"], ["TASK-ADJ"])
        self.assertEqual(resolved["receipts"], ["receipts/preflight/TASK-001.json"])
        self.assertEqual(
            resolved["execution_request_refs"],
            ["control/resident-execution-request.d/task-001.json"],
        )
        self.assertEqual(
            resolved["next_admissible_work"]["ref"],
            "control/resident-execution-request.d/task-001.json",
        )

    def test_resolved_task_builds_machine_continuation_request(self) -> None:
        index, registry, tmp = self._canonical_files()
        self.addCleanup(tmp.cleanup)
        resolved = MODULE.resolve_compact_task_pointer(
            "TASK-001",
            "10100000100000",
            task_index_path=index,
            task_registry_path=registry,
        )
        request = MODULE._build_continuation_request(MODULE._normalize_task(resolved))
        self.assertIsNotNone(request)
        assert request is not None
        self.assertTrue(request["automatic_pickup_required"])
        self.assertFalse(request["human_reentry_required"])
        self.assertFalse(request["status_only_response_is_completion"])
        self.assertEqual(
            request["next_admissible_work"]["ref"],
            "control/resident-execution-request.d/task-001.json",
        )

    def test_mismatched_vector_fails_closed(self) -> None:
        index, registry, tmp = self._canonical_files()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            MODULE.resolve_compact_task_pointer(
                "TASK-001",
                "00100000100000",
                task_index_path=index,
                task_registry_path=registry,
            )

    def test_missing_task_fails_closed(self) -> None:
        index, registry, tmp = self._canonical_files()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(ValueError, "resolve exactly once"):
            MODULE.resolve_compact_task_pointer(
                "TASK-MISSING",
                "10100000100000",
                task_index_path=index,
                task_registry_path=registry,
            )


if __name__ == "__main__":
    unittest.main()
