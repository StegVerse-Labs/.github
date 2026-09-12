from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

DISPATCHER_SPEC = importlib.util.spec_from_file_location(
    "resident_dispatcher", ROOT / "scripts" / "dispatch_resident_execution_requests.py"
)
DISPATCHER = importlib.util.module_from_spec(DISPATCHER_SPEC)
assert DISPATCHER_SPEC and DISPATCHER_SPEC.loader
DISPATCHER_SPEC.loader.exec_module(DISPATCHER)

CONSUMER_PATH = ROOT / "workers" / "gadi_runtime_observation_request_consumer.py"
CONSUMER_SPEC = importlib.util.spec_from_file_location(
    "gadi_runtime_observation_consumer", CONSUMER_PATH
)
CONSUMER = importlib.util.module_from_spec(CONSUMER_SPEC)
assert CONSUMER_SPEC and CONSUMER_SPEC.loader
CONSUMER_SPEC.loader.exec_module(CONSUMER)


class GADIRuntimeObservationResidentDispatchTests(unittest.TestCase):
    def test_consumer_registered_exactly_once(self) -> None:
        matches = [row for row in DISPATCHER.CONSUMERS if row[0] == "gadi_runtime_observation"]
        self.assertEqual(matches, [("gadi_runtime_observation", "workers/gadi_runtime_observation_request_consumer.py")])

    def test_static_request_is_non_authorizing(self) -> None:
        request = json.loads((ROOT / CONSUMER.REQUEST_REL).read_text(encoding="utf-8"))
        CONSUMER.validate_request(request)
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["second_machine_required"])
        self.assertTrue(request["workercoordinator_may_be_visited_only_after_nonclaim_readiness"])

    def test_consumer_reuses_existing_local_source_and_claimless_gadi_dispatcher(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            request_target = runtime / CONSUMER.REQUEST_REL
            request_target.parent.mkdir(parents=True, exist_ok=True)
            request_target.write_text((ROOT / CONSUMER.REQUEST_REL).read_text(encoding="utf-8"), encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps({
                        "state": "NONCLAIM_RUNTIME_EVIDENCE_PENDING",
                        "targeted_execution_attempted": False,
                        "workercoordinator_claim_created": False,
                        "authority_effect": "NONE_READINESS_ONLY",
                    }) + "\n",
                    stderr="",
                )

            receipt = CONSUMER.consume(
                runtime,
                runtime,
                runner=runner,
                env={"STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(ROOT)},
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(Path(calls[0][1]), ROOT / "scripts" / "dispatch_gadi_resident_execution.py")
        self.assertEqual(calls[0][calls[0].index("--source-root") + 1], str(ROOT))
        self.assertEqual(calls[0][calls[0].index("--runtime-root") + 1], str(runtime.resolve()))
        self.assertEqual(receipt["canonical_local_source_root"], str(ROOT))
        self.assertFalse(receipt["network_source_fetch_performed"])
        self.assertEqual(receipt["state"], "OBSERVATION_ATTEMPT_RECORDED")
        self.assertEqual(receipt["dispatcher_state"], "NONCLAIM_RUNTIME_EVIDENCE_PENDING")
        self.assertFalse(receipt["claim_or_fence_created_by_consumer"])
        self.assertFalse(receipt["runtime_created_by_consumer"])
        self.assertFalse(receipt["listener_created_by_consumer"])

    def test_missing_existing_local_gadi_source_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, "claimless GADI dispatcher unavailable"):
                CONSUMER.resolve_source_root(runtime, env={})

    def test_observation_consumer_does_not_call_raw_post_claim_consumer(self) -> None:
        text = CONSUMER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("consume-gadi-resident-execution.py", text)
        self.assertIn("dispatch_gadi_resident_execution.py", text)


if __name__ == "__main__":
    unittest.main()
