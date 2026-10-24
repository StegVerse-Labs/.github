"""Every workflow declares an explicit top-level `permissions` block.

Without one, GITHUB_TOKEN takes the repository's default scope, which can be
write. Each workflow therefore states its workflow-scope permissions
(`{}` or a least-privilege map such as `contents: read`); a job that truly
needs more declares it at job scope. A workflow triggered by pull_request or
pull_request_target may not declare write at workflow scope.

Stdlib only. Coexists with tests/test_transition_job_runs_on_pull_request.py
(Labs#3255), which checks job-scope write on pull_request-triggered workflows.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted(p for p in (ROOT / ".github" / "workflows").iterdir()
                   if p.is_file() and p.suffix in {".yml", ".yaml"})
PR_EVENTS = {"pull_request", "pull_request_target"}


def top_level_permissions(text: str) -> str | None:
    """The workflow-scope permissions value (inline or block), or None if absent."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^permissions:\s*(.*?)\s*(?:#.*)?$", line)
        if not match:
            continue
        if match.group(1):
            return match.group(1)
        block = []
        for follow in lines[index + 1:]:
            if follow.strip() and not follow.startswith((" ", "\t")):
                break
            if follow.strip() and not follow.strip().startswith("#"):
                block.append(follow.strip())
        return "\n".join(block)
    return None


def triggers(text: str) -> set[str]:
    match = re.search(r"^on:[ \t]*(.*)$", text, re.MULTILINE)
    if match is None:
        return set()
    inline = match.group(1).strip()
    if inline:
        return {item.strip() for item in inline.strip("[]").split(",") if item.strip()}
    events = set()
    for line in text[match.end():].splitlines():
        if line and not line.startswith(" ") and not line.startswith("#"):
            break
        found = re.match(r"^  ([a-z_]+):", line)
        if found:
            events.add(found.group(1))
    return events


class WorkflowTopLevelPermissions(unittest.TestCase):
    def test_there_are_workflows(self):
        self.assertTrue(WORKFLOWS)

    def test_every_workflow_declares_top_level_permissions(self):
        missing = [p.name for p in WORKFLOWS if top_level_permissions(p.read_text(encoding="utf-8")) is None]
        self.assertEqual(missing, [], "workflows without a top-level permissions block")

    def test_top_level_permissions_are_a_least_privilege_map(self):
        for path in WORKFLOWS:
            value = top_level_permissions(path.read_text(encoding="utf-8"))
            if value is None:
                continue
            self.assertNotIn(value, {"write-all", "read-all"}, path.name)
            if value == "{}":
                continue
            for entry in value.splitlines():
                self.assertRegex(entry, r"^[a-z-]+:\s*(read|write|none)$", f"{path.name}: {entry}")

    def test_pull_request_workflows_hold_no_write_at_workflow_scope(self):
        for path in WORKFLOWS:
            text = path.read_text(encoding="utf-8")
            if triggers(text) & PR_EVENTS:
                value = top_level_permissions(text) or ""
                self.assertNotRegex(value, r"write", path.name)

    def test_parser_reads_inline_and_block_forms(self):
        self.assertEqual(top_level_permissions("on: push\npermissions: {}\njobs:\n"), "{}")
        self.assertEqual(top_level_permissions("on: push\npermissions:\n  contents: read\n\njobs:\n"), "contents: read")
        self.assertIsNone(top_level_permissions("on: push\njobs:\n  a:\n    permissions:\n      contents: read\n"))


if __name__ == "__main__":
    unittest.main()
