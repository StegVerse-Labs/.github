"""Lane D I1: the Goal registration manifest is consumed by the registry transition's plan and every Goal resolves to a six-field outcome."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_task_registration_transition.py"
MANIFEST = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "i1-goal-manifests" / "MANIFEST.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


class I1GoalRegistrationManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_makes_no_registry_edit(self) -> None:
        self.assertIs(self.manifest["registry_edit"], False)
        self.assertIs(self.manifest["registry_generation_bump"], False)
        registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
        ids = {row.get("task_id") for row in registry["tasks"]}
        for goal in self.manifest["goals"]:
            self.assertNotIn(goal["task_id"], ids)

    def test_every_goal_has_six_fields_and_a_class(self) -> None:
        for goal in self.manifest["goals"]:
            outcome = goal["expected_plan"] or goal["fail_closed"]
            for field in SIX:
                self.assertTrue(outcome.get(field), (goal["task_id"], field))
            self.assertIn(outcome["failure_class"], ("A", "B", "C", "D"))

    def test_shard_only_requests_plan_as_recorded(self) -> None:
        for goal in self.manifest["goals"]:
            if goal["basis"] != "SHARD_ONLY":
                self.assertFalse((ROOT / "data" / "canonical-task-records" / f"{goal['task_id']}.json").exists())
                continue
            request = json.loads((ROOT / goal["request"]).read_text(encoding="utf-8"))
            self.assertEqual(request["registration_mode"], "EXISTING_IDENTITY")
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "receipt.json"
                subprocess.run([sys.executable, str(SCRIPT), "plan", "--request", str(ROOT / goal["request"]),
                                "--receipt-out", str(out)], cwd=ROOT, capture_output=True, text=True, check=False)
                receipt = json.loads(out.read_text(encoding="utf-8"))
            expected = goal["expected_plan"]
            self.assertEqual(receipt["disposition"], expected["disposition"], goal["task_id"])
            for field in SIX:
                self.assertEqual(receipt[field], expected[field], (goal["task_id"], field))
            for flag in ("consequence_committed", "organization_ledger_appended", "execution_authority_minted",
                         "workercoordinator_claim_or_fence_minted", "intr_admission_minted"):
                self.assertFalse(receipt[flag], (goal["task_id"], flag))


    def _plan(self, request: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "receipt.json"
            subprocess.run([sys.executable, str(SCRIPT), "plan", "--request", str(ROOT / request),
                            "--receipt-out", str(out)], cwd=ROOT, capture_output=True, text=True, check=False)
            return json.loads(out.read_text(encoding="utf-8"))

    def _new_identity_goals(self) -> list:
        goals = [g for g in self.manifest["goals"] if g["basis"] == "NEW_IDENTITY_REQUEST"]
        self.assertTrue(goals, "at least one NEW_IDENTITY request is carried by the manifest")
        return goals

    def test_new_identity_requests_plan_as_recorded(self) -> None:
        for goal in self._new_identity_goals():
            request = json.loads((ROOT / goal["request"]).read_text(encoding="utf-8"))
            self.assertEqual(request["registration_mode"], "NEW_IDENTITY")
            self.assertEqual(request["record"]["coordination_state"], "PROPOSED")
            self.assertTrue((ROOT / request["allocation_request_ref"]).is_file(), goal["task_id"])
            receipt = self._plan(goal["request"])
            expected = goal["expected_plan"]
            self.assertEqual(receipt["disposition"], expected["disposition"], goal["task_id"])
            for field in SIX:
                self.assertEqual(receipt[field], expected[field], (goal["task_id"], field))
            for flag in ("consequence_committed", "organization_ledger_appended", "execution_authority_minted",
                         "workercoordinator_claim_or_fence_minted", "intr_admission_minted"):
                self.assertFalse(receipt[flag], (goal["task_id"], flag))

    def test_new_identity_requests_carry_a_sealed_testable_finish_point(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import goal_scope_seal
        for goal in self._new_identity_goals():
            request = json.loads((ROOT / goal["request"]).read_text(encoding="utf-8"))
            sealed = request["sealed_scope"]
            body = goal_scope_seal.validate_sealed_scope(sealed, request["task_id"], request["record"], new_identity=True)
            self.assertEqual(body["scope_digest"], goal["scope_digest"])
            self.assertEqual(sealed["scope"]["finish_point"], goal["finish_point"])
            allocation = json.loads((ROOT / request["allocation_request_ref"]).read_text(encoding="utf-8"))
            self.assertEqual(allocation["proposed_task_id"], request["task_id"])
            self.assertEqual(allocation["proposed_task_id_authority"], "NONE_PROPOSAL_ONLY")
            self.assertIsNone(allocation["cosv_task_vector"])
            self.assertEqual(allocation["scope_digest"], goal["scope_digest"])


if __name__ == "__main__":
    unittest.main()
