"""C1 (org#160 issuecomment-6353130407 section 3): the organization-ledger component validation workflow is triggered only
by state transitions (pull_request / push path filters on the component and its manifest), never by workflow_dispatch,
schedule or repository_dispatch. Stdlib only: the top-level `on:` block is read line by line."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/organization-ledger-component-validation.yml"
STATE_FILES = ["org-kernel/organization-ledger/**", "org-kernel/kernel.py",
               "data/reusable-task-components/RTC-EVIDENCE-CUSTODY-004.json"]


def on_block(text: str) -> dict[str, list[str]]:
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if re.fullmatch(r"(on|\"on\"|'on'):\s*", l))
    triggers: dict[str, list[str]] = {}
    current = None
    for l in lines[start + 1:]:
        if l and not l.startswith(" ") and not l.startswith("#"):
            break
        m = re.fullmatch(r"  ([A-Za-z_]+):.*", l)
        if m:
            current = m.group(1)
            triggers[current] = []
            continue
        m = re.fullmatch(r"\s+- '([^']+)'\s*", l)
        if m and current:
            triggers[current].append(m.group(1))
    return triggers


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.on = on_block(WORKFLOW.read_text())

    def test_only_state_transition_triggers(self):
        self.assertEqual(sorted(self.on), ["pull_request", "push"])
        code = "".join(l for l in WORKFLOW.read_text().splitlines(True) if not l.lstrip().startswith("#"))
        for banned in ("workflow_dispatch", "schedule", "repository_dispatch", "cron"):
            self.assertNotIn(banned, code)

    def test_both_triggers_filter_on_the_component_state_files(self):
        for t in ("pull_request", "push"):
            for f in STATE_FILES:
                self.assertIn(f, self.on[t], (t, f))
            self.assertIn(".github/workflows/organization-ledger-component-validation.yml", self.on[t])

    def test_parser_sees_a_dispatch_trigger(self):
        text = WORKFLOW.read_text().replace("\npermissions:", "  workflow_dispatch:\n\npermissions:", 1)
        self.assertIn("workflow_dispatch", on_block(text))


if __name__ == "__main__":
    unittest.main()
