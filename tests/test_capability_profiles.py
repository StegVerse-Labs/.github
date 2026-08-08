from __future__ import annotations

import json
import unittest

from heartbeat_runtime.engine_v8 import HeartbeatRuntime
from tests.test_heartbeat_runtime import RuntimeFixture, write


PROFILES = {
    "schema": "stegverse.worker-capability-profiles/v0.1",
    "generation": 1,
    "profiles": [
        {
            "profile_id": "repo",
            "executor_type": "repository_worker",
            "effect_class": "repository_maintenance",
            "allowed_capabilities": ["read", "write"],
            "mutation_allowed": True,
            "deployment_allowed": False,
            "availability_grants_authority": False,
            "capability_match_grants_authority": False,
        },
        {
            "profile_id": "observer",
            "executor_type": "observer",
            "effect_class": "read_only_observer",
            "allowed_capabilities": ["read", "github_repository_write"],
            "mutation_allowed": False,
            "deployment_allowed": False,
            "availability_grants_authority": False,
            "capability_match_grants_authority": False,
        },
    ],
}


def strict_task(fx: RuntimeFixture, capability: str = "read") -> dict:
    task = fx.task("TASK-A")
    path = fx.root / task["handoff_ref"]
    handoff = json.loads(path.read_text())
    handoff["task"]["repository"] = "StegVerse-Labs/capability-fixture"
    handoff["execution"]["required_capabilities"] = [capability]
    write(path, handoff)
    return task


def worker(worker_id: str, *, executor_type: str = "repository_worker", capabilities=None, profile="repo") -> dict:
    return {
        "worker_id": worker_id,
        "executor_type": executor_type,
        "capabilities": capabilities or ["read"],
        "capability_profile_ref": f"control/worker-capability-profiles.json#{profile}",
        "status": "AVAILABLE",
        "adapter_ref": "fixture",
        "authority_source": "fixture authority",
        "last_seen_at": None,
    }


class CapabilityProfileTests(unittest.TestCase):
    def test_exact_profile_and_capability_match_selects_one_worker(self):
        fx = RuntimeFixture()
        try:
            task = strict_task(fx)
            write(fx.root / "control/worker-capability-profiles.json", PROFILES)
            registry = {"workers": [worker("one")], "tasks": [task]}
            selected = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: None})._worker_for(task, registry)
            self.assertEqual(selected["worker_id"], "one")
        finally:
            fx.close()

    def test_missing_or_executor_mismatched_profile_is_not_eligible(self):
        fx = RuntimeFixture()
        try:
            task = strict_task(fx)
            write(fx.root / "control/worker-capability-profiles.json", PROFILES)
            missing = worker("missing")
            missing["capability_profile_ref"] = "control/worker-capability-profiles.json#absent"
            mismatch = worker("mismatch", executor_type="agent_runtime")
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: None})
            self.assertIsNone(runtime._worker_for(task, {"workers": [missing], "tasks": [task]}))
            self.assertIsNone(runtime._worker_for(task, {"workers": [mismatch], "tasks": [task]}))
        finally:
            fx.close()

    def test_read_only_profile_cannot_match_mutation_requirement(self):
        fx = RuntimeFixture()
        try:
            task = strict_task(fx, "github_repository_write")
            write(fx.root / "control/worker-capability-profiles.json", PROFILES)
            candidate = worker("observer", executor_type="observer", capabilities=["github_repository_write"], profile="observer")
            selected = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: None})._worker_for(task, {"workers": [candidate], "tasks": [task]})
            self.assertIsNone(selected)
        finally:
            fx.close()

    def test_two_equally_eligible_profiled_workers_fail_closed(self):
        fx = RuntimeFixture()
        try:
            task = strict_task(fx)
            write(fx.root / "control/worker-capability-profiles.json", PROFILES)
            runtime = HeartbeatRuntime(fx.root, adapters={"fixture": lambda *_: None})
            selected = runtime._worker_for(task, {"workers": [worker("one"), worker("two")], "tasks": [task]})
            self.assertIsNone(selected)
        finally:
            fx.close()


if __name__ == "__main__":
    unittest.main()
