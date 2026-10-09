"""The organization manifest-ingress receipt names the revision of its own rule.

Source-only. Ledgers are written to temporary roots and nothing here is a live
receipt. The SDK package is stubbed only when it is not installed; the stub
refuses every manifest, which drives `receive` down its recorded-refusal path.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
REVISION = "0123456789abcdef0123456789abcdef01234567"


def _sdk_stub() -> dict[str, types.ModuleType]:
    """A stub SDK, or nothing when the real one is installed."""
    try:
        import stegverse.manifest_state_transition_runtime  # noqa: F401
        return {}
    except ImportError:
        pass
    package = types.ModuleType("stegverse")
    package.__path__ = []
    runtime = types.ModuleType("stegverse.manifest_state_transition_runtime")
    runtime.RESULT_SCHEMA = "stub"

    def derive_execution_request(manifest, boundary):
        raise ValueError("STUB_SDK_REFUSES_EVERY_MANIFEST")

    def admit_runtime_result(*args, **kwargs):
        raise AssertionError("not reached on the refusal path")

    def refuses_every_manifest(*args, **kwargs):
        raise ValueError("STUB_SDK_REFUSES_EVERY_MANIFEST")

    runtime.derive_execution_request = derive_execution_request
    runtime.admit_runtime_result = admit_runtime_result
    package.manifest_state_transition_runtime = runtime
    contract = types.ModuleType("stegverse.manifest_contract")
    contract.validate_ingress_manifest = refuses_every_manifest
    routes = types.ModuleType("stegverse.route_resolution")
    routes.route_from_manifest = refuses_every_manifest
    package.manifest_contract, package.route_resolution = contract, routes
    return {"stegverse": package, "stegverse.manifest_state_transition_runtime": runtime,
            "stegverse.manifest_contract": contract, "stegverse.route_resolution": routes}


def _load():
    # The stub is visible only while the module binds its imports, so no other
    # test in the same process sees a fake `stegverse` package.
    with mock.patch.dict(sys.modules, _sdk_stub()):
        spec = importlib.util.spec_from_file_location(
            "organization_manifest_ingress_under_test",
            ROOT / "resident-runtime/organization_manifest_ingress.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


ingress = _load()


class RecomputationRuleRefTest(unittest.TestCase):
    def test_github_sha_is_used_in_actions(self):
        self.assertEqual(
            ingress.recomputation_rule_ref({"GITHUB_SHA": REVISION}),
            f"StegVerse-Labs/.github@{REVISION}:resident-runtime/organization_manifest_ingress.py")

    def test_local_head_is_used_outside_actions(self):
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(ingress.recomputation_rule_ref({}),
                         f"StegVerse-Labs/.github@{head}:resident-runtime/organization_manifest_ingress.py")

    def test_unresolvable_revision_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": temp}):
                with self.assertRaisesRegex(RuntimeError, "RECOMPUTATION_RULE_REVISION_UNRESOLVABLE"):
                    ingress.recomputation_rule_ref({}, root=Path(temp))
        with self.assertRaisesRegex(RuntimeError, "RECOMPUTATION_RULE_REVISION_UNRESOLVABLE"):
            ingress.recomputation_rule_ref({"GITHUB_SHA": "not-a-revision"})


class ReceiptBindingTest(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        base = Path(self._temp.name)
        self.org_root = base / "org"
        self._env = mock.patch.dict(os.environ, {
            "GITHUB_SHA": REVISION,
            "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
            "STEGVERSE_REPO_LEDGER_ROOT": str(base / "repo"),
        })
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._temp.cleanup()

    def _receipt(self, result):
        digest = result["refusal_organization_receipt_sha256"].split(":", 1)[1]
        return json.loads((self.org_root / "receipts" / f"{digest}.json").read_text())

    def test_refusal_receipt_binds_the_rule_ref_into_its_digest(self):
        result = ingress.receive({"processing": {"capability": "x"}}, registry={})
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        expected = f"StegVerse-Labs/.github@{REVISION}:resident-runtime/organization_manifest_ingress.py"
        self.assertEqual(result["recomputation_rule_ref"], expected)

        receipt = self._receipt(result)
        self.assertEqual(receipt["boundary_evidence"]["recomputation_rule_ref"], expected)
        body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        self.assertEqual(ingress.organization_ledger.sha(body), receipt["receipt_sha256"])

        tampered = json.loads(json.dumps(body))
        tampered["boundary_evidence"]["recomputation_rule_ref"] = expected.replace(REVISION, "f" * 40)
        self.assertNotEqual(ingress.organization_ledger.sha(tampered), receipt["receipt_sha256"])

    def test_unresolvable_revision_writes_no_receipt(self):
        with mock.patch.object(ingress, "recomputation_rule_ref",
                               side_effect=RuntimeError("RECOMPUTATION_RULE_REVISION_UNRESOLVABLE")):
            with self.assertRaises(RuntimeError):
                ingress.receive({}, registry={})
        self.assertFalse((self.org_root / "receipts").exists())

    def test_step_summary_carries_only_non_secret_fields(self):
        result = ingress.receive({"processing": {"capability": "x"}}, registry={})
        with tempfile.TemporaryDirectory() as temp:
            summary = Path(temp) / "summary.md"
            environ = {"GITHUB_STEP_SUMMARY": str(summary), "GITHUB_RUN_ID": "42",
                       "GITHUB_SHA": REVISION, "GITHUB_TOKEN": "must-not-appear"}
            self.assertTrue(ingress.write_step_summary(result, environ))
            text = summary.read_text()
        projection = ingress.step_summary_projection(result, environ)
        self.assertEqual(tuple(projection), ingress.STEP_SUMMARY_FIELDS)
        self.assertEqual(projection["receipt_id"], result["refusal_transition_id"])
        self.assertEqual(projection["receipt_sha256"], result["refusal_organization_receipt_sha256"])
        self.assertEqual(projection["recomputation_rule_ref"], result["recomputation_rule_ref"])
        self.assertEqual((projection["run_id"], projection["commit"]), ("42", REVISION))
        self.assertNotIn("must-not-appear", text)
        self.assertEqual(sorted(re.findall(r"^\| (\w+) \| `", text, re.M)),
                         sorted(ingress.STEP_SUMMARY_FIELDS))
        self.assertFalse(ingress.write_step_summary(result, {}))


if __name__ == "__main__":
    unittest.main()
