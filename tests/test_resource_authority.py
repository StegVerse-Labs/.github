from __future__ import annotations

import json
import unittest

from heartbeat_runtime.engine_v6 import HeartbeatRuntime
from heartbeat_runtime.engine_v2 import WorkerResponse
from tests.test_heartbeat_runtime import RuntimeFixture, write


def configure(fx: RuntimeFixture, task: dict, *, max_actions=2, max_retries=1, cost=0, window=8, services=None):
    path = fx.root / task["handoff_ref"]
    value = json.loads(path.read_text())
    value["execution"]["max_actions"] = max_actions
    value["execution"]["max_retries"] = max_retries
    value["execution"]["external_cost_ceiling_usd"] = cost
    value["execution"]["runtime_window_beats"] = window
    value["execution"]["rate_class"] = "fixture"
    value["execution"]["allowed_services"] = services or []
    write(path, value)
    return value


class ResourceAuthorityTests(unittest.TestCase):
    def test_runtime_window_caps_cost_basis_expiry(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis("fixture", beats=10)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            configure(fx, task, window=2)
            fx.registry([task])
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: WorkerResponse(state="ACTIVE", transition_id="WORK", transition_sequence=1)})
            runtime.cycle()
            state = json.loads((fx.root / "control/worker-registry.json").read_text())
            active = state["tasks"][0]
            self.assertEqual(active["heartbeat_timing"]["expiry_epoch"], 3)
            self.assertEqual(active["resource_budget"]["runtime_window_beats"], 2)
        finally:
            fx.close()

    def test_action_limit_stops_second_mutation_without_silent_reset(self):
        fx = RuntimeFixture()
        calls = []
        try:
            basis = fx.cost_basis("fixture", beats=10)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            configure(fx, task, max_actions=1, window=5)
            fx.registry([task])
            def adapter(*_):
                calls.append("call")
                return WorkerResponse(state="ACTIVE", transition_id="WORK", transition_sequence=len(calls))
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            first = runtime.cycle()
            second = runtime.cycle()
            self.assertEqual(calls, ["call"])
            state = json.loads((fx.root / "control/worker-registry.json").read_text())
            current = state["tasks"][0]
            self.assertEqual(current["state"], "EXPIRING")
            self.assertEqual(current["resource_budget"]["actions_used"], 1)
            self.assertIn("RESOURCE_AUTHORIZATION_RENEWAL_REQUIRED", current["archive_reason_codes"])
            self.assertTrue(any(e["event_type"] == "resource_authority_exhausted" for e in first["events"] + second["events"]))
        finally:
            fx.close()

    def test_separate_admitted_renewal_extends_exhausted_action_budget(self):
        fx = RuntimeFixture()
        calls = []
        try:
            basis = fx.cost_basis("fixture", beats=10)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            handoff = configure(fx, task, max_actions=1, window=5)
            fx.registry([task])
            def adapter(*_):
                calls.append("call")
                return WorkerResponse(state="ACTIVE" if len(calls) == 1 else "COMPLETED", transition_id=f"WORK-{len(calls)}", transition_sequence=len(calls))
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            runtime.cycle()
            registry_path = fx.root / "control/worker-registry.json"
            registry = json.loads(registry_path.read_text())
            current = registry["tasks"][0]
            prior_expiry = current["heartbeat_timing"]["expiry_epoch"]
            ref = "renewals/TASK-A.json"
            write(fx.root / ref, {
                "schema": "stegverse.worker-renewal-admission/v0.1",
                "renewal_id": "REN-TASK-A",
                "task_id": "TASK-A",
                "claim_id": current["claim_id"],
                "fencing_token": current["heartbeat_timing"]["fencing_token"],
                "prior_expiry_epoch": prior_expiry,
                "additional_beats": 2,
                "additional_actions": 1,
                "additional_retries": 0,
                "additional_external_cost_usd": 0,
                "scope_sha256": runtime._scope_sha256(handoff),
                "authority_source": handoff["authority"]["authority_source"],
                "policy_version": handoff["authority"]["policy_version"],
                "status": "ADMITTED",
                "heartbeat_grants_renewal": False
            })
            current["renewal_ref"] = ref
            write(registry_path, registry)
            result = runtime.cycle()
            self.assertEqual(calls, ["call", "call"])
            final = json.loads(registry_path.read_text())["tasks"][0]
            self.assertEqual(final["state"], "COMPLETED")
            self.assertEqual(final["resource_budget"]["max_actions"], 2)
            self.assertEqual(final["resource_budget"]["renewal_count"], 1)
            self.assertTrue(any(e["event_type"] == "resource_authority_renewed" for e in result["events"]))
        finally:
            fx.close()

    def test_retry_limit_stops_additional_retry(self):
        fx = RuntimeFixture()
        calls = []
        try:
            basis = fx.cost_basis("fixture", beats=10)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            configure(fx, task, max_actions=4, max_retries=0, window=5)
            fx.registry([task])
            def adapter(*_):
                calls.append("call")
                return WorkerResponse(state="FAILED_RETRYABLE", transition_id="RETRY", transition_sequence=len(calls))
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": adapter})
            runtime.cycle()
            runtime.cycle()
            self.assertEqual(calls, ["call"])
            current = json.loads((fx.root / "control/worker-registry.json").read_text())["tasks"][0]
            self.assertEqual(current["resource_budget"]["retries_used"], 1)
            self.assertIn("RESOURCE_RETRY_LIMIT_EXCEEDED", current["archive_reason_codes"])
        finally:
            fx.close()

    def test_unadmitted_service_quarantines_and_releases_claim(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis("fixture", beats=10)
            task = fx.task("TASK-A", cost_basis_ref=basis)
            configure(fx, task, max_actions=3, services=["github"], window=5)
            fx.registry([task])
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: WorkerResponse(state="ACTIVE", transition_id="WORK", transition_sequence=1, cost_observation={"external_cost_usd": 0, "services_used": ["render"]})})
            result = runtime.cycle()
            current = json.loads((fx.root / "control/worker-registry.json").read_text())["tasks"][0]
            self.assertEqual(current["state"], "QUARANTINED")
            self.assertIsNone(current["claim_id"])
            self.assertIn("RESOURCE_SERVICE_SCOPE_VIOLATION", current["archive_reason_codes"])
            self.assertTrue(any(e["event_type"] == "resource_authority_violation" for e in result["events"]))
        finally:
            fx.close()


if __name__ == "__main__":
    unittest.main()
