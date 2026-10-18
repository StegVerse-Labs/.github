import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_task_handoff_projection import (  # noqa: E402
    build_projection, normalize_dependency, project_owner_questions, project_work_items, resolve_task)

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

    # C3: tasks recorded outside the aggregate Registry resolve from their own canonical source.
    def test_registry_row_wins_over_fallbacks(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        task_id = registry["tasks"][0]["task_id"]
        self.assertEqual(resolve_task(registry, task_id, ROOT)[1], "AGGREGATE_REGISTRY")

    def test_standalone_record_task_vector_and_reusable_bundle_resolve(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        in_registry = {t["task_id"] for t in registry["tasks"]}
        expected = {
            "STANDALONE_CANONICAL_TASK_RECORD": ROOT / "data/canonical-task-records",
            "TASK_VECTOR": ROOT / "control/task-vectors",
            "REUSABLE_TASK_BUNDLE": ROOT / "source-bundles/reusable-task-registry.d",
        }
        seen = {}
        for path in sorted(ROOT.glob("data/canonical-task-records/*.json")) + sorted(ROOT.glob("control/task-vectors/*.json")) \
                + sorted(ROOT.glob("source-bundles/reusable-task-registry.d/*.json")):
            task_id = path.stem
            if task_id in in_registry:
                continue
            try:
                task, source = resolve_task(registry, task_id, ROOT)
            except SystemExit:
                continue
            seen.setdefault(source, (task_id, task))
        for source, directory in expected.items():
            with self.subTest(source=source):
                self.assertIn(source, seen, f"no fallback task resolved from {directory}")
                task_id, task = seen[source]
                self.assertEqual(task["task_id"], task_id)
                self.assertEqual(build_projection(task, None, registry, source)["task_source"], source)

    def test_unknown_or_unsafe_task_id_fails_closed(self):
        registry = {"tasks": []}
        for task_id in ("NO-SUCH-TASK-001", "../data/canonical-task-registry"):
            with self.subTest(task_id=task_id):
                with self.assertRaises(SystemExit):
                    resolve_task(registry, task_id, ROOT)

    def test_duplicate_registry_rows_fail_closed(self):
        with self.assertRaises(SystemExit):
            resolve_task({"tasks": [{"task_id": "T"}, {"task_id": "T"}]}, "T", ROOT)

    # C4: existing issue/owner/handoff fields and work items are projected.
    def test_existing_issue_owner_and_handoff_fields_are_projected(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for field in ("issue_ref", "canonical_issue", "owners", "handoff_projection_refs"):
            task = next(t for t in registry["tasks"] if field in t)
            with self.subTest(field=field):
                self.assertEqual(build_projection(task, None, registry)[field], task[field])

    def test_work_items_keep_well_formed_and_count_malformed(self):
        good = {"kind": "PULL_REQUEST", "repo": "StegVerse-Labs/.github", "number": 3257, "state": "DRAFT",
                "head": "c9f7c84", "ci": "GREEN", "owner_approved": False, "extra": "dropped"}
        kept, rejected = project_work_items([good, {"kind": "PULL_REQUEST", "repo": "x", "number": 1, "state": "DRAFT", "owner_approved": False},
                                             {"kind": "ISSUE", "repo": "a/b", "number": 0, "state": "OPEN", "owner_approved": True},
                                             {"kind": "ISSUE", "repo": "a/b", "number": 2, "state": "DONE", "owner_approved": True},
                                             {"kind": "ISSUE", "repo": "a/b", "number": 2, "state": "OPEN", "owner_approved": "yes"}, "x"])
        self.assertEqual(kept, [{k: good[k] for k in ("kind", "repo", "number", "state", "head", "ci", "owner_approved")}])
        self.assertEqual(rejected, 5)
        self.assertEqual(project_work_items(None), ([], 0))

    # C5: owner questions come from Registry human_actions, not prose.
    def test_owner_questions_are_projected_per_task(self):
        registry = {"tasks": [{"task_id": "T"}], "human_actions": [
            {"id": "OQ-1", "task_id": "T", "question": "q?", "default_until_answered": "hold", "source_ref": "x#1", "state": "OPEN", "other": 1},
            {"id": "OQ-2", "task_id": "U", "question": "other task"},
            "malformed",
        ]}
        projection = build_projection({"task_id": "T"}, None, registry)
        self.assertEqual(projection["owner_questions"], [
            {"id": "OQ-1", "question": "q?", "default_until_answered": "hold", "source_ref": "x#1", "state": "OPEN"}])
        self.assertEqual(project_owner_questions({}, "T"), [])

    def test_markdown_carries_work_items_and_owner_questions(self):
        task_id = json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]["task_id"]
        result = subprocess.run([sys.executable, str(ROOT / "scripts/render_task_handoff_projection.py"), "--task-id", task_id,
                                 "--format", "markdown"], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn("## Work items / owner questions", result.stdout)


if __name__ == "__main__":
    unittest.main()
