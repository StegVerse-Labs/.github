"""Lane C (C): GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001 NEW_IDENTITY request, sealed scope and recorded plan outcome.

The request is a fixture (outside control/canonical-task-registration-requests/), so a
merge applies nothing. The test pins: GOAL_SCOPE_SEALED holds (digest, record equality,
testable finish point), the allocation request binds the same digest with no vector,
and plan resolves to the recorded six-field outcome with no consequence. Lowest
supported mode: E0 (stdlib, committed files, no clock, no network).
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_task_registration_transition.py"
TASK_ID = "GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001"
REQUEST = f"tests/fixtures/canonical_task_registration/github-universal-governance-product/{TASK_ID}.request.json"
ADJACENCY = f"tests/fixtures/canonical_task_registration/github-universal-governance-product/{TASK_ID}.adjacency-test.json"
SCOPE_DIGEST = "sha256:af91ec48f3fdeaf0233777a2b798829a4544622bd342ddaf8ffdc72252d5f3b5"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
EXPECTED_PLAN = {
    "disposition": "FAIL_CLOSED",
    "failure_code": "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE",
    "failed_predicate": "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE",
    "required_evidence_or_repair": (
        f"coordinate {TASK_ID} with ['PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001', "
        "'STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001'] (COORDINATE_BEFORE_MUTATION) or narrow its targets before merge"),
    "retry_entrypoint": (".github/workflows/canonical-task-registration-transition.yml / "
                         "python scripts/canonical_task_registration_transition.py plan"),
    "owning_existing_goal": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
    "next_attempt": "on the next registration request event after the repair is recorded",
}


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class GovernanceProductGoalRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = load(REQUEST)

    def test_request_is_new_identity_and_makes_no_registry_edit(self) -> None:
        self.assertEqual(self.request["registration_mode"], "NEW_IDENTITY")
        self.assertEqual(self.request["task_id"], TASK_ID)
        self.assertEqual(self.request["authority_effect"], "NONE_REGISTRATION_ONLY")
        self.assertEqual(self.request["record"]["coordination_state"], "PROPOSED")
        self.assertNotIn("cosv_task_vector", self.request["record"])
        registry = load("data/canonical-task-registry.json")
        self.assertNotIn(TASK_ID, {row.get("task_id") for row in registry["tasks"]})
        self.assertEqual(self.request["observed_registry_generation"], registry.get("generation", registry.get("registry_generation")))
        self.assertFalse((ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json").exists())
        self.assertFalse((ROOT / "control" / "goal-scope-seals" / f"{TASK_ID}.json").exists())

    def test_scope_is_sealed_with_a_testable_finish_point(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import goal_scope_seal
        body = goal_scope_seal.validate_sealed_scope(self.request["sealed_scope"], TASK_ID, self.request["record"], new_identity=True)
        self.assertEqual(body["scope_digest"], SCOPE_DIGEST)
        self.assertEqual(body["authority_effect"], "NONE_SCOPE_SEAL_ONLY")
        finish = self.request["sealed_scope"]["scope"]["finish_point"]
        self.assertEqual(finish["lowest_supported_mode"], "E0")

    def test_allocation_request_binds_the_same_digest_without_a_vector(self) -> None:
        allocation = load(self.request["allocation_request_ref"])
        self.assertTrue(self.request["allocation_request_ref"].startswith("control/goal-task-allocation-requests/"))
        self.assertEqual(allocation["schema"], "stegverse.goal-task-allocation-request/v0.1")
        self.assertEqual(allocation["proposed_task_id"], TASK_ID)
        self.assertEqual(allocation["proposed_task_id_authority"], "NONE_PROPOSAL_ONLY")
        self.assertIsNone(allocation["cosv_task_vector"])
        self.assertEqual(allocation["scope_digest"], SCOPE_DIGEST)

    def test_adjacency_test_folds_overlap_and_records_consumes_dependencies(self) -> None:
        adjacency = load(ADJACENCY)
        record = self.request["record"]
        components = set(record["targets"]["components"])
        consumes = {d["ref"] for d in record["dependencies"] if d["dependency_id"].startswith("CONSUMES-")}
        registry = {row["task_id"]: row for row in load("data/canonical-task-registry.json")["tasks"]}
        for task_id, result in adjacency["results"].items():
            adjacent = all(result[k] for k in ("a_components_disjoint", "b_finish_point_exercises_none",
                                                "c_reliance_is_consumes_dependency"))
            self.assertEqual(result["outcome"], "ADJACENT" if adjacent else "NOT_ADJACENT_OVERLAP_FOLDED", task_id)
            shard = ROOT / "data" / "canonical-task-records" / f"{task_id}.json"
            other = json.loads(shard.read_text(encoding="utf-8")) if shard.exists() else registry[task_id]
            self.assertFalse(components & set((other.get("targets") or {}).get("components") or []), task_id)
            if adjacent:
                self.assertIn(task_id, record["adjacent_task_refs"])
            else:
                self.assertNotIn(task_id, record["adjacent_task_refs"])
                self.assertIn(task_id, consumes)
        for folded in ("sdk-reusable-governance-gate-workflow", "tier-pricing-candidate"):
            self.assertNotIn(folded, components)
        finish = self.request["sealed_scope"]["scope"]["finish_point"]
        self.assertNotIn("test_governance_gate.py", finish["acceptance_test"])
        self.assertTrue(any(ADJACENCY in line for line in self.request["collision_analysis"]))

    def test_plan_resolves_to_the_recorded_six_field_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "receipt.json"
            subprocess.run([sys.executable, str(SCRIPT), "plan", "--request", str(ROOT / REQUEST), "--receipt-out", str(out)],
                           cwd=ROOT, capture_output=True, text=True, check=False)
            receipt = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(receipt["mode"], "plan")
        for key, value in EXPECTED_PLAN.items():
            self.assertEqual(receipt[key], value, key)
        for flag in ("consequence_committed", "organization_ledger_appended", "execution_authority_minted",
                     "workercoordinator_claim_or_fence_minted", "intr_admission_minted", "clock_read"):
            self.assertFalse(receipt[flag], flag)


if __name__ == "__main__":
    unittest.main()
