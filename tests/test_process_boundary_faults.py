"""process_boundary.py fault semantics, aligned to Data-Continuation/.github#10.

The Labs-local processor keeps its own processing. Only its faults change:
- an `--envelope` or `--registry` that cannot be read or parsed, or is not a
  JSON object, is a TERMINAL six-field PROCESS_BOUNDARY_INPUT_FAULT, exit 65,
  with nothing written;
- an `--out` it cannot write is a NON-terminal six-field
  PROCESS_BOUNDARY_WRITE_FAULT, exit 75, and no partial or temporary file stays;
- valid input writes the same bytes, and prints the same line, as before.
`sdk_manifest_crossing` carries either record as `far_side_fault` without a
traceback.

Source validation only. No authority effect is claimed.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tests.test_boundary_processing_selection as fixture

ROOT = Path(__file__).resolve().parents[1]
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
ROW = {"service_id": "target.diag", "boundary_role": "BOUNDARY_LOCAL_DIAGNOSTIC"}


class ProcessBoundaryFaultTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "org-boundary/runtime").mkdir(parents=True)
        for name in ("process_boundary.py", "manifest_selection.py", "node_standing.py"):
            shutil.copy2(ROOT / "org-boundary/runtime" / name, self.root / "org-boundary/runtime" / name)
        (self.root / "docs").mkdir()
        shutil.copy2(ROOT / fixture.CONTRACT, self.root / fixture.CONTRACT)
        self.work = self.root / "work"
        self.work.mkdir()
        packet = fixture.K.build_packet(origin_org="Source-Org", origin_service="source.sdk",
                                        destination_org="Target-Org", destination_service="target.diag",
                                        payload=fixture.manifest("governance", fixture.GOVERNANCE_ROUTE),
                                        standing=fixture.GENESIS)
        self.envelope = self.work / "envelope.json"
        self.envelope.write_text(json.dumps(packet))
        self.registry = self.work / "registry.json"
        self.registry.write_text(json.dumps({"organization": "Target-Org", "services": [ROW]}))

    def run_boundary(self, envelope, registry, out):
        return subprocess.run([sys.executable, "-B", str(self.root / "org-boundary/runtime/process_boundary.py"),
                               "--envelope", str(envelope), "--registry", str(registry), "--out", str(out)],
                              capture_output=True, text=True, cwd=self.root, timeout=120)

    def record(self, completed):
        self.assertNotIn("Traceback", completed.stderr)
        record = json.loads(completed.stdout.strip().splitlines()[-1])
        for field in SIX_FIELDS:
            self.assertTrue(str(record.get(field) or "").strip(), field)
        return record

    def test_valid_input_writes_the_result_atomically_and_prints_pass(self):
        out = self.work / "result" / "execution.json"
        completed = self.run_boundary(self.envelope, self.registry, out)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(out.read_text())
        self.assertEqual(out.read_text(), json.dumps(result, indent=2, sort_keys=True) + "\n")
        self.assertEqual(json.loads(completed.stdout),
                         {"status": "PASS", "terminal_receipt_id": result["reconstruction"]["terminal_receipt_id"]})
        self.assertEqual(sorted(p.name for p in out.parent.iterdir()), ["execution.json"])

    def test_bad_input_is_a_terminal_fault_with_exit_65_and_nothing_written(self):
        (self.work / "not-json.json").write_text("not json")
        (self.work / "list.json").write_text("[1]")
        (self.work / "binary.json").write_bytes(b"\xff\xfe\x00")
        (self.work / "a-directory").mkdir()
        bad = {"missing": self.work / "missing.json", "directory": self.work / "a-directory",
               "undecodable": self.work / "binary.json", "not-json": self.work / "not-json.json",
               "wrong-type": self.work / "list.json"}
        out = self.work / "out" / "execution.json"
        for argument in ("--envelope", "--registry"):
            for label, path in bad.items():
                with self.subTest(argument=argument, input=label):
                    envelope = path if argument == "--envelope" else self.envelope
                    registry = path if argument == "--registry" else self.registry
                    completed = self.run_boundary(envelope, registry, out)
                    self.assertEqual(completed.returncode, 65, completed.stdout)
                    record = self.record(completed)
                    self.assertEqual(record["failure_code"], "PROCESS_BOUNDARY_INPUT_FAULT")
                    self.assertIs(record["terminal"], True)
                    self.assertTrue(record["detail"].startswith(argument + ": "), record["detail"])
                    self.assertFalse((self.work / "out").exists())

    def test_an_unwritable_out_is_a_non_terminal_fault_with_exit_75_and_no_partial_file(self):
        cases = {"out-is-a-directory": self.work / "taken",
                 "parent-is-a-file": self.work / "a-file" / "execution.json"}
        (self.work / "taken").mkdir()
        (self.work / "a-file").write_text("occupied")
        for label, out in cases.items():
            with self.subTest(case=label):
                before = sorted(p.relative_to(self.work).as_posix() for p in self.work.rglob("*"))
                completed = self.run_boundary(self.envelope, self.registry, out)
                self.assertEqual(completed.returncode, 75, completed.stdout)
                record = self.record(completed)
                self.assertEqual(record["failure_code"], "PROCESS_BOUNDARY_WRITE_FAULT")
                self.assertIs(record["terminal"], False)
                after = sorted(p.relative_to(self.work).as_posix() for p in self.work.rglob("*"))
                self.assertEqual(after, before, "no partial or temporary file stays")


class CrossingCarriesTheFaultTests(unittest.TestCase):
    def test_exit_65_and_75_are_carried_as_far_side_fault_without_a_traceback(self):
        crossing = fixture.importlib.util.module_from_spec(fixture.importlib.util.spec_from_file_location(
            "sdk_manifest_crossing_faults", ROOT / "resident-runtime/sdk_manifest_crossing.py"))
        crossing.__spec__.loader.exec_module(crossing)
        for code, terminal in ((65, True), (75, False)):
            with self.subTest(exit=code):
                record = {"failure_code": "F", "terminal": terminal}
                done = subprocess.CompletedProcess([], code, stdout=json.dumps(record) + "\n", stderr="")
                registry = {"organization": "StegVerse-Labs", "services": []}
                with mock.patch.object(crossing.subprocess, "run", return_value=done), \
                     mock.patch.object(crossing, "declared_destination",
                                       return_value={"surface": "s", "transport": "INTERLOCK_INTR",
                                                     "far_side_transition_required": False}), \
                     mock.patch.object(crossing, "processing_service", return_value={"service_id": "x"}), \
                     mock.patch.object(crossing, "crossing_packet",
                                       return_value={"payload": {"manifest_sha256": "m"}, "packet_id": "p"}), \
                     mock.patch.object(crossing.intr_transport, "validate_org_crossing"):
                    result = crossing.cross({}, registry=registry, standing=fixture.GENESIS, packet_id="p")
                self.assertIs(result["crossing_completed"], False)
                self.assertEqual(result["far_side_fault"], record)
                self.assertIs(result["retry_permitted"], not terminal)


if __name__ == "__main__":
    unittest.main()
