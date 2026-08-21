from __future__ import annotations

import inspect
import unittest

from heartbeat_runtime.worker_runtime import WorkerCoordinator


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

    def test_fresh_fence_floor_is_enforced_inside_canonical_assignment_path(self):
        source = inspect.getsource(WorkerCoordinator._activate_from_trigger)
        self.assertIn('minimum_fencing_token_exclusive', source)
        self.assertIn('generation = minimum_fence + 1', source)
        self.assertIn('source_admission_ref', source)
        self.assertIn('source_carrier_event_ref"] = None', source)
        self.assertIn('carrier_granted_authority=False', source)


if __name__ == "__main__":
    unittest.main()
