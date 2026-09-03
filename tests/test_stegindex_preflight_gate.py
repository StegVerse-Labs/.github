import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StegIndexPreflightGateTests(unittest.TestCase):
    def run_gate(self, *args):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "stegindex_preflight_gate.py"), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def write_fake_preflight(self, root, payload):
        scripts = Path(root) / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        body = (
            "import json\n"
            f"print(json.dumps({payload!r}))\n"
        )
        (scripts / "preflight.py").write_text(body, encoding="utf-8")

    def test_missing_root_is_exact_dependency(self):
        result = self.run_gate("--query", "heartbeat")
        self.assertEqual(result["adapter_state"], "STEGINDEX_ROOT_NOT_DECLARED")
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertFalse(result["generic_blocker_permitted"])

    def test_missing_preflight_file_is_exact_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_gate(
                "--query", "heartbeat",
                "--stegindex-root", tmp,
            )
        self.assertEqual(result["adapter_state"], "STEGINDEX_SOURCE_UNAVAILABLE")
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertFalse(result["generic_blocker_permitted"])

    def test_stale_or_contradictory_truth_is_not_reused(self):
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "indexed_truth_usable": False,
            "existing_capability_found": True,
            "duplicate_implementation_guard": "RECONCILE_BEFORE_REUSE_OR_NEW_WORK",
            "machine_continuation_required": False,
            "generic_blocker_permitted": False,
            "purpose_contributions": [],
            "capability_risk": {
                "matches": [{"source_id": "external:lolbas:v1"}],
                "transition_surfaces": ["execution", "egress"],
                "required_governance": ["execution authority predicate"],
                "trusted_or_available_implies_authority": False,
                "runtime_dependency": False,
                "copy_payloads": False,
                "authority_effect": "NONE_INDEX_ONLY",
            },
            "truth_reconciliation": {
                "preflight_truth_usable": False,
                "records": [{"capability_id": "x", "truth_state": "STALE"}],
            },
            "first_actionable_predicate": {
                "predicate_id": "indexed_truth_reconciled",
                "machine_executable_now": False,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            self.write_fake_preflight(tmp, payload)
            result = self.run_gate(
                "--query", "heartbeat",
                "--stegindex-root", tmp,
            )
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertEqual(result["exact_dependency"], "indexed_truth_reconciled")
        self.assertFalse(result["indexed_truth_usable"])
        self.assertFalse(result["generic_blocker_permitted"])

    def test_machine_continuation_survives_only_usable_truth(self):
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "indexed_truth_usable": True,
            "existing_capability_found": True,
            "duplicate_implementation_guard": "REUSE_OR_EXTEND_EXISTING",
            "machine_continuation_required": True,
            "generic_blocker_permitted": False,
            "purpose_contributions": [],
            "capability_risk": {
                "matches": [{"source_id": "external:lolbas:v1"}],
                "transition_surfaces": ["execution", "egress"],
                "required_governance": ["execution authority predicate"],
                "trusted_or_available_implies_authority": False,
                "runtime_dependency": False,
                "copy_payloads": False,
                "authority_effect": "NONE_INDEX_ONLY",
            },
            "truth_reconciliation": {
                "preflight_truth_usable": True,
                "records": [{"capability_id": "x", "truth_state": "TRUE"}],
            },
            "first_actionable_predicate": {
                "predicate_id": "runtime_receipt_present",
                "machine_executable_now": True,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            self.write_fake_preflight(tmp, payload)
            result = self.run_gate(
                "--query", "worker",
                "--stegindex-root", tmp,
            )
        self.assertEqual(result["decision"], "CONTINUE_MACHINE_EXECUTION")
        self.assertTrue(result["indexed_truth_usable"])
        self.assertTrue(result["machine_continuation_required"])
        self.assertEqual(
            result["capability_risk"]["authority_effect"],
            "NONE_INDEX_ONLY",
        )
        self.assertFalse(
            result["capability_risk"]["trusted_or_available_implies_authority"]
        )

if __name__ == "__main__":
    unittest.main()
