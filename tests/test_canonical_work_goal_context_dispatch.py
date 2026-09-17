from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


DISPATCHER = load("resident_dispatch_goal_context", SCRIPTS / "dispatch_resident_execution_requests.py")
BRIDGE = load("portable_dispatch_goal_context", SCRIPTS / "refresh_and_dispatch_resident_requests.py")
GOAL = "HYGIENE-CAUSAL-ROOTS-001"


class CanonicalWorkGoalContextDispatchTests(unittest.TestCase):
    def test_dispatcher_forwards_goal_only_to_exact_canonical_work_selector(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            source.mkdir()
            consumer = runtime / dict(DISPATCHER.CONSUMERS)["canonical_work_coordination"]
            consumer.parent.mkdir(parents=True, exist_ok=True)
            consumer.write_text("# consumer\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "schema": "stegverse.canonical-work-bootstrap-plus-mir-request-consumption/v1",
                    "state": "COMPLETED",
                    "current_goal_task_id": GOAL,
                }) + "\n", stderr="")

            receipt = DISPATCHER.dispatch(
                source,
                runtime,
                runner=runner,
                env={"PATH": "/bin", "HOME": td},
                only_consumers=("canonical_work_coordination",),
                goal_task_id=GOAL,
            )
            self.assertEqual(receipt["state"], "DISPATCH_COMPLETE")
            self.assertEqual(receipt["current_goal_task_id"], GOAL)
            self.assertEqual(receipt["goal_context_forwarded_to"], "canonical_work_coordination")
            self.assertEqual(len(calls), 1)
            command, _ = calls[0]
            self.assertEqual(command[command.index("--goal-task-id") + 1], GOAL)

    def test_dispatcher_rejects_goal_context_for_unrelated_selector(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            runtime = Path(td) / "runtime"
            source.mkdir()
            runtime.mkdir()
            with self.assertRaisesRegex(RuntimeError, "exact canonical_work_coordination selector"):
                DISPATCHER.dispatch(
                    source,
                    runtime,
                    env={"PATH": "/bin", "HOME": td},
                    only_consumers=("hil",),
                    goal_task_id=GOAL,
                )

    def test_portable_bridge_preserves_goal_context_in_exact_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            source.mkdir()
            runtime.mkdir()
            dispatcher = runtime / BRIDGE.DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True, exist_ok=True)
            dispatcher.write_text("# dispatcher\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                receipt = runtime / BRIDGE.DISPATCH_RECEIPT_REL
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "consumer_count": 1,
                    "selected_consumers": ["canonical_work_coordination"],
                    "selection_scope": "EXACT_SELECTOR",
                    "current_goal_task_id": GOAL,
                    "goal_context_forwarded_to": "canonical_work_coordination",
                    "request_failures": [],
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            refresh_receipt = {
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
            }
            with mock.patch.object(BRIDGE, "refresh", return_value=refresh_receipt):
                result = BRIDGE.refresh_and_dispatch(
                    source,
                    runtime,
                    target_consumer="canonical_work_coordination",
                    goal_task_id=GOAL,
                    runner=runner,
                    env={"PATH": "/bin", "HOME": td},
                )

            self.assertEqual(result["state"], "REFRESH_AND_DISPATCH_COMPLETE")
            self.assertEqual(result["current_goal_task_id"], GOAL)
            self.assertTrue(result["goal_context_forwarded_to_dispatcher"])
            self.assertTrue(result["goal_context_match_observed"])
            self.assertEqual(len(calls), 1)
            command, _ = calls[0]
            self.assertEqual(command[command.index("--only-consumer") + 1], "canonical_work_coordination")
            self.assertEqual(command[command.index("--goal-task-id") + 1], GOAL)

    def test_portable_bridge_rejects_goal_context_for_other_consumer_before_refresh(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            runtime = Path(td) / "runtime"
            source.mkdir()
            runtime.mkdir()
            with mock.patch.object(BRIDGE, "refresh") as refresh:
                with self.assertRaisesRegex(RuntimeError, "requires canonical_work_coordination target"):
                    BRIDGE.refresh_and_dispatch(
                        source,
                        runtime,
                        target_consumer="hil",
                        goal_task_id=GOAL,
                        env={"PATH": "/bin", "HOME": td},
                    )
                refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
