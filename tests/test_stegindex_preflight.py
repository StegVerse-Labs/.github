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
        (root / "registry").mkdir()
        (root / "STEGINDEX_MIRROR_HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
        (root / "registry" / "capabilities.json").write_text(json.dumps({
            "entries": [{
                "capability_id": "stegverse:capability:runtime-proof:v1",
                "aliases": ["runtime evidence"],
                "purpose": "Produce authentic runtime proof",
                "owner_repo": "StegVerse-Labs/example",
                "lifecycle_state": "RELEASED",
                "authority_effect": "NONE",
                "dependencies": [],
                "missing_predicates": ["runtime_receipt_present"],
                "current_evidence_state": "SOURCE_READY_RUNTIME_UNOBSERVED",
                "blocking_owner": "StegVerse-Labs/example#1",
                "invocation_surface": "scripts/run_runtime.py",
                "user_action_required": False,
                "provenance": ["EXAMPLE_MIRROR_HANDOFF.md"]
            }]
        }), encoding="utf-8")
        (root / "registry" / "predicates.json").write_text(json.dumps({
            "predicates": [{
                "predicate_id": "runtime_receipt_present",
                "default_satisfier": "runtime owner"
            }]
        }), encoding="utf-8")
        return root

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_runtime_evidence_resolves_to_exact_predicate_and_owner(self):
        result = module.resolve(
            index_root=self.make_index(),
            query="runtime evidence",
            requested_predicate="runtime_receipt_present",
        )
        self.assertEqual(result["first_actionable_predicate"]["predicate_id"], "runtime_receipt_present")
        self.assertEqual(result["first_actionable_predicate"]["satisfier_owner"], "StegVerse-Labs/example#1")
        self.assertFalse(result["machine_continuation_required"])
        self.assertTrue(result["generic_blocker_permitted"])

    def test_missing_index_is_not_reclassified_as_missing_implementation(self):
        old = os.environ.pop("STEGVERSE_STEGINDEX_SOURCE_ROOT", None)
        try:
            with self.assertRaises(module.PreflightError):
                module._index_root()
        finally:
            if old is not None:
                os.environ["STEGVERSE_STEGINDEX_SOURCE_ROOT"] = old


if __name__ == "__main__":
    unittest.main()
