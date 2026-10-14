from __future__ import annotations

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import workers.hil_sovereign_receiver_worker as worker

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
READY = {"state": "READY", "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE"}


def invocation() -> dict:
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 40,
        "task": {
            "task_id": TASK_ID,
            "claim_id": "SHWP-HIL-SOVEREIGN-RECEIVER-001-G26",
            "heartbeat_timing": {"fencing_token": 26},
            "machine_readable_state": {
                "browser_predecessor_lineage": {
                    "task_id": TASK_ID,
                    "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25",
                    "fencing_token": 25,
                    "lease_id": "HIL-BROWSER-ESRL-7bafde4a280e847758da157e",
                    "request_id": "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002",
                    "state": "SATISFIED_PREDECESSOR_ONLY",
                    "machine_worker_claim_reuse_allowed": False,
                }
            },
        },
        "handoff": {
            "execution": {
                "required_capabilities": [
                    "runtime_observation", "bounded_process_execution", "sovereign_hil_receiver_activation",
                ],
                "allowed_paths": ["receipts/hil-sovereign-receiver/**"],
            }
        },
    }


class FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.terminated = False

    def poll(self):
        return None

    def terminate(self) -> None:
        self.terminated = True


class HILReceiverLaunchTransitionTests(unittest.TestCase):
    def run_worker(self, root: Path, *, observations: list, launched: list, live_pid: int | None = None) -> tuple[dict, dict]:
        receipt_path = root / "receipts" / "hil-sovereign-receiver" / f"{TASK_ID}.json"
        if live_pid is not None:
            pid_path = root / worker.RECEIVER_PID_REL
            pid_path.parent.mkdir(parents=True, exist_ok=True)
            pid_path.write_text(f"{live_pid}\n", encoding="utf-8")
        calls = iter(observations)

        def launch(adapter_root, durable_root, port):
            process = FakeProcess(4242)
            launched.append(process)
            return process

        stdout = io.StringIO()
        with patch.object(worker, "ROOT", root), \
                patch.object(worker, "RECEIPT", receipt_path), \
                patch.object(worker, "find_hil_receiver_root", return_value=root / "adapter"), \
                patch.object(worker, "verify_receiver", side_effect=lambda url: next(calls)), \
                patch.object(worker, "launch_detached", side_effect=launch), \
                patch.object(worker, "launch_tvc_lifecycle_watch", return_value=None), \
                patch.object(worker, "_pid_live", side_effect=lambda pid: pid in {4242, live_pid}), \
                patch.dict(os.environ, {"STEGVERSE_HIL_STATE_ROOT": str(root / "state")}), \
                patch("sys.stdin", io.StringIO(json.dumps(invocation()))), \
                patch("sys.stdout", stdout):
            self.assertEqual(worker.main(), 0)
        return json.loads(stdout.getvalue()), json.loads(receipt_path.read_text(encoding="utf-8"))

    def test_launch_closes_on_spawned_process_without_readiness_poll(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            launched: list = []
            response, receipt = self.run_worker(Path(tmp), observations=[{"state": "NOT_READY"}], launched=launched)
            self.assertEqual(len(launched), 1)
            self.assertFalse(launched[0].terminated)
            self.assertEqual(response["transition_id"], "HIL_RECEIVER_LOCAL_LAUNCHED")
            self.assertEqual(response["expected_next_transition"], "HIL_RECEIVER_LOCAL_READY")
            self.assertNotIn("blocker", response)
            self.assertEqual(receipt["receiver_pid"], 4242)
            self.assertFalse(receipt["receiver_ready"])
            self.assertFalse(receipt["readiness"]["gates_transition"])
            self.assertFalse(receipt["destination_liveness_is_transition_predicate"])
            self.assertEqual((Path(tmp) / worker.RECEIVER_PID_REL).read_text().strip(), "4242")

    def test_live_receiver_is_reused_not_relaunched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            launched: list = []
            response, receipt = self.run_worker(Path(tmp), observations=[None], launched=launched, live_pid=5151)
            self.assertEqual(launched, [])
            self.assertEqual(response["transition_id"], "HIL_RECEIVER_LOCAL_LAUNCHED")
            self.assertTrue(receipt["receiver_launch_reused_live_process"])
            self.assertEqual(receipt["receiver_pid"], 5151)

    def test_ready_observation_advances_with_the_launched_receiver_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            launched: list = []
            response, receipt = self.run_worker(Path(tmp), observations=[READY], launched=launched, live_pid=5151)
            self.assertEqual(launched, [])
            self.assertEqual(response["transition_id"], "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED")
            self.assertTrue(receipt["receiver_ready"])
            self.assertEqual(receipt["receiver_pid"], 5151)


if __name__ == "__main__":
    unittest.main()
