#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
PARENT_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-entity-autonomous-governed-progression-runtime-adoption-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
TASK_SHARD = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"
HANDOFF = ROOT / "docs" / "ENTITY_AUTONOMOUS_GOVERNED_PROGRESSION_RUNTIME_ADOPTION_MIRROR_HANDOFF.md"


class EntityAutonomousProgressionCanonicalWorkIngressTests(unittest.TestCase):
    def test_request_reuses_existing_canonical_work_path_without_authority(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], "RESIDENT-EXEC-CANONICAL-WORK-ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001")
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["entrypoint"], "scripts/install_and_run_canonical_work_event_bootstrap.py")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["second_machine_required"])

    def test_task_shard_preserves_existing_goal_and_runtime_boundaries(self):
        task = json.loads(TASK_SHARD.read_text(encoding="utf-8"))
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["root_correlation_id"], PARENT_GOAL)
        self.assertEqual(task["parent_task_id"], PARENT_GOAL)
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertEqual(task["checkout_state"], "CHECKED_OUT")
        self.assertIn("INGRESS_ADMITTED", task["allowed_next_transitions"])
        self.assertFalse(task["authority_model"]["task_registry_mints_execution_authority"])
        self.assertTrue(task["authority_model"]["interlock_intr_required_for_governed_ingress_egress"])
        self.assertEqual(task["authority_model"]["credential_authority"], "TV/TVC")
        self.assertEqual(task["authority_model"]["github_runtime_authority"], "NONE")
        self.assertFalse(task["authority_model"]["human_reentry_required_for_machine_owned_continuation"])

    def test_runtime_routing_metadata_matches_canonical_work_profile(self):
        task = json.loads(TASK_SHARD.read_text(encoding="utf-8"))
        runtime_map = json.loads((ROOT / "control" / "runtime-profile-map.json").read_text(encoding="utf-8"))
        profile = next(row for row in runtime_map["profiles"] if row["profile_id"] == "canonical-work-coordination-runtime-v1")
        requirements = task["runtime_requirements"]
        self.assertEqual(requirements["environment"], "SOVEREIGN_RESIDENT")
        self.assertEqual(requirements["direction"], "INTERNAL")
        self.assertTrue(requirements["mutation_required"])
        self.assertFalse(requirements["deployment_required"])
        self.assertFalse(requirements["current_observation_required"])
        self.assertTrue(set(requirements["capabilities"]).issubset(set(profile["declared"]["capabilities"])))
        self.assertIn(requirements["environment"], profile["declared"]["environment_classes"])
        self.assertIn(requirements["direction"], profile["declared"]["directions"])
        self.assertTrue(profile["declared"]["mutation_allowed"])
        self.assertIsNone(task["runtime_resolution"])
        runtime_adoption_dep = next(row for row in task["dependencies"] if row["dependency_id"] == "DEP-ENTITY-AUTONOMOUS-PROGRESSION-RUNTIME-ADOPTION")
        self.assertEqual(runtime_adoption_dep["kind"], "RUNTIME_PREDICATE")
        self.assertIn("CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED", task["expected_evidence_predicates"])
        self.assertIn("CURRENT_GOVERNANCE_DECISION_OBSERVED", task["expected_evidence_predicates"])
        self.assertIn("EXECUTION_OR_DENIAL_RECEIPT_RETAINED", task["expected_evidence_predicates"])
        self.assertIn("NEXT_STATE_RECONSTRUCTED", task["expected_evidence_predicates"])

    def test_existing_generalized_consumer_visits_autonomous_progression_request(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("AUTONOMOUS_PROGRESSION_SPEC", consumer)
        self.assertIn("canonical-work-entity-autonomous-governed-progression-runtime-adoption-001.json", consumer)
        self.assertIn("canonical-work-entity-autonomous-governed-progression-runtime-adoption-request-consumption.latest.json", consumer)
        self.assertIn(f'"task_id": "{TASK_ID}"', consumer)
        self.assertIn("AUTONOMOUS_PROGRESSION_SPEC,", consumer)
        self.assertIn('"later_request_attempts_blocked_by_earlier_failure": False', consumer)
        self.assertIn('"second_machine_required": False', consumer)
        self.assertIn('"claim_or_fence_minted": False', consumer)

    def test_handoff_states_runtime_adoption_predicates_and_nonclaims(self):
        handoff = HANDOFF.read_text(encoding="utf-8")
        for predicate in (
            "machine_owned_transition_selected=true",
            "current_governance_decision_observed=true",
            "human_approval_checkpoint_inserted=false",
            "execution_or_denial_receipt_retained=true",
            "next_state_reconstructed=true",
            "returned_task_cosv_handoff_state_reingested=true",
            "human_reentry_for_intermediate_ids=false",
        ):
            self.assertIn(predicate, handoff)
        self.assertIn("no second scheduler", handoff)
        self.assertIn("no connected-device discovery prerequisite", handoff)
        self.assertIn("source/CI/merge proves runtime execution", handoff)


if __name__ == "__main__":
    unittest.main()
