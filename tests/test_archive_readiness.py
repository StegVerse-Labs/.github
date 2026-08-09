#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

with (ROOT / "control" / "archive-readiness.json").open("r", encoding="utf-8") as f:
    GATE = json.load(f)
with (ROOT / "control" / "worker-registry.json").open("r", encoding="utf-8") as f:
    REGISTRY = json.load(f)

TERMINAL = {"COMPLETED", "COMPLETE", "CLOSED", "CANCELLED", "SUPERSEDED"}


def archive_allowed(gate, registry):
    tasks = {t["task_id"]: t for t in registry.get("tasks", [])}
    unfinished = gate.get("unfinished_production_tasks", [])
    all_terminal = all((tasks.get(e["task_id"]) or {}).get("state") in TERMINAL for e in unfinished) if unfinished else True
    all_progressing = bool(unfinished) and all(e.get("progress_class") == "PROGRESSING" for e in unfinished)
    return all_terminal or all_progressing


class ArchiveReadinessTests(unittest.TestCase):
    def test_current_state_is_not_archive_ready(self):
        self.assertFalse(GATE["thread_archive_ready"])
        self.assertFalse(archive_allowed(GATE, REGISTRY))

    def test_busy_or_claimed_does_not_equal_progress(self):
        for entry in GATE["unfinished_production_tasks"]:
            self.assertNotEqual(entry["progress_class"], "PROGRESSING")

    def test_monitoring_blocked_cannot_be_archived(self):
        gate = copy.deepcopy(GATE)
        gate["thread_archive_ready"] = True
        self.assertFalse(archive_allowed(gate, REGISTRY))

    def test_all_terminal_can_archive(self):
        registry = copy.deepcopy(REGISTRY)
        target_ids = {e["task_id"] for e in GATE["unfinished_production_tasks"]}
        for task in registry["tasks"]:
            if task["task_id"] in target_ids:
                task["state"] = "COMPLETED"
        self.assertTrue(archive_allowed(GATE, registry))

    def test_all_demonstrably_progressing_can_handoff(self):
        gate = copy.deepcopy(GATE)
        for entry in gate["unfinished_production_tasks"]:
            entry["progress_class"] = "PROGRESSING"
        self.assertTrue(archive_allowed(gate, REGISTRY))


if __name__ == "__main__":
    unittest.main()
