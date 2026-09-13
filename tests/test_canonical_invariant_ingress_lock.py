import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "canonical-policy-context-registry.json"
LOCK_HANDOFF = ROOT / "docs" / "CANONICAL_INVARIANT_INGRESS_LOCK_MIRROR_HANDOFF.md"
MODEL = ROOT / "data" / "reusable-task-component-model.json"


class CanonicalInvariantIngressLockTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_lock_applies_before_interpretation_and_mutation(self):
        scope = self.registry["ingress_scope"]
        self.assertTrue(scope["must_resolve_before_local_interpretation"])
        self.assertTrue(scope["must_resolve_before_source_mutation"])
        self.assertTrue(scope["must_resolve_before_new_task_or_component_creation"])
        self.assertIn("NEW_SESSION_ENTRY", scope["applies_to"])
        self.assertIn("TASK_OR_COSV_CONTINUATION", scope["applies_to"])
        self.assertIn("SOURCE_MUTATION_PROPOSAL", scope["applies_to"])

    def test_required_global_sources_include_lock_and_component_model(self):
        refs = {row["ref"] for row in self.registry["required_global_sources"] if row.get("required")}
        self.assertIn("docs/CANONICAL_INVARIANT_INGRESS_LOCK_MIRROR_HANDOFF.md", refs)
        self.assertIn("data/reusable-task-component-model.json", refs)
        self.assertTrue(LOCK_HANDOFF.is_file())
        self.assertTrue(MODEL.is_file())

    def test_invariant_restatement_cannot_become_new_work(self):
        lock = self.registry["canonical_invariant_lock"]
        self.assertTrue(lock["canonical_source_precedes_local_reasoning"])
        self.assertTrue(lock["conflicting_local_interpretation_is_invalid"])
        self.assertTrue(lock["existing_canonical_invariant_must_be_reused_not_recreated"])
        self.assertTrue(lock["restatement_of_existing_invariant_is_not_new_work"])
        self.assertTrue(lock["restatement_alone_must_not_create_pr_task_component_handoff_or_policy_artifact"])
        self.assertTrue(lock["human_correction_matching_existing_canonical_truth_requires_no_source_mutation"])

    def test_new_role_requires_absence_proof(self):
        lock = self.registry["canonical_invariant_lock"]
        self.assertTrue(lock["new_role_authority_identity_class_or_execution_owner_requires_proof_canonical_model_lacks_equivalent"])

    def test_device_and_verifier_invariants_resolve_from_component_model(self):
        model = json.loads(MODEL.read_text(encoding="utf-8"))
        invariants = model["composition_invariants"]
        self.assertEqual(invariants["stegos_device_role"], "INTERCHANGEABLE_TRANSPORT_NODE")
        self.assertEqual(invariants["user_verification"], "KV/SKAP Vault")


if __name__ == "__main__":
    unittest.main()
