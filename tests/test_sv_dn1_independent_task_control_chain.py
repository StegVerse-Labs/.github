import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator


TASKS = [
    (
        "SV-DN1-SOURCE-MATERIALIZATION-001",
        "handoffs/SV-DN1-SOURCE-MATERIALIZATION-001.json",
        "control/worker-registry.d/sv-dn1-source-materialization-001.json",
        [],
        None,
        None,
    ),
    (
        "SV-DN1-RESIDENT-OBSERVER-001",
        "handoffs/SV-DN1-RESIDENT-OBSERVER-001.json",
        "control/worker-registry.d/sv-dn1-resident-observer-001.json",
        ["SV-DN1-SOURCE-MATERIALIZATION-001"],
        "SV-DN1-SOURCE-MATERIALIZATION-001",
        "SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE",
    ),
    (
        "SV-DN1-INTR-RUNTIME-001",
        "handoffs/SV-DN1-INTR-RUNTIME-001.json",
        "control/worker-registry.d/sv-dn1-intr-runtime-001.json",
        ["SV-DN1-RESIDENT-OBSERVER-001"],
        "SV-DN1-RESIDENT-OBSERVER-001",
        "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
    ),
    (
        "SV-DN1-PRODUCTION-SOURCE-PREP-001",
        "handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json",
        "control/worker-registry.d/sv-dn1-production-source-prep-001.json",
        ["SV-DN1-INTR-RUNTIME-001"],
        "SV-DN1-INTR-RUNTIME-001",
        "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE",
    ),
    (
        "SV-DN1-SDK-FIRST-ROUND-001",
        "handoffs/SV-DN1-SDK-FIRST-ROUND-001.json",
        "control/worker-registry.d/sv-dn1-sdk-first-round-001.json",
        ["SV-DN1-INTR-RUNTIME-001", "SV-DN1-PRODUCTION-SOURCE-PREP-001"],
        "SV-DN1-INTR-RUNTIME-001",
        "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE",
    ),
]


class SvDn1IndependentTaskControlTests(unittest.TestCase):
    def test_every_lane_is_explicitly_independent_and_fenced(self):
        root = Path(__file__).resolve().parents[1]
        for task_id, handoff_rel, registry_rel, deps, parent, transition in TASKS:
            handoff = json.loads((root / handoff_rel).read_text())
            fragment = json.loads((root / registry_rel).read_text())
            task = fragment["tasks"][0]
            admission = task["admission"]

            self.assertEqual(task["task_id"], task_id)
            self.assertEqual(handoff["task"]["dependencies"], deps)
            self.assertEqual(handoff["task"]["execution_admission_mode"], "INDEPENDENT_TASK_CONTROL")
            self.assertEqual(handoff["activation"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
            self.assertTrue(handoff["activation"]["fresh_fence_required"])
            self.assertFalse(handoff["activation"]["carrier_trigger_required"])
            self.assertFalse(handoff["activation"]["heartbeat_grants_execution_authority"])
            self.assertEqual(
                handoff["activation"]["claim_state"],
                "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
            )

            self.assertEqual(admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
            self.assertEqual(
                admission["claim_state"],
                "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
            )
            self.assertTrue(admission["fresh_fence_required"])
            self.assertFalse(admission["carrier_trigger_required"])
            self.assertFalse(admission["heartbeat_grants_execution_authority"])
            self.assertEqual(admission["minimum_fencing_token_exclusive"], 22)

            if parent is None:
                self.assertNotIn("parent_task_id", admission)
                self.assertIsNone(handoff["task"]["upstream_runtime_dependency"])
            else:
                self.assertEqual(admission["parent_task_id"], parent)
                self.assertEqual(admission["parent_terminal_state_required"], "COMPLETED")
                self.assertEqual(admission["parent_terminal_transition_required"], transition)
                self.assertEqual(
                    handoff["task"]["upstream_runtime_dependency"],
                    {
                        "task_id": parent,
                        "terminal_state_required": "COMPLETED",
                        "terminal_transition_required": transition,
                    },
                )

    def test_workercoordinator_dependency_gate_blocks_until_parent_completed(self):
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoffs").mkdir()
            for _, handoff_rel, _, _, _, _ in TASKS:
                src = source_root / handoff_rel
                dst = root / handoff_rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())

            runtime = WorkerCoordinator.__new__(WorkerCoordinator)
            runtime.root = root

            records = {
                task_id: {
                    "task_id": task_id,
                    "handoff_ref": handoff_rel,
                    "state": "HANDOFF_READY",
                }
                for task_id, handoff_rel, *_ in TASKS
            }

            source = records["SV-DN1-SOURCE-MATERIALIZATION-001"]
            resident = records["SV-DN1-RESIDENT-OBSERVER-001"]
            intr = records["SV-DN1-INTR-RUNTIME-001"]
            prep = records["SV-DN1-PRODUCTION-SOURCE-PREP-001"]
            sdk = records["SV-DN1-SDK-FIRST-ROUND-001"]

            self.assertTrue(runtime._dependencies_complete(source, records))
            self.assertFalse(runtime._dependencies_complete(resident, records))
            self.assertFalse(runtime._dependencies_complete(intr, records))
            self.assertFalse(runtime._dependencies_complete(prep, records))
            self.assertFalse(runtime._dependencies_complete(sdk, records))

            source["state"] = "COMPLETED"
            self.assertTrue(runtime._dependencies_complete(resident, records))
            self.assertFalse(runtime._dependencies_complete(intr, records))

            resident["state"] = "COMPLETED"
            self.assertTrue(runtime._dependencies_complete(intr, records))
            self.assertFalse(runtime._dependencies_complete(prep, records))
            self.assertFalse(runtime._dependencies_complete(sdk, records))

            intr["state"] = "COMPLETED"
            self.assertTrue(runtime._dependencies_complete(prep, records))
            self.assertFalse(runtime._dependencies_complete(sdk, records))

            prep["state"] = "COMPLETED"
            self.assertTrue(runtime._dependencies_complete(sdk, records))

    def test_dependency_gate_does_not_accept_active_blocked_or_handoff_ready_parent(self):
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_rel = "handoffs/SV-DN1-RESIDENT-OBSERVER-001.json"
            dst = root / handoff_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((source_root / handoff_rel).read_bytes())

            runtime = WorkerCoordinator.__new__(WorkerCoordinator)
            runtime.root = root
            child = {
                "task_id": "SV-DN1-RESIDENT-OBSERVER-001",
                "handoff_ref": handoff_rel,
                "state": "HANDOFF_READY",
            }
            for state in ("HANDOFF_READY", "ACTIVE", "BLOCKED"):
                parent = {
                    "task_id": "SV-DN1-SOURCE-MATERIALIZATION-001",
                    "state": state,
                }
                self.assertFalse(
                    runtime._dependencies_complete(
                        child,
                        {
                            child["task_id"]: child,
                            parent["task_id"]: parent,
                        },
                    )
                )


if __name__ == "__main__":
    unittest.main()
