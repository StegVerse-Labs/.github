from __future__ import annotations

import json
import unittest

from heartbeat_runtime.engine_v7_1 import HeartbeatRuntime, WorkerResponse
from tests.test_heartbeat_runtime import RuntimeFixture, write


class CheckpointPolicyTests(unittest.TestCase):
    def test_control_plane_writes_hash_valid_canonical_checkpoint(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis("fixture", beats=5)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            fx.registry([task])

            runtime = HeartbeatRuntime(
                fx.root,
                adapters={"fixture": lambda *_: WorkerResponse(
                    state="ACTIVE",
                    transition_id="IMPLEMENTING",
                    transition_sequence=1,
                    checkpoint_ref="worker-local/checkpoint-1",
                    evidence_refs=("evidence:one",),
                )},
            )
            runtime.cycle()
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            current = registry["tasks"][0]
            ref = current["last_checkpoint_ref"]
            self.assertTrue(ref.startswith("checkpoints/workers/TASK-A/"))
            checkpoint = json.loads((fx.root / ref).read_text())
            self.assertEqual(checkpoint["schema"], "stegverse.worker-checkpoint/v0.1")
            self.assertEqual(checkpoint["task_id"], "TASK-A")
            self.assertEqual(checkpoint["claim_id"], current["claim_id"])
            self.assertEqual(checkpoint["fencing_token"], current["heartbeat_timing"]["fencing_token"])
            self.assertEqual(checkpoint["policy_version"], "test")
            self.assertEqual(checkpoint["worker_checkpoint_ref"], "worker-local/checkpoint-1")
            self.assertFalse(checkpoint["execution_authority"])
            self.assertEqual(checkpoint["checkpoint_sha256"], runtime._checkpoint_hash(checkpoint))
            self.assertEqual(checkpoint["completed_transitions"][-1]["transition_id"], "IMPLEMENTING")
            self.assertIn(ref, current["evidence_refs"])
        finally:
            fx.close()

    def test_policy_drift_stops_worker_until_separate_rebind(self):
        fx = RuntimeFixture()
        calls: list[int] = []
        try:
            basis = fx.cost_basis("fixture", beats=8)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                calls.append(epoch)
                if len(calls) == 1:
                    return WorkerResponse(state="ACTIVE", transition_id="WORK", transition_sequence=1)
                return WorkerResponse(state="COMPLETED", transition_id="DONE", transition_sequence=2)

            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            runtime.cycle()
            self.assertEqual(calls, [1])

            handoff_path = fx.root / "handoffs/TASK-A.json"
            changed = json.loads(handoff_path.read_text())
            changed["authority"]["policy_version"] = "test-v2"
            write(handoff_path, changed)

            second = runtime.cycle()
            self.assertEqual(calls, [1])
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            current = registry["tasks"][0]
            self.assertEqual(current["state"], "EXPIRING")
            self.assertEqual(current["authorized_policy_version"], "test")
            self.assertIn("POLICY_REBIND_REQUIRED", current["archive_reason_codes"])
            self.assertIsNotNone(current["claim_id"])
            self.assertTrue(any(event["event_type"] == "policy_drift_detected" for event in second["events"]))

            ref = "authorizations/TASK-A-policy-rebind.json"
            write(fx.root / ref, {
                "schema": "stegverse.worker-policy-rebind/v0.1",
                "rebind_id": "REBIND-TASK-A-G1",
                "status": "ADMITTED",
                "task_id": "TASK-A",
                "claim_id": current["claim_id"],
                "fencing_token": current["heartbeat_timing"]["fencing_token"],
                "old_policy_version": "test",
                "new_policy_version": "test-v2",
                "handoff_sha256": runtime._handoff_hash(changed),
                "authority_source": "fixture authority",
                "heartbeat_grants_rebind": False,
                "evidence_refs": ["authority:test-policy-change"],
            })
            current["policy_rebind_ref"] = ref
            write(fx.root / "control/worker-registry.json", registry)

            third = runtime.cycle()
            self.assertEqual(calls, [1, 3])
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            current = registry["tasks"][0]
            self.assertEqual(current["state"], "COMPLETED")
            self.assertEqual(current["authorized_policy_version"], "test-v2")
            self.assertIsNone(current["policy_rebind_ref"])
            self.assertIn(ref, current["evidence_refs"])
            self.assertTrue(any(event["event_type"] == "policy_rebound" for event in third["events"]))
            checkpoint = json.loads((fx.root / current["last_checkpoint_ref"]).read_text())
            self.assertEqual(checkpoint["policy_version"], "test-v2")
        finally:
            fx.close()

    def test_successor_reconstruction_accepts_canonical_checkpoint_and_rejects_tamper(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis("fixture", beats=8)
            parent = fx.task("PARENT", cost_basis_ref=basis)
            fx.registry([parent])
            runtime = HeartbeatRuntime(
                fx.root,
                adapters={"fixture": lambda *_: WorkerResponse(state="COMPLETED", transition_id="DONE", transition_sequence=1)},
            )
            runtime.cycle()
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            parent_state = registry["tasks"][0]
            checkpoint_ref = parent_state["last_checkpoint_ref"]
            checkpoint = json.loads((fx.root / checkpoint_ref).read_text())

            proof_ref = "reconstruction/CHILD.json"
            write(fx.root / proof_ref, {
                "schema": "stegverse.worker-reconstruction-proof/v0.1",
                "reconstruction_id": "R-CHILD",
                "task_id": "CHILD",
                "goal_id": "CHILD",
                "parent_task_id": "PARENT",
                "authority_source": "fixture authority",
                "policy_version": "test",
                "last_valid_fencing_token": checkpoint["fencing_token"],
                "checkpoint_ref": checkpoint_ref,
                "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                "master_records_refs": ["master-records/orchestration:fixture-lineage"],
                "evidence_lineage_refs": ["master-records/orchestration:fixture-lineage"],
                "unresolved_work": ["continue child work"],
                "reconstruction_status": "PASS",
                "execution_authority": False,
            })
            child = fx.task(
                "CHILD",
                cost_basis_ref=basis,
                parent_task_id="PARENT",
                reconstruction_ref=proof_ref,
                checkpoint_ref=checkpoint_ref,
            )
            registry["tasks"].append(child)
            write(fx.root / "control/worker-registry.json", registry)

            handoff = json.loads((fx.root / "handoffs/CHILD.json").read_text())
            ok, reason, _ = runtime._successor_reconstruction(registry, handoff)
            self.assertTrue(ok, reason)

            checkpoint["current_state"] = "TAMPERED"
            write(fx.root / checkpoint_ref, checkpoint)
            ok, reason, _ = runtime._successor_reconstruction(registry, handoff)
            self.assertFalse(ok)
            self.assertEqual(reason, "SUCCESSOR_CANONICAL_CHECKPOINT_INVALID")
        finally:
            fx.close()


if __name__ == "__main__":
    unittest.main()
