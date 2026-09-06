import json
import tempfile
import unittest
from pathlib import Path

from scripts.resolve_machine_preflight_receipt import resolve_current_preflight


class PreflightSupersessionResolutionTests(unittest.TestCase):
    def _write(self, root: Path, rel: str, value: dict) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_unsuperseded_pass_remains_current(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "receipts/preflight/A.json"
            self._write(root, rel, {"state": "PASS", "verdict": "PASS"})
            result = resolve_current_preflight(root, rel)
            self.assertTrue(result["current_admissible"])
            self.assertEqual(result["current_disposition"], "PASS")
            self.assertIsNone(result["supersession_ref"])

    def test_valid_supersession_preserves_history_but_revokes_current_admissibility(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "receipts/preflight/A.json"
            self._write(root, rel, {"state": "PASS", "verdict": "PASS"})
            self._write(
                root,
                "receipts/preflight/A.supersession.json",
                {
                    "schema": "stegverse.preflight-supersession/v1",
                    "supersession_id": "A-S1",
                    "supersedes": rel,
                    "current_disposition": "NOT_ADMISSIBLE_UNTIL_NEW_EVIDENCE",
                    "runtime_truth_inferred": False,
                    "execution_admission_inferred": False,
                    "authority_effect": "NONE_EVIDENCE_RECONCILIATION_ONLY",
                },
            )
            result = resolve_current_preflight(root, rel)
            self.assertEqual(result["historical_state"], "PASS")
            self.assertFalse(result["current_admissible"])
            self.assertEqual(result["current_disposition"], "NOT_ADMISSIBLE_UNTIL_NEW_EVIDENCE")
            self.assertEqual(result["supersession_id"], "A-S1")

    def test_mismatched_supersession_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "receipts/preflight/A.json"
            self._write(root, rel, {"state": "PASS", "verdict": "PASS"})
            self._write(
                root,
                "receipts/preflight/A.supersession.json",
                {
                    "schema": "stegverse.preflight-supersession/v1",
                    "supersedes": "receipts/preflight/B.json",
                    "current_disposition": "STOP",
                    "runtime_truth_inferred": False,
                    "execution_admission_inferred": False,
                    "authority_effect": "NONE",
                },
            )
            with self.assertRaisesRegex(ValueError, "SUPERSESSION_TARGET_MISMATCH"):
                resolve_current_preflight(root, rel)

    def test_authority_escalation_in_supersession_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "receipts/preflight/A.json"
            self._write(root, rel, {"state": "PASS", "verdict": "PASS"})
            self._write(
                root,
                "receipts/preflight/A.supersession.json",
                {
                    "schema": "stegverse.preflight-supersession/v1",
                    "supersedes": rel,
                    "current_disposition": "STOP",
                    "runtime_truth_inferred": False,
                    "execution_admission_inferred": False,
                    "authority_effect": "EXECUTION_ALLOWED",
                },
            )
            with self.assertRaisesRegex(ValueError, "SUPERSESSION_AUTHORITY_ESCALATION"):
                resolve_current_preflight(root, rel)

    def test_repository_runtime_presence_supersession_is_currently_non_admissible(self):
        root = Path(__file__).resolve().parents[1]
        result = resolve_current_preflight(
            root,
            "receipts/preflight/CROSS-TASK-RUNTIME-PRESENCE-PREDICATE-001.json",
        )
        self.assertFalse(result["current_admissible"])
        self.assertEqual(
            result["current_disposition"],
            "NOT_ADMISSIBLE_UNTIL_EXACT_RUNTIME_SUBJECT_BINDING_EXISTS",
        )
        self.assertFalse(result["runtime_truth_inferred"])
        self.assertFalse(result["execution_admission_inferred"])


if __name__ == "__main__":
    unittest.main()
