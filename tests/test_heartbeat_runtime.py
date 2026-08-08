from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime import HeartbeatRuntime, WorkerResponse


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def handoff(task_id: str, state: str = "HANDOFF_READY", dependencies: list[str] | None = None) -> dict:
    return {
        "schema": "stegverse.executable-handoff/v0.1",
        "handoff_id": f"H-{task_id}",
        "created_at": "2026-08-08T00:00:00Z",
        "state": state,
        "goal": {
            "goal_id": task_id,
            "objective": "fixture",
            "success_predicates": ["done"],
            "failure_predicates": [],
            "expires_at": None,
            "authority_ceiling": ["fixture"]
        },
        "task": {
            "task_id": task_id,
            "repository": "StegVerse-Labs/fixture",
            "source_refs": ["fixture"],
            "dependencies": dependencies or [],
            "parent_task_id": None,
            "derivation_reason": "test",
            "priority": "normal"
        },
        "authority": {
            "authority_source": "fixture authority",
            "heartbeat_grants_execution_authority": False,
            "policy_version": "test"
        },
        "execution": {
            "required_capabilities": ["fixture_execute"],
            "allowed_paths": ["StegVerse-Labs/fixture"],
            "allowed_services": [],
            "max_actions": 5,
            "max_retries": 1,
            "external_cost_ceiling_usd": 0
        },
        "activation": {
            "carrier": "heartbeat",
            "executor_binding": "UNBOUND",
            "recheck_trigger": "heartbeat",
            "checkout_policy": "fenced_atomic_checkout"
        },
        "continuity": {
            "checkpoint_ref": None,
            "handoff_destination": "control/worker-registry.json",
            "master_records_required": True,
            "status_projection": "control/worker-status.json"
        },
        "completion": {
            "next_authorized_action": "execute fixture",
            "terminal_when": ["done"]
        },
        "block": None
    }


class RuntimeFixture:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root / "control/heartbeat-state.json", {
            "schema": "stegverse.org-heartbeat-state/v1",
            "generation": 0,
            "epoch": 0,
            "expected_returns": 0,
            "issued": [],
            "received": [],
            "open_warrants": [],
            "deterministic_tolerances": {},
            "ordered_tolerances": {},
            "statistical_detection_active": False
        })
        write(self.root / "control/worker-cost-observations.json", {
            "schema": "stegverse.worker-cost-observation-log/v0.1",
            "generation": 0,
            "records": []
        })

    def close(self):
        self.tmp.cleanup()

    def cost_basis(self, name: str, beats: int = 4):
        path = self.root / "cost-basis" / f"{name}.json"
        write(path, {
            "schema": "stegverse.worker-runtime-cost-basis/v0.1",
            "task_class": name,
            "sample_count": 3,
            "hb_estimate": {
                "expected_completion_beats": 2,
                "expected_idle_beats": 1,
                "expiry_candidate_beats": beats,
                "confidence": "MEDIUM"
            },
            "cost_estimate": {},
            "evidence_refs": ["fixture"]
        })
        return str(path.relative_to(self.root))

    def registry(self, tasks: list[dict], worker_status: str = "AVAILABLE"):
        write(self.root / "control/worker-registry.json", {
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 0,
            "updated_at": "2026-08-08T00:00:00Z",
            "workers": [{
                "worker_id": "fixture-worker",
                "executor_type": "repository_worker",
                "capabilities": ["fixture_execute"],
                "status": worker_status,
                "adapter_ref": "fixture",
                "authority_source": "fixture authority",
                "last_seen_at": None
            }],
            "tasks": tasks
        })

    def task(self, task_id: str, state: str = "HANDOFF_READY", cost_basis_ref: str | None = None, deps: list[str] | None = None):
        write(self.root / "handoffs" / f"{task_id}.json", handoff(task_id, dependencies=deps))
        return {
            "task_id": task_id,
            "goal_id": task_id,
            "state": state,
            "handoff_ref": f"handoffs/{task_id}.json",
            "executor_binding": "UNBOUND",
            "worker_id": None,
            "worker_instance_id": None,
            "claim_id": None,
            "lease": None,
            "heartbeat_timing": None,
            "cost_basis_ref": cost_basis_ref,
            "external_entity_job_ref": None,
            "last_checkpoint_ref": None,
            "block_ref": None,
            "archive_eligible": False,
            "archive_reason_codes": [],
            "evidence_refs": []
        }


