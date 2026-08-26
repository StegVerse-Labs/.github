import inspect
from pathlib import Path
import unittest

from heartbeat_runtime import CarrierHeartbeatRuntime, HeartbeatRuntime
from heartbeat_runtime.worker_runtime import WorkerCoordinator


class HeartbeatCarrierNonAuthorityTests(unittest.TestCase):
    def test_canonical_carrier_is_fragment_aware_v13_without_authority(self):
        self.assertEqual(CarrierHeartbeatRuntime.__module__, "heartbeat_runtime.engine_v13")
        source = inspect.getsource(CarrierHeartbeatRuntime.cycle)
        forbidden = (
            "issue_claim_assertions",
            "_invoke(",
            "_activate_one(",
            "_expire(",
            "_reconcile_orphan_recovery_quarantines(",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        self.assertIn('"claims_issued": 0', source)
        self.assertIn('"workers_invoked": 0', source)
        self.assertIn('"tasks_activated": 0', source)
        self.assertIn('"leases_expired": 0', source)
        self.assertIn('"authority_effect": "NONE_CARRIER_ONLY"', source)

        fragment_source = inspect.getsource(CarrierHeartbeatRuntime._assignment_triggers)
        self.assertIn("_apply_registry_fragments", fragment_source)
        self.assertIn("return super()._assignment_triggers", fragment_source)

    def test_worker_surfaces_are_not_the_production_carrier(self):
        self.assertEqual(HeartbeatRuntime.__module__, "heartbeat_runtime.engine_v11")
        self.assertEqual(WorkerCoordinator.__module__, "heartbeat_runtime.admitted_worker_runtime")
        self.assertIsNot(HeartbeatRuntime, CarrierHeartbeatRuntime)
        self.assertIsNot(WorkerCoordinator, CarrierHeartbeatRuntime)
        source = inspect.getsource(WorkerCoordinator._activate_from_trigger)
        self.assertIn("review_worker_task_admission", source)
        self.assertIn('verdict != "ADMIT"', source)
        self.assertIn("return super()._activate_from_trigger", source)

    def test_public_heartbeat_runner_is_oscillator_phase_driven(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts" / "run_heartbeat_runtime.py").read_text(encoding="utf-8")
        self.assertIn("CarrierHeartbeatRuntime", source)
        self.assertIn("runtime = CarrierHeartbeatRuntime(root)", source)
        self.assertIn("OscillatorProducer", source)
        self.assertIn("producer.next_due_unix_ns", source)
        self.assertIn("_sleep_until(producer.next_due_unix_ns)", source)
        self.assertIn("runtime.cycle(write=True, now_ns=batch.produced_unix_ns)", source)
        self.assertNotIn("time.sleep(args.interval_ms / 1000.0)", source)
        self.assertNotIn("runtime = WorkerCoordinator", source)
        self.assertNotIn("runtime = HeartbeatRuntime(root", source)

    def test_worker_runner_is_explicitly_separate(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts" / "run_worker_runtime.py").read_text(encoding="utf-8")
        self.assertIn("WorkerCoordinator", source)
        self.assertIn("ProcessWorkerAdapter", source)
        self.assertIn("--continuous", source)


if __name__ == "__main__":
    unittest.main()
