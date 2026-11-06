"""merge_transfer_gitstore_sweep: a main merge whose writer run was cancelled is appended on the next push.

GitHub cancels an older pending run in a concurrency group when a newer one
queues (cancel-in-progress: false notwithstanding). StegVerse-Labs/.github
0ab9949d (#3362) and 47daca11 (#3363) lost their runs that way while the next
merge, 7963db6a, was appended by its own run. These tests rebuild that shape
in a temp git repository with synthetic commits and a synthetic ledger ref:
no clock (fixed commit dates), no network, nothing published. Every receipt
here is SYNTHETIC_NOT_LEDGERED.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:  # mirrors tests/test_merge_transfer_gitstore.py: this suite binds its own ledger locus
    import pytest
    pytestmark = pytest.mark.repository_ledger_locus
except (ImportError, AttributeError):
    pass

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "resident-runtime/merge_transfer_gitstore_sweep.py"
WRITER = ROOT / ".github/workflows/organization-ledger-merge-transfer.yml"
PENDING = ROOT / ".stegverse/merge-transfer/pending.json"
LEDGER_REF = "refs/stegverse/organization-ledger"
IDENTITY = {"GIT_AUTHOR_NAME": "sweep-test", "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "sweep-test", "GIT_COMMITTER_EMAIL": "test@invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


s = load("merge_transfer_gitstore_sweep_under_test", SCRIPT)
g = s._gitstore()
REPO = g.repository(ROOT)


def seal(body: dict) -> dict:
    return {**body, "receipt_sha256": g.sha(body)}


class Repo:
    """A temp git repository: a first-parent main of synthetic commits and a synthetic ledger ref."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.git("init", "-q")

    def git(self, *args: str, data: bytes | None = None, env: dict | None = None) -> str:
        return subprocess.run(["git", "-C", self.dir, *args], input=data, check=True, capture_output=True,
                              env={**os.environ, **IDENTITY, **(env or {})}).stdout.decode().strip()

    def main(self, names: list[str]) -> dict[str, str]:
        tree = self.git("hash-object", "-t", "tree", "-w", "--stdin", data=b"")
        out, parent = {}, None
        for name in names:
            parent = self.git("commit-tree", tree, *(["-p", parent] if parent else []), data=name.encode())
            out[name] = parent
        self.git("update-ref", "refs/heads/main", parent)
        return out

    def ledger(self, merges: list[str], *, other_repo: str | None = None, break_seal_at: int | None = None) -> None:
        """A chain of org receipts, oldest first; each names one merge (or a non-transfer operation if None)."""
        files, previous = {}, None
        for i, merge in enumerate(merges):
            boundary = ({"operation": g.OPERATION, "repository": other_repo or REPO, "merge_commit": merge}
                        if merge else {"operation": "INTR_PATH_TRANSFER", "repository": REPO})
            receipt = seal({"boundary_evidence": boundary, "previous_receipt_sha256": previous, "n": i})
            if break_seal_at == i:
                receipt = {**receipt, "n": -1}
            files[g.receipt_key(receipt["receipt_sha256"])] = receipt
            previous = receipt["receipt_sha256"]
        files[g.HEAD_KEY] = {"receipt_sha256": previous}
        index = {"GIT_INDEX_FILE": os.path.join(self.dir, ".git", "ledger-index")}
        self.git("read-tree", "--empty", env=index)
        for path, value in files.items():
            oid = self.git("hash-object", "-w", "--stdin", data=json.dumps(value, sort_keys=True).encode())
            self.git("update-index", "--add", "--cacheinfo", "100644," + oid + "," + path, env=index)
        tree = self.git("write-tree", env=index)
        self.git("update-ref", LEDGER_REF, self.git("commit-tree", tree, data=b"synthetic ledger"))

    def readers(self):
        return g.bind_readers(ROOT, git_dir=os.path.join(self.dir, ".git"), ref=LEDGER_REF, namespace="")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.tmp.cleanup()