class HeartbeatRuntimeTests(unittest.TestCase):
    def test_no_available_job_initiates_no_worker(self):
        fx = RuntimeFixture()
        try:
            fx.registry([])
            result = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: None}).cycle()
            self.assertFalse(result["activated"])
            self.assertEqual(result["epoch"], 1)
            self.assertEqual(result["events"][-1]["event_type"], "no_worker_initiated")
        finally:
            fx.close()

    def test_dry_run_never_mutates_state(self):
        fx = RuntimeFixture()
        try:
            task = fx.task("TASK-A")
            fx.registry([task])
            before_hb = (fx.root / "control/heartbeat-state.json").read_text()
            before_registry = (fx.root / "control/worker-registry.json").read_text()
            result = HeartbeatRuntime(fx.root).cycle(write=False)
            self.assertFalse(result["activated"])
            self.assertEqual((fx.root / "control/heartbeat-state.json").read_text(), before_hb)
            self.assertEqual((fx.root / "control/worker-registry.json").read_text(), before_registry)
        finally:
            fx.close()

    def test_job_without_cost_basis_does_not_guess_expiry(self):
        fx = RuntimeFixture()
        try:
            task = fx.task("TASK-A")
            fx.registry([task])
            result = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: None}).cycle()
            self.assertFalse(result["activated"])
            state = json.loads((fx.root / "control/worker-registry.json").read_text())
            self.assertEqual(state["tasks"][0]["state"], "HANDOFF_READY")
            self.assertIn("EXPIRY_BASIS_UNAVAILABLE", state["tasks"][0]["archive_reason_codes"])
        finally:
            fx.close()

    def test_eligible_job_activates_exactly_one_worker_and_uses_same_hb(self):
        fx = RuntimeFixture()
        calls = []
        try:
            basis = fx.cost_basis("fixture")
            task = fx.task("TASK-A", cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                calls.append((task["task_id"], epoch))
                return WorkerResponse(
                    state="ACTIVE",
                    transition_id="IMPLEMENTING",
                    transition_sequence=1,
                    expected_next_transition="CHECKPOINT",
                    expected_next_earliest_epoch=epoch + 1,
                    expected_next_latest_epoch=epoch + 2,
                    evidence_refs=("fixture-evidence",),
                    cost_observation={"compute_units": 1, "external_cost_usd": 0}
                )

            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            first = runtime.cycle()
            self.assertTrue(first["activated"])
            self.assertEqual(calls, [("TASK-A", 1)])
            state = json.loads((fx.root / "control/worker-registry.json").read_text())
            active = state["tasks"][0]
            self.assertEqual(active["state"], "ACTIVE")
            self.assertEqual(active["heartbeat_timing"]["last_response_epoch"], 1)
            self.assertEqual(active["heartbeat_timing"]["last_transition_epoch"], 1)
            self.assertEqual(active["heartbeat_timing"]["fencing_token"], 1)
            self.assertEqual(active["heartbeat_timing"]["expiry_epoch"], 5)
            self.assertEqual(active["heartbeat_timing"]["expiry_basis"], "TASK_CLASS_COST_BASIS")

            second = runtime.cycle()
            self.assertFalse(second["activated"])
            self.assertEqual(calls[-1], ("TASK-A", 2))
            state2 = json.loads((fx.root / "control/worker-registry.json").read_text())
            self.assertEqual(len([t for t in state2["tasks"] if t["task_id"] == "TASK-A"]), 1)
            self.assertEqual(state2["tasks"][0]["claim_id"], active["claim_id"])
        finally:
            fx.close()

    def test_completion_releases_worker_and_prevents_reactivation(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis("fixture")
            task = fx.task("TASK-A", cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                return WorkerResponse(state="COMPLETED", transition_id="COMPLETE", transition_sequence=1, evidence_refs=("done",))

            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            first = runtime.cycle()
            self.assertTrue(first["activated"])
            state = json.loads((fx.root / "control/worker-registry.json").read_text())
            self.assertEqual(state["tasks"][0]["state"], "COMPLETED")
            self.assertIsNone(state["tasks"][0]["worker_id"])
            self.assertEqual(state["workers"][0]["status"], "AVAILABLE")
            second = runtime.cycle()
            self.assertFalse(second["activated"])
        finally:
            fx.close()

    def test_known_expiry_without_master_records_final_blocks_parent_and_admits_recovery(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis("fixture", beats=1)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                return WorkerResponse(state="ACTIVE", transition_id="WORK", transition_sequence=1)

            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            runtime.cycle()  # activates at HB1, expiry HB2
            runtime.cycle()  # expiry path
            state = json.loads((fx.root / "control/worker-registry.json").read_text())
            parent = next(t for t in state["tasks"] if t["task_id"] == "TASK-A")
            recovery = [t for t in state["tasks"] if t["task_id"].startswith("RECOVER-TASK-A-HB2")]
            self.assertEqual(parent["state"], "BLOCKED")
            self.assertIsNone(parent["worker_id"])
            self.assertIn("MASTER_RECORDS_FINAL_WORKER_REPORT_MISSING", parent["archive_reason_codes"])
            self.assertEqual(len(recovery), 1)
            self.assertEqual(recovery[0]["state"], "HANDOFF_READY")
            self.assertEqual(parent["block_ref"], recovery[0]["handoff_ref"])
            self.assertTrue((fx.root / recovery[0]["handoff_ref"]).exists())
        finally:
            fx.close()


if __name__ == "__main__":
    unittest.main()
