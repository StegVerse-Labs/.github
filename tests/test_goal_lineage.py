from __future__ import annotations

import json
import unittest

from heartbeat_runtime.engine_v5 import HeartbeatRuntime
from tests.test_heartbeat_runtime import RuntimeFixture, write


def bind_strict(
    fx: RuntimeFixture,
    task: dict,
    *,
    owner: str = "StegVerse-Labs/.github#12",
    lineage: str,
    goal_id: str | None = None,
    depth: int = 0,
    parent_task_id: str | None = None,
    successor_policy: str = "INHERIT_OR_NARROW",
    max_depth: int = 3,
    allowed_paths: list[str] | None = None,
    max_actions: int = 5,
) -> dict:
    path = fx.root / task["handoff_ref"]
    value = json.loads(path.read_text())
    value["goal"]["goal_id"] = goal_id or task["task_id"]
    value["goal"]["failure_predicates"] = ["authority or lineage validation fails"]
    value["goal"]["successor_policy"] = successor_policy
    value["goal"]["max_successor_depth"] = max_depth
    value["task"]["repository"] = "StegVerse-Labs/strict-fixture"
    value["task"]["canonical_owner_ref"] = owner
    value["task"]["canonical_lineage_key"] = lineage
    value["task"]["derivation_depth"] = depth
    value["task"]["parent_task_id"] = parent_task_id
    value["task"]["derivation_reason"] = "strict lineage test"
    if parent_task_id:
        parent_ref = f"handoffs/{parent_task_id}.json"
        if parent_ref not in value["task"]["source_refs"]:
            value["task"]["source_refs"].append(parent_ref)
    value["execution"]["allowed_paths"] = allowed_paths or ["StegVerse-Labs/strict-fixture/**"]
    value["execution"]["max_actions"] = max_actions
    write(path, value)
    task["goal_id"] = value["goal"]["goal_id"]
    return value


