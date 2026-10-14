from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workers"))
import va_conversational_runtime_bridge as bridge  # noqa: E402


class FakeProcess:
    def __init__(self, pid: int = 4242) -> None:
        self.pid = pid

    def poll(self):
        return None


class VAGatewayStartTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.adapter = root / "adapter"
        (self.adapter / "va_claim_assistant").mkdir(parents=True)
        (self.adapter / "va_claim_assistant" / "source-registry.site-projection.json").write_text("{}\n")
        self.proof = root / "proof.json"
        self.route = root / "route.json"
        self.state = root / "state.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def start(self, *, readiness, live_pids=(4242,)):
        terminated: list[int] = []
        popen = mock.Mock(return_value=FakeProcess())
        with mock.patch.object(bridge.subprocess, "Popen", popen), \
                mock.patch.object(bridge, "_free_port", return_value=31415), \
                mock.patch.object(bridge, "_readiness", return_value=readiness), \
                mock.patch.object(bridge, "_pid_alive", side_effect=lambda pid: pid in live_pids), \
                mock.patch.object(bridge, "_terminate", side_effect=terminated.append):
            result = bridge.ensure_runtime_gateway(
                self.adapter, proof_path=self.proof, route_path=self.route, state_path=self.state,
            )
        return result, popen, terminated

    def test_start_closes_on_spawned_process_without_readiness(self) -> None:
        result, popen, terminated = self.start(readiness=None)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(terminated, [])
        self.assertEqual(result["state"], "COMPLETE")
        self.assertEqual(result["reason"], "VA_RUNTIME_GATEWAY_STARTED")
        self.assertFalse(result["readiness"]["gates_transition"])
        state = json.loads(self.state.read_text())
        self.assertEqual(state["state"], "STARTED")
        self.assertEqual(state["pid"], 4242)
        self.assertFalse(state["destination_liveness_is_transition_predicate"])

    def test_ready_observation_is_recorded_not_required(self) -> None:
        result, _, _ = self.start(readiness={"state": "READY"})
        self.assertEqual(result["readiness"]["observation"], "OBSERVED")
        self.assertFalse(result["readiness"]["gates_transition"])

    def test_started_gateway_with_same_bindings_is_reused_even_if_not_ready(self) -> None:
        self.start(readiness=None)
        result, popen, terminated = self.start(readiness=None)
        self.assertEqual(popen.call_count, 0)
        self.assertEqual(terminated, [])
        self.assertEqual(result["reason"], "REUSED_STARTED_VA_RUNTIME")

    def test_gateway_bound_to_another_proof_is_replaced(self) -> None:
        self.start(readiness=None)
        state = json.loads(self.state.read_text())
        state["proof_path"] = "/elsewhere/proof.json"
        self.state.write_text(json.dumps(state))
        result, popen, terminated = self.start(readiness=None)
        self.assertEqual(terminated, [4242])
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(result["reason"], "VA_RUNTIME_GATEWAY_STARTED")

    def test_readiness_poll_exemption_is_not_re_registered(self) -> None:
        register = json.loads((ROOT / "data" / "organization-role-exemption-register.json").read_text())
        self.assertNotIn(
            "VA_RUNTIME_GATED_ON_GATEWAY_READINESS_POLL",
            {entry["failed_predicate"] for entry in register["exemptions"]},
        )


if __name__ == "__main__":
    unittest.main()
