import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_stegindex_preflight.py"

spec = importlib.util.spec_from_file_location("stegindex_preflight", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class StegIndexPreflightTests(unittest.TestCase):
    def make_index(self) -> Path:
        root = Path(self.temp.name)
        (root / "scripts").mkdir()
        (root / "STEGINDEX_MIRROR_HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
        (root / "scripts" / "preflight.py").write_text(
            "import json, os\n"
            "print(json.dumps({"
            "'query':'runtime evidence',"
            "'capabilities':[{'capability_id':'stegverse:capability:runtime-proof:v1'}],"
            "'purpose_contributions':[],"
            "'capability_risk':{'matches':[{'source_id':'external:lolbas:v1'}],'transition_surfaces':['execution','egress'],'required_governance':['execution authority predicate'],'trusted_or_available_implies_authority':False,'runtime_dependency':False,'copy_payloads':False,'authority_effect':'NONE_INDEX_ONLY'},"
            "'existing_capability_found':True,"
            "'duplicate_implementation_guard':'REUSE_OR_EXTEND_EXISTING',"
            "'first_actionable_predicate':{'predicate_id':'runtime_receipt_present','machine_executable_now':False},"
            "'machine_continuation_required':False,"
            "'generic_blocker_permitted':True,"
            "'source_refresh':{'state':'COMPLETE' if os.environ.get('STEGVERSE_REPO_ROOTS_JSON') else 'ABSENT'},,"
            "'authority_effect':'NONE_INDEX_RESOLUTION_ONLY'"
            "}))\n",
            encoding="utf-8",
        )
        return root

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_runtime_evidence_delegates_to_canonical_index(self):
        root = self.make_index()
        result = module.run_canonical(
            index_root=root,
            query="runtime evidence",
            predicate="runtime_receipt_present",
            capability_id="stegverse:capability:runtime-proof:v1",
            intent="RUNTIME_EVIDENCE",
        )
        self.assertTrue(result["canonical_resolver_invoked"])
        self.assertEqual(result["first_actionable_predicate"]["predicate_id"], "runtime_receipt_present")
        self.assertEqual(result["duplicate_implementation_guard"], "REUSE_OR_EXTEND_EXISTING")
        self.assertFalse(result["network_fetch_performed"])
        self.assertFalse(result["github_token_required"])
        self.assertIn("execution", result["capability_risk"]["transition_surfaces"])
        self.assertEqual(result["capability_risk"]["authority_effect"], "NONE_INDEX_ONLY")
        self.assertFalse(result["capability_risk"]["trusted_or_available_implies_authority"])

    def test_repo_roots_map_is_propagated_to_canonical_child(self):
        root = self.make_index()
        old_map = os.environ.get("STEGVERSE_REPO_ROOTS_JSON")
        try:
            os.environ["STEGVERSE_REPO_ROOTS_JSON"] = json.dumps({
                "StegVerse-Labs/StegIndex": str(root),
                "StegVerse-Labs/Site": "/tmp/site",
            })
            result = module.run_canonical(
                index_root=root,
                query="runtime evidence",
                intent="DISCOVER",
            )
        finally:
            if old_map is None:
                os.environ.pop("STEGVERSE_REPO_ROOTS_JSON", None)
            else:
                os.environ["STEGVERSE_REPO_ROOTS_JSON"] = old_map
        self.assertEqual(result["source_refresh"]["state"], "COMPLETE")

    def test_repo_roots_map_resolves_canonical_stegindex(self):
        root = self.make_index()
        old_direct = os.environ.pop("STEGVERSE_STEGINDEX_SOURCE_ROOT", None)
        old_map = os.environ.get("STEGVERSE_REPO_ROOTS_JSON")
        try:
            os.environ["STEGVERSE_REPO_ROOTS_JSON"] = json.dumps({"StegVerse-Labs/StegIndex": str(root)})
            self.assertEqual(module._index_root(), root.resolve())
        finally:
            if old_direct is not None:
                os.environ["STEGVERSE_STEGINDEX_SOURCE_ROOT"] = old_direct
            if old_map is None:
                os.environ.pop("STEGVERSE_REPO_ROOTS_JSON", None)
            else:
                os.environ["STEGVERSE_REPO_ROOTS_JSON"] = old_map

    def test_missing_index_is_not_reclassified_as_missing_implementation(self):
        old_direct = os.environ.pop("STEGVERSE_STEGINDEX_SOURCE_ROOT", None)
        old_map = os.environ.pop("STEGVERSE_REPO_ROOTS_JSON", None)
        try:
            with self.assertRaises(module.PreflightError):
                module._index_root()
        finally:
            if old_direct is not None:
                os.environ["STEGVERSE_STEGINDEX_SOURCE_ROOT"] = old_direct
            if old_map is not None:
                os.environ["STEGVERSE_REPO_ROOTS_JSON"] = old_map


if __name__ == "__main__":
    unittest.main()
