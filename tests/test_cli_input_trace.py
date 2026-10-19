"""F-INPUT-TRACE and F-WRITER-TRACE on the command lines B-P37 changed.

Every JSON input argument of the emit, aggregate and egress command lines is
read before, and outside, any write-fault handling. A missing path, a
directory, undecodable bytes, non-JSON text or the wrong top-level type is the
caller's fault: a TERMINAL six-field record (CLI_INPUT_UNREADABLE), exit 1,
nothing written and no traceback. The egress command line's own write fault
is a NON-terminal six-field record (EGRESS_WRITE_FAILED), exit 1, no
traceback. (batch-custody's command line takes no JSON input file.)

Supplied epochs are 4096. Source validation only. No authority effect is claimed.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import tests.test_reverse_intr_inter_org_route as route

ROOT = Path(__file__).resolve().parents[1]
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64


def files(root: Path) -> list:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


class CliInputTraceTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.inputs = self.work / "inputs"
        self.inputs.mkdir()
        self.state = self.work / "state"
        self.env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": str(self.state / "repo-ledger"),
                    "STEGVERSE_ORG_LEDGER_ROOT": str(self.state / "org-ledger"),
                    "PYTHONDONTWRITEBYTECODE": "1"}
        (self.inputs / "object.json").write_text(json.dumps({"schema": "stegverse.repo-transition-receipt/v1"}))
        (self.inputs / "not-json.json").write_text("this is not JSON")
        (self.inputs / "list.json").write_text("[1, 2]")
        (self.inputs / "binary.json").write_bytes(b"\xff\xfe\x00not utf-8")
        (self.inputs / "a-directory").mkdir()
        self.bad = {"missing": str(self.inputs / "missing.json"),
                    "directory": str(self.inputs / "a-directory"),
                    "undecodable": str(self.inputs / "binary.json"),
                    "not-json": str(self.inputs / "not-json.json"),
                    "wrong-type": str(self.inputs / "list.json")}

    def run_cli(self, relative, *arguments):
        before = files(self.work)
        completed = subprocess.run([sys.executable, "-B", str(ROOT / relative), *arguments],
                                   capture_output=True, text=True, cwd=self.work, env=self.env, timeout=120)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(files(self.work), before, "nothing is written")
        self.assertFalse(self.state.exists())
        return json.loads(completed.stdout.strip().splitlines()[-1])

    def assertTerminalInputRefusal(self, record, argument):
        self.assertEqual(record["failure_code"], "CLI_INPUT_UNREADABLE")
        self.assertIs(record["terminal"], True)
        self.assertIs(record["consequence_committed"], False)
        self.assertTrue(record["detail"].startswith(argument + ": "), record["detail"])
        for field in SIX_FIELDS:
            self.assertTrue(str(record.get(field) or "").strip(), field)

    def test_each_aggregate_input_argument_is_refused_terminal(self):
        good = str(self.inputs / "object.json")
        for argument in ("--repo-receipt", "--transition-receipt", "--parent-manifest"):
            for label, path in self.bad.items():
                with self.subTest(argument=argument, input=label):
                    arguments = ["--hb-epoch", "4096", argument, path]
                    if argument == "--parent-manifest":
                        arguments += ["--repo-receipt", good]
                    record = self.run_cli("resident-runtime/aggregate_repo_transition.py", *arguments)
                    self.assertTerminalInputRefusal(record, argument)
        for label, text in (("not-json", "not json"), ("wrong-type", "[1]")):
            with self.subTest(argument="--boundary-evidence-json", input=label):
                record = self.run_cli("resident-runtime/aggregate_repo_transition.py", "--hb-epoch", "4096",
                                      "--repo-receipt", good, "--boundary-evidence-json", text)
                self.assertTerminalInputRefusal(record, "--boundary-evidence-json")

    def test_the_emit_evidence_argument_is_refused_terminal(self):
        for label, text in (("not-json", "not json"), ("wrong-type", "[1]")):
            with self.subTest(input=label):
                record = self.run_cli(".stegverse/transition-ledger/emit.py", "--hb-epoch", "4096",
                                      "--transition-id", "t", "--transition-class", "TEST",
                                      "--predecessor-state-sha256", SHA_A, "--successor-state-sha256", SHA_B,
                                      "--evidence-json", text)
                self.assertTerminalInputRefusal(record, "--evidence-json")

    def test_each_egress_input_argument_is_refused_terminal(self):
        standing = self.inputs / "standing.json"
        standing.write_text(json.dumps(route.GENESIS))
        for argument in ("--payload", "--standing"):
            for label, path in self.bad.items():
                with self.subTest(argument=argument, input=label):
                    other = ["--standing", str(standing)] if argument == "--payload" else \
                            ["--payload", str(self.inputs / "object.json")]
                    record = self.run_cli("resident-runtime/organization_egress_boundary.py",
                                          "--destination-organization", route.PEER, "--hb-epoch", "4096",
                                          argument, path, *other)
                    self.assertTerminalInputRefusal(record, argument)


class EgressWriteFaultTests(route.ReverseIntrRouteCase):
    payload = route.GovernanceReverseLegTests.payload

    def test_an_own_write_fault_is_a_non_terminal_record_without_a_traceback(self):
        work = Path(self._work.name)
        (work / "payload.json").write_text(json.dumps(self.payload()))
        (work / "standing.json").write_text(json.dumps(route.GENESIS))
        argv = ["organization_egress_boundary.py", "--destination-organization", route.PEER,
                "--capability", "governance", "--transition-reference", "ecosystem.transition.reverse-intr.v1",
                "--payload", str(work / "payload.json"), "--standing", str(work / "standing.json"),
                "--hb-epoch", "4096"]
        out = io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(route.egress.kernel, "publish_packet", side_effect=OSError("disk full")), \
             redirect_stdout(out):
            code = route.egress.main()
        self.assertEqual(code, 1)
        record = json.loads(out.getvalue().strip().splitlines()[-1])
        self.assertEqual(record["failure_code"], "EGRESS_WRITE_FAILED")
        self.assertIs(record["terminal"], False)
        for field in SIX_FIELDS:
            self.assertTrue(str(record.get(field) or "").strip(), field)


if __name__ == "__main__":
    unittest.main()
