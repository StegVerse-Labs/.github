from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "out-of-scope-remediation-request-contract.json"
TASK = ROOT / "data" / "canonical-task-records" / "STEGVERSE-OUT-OF-SCOPE-REMEDIATION-REQUEST-CONTRACT-001.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class OutOfScopeRemediationRequestContractTests(unittest.TestCase):
    def test_request_does_not_trigger_or_authorize_healer(self) -> None:
        contract = load(CONTRACT)
        semantics = contract["request_semantics"]
        self.assertFalse(semantics["request_is_healer_trigger"])
        self.assertFalse(semantics["request_transfers_authority"])
        self.assertFalse(semantics["request_authorizes_remedy"])
        self.assertTrue(semantics["healer_independently_evaluates_authorized_trigger"])
        self.assertFalse(semantics["originating_goal_may_repair_foreign_domain"])
        self.assertFalse(semantics["pending_predicate_alone_is_broken_condition"])

    def test_nonblocking_foreign_defect_continues_originating_goal(self) -> None:
        contract = load(CONTRACT)
        policy = contract["continuation_policy"]
        self.assertEqual(
            policy["nonblocking_foreign_defect"],
            "EMIT_REMEDIATION_REQUEST_AND_CONTINUE_CURRENT_GOAL",
        )
        self.assertTrue(policy["unrelated_current_goal_work_may_continue"])
        self.assertEqual(policy["scope_expansion_into_foreign_domain"], "PROHIBITED")

    def test_blocking_foreign_defect_holds_only_dependent_transition(self) -> None:
        contract = load(CONTRACT)
        self.assertEqual(
            contract["continuation_policy"]["blocking_foreign_defect"],
            "EMIT_REMEDIATION_REQUEST_AND_HOLD_ONLY_THE_DEPENDENT_TRANSITION_AS_EXTERNALLY_OWNED_CONDITION",
        )
        self.assertTrue(contract["remediation_return_contract"]["return_to_interrupted_gc_transition_if_blocking"])

    def test_gadi_fixture_is_out_of_scope_nonblocking_and_no_authority_transfer(self) -> None:
        fixture = load(CONTRACT)["first_fixture"]
        self.assertEqual(fixture["fixture_id"], "GADI-SOURCE-SCHEMA-COMPATIBILITY-MISMATCH-001")
        self.assertEqual(fixture["owning_domain"], "GADI")
        self.assertTrue(fixture["out_of_scope_for_current_goal"])
        self.assertFalse(fixture["blocks_originating_transition"])
        self.assertIsNone(fixture["interrupted_gc_transition"])
        self.assertEqual(fixture["authority_transfer"], "NONE")
        self.assertEqual(
            fixture["originating_goal_action"],
            "RETAIN_EVIDENCE_EMIT_REQUEST_CONTINUE_STEGBROWSER_SPECIFIC_VALIDATION",
        )

    def test_child_task_preserves_parent_cosv_and_healer_role(self) -> None:
        task = load(TASK)
        self.assertEqual(task["parent_task_id"], "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001")
        self.assertEqual(task["cosv_task_vector"], "40000100100000")
        model = task["authority_model"]
        self.assertFalse(model["remediation_request_triggers_healer"])
        self.assertTrue(model["healer_independent_trigger_evaluation_required"])
        self.assertFalse(model["originating_goal_may_repair_foreign_domain"])
        self.assertEqual(model["github_runtime_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
