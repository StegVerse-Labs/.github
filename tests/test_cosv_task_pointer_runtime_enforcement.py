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


class CosvTaskPointerRuntimeEnforcementTests(unittest.TestCase):
    def _runtime(self, vector: str = "10100000100000") -> Path:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        index_path = root / "control" / "task-vector-index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "task_id": "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001",
                            "vector": vector,
                            "registry_ref": "data/canonical-task-registry.json",
                            "source_state_vector_ref": "control/task-vectors/COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001.json",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return root

    def test_exact_pointer_resolves(self) -> None:
        runtime = self._runtime()
        receipt = MODULE.validate_cosv_task_pointer(
            runtime,
            "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001",
            "10100000100000",
        )
        self.assertTrue(receipt["binding_verified"])
        self.assertEqual(receipt["profile"], "task.v1")
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_vector_mismatch_fails_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaisesRegex(RuntimeError, "binding mismatch"):
            MODULE.validate_cosv_task_pointer(
                runtime,
                "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001",
                "00100000100000",
            )

    def test_duplicate_task_identity_fails_closed(self) -> None:
        runtime = self._runtime()
        index_path = runtime / "control" / "task-vector-index.json"
        value = json.loads(index_path.read_text(encoding="utf-8"))
        value["tasks"].append(dict(value["tasks"][0]))
        index_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "exactly once"):
            MODULE.validate_cosv_task_pointer(
                runtime,
                "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001",
                "10100000100000",
            )

    def test_malformed_vector_fails_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaisesRegex(RuntimeError, "14-digit"):
            MODULE.validate_cosv_task_pointer(
                runtime,
                "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001",
                "101",
            )


if __name__ == "__main__":
    unittest.main()
