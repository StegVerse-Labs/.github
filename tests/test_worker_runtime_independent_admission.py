from __future__ import annotations

import inspect
import unittest

from heartbeat_runtime.worker_runtime import WorkerCoordinator
from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator as LegacyWorkerCoordinator


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


if __name__ == "__main__":
    unittest.main()
