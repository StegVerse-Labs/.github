from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_worker_runtime.py"

spec = importlib.util.spec_from_file_location("run_worker_runtime", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class HB29WorkerBootstrapDeadlockTests(unittest.TestCase):
    def test_bootstrap_materializes_hb30_before_worker_coordinator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "receipts" / "heartbeat-transition-continuity").mkdir(parents=True)
            (root / "control" / "heartbeat-state.json").write_text(
                json.dumps({"schema": "stegverse.org-heartbeat-state/v1", "epoch": 29, "generation": 29}), encoding="utf-8"
            )
            (root / "scripts" / "advance_heartbeat_transition.py").write_text("# canonical producer test stub\n", encoding="utf-8")
            captured_env = {}
            def fake_run(command, **kwargs):
                captured_env.update(kwargs.get("env") or {})
                (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(
                    json.dumps({"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 30, "generation": 30}), encoding="utf-8"
                )
                (root / "receipts" / "heartbeat-transition-continuity" / "latest.json").write_text(
                    json.dumps({"schema": "stegverse.heartbeat-state-transition-receipt/v1", "state": "CARRIER_TRANSITION_COMPLETE", "carrier_epoch_after": 30}), encoding="utf-8"
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            result = module.bootstrap_initial_carrier(
                root,
                env={"HOME": str(root), "PATH": "/usr/bin", "GITHUB_TOKEN": "must-not-forward", "GH_TOKEN": "must-not-forward", "TVC_PRIVATE_SOURCE_READ_TOKEN": "must-not-forward", "RENDER_API_KEY": "must-not-forward"},
                runner=fake_run,
            )
            self.assertTrue(result["attempted"])
            self.assertEqual(result["state"], "CARRIER_TRANSITION_COMPLETE")
            self.assertEqual(result["carrier_epoch"], 30)
            self.assertNotIn("GITHUB_TOKEN", captured_env)
            self.assertNotIn("GH_TOKEN", captured_env)
            self.assertNotIn("TVC_PRIVATE_SOURCE_READ_TOKEN", captured_env)
            self.assertNotIn("RENDER_API_KEY", captured_env)
            legacy = json.loads((root / "control" / "heartbeat-state.json").read_text(encoding="utf-8"))
            self.assertEqual(legacy["epoch"], 29)

    def test_existing_hb30_is_reused_without_second_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(
                json.dumps({"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 30, "generation": 30}), encoding="utf-8"
            )
            def forbidden_runner(*_args, **_kwargs):
                raise AssertionError("transition producer must not run when HB30+ already exists")
            result = module.bootstrap_initial_carrier(root, runner=forbidden_runner)
            self.assertFalse(result["attempted"])
            self.assertEqual(result["state"], "CARRIER_ALREADY_PRESENT")
            self.assertEqual(result["carrier_epoch"], 30)

    def test_missing_or_invalid_hb29_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "advance_heartbeat_transition.py").write_text("# stub\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "source is incomplete"):
                module.bootstrap_initial_carrier(root)
            (root / "control" / "heartbeat-state.json").write_text(json.dumps({"epoch": 28, "generation": 28}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "requires immutable legacy HB29"):
                module.bootstrap_initial_carrier(root)

    def test_failed_transition_never_starts_from_fake_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "receipts" / "heartbeat-transition-continuity").mkdir(parents=True)
            (root / "control" / "heartbeat-state.json").write_text(json.dumps({"epoch": 29, "generation": 29}), encoding="utf-8")
            (root / "scripts" / "advance_heartbeat_transition.py").write_text("# stub\n", encoding="utf-8")
            def failed_run(*_args, **_kwargs):
                (root / "receipts" / "heartbeat-transition-continuity" / "latest.json").write_text(
                    json.dumps({"state": "FAIL_CLOSED", "reason": "HOSTED_ENVIRONMENT_CANNOT_PRODUCE_SOVEREIGN_TRANSITION"}), encoding="utf-8"
                )
                return SimpleNamespace(returncode=1, stdout="", stderr="")
            with self.assertRaisesRegex(RuntimeError, "failed closed"):
                module.bootstrap_initial_carrier(root, runner=failed_run)
            self.assertFalse((root / "control" / "heartbeat-carrier-runtime-state.json").exists())


if __name__ == "__main__":
    unittest.main()
