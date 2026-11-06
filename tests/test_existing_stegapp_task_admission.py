"""Existing-record StegApp admission must never create authority or change state."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "evaluate_existing_task_admission.py"
spec = importlib.util.spec_from_file_location("stegapp_existing_admission", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ExistingStegAppAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "task_id": mod.TASK_ID,
            "correlation_id": mod.TASK_ID,
            "root_correlation_id": mod.TASK_ID,
            "parent_task_id": None,
            "goal": "StegApp composition",
            "source_refs": ["StegVerse-Labs/.github#3291"],
            "targets": {"repositories": ["StegVerse-Labs/StegApp"]},
            "dependencies": [], "blockers": [],
            "expected_evidence_predicates": ["AUTHENTIC_MANIFEST_BOUND_DISPOSITION"],
            "worker_claim": {"claim_ref": None, "fence_ref": None,
                             "projection_only": True},
            "coordination_state": "PROPOSED",
            "allowed_next_transitions": ["INGRESS_ADMITTED"],
        }
        self.registry = {"generation": 320, "tasks": [self.row]}
        self.shard = {k: copy.deepcopy(v) for k, v in self.row.items()
                      if k != "cosv_task_vector"}
        self.vector = {"schema": "stegverse.cosv-task-vector/v0.1",
                       "identity": "StegVerse-Labs/.github:task:" + mod.TASK_ID,
                       "profile": "task.v1", "level": "task",
                       "vector": "10300000011000",
                       "authority_effect": "NONE",
                       "exact_metrics": {"lifecycle": "UNCLAIMED"}}
        self.decision = dict(task_id=mod.TASK_ID, from_state="PROPOSED",
                             to_state="INGRESS_ADMITTED", observed_registry_generation=320,
                             next_registry_generation=321,
                             previous_task_sha256=mod._hash(self.row),
                             cosv="10300000011000", claim_or_fence_minted=False,
                             disposition="ALLOW",
                             organization_receipt_sha256="sha256:" + "a"*64)
        self.native = lambda _: dict(
            disposition="ALLOW", original_manifest_bound=True,
            task_id=mod.TASK_ID,
            organization_receipt_sha256=self.decision["organization_receipt_sha256"])

    def verdict(self, decision=None, verifier=None):
        return mod.evaluate(self.registry, self.shard, self.vector,
                            self.decision if decision is None else decision,
                            self.native if verifier is None else verifier)

    def test_native_original_decision_only_preflight_not_worker_authority(self):
        before = copy.deepcopy((self.registry, self.shard, self.vector, self.decision))
        out = self.verdict()
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertEqual(out["authority_effect"], "NONE_PREFLIGHT_ONLY")
        self.assertFalse(out["state_written"])
        self.assertFalse(out["claim_or_fence_minted"])
        self.assertTrue(out["native_workercoordinator_claim_required"])
        self.assertEqual(before, (self.registry, self.shard, self.vector, self.decision))

    def test_missing_original_receipt_fails_closed(self):
        for receipt in ({}, {"disposition": "ALLOW"}, None):
            with self.subTest(receipt=receipt):
                outcome = mod.evaluate(self.registry, self.shard, self.vector,
                                       receipt, self.native)
                self.assertEqual(outcome["disposition"], "FAIL_CLOSED")
                self.assertFalse(outcome["state_written"])
                self.assertFalse(outcome["claim_or_fence_minted"])
                for key in ("failure_code", "failed_predicate",
                            "required_evidence_or_repair", "retry_entrypoint",
                            "owning_existing_goal", "next_attempt"):
                    self.assertTrue(outcome.get(key), key)

    def test_no_native_verifier_is_never_allow(self):
        outcome = mod.evaluate(self.registry, self.shard, self.vector,
                               self.decision, None)
        self.assertEqual(outcome["disposition"], "FAIL_CLOSED")

    def test_forged_or_incomplete_native_verification_fails_closed(self):
        for result in ({}, {"disposition": "ALLOW"}, {
                "disposition": "ALLOW", "original_manifest_bound": True,
                "task_id": mod.TASK_ID, "organization_receipt_sha256":
                    "sha256:" + "f"*64}):
            self.assertEqual(self.verdict(verifier=lambda _: result)["disposition"],
                             "FAIL_CLOSED")

    def test_existing_record_not_treated_as_duplicate_new_registration(self):
        self.assertEqual(self.verdict()["disposition"], "ALLOW")
        self.registry["tasks"].append(copy.deepcopy(self.row))
        self.assertEqual(self.verdict()["failed_predicate"],
                         "EXACTLY_ONE_CANONICAL_EXISTING_TASK")

    def test_generation_and_state_edges_cannot_drift(self):
        self.decision["observed_registry_generation"] = 319
        self.assertEqual(self.verdict()["failed_predicate"],
                         "OWNER_DECISION_EXACT_PREDECESSOR_AND_COSV")
        self.decision["observed_registry_generation"] = 320
        self.registry["generation"] = 321
        self.assertEqual(self.verdict()["disposition"], "FAIL_CLOSED")
        self.registry["generation"] = 320
        self.shard["coordination_state"] = "INGRESS_ADMITTED"
        self.assertEqual(self.verdict()["failed_predicate"], "ORIGINAL_STATE_PROPOSED")

    def test_scope_cosv_and_worker_claim_not_synthetically_accepted(self):
        self.shard["targets"] = {"repositories": ["unrelated/owner"]}
        self.assertEqual(self.verdict()["failed_predicate"],
                         "EXISTING_TASK_IDENTITY_AND_SCOPE_AGREE")
        self.shard["targets"] = copy.deepcopy(self.row["targets"])
        self.vector["vector"] = "10300000011001"
        self.assertEqual(self.verdict()["failed_predicate"], "CANONICAL_COSV_UNCHANGED")
        self.vector["vector"] = "10300000011000"
        self.shard["worker_claim"]["claim_ref"] = "synthetic"
        self.assertEqual(self.verdict()["failed_predicate"],
                         "NO_SYNTHETIC_WORKER_CLAIM_OR_FENCE")

    def test_actual_registered_task_shape_does_not_embed_cosv_field(self):
        self.assertNotIn("cosv_task_vector", self.row)
        self.assertNotIn("cosv_task_vector", self.shard)
        self.assertEqual(self.verdict()["disposition"], "ALLOW")
        self.vector["identity"] = "StegVerse-Labs/.github:task:ANOTHER-TASK"
        self.assertEqual(self.verdict()["failed_predicate"], "CANONICAL_COSV_UNCHANGED")

    def test_malformed_sovereign_digest_is_not_original_owner_receipt(self):
        for bogus in ("sha256:", "sha256:bad", "sha256:" + "g"*64,
                      "sha256:" + "A"*64, "invalid"):
            with self.subTest(bogus=bogus):
                fake = copy.deepcopy(self.decision)
                fake["organization_receipt_sha256"] = bogus
                result = self.verdict(decision=fake)
                self.assertEqual(result["disposition"], "FAIL_CLOSED")
                self.assertEqual(result["failed_predicate"],
                                 "OWNER_ALLOW_AND_SOVEREIGN_RECORDING_PRESENT")

    def test_edge_is_the_schema_edge_proposed_to_ingress_admitted(self):
        # #3304 review finding 1: HANDOFF_READY is not in the coordination_state enum
        schema = json.loads((ROOT / "schemas" / "canonical-task-record.schema.json")
                            .read_text(encoding="utf-8"))
        states = schema["properties"]["coordination_state"]["enum"]
        out = self.verdict()
        self.assertEqual(out["disposition"], "ALLOW")
        self.assertIn(out["next_state"], states)
        self.assertEqual(out["next_state"], "INGRESS_ADMITTED")
        stale = copy.deepcopy(self.decision)
        stale["to_state"] = "HANDOFF_READY"
        self.assertEqual(self.verdict(decision=stale)["failed_predicate"],
                         "OWNER_DECISION_EXACT_PREDECESSOR_AND_COSV")

    def test_edge_must_be_in_allowed_next_transitions(self):
        for allowed in (None, [], ["NATIVE_ADMISSION_EVALUATION"], "INGRESS_ADMITTED"):
            with self.subTest(allowed=allowed):
                self.shard["allowed_next_transitions"] = allowed
                self.row["allowed_next_transitions"] = allowed
                out = self.verdict()
                self.assertEqual(out["disposition"], "FAIL_CLOSED")
                self.assertEqual(out["failed_predicate"],
                                 "INGRESS_ADMITTED_IN_ALLOWED_NEXT_TRANSITIONS")

    def test_digest_without_sha256_prefix_is_refused(self):
        # #3304 review finding 2: length 71 and hex tail are not enough
        for bogus in ("md5:XYZ" + "a"*64, "SHA256:" + "a"*64, "sha512:" + "a"*64,
                      "sha256:" + "a"*64 + "\n"):
            with self.subTest(bogus=bogus):
                fake = copy.deepcopy(self.decision)
                fake["organization_receipt_sha256"] = bogus
                echo = lambda _, b=bogus: dict(
                    disposition="ALLOW", original_manifest_bound=True,
                    task_id=mod.TASK_ID, organization_receipt_sha256=b)
                result = self.verdict(decision=fake, verifier=echo)
                self.assertEqual(result["disposition"], "FAIL_CLOSED")
                self.assertEqual(result["failed_predicate"],
                                 "OWNER_ALLOW_AND_SOVEREIGN_RECORDING_PRESENT")

    def test_owner_claim_cannot_be_minted_with_admission(self):
        forged = copy.deepcopy(self.decision)
        forged["claim_or_fence_minted"] = True
        self.assertEqual(self.verdict(decision=forged)["disposition"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
