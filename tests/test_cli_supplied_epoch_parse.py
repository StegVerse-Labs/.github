"""Every --hb-epoch command line hands the raw text to the shared supplied-epoch rule.

An argparse `type=int` coerced '+33', fullwidth '３３' and ' 33' to 33 before
the kernel's supplied_epoch_failure ever saw them, and the command then wrote
a receipt. Each command now parses --hb-epoch as a string: a coerced, non-ASCII,
fractional, boolean or empty value is refused with the six-field FAIL_CLOSED,
the exit is non-zero and nothing is written. '4096' is accepted.

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

ROOT = Path(__file__).resolve().parents[1]
PREDICATE = "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
REFUSED = ("+33", "３３", " 33", "True", "abc", "33.7", "")
SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64

#: Each command, with arguments that would otherwise reach a write.
COMMANDS = {
    ".stegverse/transition-ledger/emit.py": [
        "--transition-id", "t-cli-epoch", "--transition-class", "TEST",
        "--predecessor-state-sha256", SHA_A, "--successor-state-sha256", SHA_B],
    "resident-runtime/intr_destination_ingress.py": [
        "--payload", "payload.json", "--registry", "registry.json", "--out", "out.json"],
    "resident-runtime/organization_egress_boundary.py": [
        "--destination-organization", "StegVerse-org", "--payload", "payload.json",
        "--standing", "standing.json", "--out", "out.json"],
    "resident-runtime/organization_manifest_ingress.py": [
        "--manifest", "manifest.json", "--registry", "registry.json", "--out", "out.json"],
}


#: organization_manifest_ingress imports the SDK at load. Where it is not
#: installed, a stub that refuses every manifest stands in for it.
SDK_STUB = {
    "__init__.py": "",
    "manifest_contract.py": "def validate_ingress_manifest(*a, **k):\n    raise ValueError('STUB_SDK')\n",
    "manifest_state_transition_runtime.py": (
        "RESULT_SCHEMA = 'stub'\n"
        "def derive_execution_request(*a, **k):\n    raise ValueError('STUB_SDK')\n"
        "def admit_runtime_result(*a, **k):\n    raise ValueError('STUB_SDK')\n"),
    "route_resolution.py": "def route_from_manifest(*a, **k):\n    raise ValueError('STUB_SDK')\n",
}


def sdk_path():
    if importlib.util.find_spec("stegverse") is not None:
        return None
    directory = Path(tempfile.mkdtemp())
    (directory / "stegverse").mkdir()
    for name, text in SDK_STUB.items():
        (directory / "stegverse" / name).write_text(text, encoding="utf-8")
    return directory


class CliSuppliedEpochParseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sdk = sdk_path()
        if cls.sdk is not None:
            cls.addClassCleanup(__import__("shutil").rmtree, cls.sdk, True)

    def run_cli(self, relative, epoch):
        with tempfile.TemporaryDirectory() as work:
            ledgers = {name: Path(work) / name for name in ("org-ledger", "repo-ledger")}
            for path in ledgers.values():
                path.mkdir()
            env = {**os.environ, "STEGVERSE_ORG_LEDGER_ROOT": str(ledgers["org-ledger"]),
                   "STEGVERSE_REPO_LEDGER_ROOT": str(ledgers["repo-ledger"])}
            if self.sdk is not None:
                env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(self.sdk), env.get("PYTHONPATH")]))
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / relative), *COMMANDS[relative], "--hb-epoch=" + epoch],
                capture_output=True, text=True, env=env, cwd=work, timeout=120)
            written = sorted(str(p.relative_to(work)) for p in Path(work).rglob("*") if p.is_file())
        return completed, written

    def test_each_command_refuses_a_coerced_or_empty_epoch_and_writes_nothing(self):
        for relative in COMMANDS:
            for epoch in REFUSED:
                with self.subTest(command=relative, epoch=epoch):
                    completed, written = self.run_cli(relative, epoch)
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    refusal = json.loads(completed.stdout.strip().splitlines()[-1])
                    self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
                    for field in SIX_FIELDS:
                        self.assertTrue(refusal.get(field), field)
                    self.assertEqual(refusal["failed_predicate"], PREDICATE)
                    self.assertEqual(refusal["failure_code"], "HB_EPOCH_INVALID")
                    self.assertIn(relative, refusal["retry_entrypoint"])
                    self.assertIn("--hb-epoch", refusal["retry_entrypoint"])
                    self.assertEqual(written, [])

    def test_each_command_passes_4096_through_the_epoch_gate(self):
        # The resident commands then stop on their absent input files; only
        # the epoch gate is under test here.
        for relative in COMMANDS:
            with self.subTest(command=relative):
                completed, _ = self.run_cli(relative, "4096")
                self.assertNotIn(PREDICATE, completed.stdout)

    def test_the_repository_append_command_records_4096_as_supplied(self):
        relative = ".stegverse/transition-ledger/emit.py"
        completed, written = self.run_cli(relative, "4096")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
        self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
        self.assertTrue(any(path.startswith("repo-ledger") for path in written))


if __name__ == "__main__":
    unittest.main()
