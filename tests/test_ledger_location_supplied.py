"""The ledgers are written only where they were supplied or declared, never where the host is.

The repository ledger's location is supplied by whatever materialized the
execution, as the federation mesh is; with no supplied root its append fails
closed, names the missing location and writes nothing. The organization
ledger's locus is declared by the Organization manifest (OL-1b), so an
unsupplied cache resolves that declared locus -- never a host home or state
directory -- and an append the locus refuses fails closed and commits nothing.

Source validation only. The declared locus is a temporary bare repository
standing in for it (CI evidence only). No authority effect is claimed.
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

from tests.organization_ledger_standin import remote_head, standin_environment, standin_locus

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

    def test_an_unsupplied_organization_ledger_root_resolves_the_declared_locus(self):
        with standin_locus():
            with mock.patch.dict(os.environ, unsupplied(self.home, self.state), clear=True):
                root = organization.ledger_root()
        self.assertEqual(organization.bound_locus(root), organization.declared_locus())
        self.assertNotIn(Path(self.home), root.parents)
        self.assertNotIn(Path(self.state), root.parents)
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
            with standin_locus(), mock.patch.dict(os.environ, env):
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
            with standin_locus(work) as remote:
                hook = remote / "hooks" / "pre-receive"
                hook.write_text("#!/bin/sh\nexit 1\n")
                hook.chmod(0o755)
                completed = subprocess.run(
                    [sys.executable, "-B", str(ROOT / "resident-runtime/aggregate_repo_transition.py"),
                     "--repo-receipt", str(receipt), "--predecessor-org-state-sha256", "GENESIS",
                     "--successor-org-state-sha256", "sha256:" + "b" * 64],
                    capture_output=True, text=True, env={**unsupplied(self.home, self.state),
                                                         **standin_environment(remote)},
                    cwd=work, timeout=120)
                self.assertIsNone(remote_head(remote))
        self.assertEqual(completed.returncode, 1, completed.stderr)
        refusal = json.loads(completed.stdout)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failed_predicate"], "ORGANIZATION_LEDGER_REF_WRITE_AUTHORIZED")
        self.assertIs(refusal["consequence_committed"], False)
        self.assertTrue(refusal["retry_entrypoint"])
        self.assertHostUntouched()


if __name__ == "__main__":
    unittest.main()
