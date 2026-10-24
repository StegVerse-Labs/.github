"""The federation cycle takes its epoch as supplied, never from a clock (B-P36e row 20).

federation_cycle.py stamped its cycle receipt from the host clock on every
pass. It now takes --hb-epoch (or HB_EPOCH from its dispatcher) under the
kernel's shared rule: absent or invalid is the six-field refusal, exit 1,
before anything is consumed; supplied, the cycle receipt and every crossing of
the pass carry that epoch, derived_from_clock false, with no clock read. The
activation manifest binds the epoch for its declared resident cycle entrypoint.

Source validation only. No authority effect is claimed.
"""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fc = _load("federation_cycle_epoch", "resident-runtime/federation_cycle.py")
rc = _load("resident_cycle_request", "resident-runtime/resident_cycle_request.py")


class _ClockRead:
    @staticmethod
    def now(*args, **kwargs):
        raise AssertionError("a clock was read")


class FederationCycleEpochTests(unittest.TestCase):
    def run_cycle(self, hb_epoch):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            with mock.patch.object(fc.K, "datetime", _ClockRead):
                report = fc.cycle(mesh_root=work / "mesh", node_state_root=work / "node",
                                  repo_ledger_root=work / "repo", org_ledger_root=work / "org",
                                  hb_epoch=hb_epoch)
            written = sorted(str(p.relative_to(work)) for p in work.rglob("*") if p.is_file())
        return report, written

    def test_an_absent_or_invalid_cycle_epoch_is_refused_and_nothing_is_written(self):
        for epoch in (None, "", "+33", " 33", "３３", "33.0", "31", "abc"):
            with self.subTest(epoch=epoch):
                report, written = self.run_cycle(epoch)
                self.assertEqual(report["disposition"], "FAIL_CLOSED")
                self.assertEqual(report["failure_code"],
                                 "HB_EPOCH_NOT_SUPPLIED" if epoch is None else "HB_EPOCH_INVALID")
                for field in SIX:
                    self.assertTrue(report[field], field)
                self.assertEqual(written, [])

    def test_a_supplied_4096_stamps_the_cycle_receipt_with_no_clock_read(self):
        report, written = self.run_cycle("4096")
        self.assertEqual(report["heartbeat_reference"]["epoch"], 4096)
        self.assertIs(report["heartbeat_reference"]["derived_from_clock"], False)
        self.assertTrue(any("cycles.d" in path for path in written))

    def test_the_activation_manifest_binds_the_resident_cycle_epoch(self):
        manifest = json.loads((ROOT / "resident-runtime/activation-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["resident_cycle_entrypoint"], "resident-runtime/federation_cycle.py")
        binding = manifest["resident_cycle_hb_epoch"]
        self.assertEqual(binding["argument"], "--hb-epoch")
        # Row 16: the epoch is committed before the cycle reads it (COMMITTED_REQUEST).
        self.assertEqual((binding["from"], binding["dispatch_pattern"]), ("committed_request", "COMMITTED_REQUEST"))
        self.assertIs(binding["workflow_inputs"], False)
        self.assertEqual(binding["request_path"], rc.REQUEST_PATH)
        self.assertEqual(binding["request_schema"], rc.SCHEMA)
        self.assertTrue((ROOT / binding["dispatcher"]).is_file())
        self.assertNotIn("dispatcher_status", binding)
        text = (ROOT / binding["dispatch_workflow"]).read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        trigger = lines[lines.index("on:") + 1:lines.index("permissions:")]
        self.assertEqual(trigger, ["  push:", "    branches: [main]", "    paths:", "      - '" + rc.REQUEST_PATH + "'"])
        self.assertFalse([line for line in lines if "workflow_dispatch" in line or "inputs" in line])
        self.assertIn("        run: python " + binding["dispatcher"], lines)


class CommittedRequestDispatchTests(unittest.TestCase):
    def dispatch(self, request, *argv):
        """Run the dispatcher on a request file; return (exit, stdout record, argv the cycle got)."""
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "request.json"
            if request is not None:
                path.write_text(request if isinstance(request, str) else json.dumps(request), encoding="utf-8")
            calls = []

            class Cycle:
                @staticmethod
                def main(cycle_argv):
                    calls.append(cycle_argv)
                    return 0

            out = io.StringIO()
            with mock.patch.object(rc, "_cycle", lambda: Cycle), contextlib.redirect_stdout(out):
                code = rc.K.run_writer_cli(lambda: rc.main(["--request", str(path), *argv]),
                                           retry_entrypoint="test")
        text = out.getvalue().strip()
        return code, json.loads(text) if text else None, calls

    def test_the_cycle_runs_at_the_committed_epoch_and_locations_pass_through(self):
        for epoch in ("4096", 4096):
            with self.subTest(epoch=epoch):
                code, record, calls = self.dispatch({"schema": rc.SCHEMA, "hb_epoch": epoch}, "--mesh-root", "/m")
                self.assertEqual((code, record), (0, None))
                self.assertEqual(calls, [["--mesh-root", "/m", "--hb-epoch", "4096"]])

    def test_a_refused_epoch_is_six_fields_and_the_cycle_never_runs(self):
        for epoch in ("31", "+33", "33.0", None, True):
            with self.subTest(epoch=epoch):
                code, record, calls = self.dispatch({"schema": rc.SCHEMA, "hb_epoch": epoch})
                self.assertEqual((code, record["disposition"], calls), (1, "FAIL_CLOSED", []))
                for field in SIX:
                    self.assertTrue(record[field], field)

    def test_a_malformed_request_or_an_argument_epoch_is_terminal_cli_input_invalid(self):
        cases = {
            "absent": (None, ()),
            "not json": ("{", ()),
            "no epoch": ({"schema": rc.SCHEMA}, ()),
            "wrong schema": ({"schema": "other/v1", "hb_epoch": "4096"}, ()),
            "extra key": ({"schema": rc.SCHEMA, "hb_epoch": "4096", "mesh_root": "/m"}, ()),
            "argument epoch": ({"schema": rc.SCHEMA, "hb_epoch": "4096"}, ("--hb-epoch", "5000")),
            "argument epoch joined": ({"schema": rc.SCHEMA, "hb_epoch": "4096"}, ("--hb-epoch=5000",)),
        }
        for name, (request, argv) in cases.items():
            with self.subTest(name):
                code, record, calls = self.dispatch(request, *argv)
                self.assertEqual((code, record["failure_code"], record["terminal"], calls),
                                 (2, "CLI_INPUT_INVALID", True, []))
                for field in SIX:
                    self.assertTrue(record[field], field)

if __name__ == "__main__":
    unittest.main()
