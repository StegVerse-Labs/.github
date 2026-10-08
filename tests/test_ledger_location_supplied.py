"""The organization and repository ledgers are written only where they were supplied.

A ledger is the organization's runtime reality. Its location is supplied by
whatever materialized the execution, as the federation mesh is; it is never
derived from the host. With no supplied root an append fails closed, names
the missing location, writes nothing and leaves the host untouched.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LEDGER_VARIABLES = ("STEGVERSE_ORG_LEDGER_ROOT", "STEGVERSE_REPO_LEDGER_ROOT")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


organization = _load("aggregate_repo_transition_location", "resident-runtime/aggregate_repo_transition.py")
repository = _load("transition_ledger_emit_location", ".stegverse/transition-ledger/emit.py")


def unsupplied(home, state):
    """No ledger root, and a host home and XDG state directory that must stay empty."""
    env = {key: value for key, value in os.environ.items()
           if key not in LEDGER_VARIABLES + ("XDG_STATE_HOME", "HOME")}
    env["HOME"] = home
    env["XDG_STATE_HOME"] = state
    return env


class LedgerLocationIsSuppliedTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.state = tempfile.mkdtemp()
        self.addCleanup(lambda: [__import__("shutil").rmtree(p, True) for p in (self.home, self.state)])

    def assertHostUntouched(self):
        self.assertEqual(list(Path(self.home).iterdir()), [])
        self.assertEqual(list(Path(self.state).iterdir()), [])

    def test_an_unsupplied_organization_ledger_root_fails_closed_by_name(self):
        with mock.patch.dict(os.environ, unsupplied(self.home, self.state), clear=True):
            with self.assertRaises(organization.LedgerLocationRequired) as raised:
                organization.ledger_root()
        self.assertEqual(raised.exception.failed_predicate, "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertEqual(raised.exception.variable, "STEGVERSE_ORG_LEDGER_ROOT")
        self.assertHostUntouched()

    def test_an_unsupplied_repository_ledger_root_fails_closed(self):
        with mock.patch.dict(os.environ, unsupplied(self.home, self.state), clear=True):
            with self.assertRaisesRegex(ValueError, "ledger_location_required_from_materializer"):
                repository.lr()
            with self.assertRaisesRegex(ValueError, "ledger_location_required_from_materializer"):
                repository.append("t-1", "TEST", "sha256:" + "a" * 64, "sha256:" + "b" * 64, hb_epoch=40)
        self.assertHostUntouched()

    def test_a_supplied_root_is_used_as_given(self):
        with tempfile.TemporaryDirectory() as supplied:
            env = {**unsupplied(self.home, self.state),
                   "STEGVERSE_ORG_LEDGER_ROOT": supplied, "STEGVERSE_REPO_LEDGER_ROOT": supplied}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(organization.ledger_root(), Path(supplied).resolve())
                self.assertEqual(repository.lr(), Path(supplied).resolve())
        self.assertHostUntouched()

    def test_a_repository_receipt_takes_a_supplied_epoch(self):
        # emit.py already passed `epoch=` to the kernel, which did not accept it,
        # so `--hb-epoch` raised TypeError instead of appending.
        with tempfile.TemporaryDirectory() as supplied:
            env = {**unsupplied(self.home, self.state), "STEGVERSE_REPO_LEDGER_ROOT": supplied}
            with mock.patch.dict(os.environ, env, clear=True):
                receipt = repository.append("t-epoch", "TEST", "sha256:" + "a" * 64, "sha256:" + "b" * 64,
                                            hb_epoch=40)
        self.assertEqual(receipt["hb_reference"]["epoch"], 40)
        self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
        self.assertHostUntouched()

    def test_the_append_command_records_its_refusal_and_commits_nothing(self):
        with tempfile.TemporaryDirectory() as work:
            body = {"schema": "stegverse.repo-transition-receipt/v1",
                    "repository": "StegVerse-Labs/.github", "transition_id": "unsupplied-ledger"}
            receipt = Path(work) / "receipt.json"
            receipt.write_text(json.dumps({**body, "receipt_sha256": organization.sha(body)}))
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "resident-runtime/aggregate_repo_transition.py"),
                 "--repo-receipt", str(receipt), "--predecessor-org-state-sha256", "GENESIS",
                 "--successor-org-state-sha256", "sha256:" + "b" * 64],
                capture_output=True, text=True, env=unsupplied(self.home, self.state), cwd=work, timeout=120)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        refusal = json.loads(completed.stdout)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failed_predicate"], "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertIs(refusal["consequence_committed"], False)
        self.assertTrue(refusal["retry_entrypoint"])
        self.assertHostUntouched()


if __name__ == "__main__":
    unittest.main()
