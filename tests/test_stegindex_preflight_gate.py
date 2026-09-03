import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StegIndexPreflightGateTests(unittest.TestCase):
    def run_gate(self, *args, env=None):
        values = dict(os.environ)
        if env:
            values.update(env)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "stegindex_preflight_gate.py"), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            env=values,
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

    def test_repo_roots_map_can_supply_stegindex_root(self):
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "indexed_truth_usable": True,
            "existing_capability_found": False,
            "duplicate_implementation_guard": "NO_EXISTING_CAPABILITY_MATCH",
            "machine_continuation_required": False,
            "generic_blocker_permitted": True,
            "purpose_contributions": [],
            "capability_risk": {},
            "first_actionable_predicate": None,
        }
        with tempfile.TemporaryDirectory() as tmp:
            self.write_fake_preflight(tmp, payload)
            result = self.run_gate(
                "--query", "new thing",
                env={"STEGINDEX_ROOT": "", "STEGVERSE_REPO_ROOTS_JSON": json.dumps({"StegVerse-Labs/StegIndex": tmp})},
            )
        self.assertEqual(result["adapter_state"], "RESOLVED")
        self.assertEqual(result["decision"], "NO_EXISTING_CAPABILITY_MATCH")

    def test_discovered_candidate_is_exact_blocker_not_new_work(self):
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "indexed_truth_usable": True,
            "existing_capability_found": False,
            "discovered_candidate_found": True,
            "duplicate_implementation_guard": "REVIEW_DISCOVERED_CANDIDATE_BEFORE_NEW_WORK",
            "machine_continuation_required": False,
            "generic_blocker_permitted": False,
            "purpose_contributions": [],
            "capability_risk": {},
            "first_actionable_predicate": {"predicate_id": "candidate_reconciled", "machine_executable_now": False},
        }
        with tempfile.TemporaryDirectory() as tmp:
            self.write_fake_preflight(tmp, payload)
            result = self.run_gate("--query", "candidate only", "--stegindex-root", tmp)
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertEqual(result["exact_dependency"], "candidate_reconciled")
        self.assertFalse(result["generic_blocker_permitted"])

    def test_incomplete_source_discovery_is_exact_blocker_not_new_work(self):
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "indexed_truth_usable": True,
            "existing_capability_found": False,
            "discovered_candidate_found": False,
            "duplicate_implementation_guard": "COMPLETE_SOURCE_DISCOVERY_BEFORE_NEW_WORK",
            "machine_continuation_required": False,
            "generic_blocker_permitted": False,
            "purpose_contributions": [],
            "capability_risk": {},
            "first_actionable_predicate": {"predicate_id": "source_discovery_complete", "machine_executable_now": False},
        }
        with tempfile.TemporaryDirectory() as tmp:
            self.write_fake_preflight(tmp, payload)
            result = self.run_gate("--query", "unknown capability", "--stegindex-root", tmp)
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertEqual(result["exact_dependency"], "source_discovery_complete")
        self.assertFalse(result["generic_blocker_permitted"])

if __name__ == "__main__":
    unittest.main()
