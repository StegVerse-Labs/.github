import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.engine_v9 import HeartbeatRuntime


class WorkerCoordinationSubsignalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "control").mkdir(parents=True)
        (self.root / "control" / "heartbeat-subsignals.json").write_text(
            json.dumps({
                "schema": "stegverse.heartbeat-subsignals/v1",
                "generation": 1,
                "subsignals": {}
            }),
            encoding="utf-8",
        )
        self.runtime = HeartbeatRuntime(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _registry(self):
        return {
            "generation": 17,
            "workers": [],
            "tasks": [{
                "task_id": "EXT-FRAMEWORK-WORKER-C",
                "goal_id": "EXT-FRAMEWORK-SECOND-PAGE-36",
                "state": "ACTIVE",
                "handoff_ref": "handoffs/ext-worker-c.json",
                "worker_id": "external-framework-worker-c",
                "worker_instance_id": "external-framework-worker-c-HB100-G17",
                "claim_id": "SHWP-EXT-FRAMEWORK-WORKER-C-G17",
                "heartbeat_timing": {
                    "start_epoch": 100,
                    "expiry_epoch": 160,
                    "expiry_basis": "TASK_CLASS_COST_BASIS",
                    "fencing_token": 17,
                    "current_transition": "POLICY_CARDS_EVALUATION"
                }
            }]
        }

    def test_worker_lease_is_cycle_bound_not_wall_clock(self):
        signal = self.runtime._worker_coordination_subsignal(self._registry(), 120)
        self.assertEqual(signal["state"], "ACTIVE")
        self.assertEqual(signal["carrier_cycle_unit"], "heartbeat_cycle")
        self.assertEqual(signal["worker_lease_unit"], "heartbeat_cycle")
        self.assertFalse(signal["worker_lease_is_heartbeat_lifetime"])
        self.assertFalse(signal["wall_clock_expiry_authority"])
        self.assertEqual(len(signal["active_leases"]), 1)
        lease = signal["active_leases"][0]
        self.assertEqual(lease["lease_start_cycle"], 100)
        self.assertEqual(lease["lease_end_cycle_exclusive"], 160)
        self.assertEqual(lease["assigned_cycles"], 60)
        self.assertEqual(lease["remaining_cycles"], 40)
        self.assertEqual(lease["lease_clock"], "canonical_heartbeat_cycle")
        self.assertFalse(lease["wall_clock_expiry_authority"])

    def test_same_subsignal_is_carried_and_projected_for_master_records(self):
        heartbeat = {"epoch": 120, "generation": 42}
        events = []
        signal = self.runtime._carry_subsignals(heartbeat, self._registry(), 120, events)

        carried = heartbeat["subsignals"]["worker_coordination"]
        self.assertEqual(carried, signal)
        self.assertEqual(carried["carrier_epoch"], 120)
        self.assertEqual(carried["master_records_projection"]["destination"], "master-records/orchestration")

        persisted = json.loads((self.root / "control" / "heartbeat-subsignals.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["subsignals"]["worker_coordination"], carried)

        projection = json.loads((self.root / "control" / "heartbeat-master-records-projection.json").read_text(encoding="utf-8"))
        self.assertEqual(projection["heartbeat_epoch"], 120)
        self.assertEqual(projection["worker_coordination"], carried)
        self.assertFalse(projection["execution_authority"])

        event = next(item for item in events if item["event_type"] == "worker_coordination_subsignal_carried")
        self.assertEqual(event["active_lease_count"], 1)
        self.assertFalse(event["wall_clock_expiry_authority"])

    def test_idle_signal_does_not_invent_a_worker_lease(self):
        signal = self.runtime._worker_coordination_subsignal({"tasks": [], "workers": []}, 9)
        self.assertEqual(signal["state"], "IDLE")
        self.assertEqual(signal["active_leases"], [])
        self.assertFalse(signal["authority_effect"])


if __name__ == "__main__":
    unittest.main()
