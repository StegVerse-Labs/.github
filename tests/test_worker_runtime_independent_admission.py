from __future__ import annotations

import inspect
import json
import tempfile
import unittest

from heartbeat_runtime.worker_runtime import WorkerCoordinator
from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator as LegacyWorkerCoordinator
from pathlib import Path


class WorkerRuntimeIndependentAdmissionTests(unittest.TestCase):
    def test_independent_task_control_path_does_not_require_carrier_packet(self):
        source = inspect.getsource(WorkerCoordinator._activate_independently_admitted_tasks)
        self.assertIn('"INDEPENDENT_TASK_CONTROL"', source)
        self.assertIn('"AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"', source)
        self.assertIn("independent_task_control_packet", source)
        self.assertNotIn("_trigger_packets", source)
        self.assertNotIn("carrier_event_path", source)

    def test_cycle_attempts_independent_admission_before_compatibility_packets(self):
        source = inspect.getsource(WorkerCoordinator.cycle)
        independent = source.index("_activate_independently_admitted_tasks")
        compatibility = source.index("_trigger_packets")
        self.assertLess(independent, compatibility)
        self.assertIn('"heartbeat_event_required_for_independent_task_control": False', source)
        self.assertIn('"carrier_epoch_advanced_by_worker_runtime": False', source)
        self.assertIn('"independent_task_control_activations": independent_activated', source)
        self.assertIn('"carrier_packet_activations": carrier_activated', source)

    def test_fresh_fence_floor_is_enforced_after_mandatory_admission_review(self):
        admitted_source = inspect.getsource(WorkerCoordinator._activate_from_trigger)
        self.assertIn("review_worker_task_admission", admitted_source)
        self.assertIn('verdict != "ADMIT"', admitted_source)
        self.assertIn("return super()._activate_from_trigger", admitted_source)

        legacy_source = inspect.getsource(LegacyWorkerCoordinator._activate_from_trigger)
        self.assertIn('minimum_fencing_token_exclusive', legacy_source)
        self.assertIn('generation = minimum_fence + 1', legacy_source)
        self.assertIn('source_admission_ref', legacy_source)
        self.assertIn('source_carrier_event_ref"] = None', legacy_source)
        self.assertIn('carrier_granted_authority=False', legacy_source)
        self.assertIn('worker_assignment_bound_from_independent_task_control', legacy_source)


    def test_targeted_independent_activation_selects_only_requested_task(self):
        runtime = LegacyWorkerCoordinator.__new__(LegacyWorkerCoordinator)
        observed = []

        def activate(registry, trigger, carrier_epoch, cost_log, events):
            observed.append(trigger["task_id"])
            return True

        runtime._activate_from_trigger = activate
        registry = {
            "tasks": [
                {
                    "task_id": "TASK-A",
                    "goal_id": "A",
                    "handoff_ref": "handoffs/a.json",
                    "state": "HANDOFF_READY",
                    "worker_id": None,
                    "claim_id": None,
                    "admission": {
                        "authority_domain": "INDEPENDENT_TASK_CONTROL",
                        "claim_state": "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
                    },
                },
                {
                    "task_id": "TASK-B",
                    "goal_id": "B",
                    "handoff_ref": "handoffs/b.json",
                    "state": "HANDOFF_READY",
                    "worker_id": None,
                    "claim_id": None,
                    "admission": {
                        "authority_domain": "INDEPENDENT_TASK_CONTROL",
                        "claim_state": "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
                    },
                },
            ]
        }
        count = runtime._activate_independently_admitted_tasks(
            registry, 31, {"records": []}, [], target_task_id="TASK-B"
        )
        self.assertEqual(count, 1)
        self.assertEqual(observed, ["TASK-B"])

    def test_targeted_cycle_suppresses_unrelated_execution_paths(self):
        source = inspect.getsource(LegacyWorkerCoordinator.cycle)
        self.assertIn("target_task_id: str | None = None", source)
        self.assertIn("task_id_filter=target_task_id", source)
        self.assertIn('packets = [] if targeted else self._trigger_packets', source)
        self.assertIn('reconciled = [] if targeted else self._reconcile_orphan_recovery_quarantines', source)
        self.assertIn('task.get("task_id") != target_task_id', source)
        self.assertIn('"unrelated_worker_execution_suppressed": targeted', source)
        self.assertIn('"carrier_packet_execution_suppressed": targeted', source)

    def test_targeted_cli_is_one_shot_and_cannot_bootstrap_g18(self):
        source = (Path(__file__).resolve().parents[1] / "scripts" / "run_worker_runtime.py").read_text()
        self.assertIn('parser.add_argument("--task-id"', source)
        self.assertIn("--task-id requires exactly one non-continuous worker-runtime cycle", source)
        self.assertIn("targeted independent execution requires an existing separated carrier reference", source)
        self.assertIn("target_task_id=args.task_id", source)
        self.assertIn("if not args.task_id and not args.dry_run and not (root / INITIAL_CARRIER_REL).is_file()", source)
        self.assertIn("if not args.task_id and not args.dry_run:", source)

    def test_targeted_registry_fragment_loading_is_task_scoped(self):
        from heartbeat_runtime.engine_v9 import HeartbeatRuntime as V9Runtime
        source = inspect.getsource(V9Runtime._apply_registry_fragments)
        self.assertIn("task_id_filter: str | None = None", source)
        self.assertIn("if task_id_filter not in declared_task_ids", source)
        self.assertIn("if task_id_filter is not None and task_id != task_id_filter", source)



    def test_cosv_task_record_passes_operational_preclaim_without_semantic_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vector_path = root / "control" / "task-vectors" / "TASK-COSV.json"
            vector_path.parent.mkdir(parents=True)
            vector_path.write_text(json.dumps({
                "identity": "StegVerse-Labs/.github:task:TASK-COSV",
                "profile": "task.v1",
                "level": "task",
                "vector": "50000000100000",
                "evidence_refs": ["test"],
                "observed_at": "2026-08-27T07:03:00-05:00",
                "exact_metrics": {},
            }), encoding="utf-8")
            runtime = LegacyWorkerCoordinator.__new__(LegacyWorkerCoordinator)
            runtime.root = root
            task = {
                "task_id": "TASK-COSV",
                "source_state_vector_ref": "control/task-vectors/TASK-COSV.json",
                "machine_readable_state": {
                    "cosv": {
                        "profile": "task.v1",
                        "notation": "L R U I V G O C M T B E A P",
                        "width": 14,
                        "vector": "50000000100000",
                        "vector_state": "EMITTED",
                        "authority_effect": "NONE",
                    }
                },
            }
            self.assertEqual(
                runtime._semantic_state_preclaim(task),
                (True, "CURRENT_OPERATIONAL_STATE_VECTOR_CONFIRMED"),
            )

    def test_cosv_task_record_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vector_path = root / "control" / "task-vectors" / "TASK-COSV.json"
            vector_path.parent.mkdir(parents=True)
            vector_path.write_text(json.dumps({
                "identity": "StegVerse-Labs/.github:task:TASK-COSV",
                "profile": "task.v1",
                "level": "task",
                "vector": "50000000100000",
                "evidence_refs": ["test"],
                "observed_at": "2026-08-27T07:03:00-05:00",
                "exact_metrics": {},
            }), encoding="utf-8")
            runtime = LegacyWorkerCoordinator.__new__(LegacyWorkerCoordinator)
            runtime.root = root
            task = {
                "task_id": "TASK-COSV",
                "source_state_vector_ref": "control/task-vectors/TASK-COSV.json",
                "machine_readable_state": {
                    "cosv": {
                        "profile": "task.v1",
                        "notation": "L R U I V G O C M T B E A P",
                        "width": 14,
                        "vector": "60000000101000",
                        "vector_state": "EMITTED",
                        "authority_effect": "NONE",
                    }
                },
            }
            self.assertEqual(
                runtime._semantic_state_preclaim(task),
                (False, "TASK_OPERATIONAL_STATE_VECTOR_STALE_OR_INVALID"),
            )

if __name__ == "__main__":
    unittest.main()
