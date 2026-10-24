"""B-P22: the bootstrap runs resident dispatch and the federation cycle under the
epoch the heartbeat carrier recorded, and fails closed (six fields) without one."""
from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/bootstrap_sovereign_runtime.py"

SPEC = importlib.util.spec_from_file_location("bootstrap_sovereign_runtime_bp22", SCRIPT)
assert SPEC and SPEC.loader
boot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(boot)

SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)
DECLARING_DISPATCHER = 'parser.add_argument("--hb-epoch", type=str, default=None)\n'
DECLARING_FEDERATION = 'ap.add_argument("--hb-epoch", type=str, default=None)\n'


def write_carrier(runtime: Path, value: object) -> None:
    path = runtime / "control/heartbeat-carrier-runtime-state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, command, **_kwargs):
        self.calls.append(list(command))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"disposition": "OK"}) + "\n", stderr="")


class CarrierEpochReaderTests(unittest.TestCase):
    def test_reads_the_recorded_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            write_carrier(runtime, {"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 4096})
            self.assertEqual(boot.recorded_carrier_epoch(runtime), 4096)

    def test_missing_or_unrecorded_epoch_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            self.assertIsNone(boot.recorded_carrier_epoch(runtime))
            for value in ({}, {"epoch": None}, {"epoch": True}, {"epoch": "64"}, {"epoch": 64.0}, {"epoch": -1}, []):
                write_carrier(runtime, value)
                self.assertIsNone(boot.recorded_carrier_epoch(runtime), value)

    def test_bootstrap_has_one_carrier_state_reader_and_reads_no_clock(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        literals = re.findall(r'"[^"\n]*heartbeat-carrier-runtime-state\.json"', source)
        self.assertEqual(literals, ['"control/heartbeat-carrier-runtime-state.json"'])
        self.assertEqual(source.count("load_json(runtime_root / CARRIER_STATE_REL)"), 1)
        for clock in ("time.time", "datetime", "time.monotonic", "time.perf_counter", "date.today"):
            self.assertNotIn(clock, source)


class DispatchCarrierEpochTests(unittest.TestCase):
    def make(self, base: Path, dispatcher_text: str) -> tuple[Path, Path]:
        source = base / "source"
        runtime = base / "runtime"
        dispatcher = runtime / "scripts/dispatch_resident_execution_requests.py"
        dispatcher.parent.mkdir(parents=True)
        dispatcher.write_text(dispatcher_text, encoding="utf-8")
        return source, runtime

    def test_no_recorded_epoch_fails_closed_with_six_fields_and_runs_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.make(Path(td), DECLARING_DISPATCHER)
            runner = RecordingRunner()
            result = boot._dispatch_resident_requests(source, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            self.assertEqual(runner.calls, [])
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertFalse(result["attempted"])
            self.assertFalse(result["appended"])
            for field in SIX_FIELDS:
                self.assertIsInstance(result[field], str)
                self.assertTrue(result[field])
            self.assertEqual(result["failure_code"], "CARRIER_EPOCH_NOT_RECORDED")
            self.assertIn("_dispatch_resident_requests", result["retry_entrypoint"])
            self.assertIs(result["derived_from_clock"], False)
            self.assertFalse((runtime / "receipts").exists())

    def test_recorded_epoch_is_passed_when_dispatcher_declares_the_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.make(Path(td), DECLARING_DISPATCHER)
            write_carrier(runtime, {"epoch": 4096})
            runner = RecordingRunner()
            result = boot._dispatch_resident_requests(source, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            self.assertEqual(len(runner.calls), 1)
            command = runner.calls[0]
            self.assertEqual(command[command.index("--hb-epoch") + 1], "4096")
            self.assertTrue(result["hb_epoch_forwarded"])
            self.assertEqual(result["carrier_epoch"], 4096)

    def test_flag_is_not_passed_to_a_dispatcher_that_does_not_declare_it(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.make(Path(td), "# dispatcher without --hb-epoch argument\n")
            write_carrier(runtime, {"epoch": 4096})
            runner = RecordingRunner()
            result = boot._dispatch_resident_requests(source, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            self.assertEqual(len(runner.calls), 1)
            self.assertNotIn("--hb-epoch", runner.calls[0])
            self.assertFalse(result["hb_epoch_forwarded"])

    def test_declaration_check_matches_the_main_dispatcher(self) -> None:
        dispatcher = ROOT / "scripts/dispatch_resident_execution_requests.py"
        declared = re.search(r'add_argument\(\s*"--hb-epoch"', dispatcher.read_text(encoding="utf-8")) is not None
        self.assertEqual(boot.declares_hb_epoch_flag(dispatcher), declared)


class FederationCycleCarrierEpochTests(unittest.TestCase):
    def make(self, base: Path, federation_text: str) -> tuple[Path, Path]:
        source = base / "source"
        runtime = base / "runtime"
        resident = runtime / "resident-runtime"
        resident.mkdir(parents=True)
        (resident / "resident_cycle.py").write_text("# resident cycle\n", encoding="utf-8")
        (resident / "federation_cycle.py").write_text(federation_text, encoding="utf-8")
        return source, runtime

    def test_not_materialized_is_not_available(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runner = RecordingRunner()
            result = boot._run_resident_federation_cycle(base / "s", base / "r", proof_path=base / "p.json", env={}, runner=runner)
            self.assertEqual(result["state"], "NOT_AVAILABLE")
            self.assertEqual(runner.calls, [])

    def test_no_recorded_epoch_fails_closed_with_six_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.make(Path(td), DECLARING_FEDERATION)
            runner = RecordingRunner()
            result = boot._run_resident_federation_cycle(source, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            self.assertEqual(runner.calls, [])
            self.assertEqual(result["failure_code"], "CARRIER_EPOCH_NOT_RECORDED")
            for field in SIX_FIELDS:
                self.assertTrue(result[field])
            self.assertIn("_run_resident_federation_cycle", result["retry_entrypoint"])

    def test_undeclared_flag_fails_closed_until_the_federation_hunks_land(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.make(Path(td), "# federation cycle without the flag\n")
            write_carrier(runtime, {"epoch": 4096})
            runner = RecordingRunner()
            result = boot._run_resident_federation_cycle(source, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            self.assertEqual(runner.calls, [])
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["failure_code"], "FEDERATION_CYCLE_EPOCH_FLAG_NOT_ON_MAIN")
            for field in SIX_FIELDS:
                self.assertIsInstance(result[field], str)
                self.assertTrue(result[field])
            self.assertIs(result["derived_from_clock"], False)

    def test_main_federation_cycle_fails_closed_until_it_declares_the_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            write_carrier(runtime, {"epoch": 4096})
            runner = RecordingRunner()
            result = boot._run_resident_federation_cycle(ROOT, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            if boot.declares_hb_epoch_flag(ROOT / "resident-runtime/federation_cycle.py"):
                self.assertEqual(len(runner.calls), 1)
            else:
                self.assertEqual(result["failure_code"], "FEDERATION_CYCLE_EPOCH_FLAG_NOT_ON_MAIN")
                self.assertEqual(runner.calls, [])

    def test_declared_flag_runs_resident_cycle_with_the_recorded_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.make(Path(td), DECLARING_FEDERATION)
            write_carrier(runtime, {"epoch": 4096})
            runner = RecordingRunner()
            result = boot._run_resident_federation_cycle(source, runtime, proof_path=Path(td) / "p.json", env={}, runner=runner)
            self.assertEqual(len(runner.calls), 1)
            command = runner.calls[0]
            self.assertEqual(Path(command[1]), runtime / "resident-runtime/resident_cycle.py")
            self.assertEqual(command[-2:], ["--hb-epoch", "4096"])
            self.assertTrue(result["attempted"])
            self.assertEqual(result["carrier_epoch"], 4096)

    def test_bootstrap_runs_federation_cycle_after_dispatch_before_verification(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        dispatch = source.index('body["post_bootstrap_resident_request_dispatch"] = _dispatch_resident_requests(')
        federation = source.index('body["post_bootstrap_resident_federation_cycle"] = _run_resident_federation_cycle(')
        verify = source.index('verify = runner([sys.executable, str(source_root / "scripts" / "verify_sovereign_runtime_activation.py")')
        self.assertLess(dispatch, federation)
        self.assertLess(federation, verify)


if __name__ == "__main__":
    unittest.main()
