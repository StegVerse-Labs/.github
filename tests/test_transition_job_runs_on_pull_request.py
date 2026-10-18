"""The `transition` job reports pass/fail on pull_request instead of skipping,
without letting a pull_request run publish to the Organization ledger.

Both ledger-writing workflows keep their publishing steps gated on
github.event_name != 'pull_request'; on pull_request the same job runs a
PR-safe dry run / verify against a temporary copy of the published ledger,
with no persisted credential and no push. Stdlib only (no YAML dependency).
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOCATOR = ROOT / ".github/workflows/organization-claim-allocator-transition.yml"
LEDGER = ROOT / ".github/workflows/organization-ledger-transition.yml"
# Every ledger-writing workflow with a `transition` job present on this tree.
# The allocator workflow arrives with Labs#3241; the ledger workflow is on main.
WORKFLOWS = tuple(path for path in (ALLOCATOR, LEDGER) if path.is_file())
PR = "        if: github.event_name == 'pull_request'"
NOT_PR = "        if: github.event_name != 'pull_request'"


def transition_job(text: str) -> str:
    start = text.index("\n  transition:\n")
    return text[start:]


def steps(job: str) -> list[str]:
    body = job.split("\n    steps:\n", 1)[1]
    return ["      - " + chunk for chunk in re.split(r"\n      - ", "\n" + body)[1:]]


class TransitionJobRunsOnPullRequest(unittest.TestCase):
    def test_job_is_not_skipped_on_pull_request(self):
        for path in WORKFLOWS:
            text = path.read_text(encoding="utf-8")
            self.assertIn("\n  pull_request:\n", text, path.name)
            job = transition_job(text)
            header = job.split("\n    steps:\n", 1)[0]
            self.assertNotIn("\n    if:", header, path.name)

    def test_publishing_steps_never_run_on_pull_request(self):
        for path in WORKFLOWS:
            for step in steps(transition_job(path.read_text(encoding="utf-8"))):
                writes = ('git push' in step or 'extraheader="$auth_header"' in step
                          or "STEGVERSE_ORG_LEDGER_GIT_DIR=\"$GITHUB_WORKSPACE/.git\"" in step
                          or "--self-close" in step)
                if writes:
                    self.assertIn(NOT_PR, step, f"{path.name}: {step.splitlines()[0]}")
                if PR in step:
                    self.assertNotIn("git push", step, path.name)
                    self.assertNotIn("--force", step, path.name)
                    self.assertNotIn("secrets.", step, path.name)
                    self.assertNotIn("github.token", step, path.name)
                    self.assertNotIn("GITHUB_TOKEN", step, path.name)
                    self.assertNotIn("$GITHUB_WORKSPACE/.git", step, path.name)

    def test_pull_request_checkout_persists_no_credential(self):
        for path in WORKFLOWS:
            pr_checkouts = [s for s in steps(transition_job(path.read_text(encoding="utf-8")))
                            if PR in s and "actions/checkout" in s]
            self.assertEqual(len(pr_checkouts), 1, path.name)
            self.assertIn("persist-credentials: false", pr_checkouts[0], path.name)
            writer_checkouts = [s for s in steps(transition_job(path.read_text(encoding="utf-8")))
                                if NOT_PR in s and "actions/checkout" in s]
            self.assertEqual(len(writer_checkouts), 1, path.name)

    def test_pull_request_run_uses_a_temporary_ledger_and_requires_the_published_ref_unchanged(self):
        for path in WORKFLOWS:
            pr_steps = "\n".join(s for s in steps(transition_job(path.read_text(encoding="utf-8"))) if PR in s)
            self.assertIn('git init -q --bare "$dry"', pr_steps, path.name)
            self.assertIn("credential.helper=", pr_steps, path.name)
            self.assertIn("ls-remote", pr_steps, path.name)
            self.assertIn('merge-base --is-ancestor "$before"', pr_steps, path.name)
            self.assertIn('"consequence_committed": False', pr_steps, path.name)

    def test_writer_lock_is_unchanged_and_pull_request_runs_cannot_displace_it(self):
        for path in WORKFLOWS:
            text = path.read_text(encoding="utf-8")
            self.assertIn("group: organization-ledger${{ github.event_name == 'pull_request' && "
                          "format('-pr-dry-run-{0}', github.event.pull_request.number) || '' }}", text, path.name)
            self.assertIn("cancel-in-progress: false", text, path.name)

    def test_the_ledger_workflow_is_covered(self):
        self.assertIn(LEDGER, WORKFLOWS)

    @unittest.skipUnless(ALLOCATOR.is_file(), "allocator workflow not on this tree (arrives with Labs#3241)")
    def test_allocator_dry_run_runs_the_same_consumer_without_an_epoch(self):
        text = ALLOCATOR.read_text(encoding="utf-8")
        pr_steps = "\n".join(s for s in steps(transition_job(text)) if PR in s)
        self.assertIn("scripts/consume_org_claim_allocator_request.py", pr_steps)
        self.assertIn('--repo-ledger-root "git+$DRY_RUN_LEDGER#$LEDGER_REF:$REPO_LEDGER_NAMESPACE"', pr_steps)
        self.assertIn("--readback-result", pr_steps)
        self.assertNotIn("--hb-epoch", pr_steps)
        self.assertNotIn("--org-ledger-root", pr_steps)

    def test_ledger_verify_appends_nothing_and_synthesizes_no_epoch(self):
        text = LEDGER.read_text(encoding="utf-8")
        pr_steps = "\n".join(s for s in steps(transition_job(text)) if PR in s)
        self.assertIn("organization_ledger_readback.py", pr_steps)
        self.assertNotIn("intr_destination_ingress.py --", pr_steps)
        self.assertNotIn("--self-close", pr_steps)
        self.assertNotIn("HB_EPOCH", pr_steps)
        self.assertIn('"append_attempted": False', pr_steps)


if __name__ == "__main__":
    unittest.main()
