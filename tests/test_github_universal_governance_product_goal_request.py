"""Lane C (C): GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001 NEW_IDENTITY request, sealed scope and recorded plan outcome.

The request is a fixture (outside control/canonical-task-registration-requests/), so a
merge applies nothing. The test pins: GOAL_SCOPE_SEALED holds (digest, record equality,
testable finish point), the allocation request binds the same digest with no vector,
and plan resolves to the recorded six-field outcome with no consequence. Lowest
supported mode: E0 (stdlib, committed files, no clock, no network).
"""
from __future__ import annotations

import importlib.util
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
FINISH_TEST = ("StegVerse-org/StegVerse-SDK:tests/test_governance_product_finish_point.py"
               "::GovernanceProductFinishPoint::test_finish_point_verdict")
FINISH_COMMIT = "233d16231d979c5f8baebab5200a0bfdfd511ecb"
RULING = "control/adjacency-rulings/GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001.json"
SCOPE_DIGEST = "sha256:088e015129029da435954109c6089b180e951d6196853764b71a0bcc4bbe2441"
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
        self.assertEqual(finish["acceptance_test"], FINISH_TEST)
        self.assertEqual(finish["source_commit"], FINISH_COMMIT)
        self.assertTrue(any(ADJACENCY in line for line in self.request["collision_analysis"]))

    def test_adjacency_ruling_input_is_consistent_with_the_sealed_scope(self) -> None:
        """E0 consistency only; conditions a/b/c are recomputed by the workflow's ruling step at the pinned SDK commit."""
        spec = importlib.util.spec_from_file_location("adjacency_ruling_under_test", ROOT / "scripts" / "adjacency_ruling.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ruling = json.loads((ROOT / RULING).read_text(encoding="utf-8"))
        self.assertEqual(ruling["evidence_digest"], module.ruling_digest(ruling))
        self.assertIsNotNone(module.ADDRESSABLE.match(FINISH_TEST))
        fp = ruling["subject"]["finish_point"]
        self.assertEqual((fp["acceptance_test"], fp["repository"], fp["source_commit"]),
                         (FINISH_TEST, "StegVerse-org/StegVerse-SDK", FINISH_COMMIT))
        record = self.request["record"]
        self.assertEqual(sorted(ruling["subject"]["components"]), sorted(record["targets"]["components"]))
        deps = {d["ref"] for d in record["dependencies"] if d["kind"] == "TASK"}
        cands = {c["task_id"] for c in ruling["candidates"]}
        for dep in ruling["consumes_dependencies"]:
            self.assertIn(dep["task_id"], deps)
            self.assertIn(dep["task_id"], cands)
        for cand in ruling["candidates"]:
            observed = json.loads((ROOT / "data" / "canonical-task-records" / f"{cand['task_id']}.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(cand["components"]), sorted((observed.get("targets") or {}).get("components") or []))
        self.assertIn("UNKNOWN_NOT_AUTHENTICALLY_OBSERVED", ruling["ruled_by"])

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
