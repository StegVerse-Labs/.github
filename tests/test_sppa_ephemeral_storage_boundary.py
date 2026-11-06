"""SPPA storage-route regression; temporary empty Git stores, never live authority."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


existing = load("ephemeral_existing_tests", "tests/test_site_production_promotion_dispatched_run.py")
consumer = existing.consumer
REF = "refs/stegverse/organization-ledger"
NAMESPACE = "repository-ledger/StegVerse-Labs/.github"


class EphemeralStorageBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        for rel in (*existing.sppa_tests.SOURCE_FILES, consumer.TRANSITION):
            target = self.source / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, target)
        contract = self.source / ".stegverse/transition-ledger/org-contract.json"
        value = json.loads(contract.read_text())
        value["organization_ledger"] = {
            "store": "git", "ref": REF, "custody": "PRIVATE", "propagate_target": None,
        }
        contract.write_text(json.dumps(value))
        # Both unittest and pytest install a POSIX default for other suites.
        # Restore this fixture's declared Git topology after each dynamic load,
        # then remove the override at cleanup so neighboring tests stay isolated.
        loader = importlib.machinery.SourceFileLoader
        previous_exec = loader.exec_module

        def exec_with_declared_locus(loader_self, module):
            previous_exec(loader_self, module)
            if callable(getattr(module, "declared_ledger_locus", None)):
                module.C["organization_ledger"] = dict(value["organization_ledger"])

        patcher = mock.patch.object(loader, "exec_module", exec_with_declared_locus)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.gitdir = self.base / "ledger.git"
        self.foreign = self.base / "foreign.git"
        for path in (self.gitdir, self.foreign):
            subprocess.run(["git", "init", "--bare", "-q", str(path)], check=True)
        self.runtime = self.base / "runtime"
        request_path = self.runtime / consumer.REQUEST_RELS[0]
        request_path.parent.mkdir(parents=True)
        self.request = existing.resident_request(existing.sppa_tests.fixture())
        request_path.write_text(json.dumps(self.request))
        self.env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                    "STEGVERSE_ORG_LEDGER_GIT_DIR": str(self.gitdir)}

    def locator(self, gitdir=None, ref=REF):
        return f"git+{gitdir or self.gitdir}#{ref}:{NAMESPACE}"

    def run_case(self, locator, hosted=True, org_root=None):
        env = dict(self.env)
        if hosted:
            env["GITHUB_ACTIONS"] = "true"
        with mock.patch.dict(os.environ, env, clear=True):
            result = consumer.consume(self.source, self.runtime, repo_ledger_root=locator,
                                      org_ledger_root=org_root, hb_epoch=4096, env=env)
        self.assertFalse(result.get("receipt_appended"), result)
        self.assertFalse(result.get("promotion_may_proceed"), result)
        for gitdir in (self.gitdir, self.foreign):
            refs = subprocess.check_output(["git", "--git-dir", str(gitdir), "for-each-ref"], text=True)
            self.assertEqual(refs, "", "no test may create a ledger receipt/ref")
        return result

    def test_declared_ephemeral_route_reaches_same_fail_closed_custody_on_both_hosts(self):
        ordinary = self.run_case(self.locator(), hosted=False)
        hosted = self.run_case(self.locator())
        self.assertEqual(hosted["disposition"], "FAIL_CLOSED")
        self.assertNotEqual(hosted.get("failure_code"), consumer.HOSTED_REFUSED)
        self.assertEqual(hosted.get("failed_predicates"), ordinary.get("failed_predicates"))
        self.assertIn("organization chain unverified", self.authorization(self.locator())["evidence"]["detail"])

    def test_same_ref_on_foreign_repository_is_not_admitted(self):
        result = self.run_case(self.locator(self.foreign))
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertIn("EVENT_EPHEMERAL_REPOSITORY_LEDGER_NOT_ON_DECLARED_REF",
                      self.authorization(self.locator(self.foreign))["evidence"]["detail"])

    def authorization(self, locator):
        with mock.patch.dict(os.environ, self.env, clear=True):
            result = existing.sppa_tests.sppa.authorize(self.request["promotion_request"],
                source=self.source, repo_ledger_root=locator, hb_epoch=4096)
        self.assertFalse(result["receipt_appended"])
        self.assertFalse(result["promotion_may_proceed"])
        return result

    def test_wrong_ref_keeps_hosted_refusal(self):
        result = self.run_case(self.locator(ref="refs/stegverse/decoy"))
        self.assertEqual(result["failure_code"], consumer.HOSTED_REFUSED)

    def test_explicit_organization_root_keeps_hosted_refusal(self):
        result = self.run_case(self.locator(), org_root=self.base / "other-org")
        self.assertEqual(result["failure_code"], consumer.HOSTED_REFUSED)

    def test_absent_repository_root_keeps_hosted_refusal(self):
        result = self.run_case(None)
        self.assertEqual(result["failure_code"], consumer.HOSTED_REFUSED)

    def test_request_cannot_assert_ephemeral_route(self):
        request = {**self.request, "event_ephemeral": True, "state": "INGRESS_ADMITTED"}
        (self.runtime / consumer.REQUEST_RELS[0]).write_text(json.dumps(request))
        result = self.run_case(self.locator(ref="refs/stegverse/decoy"))
        self.assertEqual(result["failure_code"], consumer.HOSTED_REFUSED)


if __name__ == "__main__":
    unittest.main()
