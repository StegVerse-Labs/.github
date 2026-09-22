import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_task_registry_canonical_work_cycle.py"
spec = importlib.util.spec_from_file_location("registry_cycle", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def record(task_id, *, checkout="CHECKED_OUT", state="PROPOSED", human_action=None, root_goal=None, goal=None, priority=None):
    row = {
        "schema": "stegverse.canonical-task-record/v1",
        "task_id": task_id,
        "correlation_id": task_id,
        "root_correlation_id": root_goal or task_id,
        "goal": goal or "ordinary goal work",
        "coordination_state": state,
        "checkout_state": checkout,
        "allowed_next_transitions": ["INGRESS_ADMITTED"],
        "human_action_ref": human_action,
        "runtime_requirements": {"capabilities": ["canonical_work_ingress"]},
        "worker_claim": {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
        "authority_model": {"task_registry_mints_execution_authority": False, "interlock_intr_required_for_governed_ingress_egress": True},
    }
    if priority is not None:
        row["work_priority_class"] = priority
    return row


def write_registry(path: Path, rows):
    path.write_text(json.dumps({"schema": "stegverse.canonical-task-registry/v1", "tasks": rows}), encoding="utf-8")


class TaskRegistryFirstCanonicalWorkCycleTests(unittest.TestCase):
    def test_candidate_requires_machine_ingress_contract(self):
        self.assertTrue(module.machine_ingress_candidate(record("A-001")))
        self.assertTrue(module.machine_ingress_candidate(record("A-001", state="ACTIVE", checkout="CHECKED_OUT")))
        self.assertFalse(module.machine_ingress_candidate(record("A-001", state="ACTIVE", checkout="UNCLAIMED")))
        self.assertFalse(module.machine_ingress_candidate(record("A-001", state="INGRESS_ADMITTED")))
        self.assertFalse(module.machine_ingress_candidate(record("A-001", human_action="USER_ONLY")))

    def test_progression_controller_is_not_selected_as_product_work(self):
        self.assertFalse(module.machine_ingress_candidate(record(module.PROGRESSION_CONTROLLER_TASK_ID)))

    def test_explicit_current_goal_is_not_controller_lineage(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp)
            controller = {
                "task_id": module.PROGRESSION_CONTROLLER_TASK_ID,
                "root_correlation_id": "CONTROLLER-LINEAGE-GOAL",
                "latest_goal_task_block_header": {
                    "goal_task_id": "CONTROLLER-LINEAGE-GOAL",
                    "handoff_task_id": "docs/CONTROLLER_MIRROR_HANDOFF.md",
                    "cosv_id": "10100000100000",
                    "session_prompt_count": 1,
                    "goal_prompt_count": "1/20",
                },
                "goal_completion_notification": {
                    "credential_authority": "TV/TVC",
                    "summary_included": False,
                    "manual_work_included": False,
                },
            }
            (records / f"{module.PROGRESSION_CONTROLLER_TASK_ID}.json").write_text(
                json.dumps(controller), encoding="utf-8"
            )
            goal_id, header, _, lineage = module.progression_context("HYGIENE-CAUSAL-ROOTS-001", records)
            self.assertEqual(goal_id, "HYGIENE-CAUSAL-ROOTS-001")
            self.assertEqual(lineage, "CONTROLLER-LINEAGE-GOAL")
            self.assertIsNone(header)

    def test_registry_only_task_is_discoverable_without_shard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [record("REGISTRY-ONLY-001", root_goal="GOAL-A")])
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual([r["task_id"] for r in rows], ["REGISTRY-ONLY-001"])

    def test_shard_only_task_is_not_work_discovery_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [record("A-001", root_goal="GOAL-A")])
            (records / "GHOST-001.json").write_text(json.dumps(record("GHOST-001", root_goal="GOAL-A")), encoding="utf-8")
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual([r["task_id"] for r in rows], ["A-001"])

    def test_shard_cannot_override_registry_coordination_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [record("A-001", state="INGRESS_ADMITTED", root_goal="GOAL-A")])
            (records / "A-001.json").write_text(json.dumps(record("A-001", state="PROPOSED", root_goal="GOAL-A")), encoding="utf-8")
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual(rows, [])

    def test_shard_may_enrich_missing_noncanonical_projection_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            registry_row = record("A-001", root_goal="GOAL-A")
            registry_row.pop("checkout_state")
            write_registry(registry, [registry_row])
            (records / "A-001.json").write_text(json.dumps(record("A-001", checkout="CHECKED_OUT", root_goal="GOAL-A")), encoding="utf-8")
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual(rows[0]["checkout_state"], "CHECKED_OUT")

    def test_repair_work_precedes_ordinary_checked_out_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [
                record("A-FEATURE-001", checkout="CHECKED_OUT", root_goal="GOAL-A", goal="add a new feature"),
                record("Z-REPAIR-001", checkout="UNCLAIMED", root_goal="GOAL-A", goal="repair ecosystem state"),
            ])
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual([r["task_id"] for r in rows], ["Z-REPAIR-001", "A-FEATURE-001"])

    def test_explicit_canonicalization_priority_class_precedes_ordinary_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [
                record("A-ORDINARY-001", root_goal="GOAL-A"),
                record("Z-NORMALIZE-001", checkout="UNCLAIMED", root_goal="GOAL-A", priority="ECOSYSTEM_CANONICALIZATION"),
            ])
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual([r["task_id"] for r in rows], ["Z-NORMALIZE-001", "A-ORDINARY-001"])

    def test_generic_canonical_word_does_not_make_ordinary_work_repair_priority(self):
        ordinary = record("CANONICAL-WORK-FEATURE-001", goal="use canonical work for a new product capability")
        self.assertEqual(module.ecosystem_priority_class(ordinary), "ORDINARY_GOAL_WORK")

    def test_excluded_task_is_absent_from_sorted_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [record("A-001", root_goal="GOAL-A"), record("B-001", root_goal="GOAL-A")])
            rows = module.load_candidates(records, {"A-001"}, "GOAL-A", registry)
            self.assertEqual([r["task_id"] for r in rows], ["B-001"])

    def test_goal_scope_excludes_other_root_goals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [record("A-001", root_goal="GOAL-A"), record("B-001", root_goal="GOAL-B")])
            rows = module.load_candidates(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual([r["task_id"] for r in rows], ["A-001"])

    def test_selection_skips_collision_and_uses_existing_continue_disposition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "records"
            records.mkdir()
            registry = root / "registry.json"
            write_registry(registry, [record("A-001", root_goal="GOAL-A"), record("B-001", root_goal="GOAL-A")])
            dispositions = {
                "A-001": {"schema": "stegverse.task-registry-checkin-disposition/v1", "task_id": "A-001", "disposition": "STOP_COLLISION", "authority_effect": "NONE"},
                "B-001": {"schema": "stegverse.task-registry-checkin-disposition/v1", "task_id": "B-001", "disposition": "CONTINUE", "authority_effect": "NONE"},
            }
            with mock.patch.object(module, "collision_check", side_effect=lambda task_id: dispositions[task_id]):
                selected, considered = module.select_task(records, goal_task_id="GOAL-A", registry_path=registry)
            self.assertEqual(selected["task_id"], "B-001")
            self.assertEqual([row["disposition"] for row in considered], ["STOP_COLLISION", "CONTINUE"])

    def test_goal_completion_requires_claimed_and_validated(self):
        self.assertTrue(module.goal_completion_validated({"completion": {"claimed": True, "validated": True}}))
        self.assertFalse(module.goal_completion_validated({"completion": {"claimed": True, "validated": False}}))
        self.assertFalse(module.goal_completion_validated({"completion": {"claimed": False, "validated": True}}))

    def test_completion_notice_contains_only_task_block_header_before_summary(self):
        header = {
            "goal_task_id": "GOAL-001",
            "handoff_task_id": "docs/GOAL_MIRROR_HANDOFF.md",
            "cosv_id": "10100000100000",
            "session_prompt_count": 6,
            "goal_prompt_count": "6/20",
            "status": "ACTIVE",
        }
        notification = {
            "notification_repository": "StegVerse-Labs/.github",
            "notification_assignee": "StegVerse",
            "summary_included": False,
            "manual_work_included": False,
            "credential_authority": "TV/TVC",
            "email_delivery": "GITHUB_NOTIFICATION_EMAIL_SUBJECT_TO_ACCOUNT_NOTIFICATION_SETTINGS",
        }
        request = module.build_completion_notification_request(
            "GOAL-001", header, notification,
            {"task_id": "GOAL-001", "coordination_state": "COMPLETED", "completion": {"claimed": True, "validated": True}},
        )
        self.assertEqual(request["body_line_count"], 6)
        self.assertNotIn("Summary of work", request["body"])
        self.assertNotIn("Manual Work", request["body"])
        self.assertTrue(request["stop_autonomous_progression"])
        self.assertFalse(request["select_successor_before_notification"])

    def test_active_checked_out_independent_task_routes_to_existing_workercoordinator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fragments = root / "worker-registry.d"
            fragments.mkdir()
            task_id = "STATE-DEPENDENT-WORK-001"
            (fragments / "state-dependent-work-001.json").write_text(json.dumps({
                "schema": "stegverse.worker-registry-fragment/v0.1",
                "fragment_id": task_id,
                "tasks": [{
                    "task_id": task_id,
                    "state": "HANDOFF_READY",
                    "claim_id": None,
                    "worker_id": None,
                    "worker_instance_id": None,
                    "admission": {
                        "authority_domain": "INDEPENDENT_TASK_CONTROL",
                        "claim_state": "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
                        "carrier_trigger_required": False,
                    },
                }],
                "workers": [],
            }), encoding="utf-8")
            row = record(task_id, state="ACTIVE", checkout="CHECKED_OUT")
            row["allowed_next_transitions"] = []
            self.assertTrue(module.workercoordinator_target_candidate(row, fragments))

    def test_ingress_admitted_edge_remains_on_existing_canonical_work_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fragments = root / "worker-registry.d"
            fragments.mkdir()
            task_id = "INGRESS-FIRST-WORK-001"
            (fragments / "ingress-first-work-001.json").write_text(json.dumps({
                "schema": "stegverse.worker-registry-fragment/v0.1",
                "fragment_id": task_id,
                "tasks": [{
                    "task_id": task_id,
                    "state": "HANDOFF_READY",
                    "claim_id": None,
                    "worker_id": None,
                    "worker_instance_id": None,
                    "admission": {
                        "authority_domain": "INDEPENDENT_TASK_CONTROL",
                        "claim_state": "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
                        "carrier_trigger_required": False,
                    },
                }],
                "workers": [],
            }), encoding="utf-8")
            row = record(task_id, state="ACTIVE", checkout="CHECKED_OUT")
            self.assertFalse(module.workercoordinator_target_candidate(row, fragments))
            self.assertTrue(module.machine_ingress_candidate(row))

    def test_workercoordinator_state_transition_requires_existing_admission_not_hb(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fragments = root / "worker-registry.d"
            fragments.mkdir()
            task_id = "STATE-DEPENDENT-WORK-001"
            base = {
                "schema": "stegverse.worker-registry-fragment/v0.1",
                "fragment_id": task_id,
                "tasks": [{
                    "task_id": task_id,
                    "state": "HANDOFF_READY",
                    "claim_id": None,
                    "worker_id": None,
                    "worker_instance_id": None,
                    "admission": {
                        "authority_domain": "INDEPENDENT_TASK_CONTROL",
                        "claim_state": "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
                        "carrier_trigger_required": True,
                    },
                }],
                "workers": [],
            }
            (fragments / "state-dependent-work-001.json").write_text(json.dumps(base), encoding="utf-8")
            row = record(task_id, state="ACTIVE", checkout="CHECKED_OUT")
            row["allowed_next_transitions"] = []
            self.assertFalse(module.workercoordinator_target_candidate(row, fragments))

    def test_state_dependent_delegation_reuses_existing_targeted_worker_runtime(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('WORKER_RUNTIME = ROOT / "scripts" / "run_worker_runtime.py"', text)
        self.assertIn('"WORKERCOORDINATOR_TARGETED_STATE_TRANSITION"', text)
        self.assertIn('str(WORKER_RUNTIME)', text)
        self.assertIn('"--task-id"', text)
        self.assertNotIn("new WorkerCoordinator", text)

    def test_selection_does_not_mint_claim_or_transition_authority(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"workercoordinator_claim_or_fence_minted": False', text)
        self.assertIn('"interlock_intr_transition_authority_preserved": True', text)
        self.assertIn('"task_registry_mints_execution_authority": False', text)
        self.assertIn('CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"', text)
        self.assertIn('"candidate_identity_source": "CANONICAL_TASK_REGISTRY"', text)
        self.assertIn('parser.add_argument("--goal-task-id")', text)
        self.assertIn('"progression_controller_lineage_goal_id": controller_lineage_goal_id', text)


if __name__ == "__main__":
    unittest.main()
