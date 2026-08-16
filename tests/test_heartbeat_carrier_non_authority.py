import inspect
from pathlib import Path
import unittest

from heartbeat_runtime import CarrierHeartbeatRuntime, HeartbeatRuntime
from heartbeat_runtime.worker_runtime import WorkerCoordinator


class HeartbeatCarrierNonAuthorityTests(unittest.TestCase):
    def test_canonical_carrier_is_v12(self):
        self.assertEqual(CarrierHeartbeatRuntime.__module__, "heartbeat_runtime.engine_v12")
        source = inspect.getsource(CarrierHeartbeatRuntime.cycle)
        forbidden = (
            "issue_claim_assertions",
            "_invoke(",
            "_activate_one(",
            "_expire(",
            "_apply_registry_fragments(",
            "_reconcile_orphan_recovery_quarantines(",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        self.assertIn('"claims_issued": 0', source)
        self.assertIn('"workers_invoked": 0', source)
        self.assertIn('"tasks_activated": 0', source)
        self.assertIn('"leases_expired": 0', source)
        self.assertIn('"authority_effect": "NONE_CARRIER_ONLY"', source)

    def test_worker_coordinator_is_separate(self):
        self.assertEqual(WorkerCoordinator.__module__, "heartbeat_runtime.engine_v11")
        self.assertIsNot(WorkerCoordinator, CarrierHeartbeatRuntime)
        self.assertIs(HeartbeatRuntime, WorkerCoordinator)

    def test_public_heartbeat_runner_instantiates_carrier_only(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts" / "run_heartbeat_runtime.py").read_text(encoding="utf-8")
        self.assertIn("CarrierHeartbeatRuntime", source)
        self.assertIn("runtime = CarrierHeartbeatRuntime(root)", source)
        self.assertNotIn("runtime = WorkerCoordinator", source)
        self.assertNotIn("runtime = HeartbeatRuntime(root", source)

    def test_worker_runner_is_explicitly_separate(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts" / "run_worker_runtime.py").read_text(encoding="utf-8")
        self.assertIn("WorkerCoordinator", source)
        self.assertIn("ProcessWorkerAdapter", source)


if __name__ == "__main__":
    unittest.main()
