"""Ledger-writing workflows are split: PR-facing checks hold no write
permission, and the publishing half lives in writer-only workflows that never
trigger on pull_request.

- PR-facing (organization-ledger-transition.yml; organization-claim-allocator-
  transition.yml where present, Labs#3241): triggered by pull_request only,
  contents: read, no persisted credential, no push; its `transition` job runs
  (never skips) the PR-safe dry run / verify against a temporary ledger.
- Writer-only (*-writer.yml): push to main / workflow_dispatch only, job-scoped
  contents: write, the shared organization-ledger lock, fast-forward push.
- Repository-wide: no workflow triggered by pull_request or
  pull_request_target declares a write permission.

Stdlib only (no YAML dependency).
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
LEDGER_PR = WORKFLOWS_DIR / "organization-ledger-transition.yml"
LEDGER_WRITER = WORKFLOWS_DIR / "organization-ledger-transition-writer.yml"
ALLOCATOR_PR = WORKFLOWS_DIR / "organization-claim-allocator-transition.yml"
ALLOCATOR_WRITER = WORKFLOWS_DIR / "organization-claim-allocator-transition-writer.yml"
PAIRS = tuple((pr, writer) for pr, writer in ((LEDGER_PR, LEDGER_WRITER), (ALLOCATOR_PR, ALLOCATOR_WRITER))
              if pr.is_file())
PR_EVENTS = {"pull_request", "pull_request_target"}
WRITE = re.compile(r"^\s*(?:[a-z-]+:\s*write\b|permissions:\s*write-all\b)", re.MULTILINE)


def triggers(text: str) -> set[str]:
    match = re.search(r"^on:[ \t]*(.*)$", text, re.MULTILINE)
    if match is None:
        match = re.search(r"^'?on'?:[ \t]*(.*)$", text, re.MULTILINE)
    inline = match.group(1).strip()
    if inline:
        return {item.strip() for item in inline.strip("[]").split(",") if item.strip()}
    block = text[match.end():]
    events = set()
    for line in block.splitlines():
        if line and not line.startswith(" ") and not line.startswith("#"):
            break
        found = re.match(r"^  ([a-z_]+):", line)
        if found:
            events.add(found.group(1))
    return events


def jobs(text: str) -> dict[str, str]:
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([A-Za-z0-9_-]+):\n", body, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def header(job: str) -> str:
    return job.split("\n    steps:\n", 1)[0]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PullRequestRunsHoldNoWritePermission(unittest.TestCase):
    def test_no_pull_request_triggered_workflow_declares_a_write_permission(self):
        checked = 0
        for path in sorted(WORKFLOWS_DIR.glob("*.y*ml")):
            text = read(path)
            if triggers(text) & PR_EVENTS:
                checked += 1
                self.assertIsNone(WRITE.search(text), f"{path.name} is pull_request-triggered and declares write")
        self.assertGreater(checked, 0)

    def test_the_ledger_pair_is_covered(self):
        self.assertIn((LEDGER_PR, LEDGER_WRITER), PAIRS)

    def test_pr_facing_workflows_trigger_on_pull_request_only_with_contents_read(self):
        for pr, _ in PAIRS:
            text = read(pr)
            self.assertEqual(triggers(text), {"pull_request"}, pr.name)
            self.assertIn("\npermissions:\n  contents: read\n", text, pr.name)
            for name, job in jobs(text).items():
                self.assertNotIn("write", header(job), f"{pr.name}:{name}")
            for forbidden in ("git push", 'extraheader="$auth_header"', "secrets.", "github.token", "GITHUB_TOKEN",
                              "--force", "$GITHUB_WORKSPACE/.git"):
                self.assertNotIn(forbidden, text, f"{pr.name}: {forbidden}")
            blocks = text.split("uses: actions/checkout@")[1:]
            self.assertTrue(blocks, pr.name)
            for block in blocks:
                self.assertIn("persist-credentials: false", "\n".join(block.splitlines()[:5]), pr.name)

    def test_pr_transition_job_runs_and_is_never_skipped(self):
        for pr, _ in PAIRS:
            text = read(pr)
            transition = jobs(text)["transition"]
            self.assertNotIn("\n    if:", "\n" + header(transition), pr.name)
            self.assertIn("    permissions:\n      contents: read\n", header(transition) + "\n", pr.name)
            self.assertNotIn("        if: github.event_name", transition, pr.name)
            self.assertIn('git init -q --bare "$dry"', transition, pr.name)
            self.assertIn("credential.helper=", transition, pr.name)
            self.assertIn('merge-base --is-ancestor "$before"', transition, pr.name)
            self.assertIn('"consequence_committed": False', transition, pr.name)

    def test_pr_runs_never_enter_the_writer_lock(self):
        for pr, _ in PAIRS:
            text = read(pr)
            self.assertIn("  group: organization-ledger-pr-dry-run-${{ github.event.pull_request.number }}\n", text)
            self.assertNotIn("  group: organization-ledger\n", text, pr.name)


class WriterWorkflowsNeverTriggerOnPullRequest(unittest.TestCase):
    def test_writer_triggers_are_push_to_main_or_dispatch_only(self):
        for pr, writer in PAIRS:
            self.assertTrue(writer.is_file(), f"{pr.name} has no writer-only workflow")
            text = read(writer)
            events = triggers(text)
            self.assertFalse(events & PR_EVENTS, writer.name)
            self.assertTrue(events <= {"push", "workflow_dispatch"}, (writer.name, events))
            if "push" in events:
                self.assertIn("  push:\n    branches: [main]\n", text, writer.name)

    def test_writer_holds_write_only_at_job_scope_under_the_shared_lock(self):
        for _, writer in PAIRS:
            text = read(writer)
            self.assertIn("\npermissions:\n  contents: read\n", text, writer.name)
            self.assertIn("    permissions:\n      contents: write\n", text, writer.name)
            self.assertIn("concurrency:\n  group: organization-ledger\n  cancel-in-progress: false\n", text, writer.name)
            self.assertIn('git push origin "$LEDGER_REF:$LEDGER_REF"', text, writer.name)
            self.assertIn("merge-base --is-ancestor", text, writer.name)
            self.assertNotIn("--force", text, writer.name)
            self.assertNotIn("secrets.", text, writer.name)
            self.assertNotIn("pull_request", text.split("\njobs:\n", 1)[1], writer.name)

    def test_split_files_are_registered(self):
        registry = json.loads(read(ROOT / "control" / "workflow-surface-registry.json"))
        entries = {entry["path"]: entry for entry in registry["surfaces"]}
        for pr, writer in PAIRS:
            for path in (pr, writer):
                rel = path.relative_to(ROOT).as_posix()
                self.assertIn(rel, entries)
                self.assertEqual(entries[rel]["classification"], "KEEP_STANDALONE_EXCEPTION", rel)
                self.assertTrue(entries[rel]["owner"].strip(), rel)
            self.assertIn("never triggers on pull_request", entries[writer.relative_to(ROOT).as_posix()]["reason"])
            self.assertIn("contents: read", entries[pr.relative_to(ROOT).as_posix()]["reason"])


class DryRunScope(unittest.TestCase):
    @unittest.skipUnless(ALLOCATOR_PR.is_file(), "allocator workflow not on this tree (arrives with Labs#3241)")
    def test_allocator_dry_run_runs_the_same_consumer_without_an_epoch(self):
        transition = jobs(read(ALLOCATOR_PR))["transition"]
        self.assertIn("scripts/consume_org_claim_allocator_request.py", transition)
        self.assertIn('--repo-ledger-root "git+$DRY_RUN_LEDGER#$LEDGER_REF:$REPO_LEDGER_NAMESPACE"', transition)
        self.assertIn("--readback-result", transition)
        self.assertNotIn("--hb-epoch", transition)
        self.assertNotIn("--org-ledger-root", transition)

    def test_ledger_verify_appends_nothing_and_synthesizes_no_epoch(self):
        transition = jobs(read(LEDGER_PR))["transition"]
        self.assertIn("organization_ledger_readback.py", transition)
        self.assertNotIn("--self-close", transition)
        self.assertNotIn("HB_EPOCH", transition)
        self.assertIn('"append_attempted": False', transition)


if __name__ == "__main__":
    unittest.main()
