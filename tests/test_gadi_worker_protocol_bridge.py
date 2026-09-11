from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.dispatch_gadi_resident_execution import stage_current_worker_claim
from workers.gadi_resident_execution_worker import (
    CONSUMPTION_RECEIPT,
    DISPATCH_RECEIPT,
    response_for_dispatch,
    validate_invocation,
)

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "GADI-RESIDENT-EXECUTION-001.json"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "gadi-resident-execution-001.json"


def claimed_task() -> dict:
    return {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "state": "ACTIVE",
        "worker_id": "gadi-resident-execution-worker",
        "worker_instance_id": "gadi-resident-execution-worker-HB31-G25",
        "claim_id": "SHWP-GADI-RESIDENT-EXECUTION-001-G25",
        "heartbeat_timing": {"fencing_token": 25},
    }


def invocation() -> dict:
    task = claimed_task()
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 31,
        "task": task,
        "handoff": {},
        "scope": {
            "claim_id": task["claim_id"],
            "fencing_token": 25,
        },
        "authority_effect": "none_adapter_only",
    }


class GADIWorkerProtocolBridgeTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_invocation_accepts_only_matching_current_claim_and_fence(self) -> None:
        task = validate_invocation(invocation())
        self.assertEqual(task["claim_id"], "SHWP-GADI-RESIDENT-EXECUTION-001-G25")
        bad = invocation()
        bad["scope"]["fencing_token"] = 26
        with self.assertRaisesRegex(ValueError, "scope claim/fence mismatch"):
            validate_invocation(bad)

    def test_dispatcher_stages_exact_existing_workercoordinator_row(self) -> None:
        task = claimed_task()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage_current_worker_claim(root, task)
            projected = self.load(root / "state/gadi-resident-execution/source/worker-claim.json")
        self.assertEqual(projected, task)

    def test_nonready_dispatch_relinquishes_claim_via_handoff_ready_response(self) -> None:
        response = response_for_dispatch({"state": "MATERIALIZATION_BLOCKED_FAIL_CLOSED"})
        self.assertEqual(response["schema"], "stegverse.worker-response/v0.1")
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertEqual(response["checkpoint_ref"], DISPATCH_RECEIPT)
        self.assertNotIn(CONSUMPTION_RECEIPT, response["evidence_refs"])
        self.assertEqual(response["authority_effect"], "NONE_WORKER_PROTOCOL_TRANSLATION_ONLY")

    def test_consumed_dispatch_maps_to_completed_without_new_authority(self) -> None:
        response = response_for_dispatch({"state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"})
        self.assertEqual(response["state"], "COMPLETED")
        self.assertEqual(response["checkpoint_ref"], CONSUMPTION_RECEIPT)
        self.assertIn(DISPATCH_RECEIPT, response["evidence_refs"])
        self.assertIn(CONSUMPTION_RECEIPT, response["evidence_refs"])
        self.assertEqual(response["cost_observation"]["external_cost_usd"], 0)

    def test_process_adapter_routes_through_bridge_and_handoff_scope_is_exact(self) -> None:
        adapter = self.load(ADAPTER)["adapters"][0]
        self.assertEqual(adapter["command"], ["python", "workers/gadi_resident_execution_worker.py"])
        handoff = self.load(HANDOFF)
        allowed = set(handoff["execution"]["allowed_paths"])
        required = {
            "state/gadi-resident-execution/source/stegos-command.json",
            "state/gadi-resident-execution/source/intr-admission.json",
            "state/gadi-resident-execution/source/worker-claim.json",
            "state/gadi-resident-execution/source/actuator-observation.json",
            "state/gadi-resident-execution/source-resolution.json",
            "state/gadi-resident-execution/materialization.json",
            "state/gadi-resident-execution/command.json",
            "state/gadi-resident-execution/execution-context.json",
            "state/gadi-resident-execution/actuator-result.json",
            "state/gadi-resident-execution/preflight.json",
            DISPATCH_RECEIPT,
            CONSUMPTION_RECEIPT,
        }
        self.assertEqual(allowed, required)


if __name__ == "__main__":
    unittest.main()
