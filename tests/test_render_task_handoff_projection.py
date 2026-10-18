import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_task_handoff_projection import build_projection, normalize_dependency  # noqa: E402

REGISTRY = ROOT / "data/canonical-task-registry.json"


class RenderTaskHandoffProjectionTests(unittest.TestCase):
    def test_string_dependency_projects_as_unknown_task_reference(self):
        projection = build_projection({"task_id": "t", "dependencies": ["DEP-001", {"task_id": "DEP-002", "state": "RESOLVED"}]})
        self.assertEqual(projection["unresolved_dependencies"], [
            {"task_id": "DEP-001", "state": "UNKNOWN", "dependency_form": "TASK_ID_REFERENCE"}])

    def test_malformed_dependency_fails_closed_as_unknown(self):
        self.assertEqual(normalize_dependency(7), {"state": "UNKNOWN", "dependency_form": "MALFORMED"})

    def test_object_dependencies_unchanged(self):
        dep = {"task_id": "D", "state": "UNRESOLVED"}
        self.assertIs(normalize_dependency(dep), dep)

    def test_every_registry_task_renders(self):
        # Regression: tasks whose dependencies are bare task ids crashed with AttributeError (org#160 D-P1).
        tasks = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"]
        for task in tasks:
            with self.subTest(task=task.get("task_id")):
                self.assertEqual(build_projection(task)["task_id"], task.get("task_id"))

    def test_cli_renders_task_with_string_dependencies(self):
        task_id = next(t["task_id"] for t in json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"]
                       if any(isinstance(d, str) for d in t.get("dependencies", [])))
        result = subprocess.run([sys.executable, str(ROOT / "scripts/render_task_handoff_projection.py"), "--task-id", task_id],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["task_id"], task_id)


if __name__ == "__main__":
    unittest.main()
