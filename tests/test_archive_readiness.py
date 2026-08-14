#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from scripts.validate_archive_readiness import evaluate

ROOT = Path(__file__).resolve().parents[1]

with (ROOT / "control" / "archive-readiness.json").open("r", encoding="utf-8") as f:
    GATE = json.load(f)
with (ROOT / "control" / "worker-registry.json").open("r", encoding="utf-8") as f:
    REGISTRY = json.load(f)


class ArchiveReadinessTests(unittest.TestCase):
    def test_current_state_is_not_archive_ready(self):
        self.assertFalse(GATE["thread_archive_ready"])
        result = evaluate(GATE, REGISTRY)
        self.assertFalse(result["archive_allowed"])

    def test_progress_label_alone_never_proves_continuation(self):
        gate = copy.deepcopy(GATE)
        for entry in gate["unfinished_production_tasks"]:
            entry["progress_class"] = "PROGRESSING"
        result = evaluate(gate, REGISTRY)
        self.assertFalse(result["archive_allowed"])
        self.assertTrue(any(row["continuation_class"] == "NO_PROVEN_EXECUTABLE_CONTINUATION" for row in result["rows"]))

    def test_all_terminal_can_archive(self):
        registry = copy.deepcopy(REGISTRY)
        target_ids = {e["task_id"] for e in GATE["unfinished_production_tasks"]}
        for task in registry["tasks"]:
            if task["task_id"] in target_ids:
                task["state"] = "COMPLETED"
        result = evaluate(GATE, registry)
        self.assertTrue(result["archive_allowed"])

    def test_live_machine_executor_is_archive_safe_continuation(self):
        gate = {"goal_id": "G", "unfinished_production_tasks": [{"task_id": "T", "progress_class": "PROGRESSING"}]}
        registry = {"tasks": [{
            "task_id": "T",
            "state": "ACTIVE",
            "executor_binding": "BOUND",
            "worker_id": "w",
            "claim_id": "c",
            "heartbeat_timing": {
                "fencing_token": 3,
                "current_transition": "IMPLEMENTING",
                "expected_next_transition": "VALIDATING",
                "start_epoch": 9,
                "expiry_epoch": 20
            },
            "lease": None
        }]}
        result = evaluate(gate, registry)
        self.assertTrue(result["archive_allowed"])
        self.assertEqual(result["rows"][0]["continuation_class"], "ACTIVE_MACHINE_EXECUTOR")

    def test_active_session_claim_is_archive_safe_only_while_live(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "claims").mkdir()
            claim = {
                "task_id": "T",
                "claim_state": "ACTIVE",
                "claim_expires_at": "2030-01-01T00:00:00Z",
                "claim_release_condition": "implementation merged and validated",
                "collision_scope": {"allowed": ["x"]}
            }
            (root / "claims/T.json").write_text(json.dumps(claim), encoding="utf-8")
            gate = {"goal_id": "G", "unfinished_production_tasks": [{
                "task_id": "T",
                "progress_class": "PROGRESSING",
                "active_session_claim_ref": "claims/T.json"
            }]}
            registry = {"tasks": [{"task_id": "T", "state": "HANDOFF_READY"}]}
            result = evaluate(gate, registry, root=root, now=datetime(2026, 8, 14, tzinfo=timezone.utc))
            self.assertTrue(result["archive_allowed"])
            self.assertEqual(result["rows"][0]["continuation_class"], "ACTIVE_SESSION_CLAIM")

    def test_expired_session_claim_does_not_make_archive_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "claims").mkdir()
            claim = {
                "task_id": "T",
                "claim_state": "ACTIVE",
                "claim_expires_at": "2026-01-01T00:00:00Z",
                "claim_release_condition": "done",
                "collision_scope": {"allowed": ["x"]}
            }
            (root / "claims/T.json").write_text(json.dumps(claim), encoding="utf-8")
            gate = {"goal_id": "G", "unfinished_production_tasks": [{"task_id": "T", "active_session_claim_ref": "claims/T.json"}]}
            registry = {"tasks": [{"task_id": "T", "state": "HANDOFF_READY"}]}
            result = evaluate(gate, registry, root=root, now=datetime(2026, 8, 14, tzinfo=timezone.utc))
            self.assertFalse(result["archive_allowed"])

    def test_blocked_task_requires_active_resolver_and_release_condition(self):
        gate = {"goal_id": "G", "unfinished_production_tasks": [{
            "task_id": "P",
            "progress_class": "MONITORING_BLOCKED",
            "resolver_task_id": "R",
            "machine_observable_release_condition": "resolver emits COMPLETED"
        }]}
        registry = {"tasks": [
            {"task_id": "P", "state": "BLOCKED"},
            {
                "task_id": "R",
                "state": "ACTIVE",
                "executor_binding": "AUTHORIZED",
                "worker_id": "resolver",
                "claim_id": "resolver-claim",
                "heartbeat_timing": {
                    "fencing_token": 7,
                    "current_transition": "RESOLVING",
                    "expected_next_transition": "RESOLVED",
                    "start_epoch": 1,
                    "expiry_epoch": 10
                },
                "lease": None
            }
        ]}
        result = evaluate(gate, registry)
        self.assertTrue(result["archive_allowed"])
        self.assertEqual(result["rows"][0]["continuation_class"], "BLOCKED_WITH_ACTIVE_MACHINE_RESOLVER")


if __name__ == "__main__":
    unittest.main()
