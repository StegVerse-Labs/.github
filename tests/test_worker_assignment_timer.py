import unittest

from heartbeat_runtime.assignment_timer import (
    AssignmentTimer,
    assignment_trigger_packet,
    bind_assignment_from_trigger,
)


class WorkerAssignmentTimerTests(unittest.TestCase):
    def test_trigger_is_non_authorizing_and_single_use(self):
        trigger = assignment_trigger_packet(
            carrier_epoch=30,
            task={
                "task_id": "TASK-A",
                "goal_id": "GOAL-A",
                "handoff_ref": "handoffs/TASK-A.json",
                "executor_binding": "AUTHORIZED",
                "cost_basis_ref": "cost-basis/TASK-A.json",
            },
        )
        self.assertEqual(trigger["observation"], "UNASSIGNED_TASK_PRESENT")
        self.assertEqual(trigger["authority_effect"], "NONE")
        self.assertFalse(trigger["execution_authority"])
        self.assertTrue(trigger["single_use"])
        self.assertTrue(trigger["dissipates_on_assignment"])

    def test_assignment_timer_counts_runtime_ticks_in_hb_units_independent_of_carrier(self):
        trigger = assignment_trigger_packet(carrier_epoch=30, task={"task_id": "TASK-A", "cost_basis_ref": "cost.json"})
        timer, transition = bind_assignment_from_trigger(
            trigger=trigger,
            worker_id="WORKER-A",
            worker_instance_id="WORKER-A-R1",
            claim_id="CLAIM-A",
            fencing_token=7,
            allocated_hb_units=3,
            expiry_basis="TASK_CLASS_COST_BASIS",
        )
        self.assertEqual(timer.remaining_hb_units, 3)
        self.assertFalse(timer.expired)
        timer = timer.tick()
        self.assertEqual(timer.remaining_hb_units, 2)
        timer = timer.tick(2)
        self.assertTrue(timer.expired)
        self.assertEqual(timer.runtime_tick, 3)
        self.assertEqual(timer.as_dict()["timer_clock"], "WORKER_RUNTIME_INTERNAL")
        self.assertFalse(timer.as_dict()["carrier_epoch_controls_expiry"])
        self.assertFalse(timer.as_dict()["carrier_presence_controls_expiry"])
        self.assertEqual(transition["source_trigger_state"], "DISSIPATED_AFTER_CONSUMPTION")
        self.assertTrue(transition["master_records_binding_required"])
        self.assertEqual(transition["recording_effect"], "STATE_TRANSITION_CUSTODY")
        self.assertFalse(transition["carrier_controls_timer"])

    def test_authorizing_trigger_is_rejected(self):
        trigger = assignment_trigger_packet(carrier_epoch=1, task={"task_id": "TASK-A"})
        trigger["execution_authority"] = True
        with self.assertRaises(ValueError):
            bind_assignment_from_trigger(
                trigger=trigger,
                worker_id="W",
                worker_instance_id="W-1",
                claim_id="C",
                fencing_token=1,
                allocated_hb_units=1,
                expiry_basis="TASK_CLASS_COST_BASIS",
            )


if __name__ == "__main__":
    unittest.main()