class Sweep(unittest.TestCase):
    NAMES = ["pre-writer", "anchor", "m3362-cancelled", "m3363-cancelled", "m7963-own-run", "pushed"]

    def test_the_cancelled_merges_behind_a_later_receipt_are_swept(self):
        with Repo() as r:
            c = r.main(self.NAMES)
            ledgered = {c["anchor"], c["m7963-own-run"]}
            swept, anchor = s.unledgered_since_anchor(c["pushed"], ledgered, r.dir)
            self.assertEqual(anchor, c["anchor"])
            self.assertEqual(swept, [c["m3362-cancelled"], c["m3363-cancelled"], c["pushed"]])
            self.assertNotIn(c["pre-writer"], swept)

    def test_no_receipt_in_the_window_sweeps_nothing(self):
        with Repo() as r:
            c = r.main(self.NAMES)
            self.assertEqual(s.unledgered_since_anchor(c["pushed"], set(), r.dir), ([], None))
            # the window is bounded: an anchor older than the limit is not reached
            self.assertEqual(s.unledgered_since_anchor(c["pushed"], {c["anchor"]}, r.dir, limit=3), ([], None))

    def test_a_fully_ledgered_main_sweeps_nothing(self):
        with Repo() as r:
            c = r.main(self.NAMES)
            swept, anchor = s.unledgered_since_anchor(c["pushed"], set(c.values()), r.dir)
            self.assertEqual((swept, anchor), ([], c["pre-writer"]))

    def test_unreadable_history_fails_closed(self):
        with Repo() as r:
            r.main(self.NAMES)
            with self.assertRaises(SystemExit) as caught:
                s.unledgered_since_anchor("ab" * 20, set(), r.dir)
            self.assertIn("MAIN_HISTORY_UNREADABLE", str(caught.exception.code))

    def test_selection_keeps_each_commit_once_swept_first(self):
        self.assertEqual(s.select(["p1", "x", "after"], ["x", "y", "after"]), ["x", "y", "after", "p1"])


class LedgeredMerges(unittest.TestCase):
    def test_only_this_repository_s_transfer_receipts_count(self):
        with Repo() as r:
            c = r.main(["a", "b", "c"])
            r.ledger([c["a"], None, c["c"]])
            self.assertEqual(s.ledgered_merges(r.readers()[0], REPO), {c["a"], c["c"]})
            r.ledger([c["a"], c["b"]], other_repo="Example/other")
            self.assertEqual(s.ledgered_merges(r.readers()[0], REPO), set())

    def test_the_walk_stops_at_a_broken_seal(self):
        with Repo() as r:
            c = r.main(["a", "b", "c"])
            r.ledger([c["a"], c["b"], c["c"]], break_seal_at=1)
            self.assertEqual(s.ledgered_merges(r.readers()[0], REPO), {c["c"]})


class Cli(unittest.TestCase):
    def test_the_writer_s_selection_appends_the_gap_on_the_next_push(self):
        with Repo() as r:
            c = r.main(Sweep.NAMES)
            r.ledger([c["anchor"], c["m7963-own-run"]])
            pushed = Path(r.dir) / "pushed.txt"
            pushed.write_text(c["pushed"] + "\n", encoding="utf-8")
            done = subprocess.run([sys.executable, str(SCRIPT), "--after", c["pushed"], "--commits-file", str(pushed),
                                   "--git-dir", os.path.join(r.dir, ".git"), "--ref", LEDGER_REF],
                                  capture_output=True, text=True, cwd=r.dir)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(done.stdout.split(), [c["m3362-cancelled"], c["m3363-cancelled"], c["pushed"]])
            self.assertIn("anchor " + c["anchor"], done.stderr)


class Shape(unittest.TestCase):
    def test_the_writer_runs_the_sweep_over_the_pushed_selection(self):
        text = WRITER.read_text(encoding="utf-8")
        step = text.split("- name: Select the merges this push carries", 1)[1].split("\n      - name:", 1)[0]
        commits = step.index("merge_transfer_gitstore.py commits")
        sweep = step.index("merge_transfer_gitstore_sweep.py --after \"$GITHUB_SHA\"")
        self.assertLess(commits, sweep)
        self.assertIn('--git-dir "$GITHUB_WORKSPACE/.git" --ref "$LEDGER_REF"', step)
        self.assertIn('> "$RUNNER_TEMP/results/commits.txt"', step[sweep:])
        # the shared lock stays: a separate group would not stop pending runs being cancelled
        self.assertIn("concurrency:\n  group: organization-ledger\n  cancel-in-progress: false\n", text)

    def test_the_sweep_is_clock_free_and_network_free(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])}
        self.assertFalse(imported & {"time", "datetime", "socket", "urllib", "http", "requests", "ssl"}, imported)
        text = SCRIPT.read_text(encoding="utf-8")
        for verb in ('"fetch"', '"ls-remote"', '"push"', '"update-ref"', '"pull"'):
            self.assertNotIn(verb, text)  # git reads of the local object store only

    def test_the_two_cancelled_merges_are_pending(self):
        document = json.loads(PENDING.read_text(encoding="utf-8"))
        listed = [row["merge_commit"] for row in document["merges"]]
        for commit in ("0ab9949d478aa3605d7f72e3689a267305804877", "47daca119e2970588e1554624960f184e7d614ac"):
            self.assertIn(commit, listed)
        self.assertEqual(g.pending(PENDING, ROOT), listed)


if __name__ == "__main__":
    unittest.main()
