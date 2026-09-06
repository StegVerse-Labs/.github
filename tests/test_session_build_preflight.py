import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "session_build_preflight.py"


class SessionBuildPreflightTests(unittest.TestCase):
    def fake_root(self, decision, *, include_coordination=True, **extra):
        tmp = tempfile.TemporaryDirectory()
        scripts = Path(tmp.name) / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "decision": decision,
            "generic_blocker_permitted": False,
            "machine_continuation_required": decision == "CONTINUE_MACHINE_EXECUTION",
            "indexed_truth_usable": decision != "EXACT_BLOCKER_ONLY",
            "existing_capability_found": decision in {
                "CONTINUE_MACHINE_EXECUTION", "REUSE_OR_EXTEND_EXISTING", "EXACT_BLOCKER_ONLY"
            },
        }
        payload.update(extra)
        (scripts / "preflight.py").write_text(
            "import json\nprint(json.dumps(" + repr(payload) + "))\n",
            encoding="utf-8",
        )
        if include_coordination:
            projection = {
                "authority_effect": "NONE_INDEX_PROJECTION_ONLY",
                "source_fragment_ids": ["F1"],
                "related_active_claims": [],
                "foreign_active_claims": [],
                "gaps": [],
                "predicate_dependency_relationships": [],
                "runtime_truth_inferred": False,
            }
            (scripts / "resolve_cross_task_coordination.py").write_text(
                "import json\nprint(json.dumps(" + repr(projection) + "))\n",
                encoding="utf-8",
            )
        return tmp

    def run_entry(self, root, goal="test goal", *extra_args):
        return subprocess.run(
            [sys.executable, str(ENTRY), "--goal", goal, "--stegindex-root", root, *extra_args],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_reuse_prevents_new_task_creation(self):
        with self.fake_root("REUSE_OR_EXTEND_EXISTING") as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "REUSE_EXISTING_CAPABILITY")
        self.assertFalse(result["task_creation_permitted"])
        self.assertTrue(result["cross_task_coordination"]["coordination_consulted"])
        self.assertTrue(result["readme_impact_complete"])

    def test_machine_continuation_prevents_new_task_creation(self):
        with self.fake_root("CONTINUE_MACHINE_EXECUTION") as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "CONTINUE_THROUGH_CANONICAL_OWNER")
        self.assertFalse(result["task_creation_permitted"])

    def test_exact_dependency_prevents_new_task_creation(self):
        with self.fake_root("EXACT_BLOCKER_ONLY", exact_dependency="indexed_truth_reconciled", indexed_truth_usable=False) as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_EXACT_DEPENDENCY")
        self.assertFalse(result["task_creation_permitted"])

    def test_no_match_permits_new_work_only_after_coordination_consulted(self):
        with self.fake_root("NO_EXISTING_CAPABILITY_MATCH") as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "NEW_WORK_MAY_BE_CONSIDERED")
        self.assertTrue(result["task_creation_permitted"])
        self.assertTrue(result["coordination_required_before_new_work"])
        self.assertTrue(result["cross_task_coordination"]["coordination_consulted"])
        self.assertFalse(result["cross_task_coordination"]["runtime_truth_inferred"])

    def test_no_match_fails_closed_when_coordination_resolver_unavailable(self):
        with self.fake_root("NO_EXISTING_CAPABILITY_MATCH", include_coordination=False) as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_COORDINATION_DEPENDENCY")
        self.assertFalse(result["task_creation_permitted"])
        self.assertFalse(result["cross_task_coordination"]["coordination_consulted"])
        self.assertEqual(result["cross_task_coordination"]["state"], "COORDINATION_RESOLVER_UNAVAILABLE")

    def test_coordination_filters_are_forwarded_without_granting_admission(self):
        with self.fake_root("REUSE_OR_EXTEND_EXISTING") as tmp:
            proc = self.run_entry(tmp, "test goal", "--coordination-task-id", "SHWP-X", "--coordination-predicate-id", "P-X")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        coordination = result["cross_task_coordination"]
        self.assertEqual(coordination["task_filter"], "SHWP-X")
        self.assertEqual(coordination["predicate_filter"], "P-X")
        self.assertFalse(coordination["candidate_consumer_execution_admission_inferred"])

    def test_discovered_candidate_prevents_new_task_creation(self):
        with self.fake_root(
            "NO_EXISTING_CAPABILITY_MATCH",
            duplicate_implementation_guard="REVIEW_DISCOVERED_CANDIDATE_BEFORE_NEW_WORK",
            discovered_candidate_found=True,
            first_actionable_predicate={"predicate_id": "candidate_reconciled", "machine_executable_now": False},
        ) as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_EXACT_DEPENDENCY")
        self.assertFalse(result["task_creation_permitted"])
        self.assertEqual(result["preflight"]["exact_dependency"], "candidate_reconciled")

    def test_incomplete_source_discovery_prevents_new_task_creation(self):
        with self.fake_root(
            "NO_EXISTING_CAPABILITY_MATCH",
            duplicate_implementation_guard="COMPLETE_SOURCE_DISCOVERY_BEFORE_NEW_WORK",
            first_actionable_predicate={"predicate_id": "source_discovery_complete", "machine_executable_now": False},
        ) as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_EXACT_DEPENDENCY")
        self.assertFalse(result["task_creation_permitted"])
        self.assertEqual(result["preflight"]["exact_dependency"], "source_discovery_complete")

    def test_material_function_change_without_readme_update_fails_closed(self):
        with self.fake_root("NO_EXISTING_CAPABILITY_MATCH") as tmp:
            proc = self.run_entry(
                tmp,
                "functional change",
                "--readme-impact-required",
                "--material-function-change", "true",
                "--readme-evidence-ref", "scripts/new_behavior.py",
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_README_IMPACT_DEPENDENCY")
        self.assertFalse(result["task_creation_permitted"])
        self.assertFalse(result["readme_impact_complete"])
        self.assertEqual(result["readme_impact"]["disposition"], "MATERIAL_FUNCTION_CHANGE_REQUIRES_README_UPDATE")

    def test_material_function_change_with_readme_update_passes_readme_gate(self):
        with self.fake_root("NO_EXISTING_CAPABILITY_MATCH") as tmp:
            proc = self.run_entry(
                tmp,
                "functional change",
                "--readme-impact-required",
                "--material-function-change", "true",
                "--readme-updated-in-change-set",
                "--readme-path", "README.md",
                "--readme-evidence-ref", "README.md",
                "--readme-evidence-ref", "scripts/new_behavior.py",
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "NEW_WORK_MAY_BE_CONSIDERED")
        self.assertTrue(result["task_creation_permitted"])
        self.assertTrue(result["readme_impact_complete"])
        self.assertEqual(result["readme_impact"]["disposition"], "README_UPDATED_FOR_MATERIAL_FUNCTION_CHANGE")

    def test_nonmaterial_determination_requires_reason_and_evidence(self):
        with self.fake_root("REUSE_OR_EXTEND_EXISTING") as tmp:
            proc = self.run_entry(
                tmp,
                "nonmaterial change",
                "--readme-impact-required",
                "--material-function-change", "false",
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_README_IMPACT_DEPENDENCY")
        self.assertFalse(result["readme_impact_complete"])

    def test_evidence_supported_nonmaterial_determination_passes(self):
        with self.fake_root("REUSE_OR_EXTEND_EXISTING") as tmp:
            proc = self.run_entry(
                tmp,
                "nonmaterial change",
                "--readme-impact-required",
                "--material-function-change", "false",
                "--no-readme-update-reason", "Only internal test fixtures changed; repository behavior is unchanged.",
                "--readme-evidence-ref", "tests/test_fixture.py",
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "REUSE_EXISTING_CAPABILITY")
        self.assertTrue(result["readme_impact_complete"])
        self.assertEqual(result["readme_impact"]["disposition"], "NONMATERIAL_CHANGE_EVIDENCE_SUPPORTED")


if __name__ == "__main__":
    unittest.main()
