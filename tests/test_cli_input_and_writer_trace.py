"""Writer CLIs answer in six fields, never with a traceback (F-INPUT-TRACE, F-WRITER-TRACE).

A missing, non-JSON or wrongly typed input file is the caller's fault: a
TERMINAL six-field CLI_INPUT_INVALID, a non-zero exit and nothing written,
classified before and outside the own-state fault handling. A fault in the
writer's own writes is a NON-terminal six-field WRITER_IO_FAILED, and the next
run completes.

Source validation only. No authority effect is claimed.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_cli_supplied_epoch_parse import sdk_path

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64

#: script, the input argument under test, and the other arguments it needs.
INPUTS = [
    ("resident-runtime/intr_destination_ingress.py", "--payload", ["--registry", "@registry", "--hb-epoch", "4096"]),
    ("resident-runtime/intr_destination_ingress.py", "--registry", ["--payload", "@object", "--hb-epoch", "4096"]),
    ("resident-runtime/organization_egress_boundary.py", "--standing",
     ["--destination-organization", "StegVerse-org", "--payload", "@object", "--hb-epoch", "4096"]),
    ("resident-runtime/organization_manifest_ingress.py", "--manifest", ["--registry", "@registry", "--hb-epoch", "4096"]),
    ("resident-runtime/governance_endpoint.py", "--packet", ["--out", "out.json", "--hb-epoch", "4096"]),
    ("resident-runtime/aggregate_repo_transition.py", "--repo-receipt", ["--hb-epoch", "4096"]),
    ("resident-runtime/remediation_endpoint.py", "--packet", ["--out", "out.json", "--hb-epoch", "4096"]),
    ("scripts/authorize_site_production_promotion.py", "--request", ["--hb-epoch", "4096"]),
    ("resident-runtime/submit_org_transition_to_master_records.py", "--org-receipt",
     ["--predecessor-ecosystem-state-sha256", SHA_A, "--successor-ecosystem-state-sha256", SHA_B,
      "--standing", "@object", "--mesh-root", "mesh"]),
]


class CliTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sdk = sdk_path()
        if cls.sdk is not None:
            cls.addClassCleanup(__import__("shutil").rmtree, cls.sdk, True)

    def run_cli(self, work, script, *args, env_extra=None):
        env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": str(work / "repo"),
               "STEGVERSE_ORG_LEDGER_ROOT": str(work / "org"), **(env_extra or {})}
        if self.sdk is not None:
            env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(self.sdk), env.get("PYTHONPATH")]))
        return subprocess.run([sys.executable, "-B", str(ROOT / script), *map(str, args)],
                              capture_output=True, text=True, env=env, cwd=work, timeout=120)

    def assertSixField(self, completed, *, terminal):
        self.assertNotIn("Traceback", completed.stderr)
        self.assertNotEqual(completed.returncode, 0)
        record = json.loads(completed.stdout.strip().splitlines()[-1])
        for field in SIX:
            self.assertTrue(record.get(field), field)
        self.assertIs(record["terminal"], terminal)
        return record

    def test_a_bad_input_file_is_terminal_six_field_and_writes_nothing(self):
        for script, argument, rest in INPUTS:
            for kind in ("missing", "not-json", "a-list"):
                with self.subTest(script=script, argument=argument, kind=kind), \
                        tempfile.TemporaryDirectory() as work:
                    work = Path(work)
                    (work / "object.json").write_text("{}", encoding="utf-8")
                    (work / "registry.json").write_text(
                        (ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"), encoding="utf-8")
                    bad = work / "bad.json"
                    if kind == "not-json":
                        bad.write_text("{not json", encoding="utf-8")
                    elif kind == "a-list":
                        bad.write_text("[1, 2, 3]", encoding="utf-8")
                    args = [argument, bad] + [str(work / (a[1:] + ".json")) if a.startswith("@") else a for a in rest]
                    before = sorted(p.name for p in work.rglob("*"))
                    record = self.assertSixField(self.run_cli(work, script, *args), terminal=True)
                    self.assertEqual(record["failure_code"], "CLI_INPUT_INVALID")
                    self.assertIn(argument, record["failed_predicate"])
                    self.assertEqual(sorted(p.name for p in work.rglob("*")), before)

    def test_a_bad_evidence_json_argument_is_terminal(self):
        with tempfile.TemporaryDirectory() as work:
            completed = self.run_cli(Path(work), ".stegverse/transition-ledger/emit.py",
                                     "--transition-id", "t", "--transition-class", "TEST",
                                     "--predecessor-state-sha256", SHA_A, "--successor-state-sha256", SHA_B,
                                     "--evidence-json", "{not json", "--hb-epoch", "4096")
            record = self.assertSixField(completed, terminal=True)
            self.assertEqual(record["failure_code"], "CLI_INPUT_INVALID")

    def test_a_fault_in_the_writers_own_write_is_non_terminal_and_the_next_run_completes(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            blocked = work / "repo"
            blocked.write_text("not a directory", encoding="utf-8")
            args = ["--transition-id", "t-trace", "--transition-class", "TEST",
                    "--predecessor-state-sha256", SHA_A, "--successor-state-sha256", SHA_B, "--hb-epoch", "4096"]
            record = self.assertSixField(self.run_cli(work, ".stegverse/transition-ledger/emit.py", *args),
                                         terminal=False)
            self.assertEqual(record["failure_code"], "WRITER_IO_FAILED")
            blocked.unlink()
            completed = self.run_cli(work, ".stegverse/transition-ledger/emit.py", *args)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["hb_reference"]["epoch"], 4096)


#: Every CLI here that writes a ledger or this node's state, or publishes for it.
WRITER_CLIS = (
    ".stegverse/transition-ledger/emit.py",
    "resident-runtime/intr_destination_ingress.py",
    "resident-runtime/organization_egress_boundary.py",
    "resident-runtime/organization_manifest_ingress.py",
    "resident-runtime/governance_endpoint.py",
    "resident-runtime/aggregate_repo_transition.py",
    "resident-runtime/organization_batch_custody.py",
    "resident-runtime/federation_cycle.py",
    "resident-runtime/submit_org_transition_to_master_records.py",
    "resident-runtime/ecosystem_control.py",
    "resident-runtime/organization_governance_decision.py",
    "scripts/authorize_site_production_promotion.py",
    "scripts/manage_heartbeat_subsignal.py",
)


class WriterCliSweepTests(unittest.TestCase):
    def test_every_writer_cli_runs_under_the_six_field_runner(self):
        for relative in WRITER_CLIS:
            with self.subTest(cli=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                main_block = text[text.rindex("if __name__"):]
                self.assertIn("run_writer_cli(", main_block)


if __name__ == "__main__":
    unittest.main()
