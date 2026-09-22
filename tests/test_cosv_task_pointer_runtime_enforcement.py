from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "refresh_and_execute_resident_task.py"
SPEC = importlib.util.spec_from_file_location("refresh_and_execute_resident_task", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

TASK_ID = "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001"


class CosvTaskPointerRuntimeEnforcementTests(unittest.TestCase):
    def _runtime(self, vector: str = "10100000100000") -> Path:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        source_ref = "control/task-vectors/COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001.json"
        index_path = root / "control" / "task-vector-index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(
                {
                    "profile": "task.v1",
                    "tasks": [
                        {
                            "task_id": TASK_ID,
                            "vector": vector,
                            "vector_state": "EMITTED",
                            "authority_effect": "NONE",
                            "registry_ref": "data/canonical-task-registry.json",
                            "source_state_vector_ref": source_ref,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        source_path = root / source_ref
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            json.dumps({
                "identity": f"StegVerse-Labs/.github:task:{TASK_ID}",
                "profile": "task.v1",
                "level": "task",
                "vector": vector,
            }),
            encoding="utf-8",
        )
        return root

    def test_exact_pointer_resolves_against_index_and_source_vector(self) -> None:
        runtime = self._runtime()
        receipt = MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "10100000100000")
        self.assertTrue(receipt["binding_verified"])
        self.assertTrue(receipt["source_vector_verified"])
        self.assertEqual(receipt["profile"], "task.v1")
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_vector_mismatch_fails_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaisesRegex(RuntimeError, "binding mismatch"):
            MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "00100000100000")

    def test_duplicate_task_identity_fails_closed(self) -> None:
        runtime = self._runtime()
        index_path = runtime / "control" / "task-vector-index.json"
        value = json.loads(index_path.read_text(encoding="utf-8"))
        value["tasks"].append(dict(value["tasks"][0]))
        index_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "exactly once"):
            MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "10100000100000")

    def test_malformed_vector_fails_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaisesRegex(RuntimeError, "14-digit"):
            MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "101")

    def test_index_source_vector_parity_drift_fails_closed(self) -> None:
        runtime = self._runtime()
        source_path = runtime / "control/task-vectors/COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001.json"
        value = json.loads(source_path.read_text(encoding="utf-8"))
        value["vector"] = "00100000100000"
        source_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "index/source state-vector parity mismatch"):
            MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "10100000100000")

    def test_source_vector_identity_mismatch_fails_closed(self) -> None:
        runtime = self._runtime()
        source_path = runtime / "control/task-vectors/COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001.json"
        value = json.loads(source_path.read_text(encoding="utf-8"))
        value["identity"] = "StegVerse-Labs/.github:task:DIFFERENT-TASK"
        source_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "index/source state-vector parity mismatch"):
            MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "10100000100000")

    def test_source_vector_path_cannot_escape_runtime_root(self) -> None:
        runtime = self._runtime()
        index_path = runtime / "control/task-vector-index.json"
        value = json.loads(index_path.read_text(encoding="utf-8"))
        value["tasks"][0]["source_state_vector_ref"] = "../../outside.json"
        index_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "escaped resident root"):
            MODULE.validate_cosv_task_pointer(runtime, TASK_ID, "10100000100000")


if __name__ == "__main__":
    unittest.main()