class GoalLineageTests(unittest.TestCase):
    def test_duplicate_canonical_lane_is_quarantined_before_checkout(self):
        fx = RuntimeFixture()
        try:
            first = fx.task("TASK-A")
            second = fx.task("TASK-B")
            bind_strict(fx, first, lineage="lane:one", goal_id="GOAL-ONE")
            bind_strict(fx, second, lineage="lane:one", goal_id="GOAL-ONE")
            fx.registry([first, second])
            runtime = HeartbeatRuntime(fx.root)
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            events = []
            runtime._preflight_ready_tasks(registry, 1, events)
            states = {item["task_id"]: item["state"] for item in registry["tasks"]}
            self.assertEqual(states["TASK-A"], "HANDOFF_READY")
            self.assertEqual(states["TASK-B"], "QUARANTINED")
            event = next(e for e in events if e.get("task_id") == "TASK-B")
            self.assertEqual(event["reason"], "DUPLICATE_CANONICAL_LANE")
            self.assertEqual(event["canonical_task_id"], "TASK-A")
        finally:
            fx.close()

    def test_authority_expanding_successor_waits_for_separate_admission(self):
        fx = RuntimeFixture()
        try:
            parent = fx.task("PARENT", state="COMPLETED")
            child = fx.task("CHILD")
            bind_strict(fx, parent, lineage="lane:parent", successor_policy="INHERIT_OR_NARROW", max_depth=2, allowed_paths=["StegVerse-Labs/strict-fixture/**"], max_actions=5)
            bind_strict(fx, child, lineage="lane:child", depth=1, parent_task_id="PARENT", allowed_paths=["StegVerse-Labs/strict-fixture/**", "StegVerse-Labs/other/**"], max_actions=6)
            fx.registry([parent, child])
            runtime = HeartbeatRuntime(fx.root)
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            events = []
            runtime._preflight_ready_tasks(registry, 1, events)
            current = next(item for item in registry["tasks"] if item["task_id"] == "CHILD")
            self.assertEqual(current["state"], "ACTIVATION_PENDING")
            self.assertIn("SUCCESSOR_AUTHORITY_EXPANSION_NOT_ADMITTED", current["archive_reason_codes"])
            pending = next(e for e in events if e.get("event_type") == "successor_authority_expansion_pending")
            self.assertFalse(pending["heartbeat_grants_expansion"])
        finally:
            fx.close()

    def test_separately_admitted_expansion_returns_successor_to_ready(self):
        fx = RuntimeFixture()
        try:
            parent = fx.task("PARENT", state="COMPLETED")
            child = fx.task("CHILD", state="ACTIVATION_PENDING")
            parent_handoff = bind_strict(fx, parent, lineage="lane:parent", successor_policy="INHERIT_OR_NARROW", max_depth=2, allowed_paths=["StegVerse-Labs/strict-fixture/**"], max_actions=5)
            child_handoff = bind_strict(fx, child, lineage="lane:child", depth=1, parent_task_id="PARENT", allowed_paths=["StegVerse-Labs/strict-fixture/**", "StegVerse-Labs/other/**"], max_actions=6)
            fx.registry([parent, child])
            runtime = HeartbeatRuntime(fx.root)
            ref = "authorizations/CHILD-expansion.json"
            child_handoff["authority"]["expansion_authorization_ref"] = ref
            write(fx.root / child["handoff_ref"], child_handoff)
            write(fx.root / ref, {
                "schema": "stegverse.worker-authority-expansion/v0.1",
                "expansion_id": "EXP-CHILD",
                "status": "ADMITTED",
                "parent_task_id": "PARENT",
                "child_task_id": "CHILD",
                "parent_scope_sha256": runtime._scope_digest(parent_handoff),
                "child_scope_sha256": runtime._scope_digest(child_handoff),
                "authority_source": child_handoff["authority"]["authority_source"],
                "policy_version": child_handoff["authority"]["policy_version"],
                "heartbeat_grants_expansion": False,
                "evidence_refs": ["fixture:separate-expansion-admission"]
            })
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            registry["tasks"][1]["state"] = "ACTIVATION_PENDING"
            registry["tasks"][1]["archive_reason_codes"] = ["SUCCESSOR_AUTHORITY_EXPANSION_NOT_ADMITTED"]
            events = []
            runtime._preflight_ready_tasks(registry, 2, events)
            current = next(item for item in registry["tasks"] if item["task_id"] == "CHILD")
            self.assertEqual(current["state"], "HANDOFF_READY")
            self.assertNotIn("SUCCESSOR_AUTHORITY_EXPANSION_NOT_ADMITTED", current["archive_reason_codes"])
            admitted = next(e for e in events if e.get("event_type") == "successor_authority_expansion_admitted")
            self.assertFalse(admitted["heartbeat_granted_expansion"])
        finally:
            fx.close()

    def test_narrowed_successor_with_parent_evidence_passes_preflight(self):
        fx = RuntimeFixture()
        try:
            parent = fx.task("PARENT", state="COMPLETED")
            child = fx.task("CHILD")
            bind_strict(fx, parent, lineage="lane:parent", successor_policy="INHERIT_OR_NARROW", max_depth=2, max_actions=5)
            bind_strict(fx, child, lineage="lane:child", depth=1, parent_task_id="PARENT", max_actions=3)
            fx.registry([parent, child])
            runtime = HeartbeatRuntime(fx.root)
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            events = []
            runtime._preflight_ready_tasks(registry, 1, events)
            current = next(item for item in registry["tasks"] if item["task_id"] == "CHILD")
            self.assertEqual(current["state"], "HANDOFF_READY")
            passed = next(e for e in events if e.get("event_type") == "successor_goal_preflight_passed")
            self.assertEqual(passed["parent_task_id"], "PARENT")
            self.assertFalse(passed["authority_expanded"])
        finally:
            fx.close()

    def test_successor_without_parent_evidence_is_quarantined(self):
        fx = RuntimeFixture()
        try:
            child = fx.task("CHILD")
            bind_strict(fx, child, lineage="lane:child", depth=1, parent_task_id="MISSING")
            fx.registry([child])
            runtime = HeartbeatRuntime(fx.root)
            registry = json.loads((fx.root / "control/worker-registry.json").read_text())
            events = []
            runtime._preflight_ready_tasks(registry, 1, events)
            self.assertEqual(registry["tasks"][0]["state"], "QUARANTINED")
            self.assertIn("SUCCESSOR_PARENT_EVIDENCE_MISSING", registry["tasks"][0]["archive_reason_codes"])
        finally:
            fx.close()


if __name__ == "__main__":
    unittest.main()
