from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workers" / "sovereign_runtime_activation_worker.py"
spec = importlib.util.spec_from_file_location("g18_worker", SCRIPT)
worker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(worker)


class G18StateTransitionWorkerTests(unittest.TestCase):
    def test_clean_exec_env_forwards_no_secret_or_token_material(self):
        env = {
            "HOME": "/tmp/home", "PATH": "/usr/bin:/bin", "XDG_STATE_HOME": "/tmp/state",
            "GITHUB_TOKEN": "forbidden", "GH_TOKEN": "forbidden", "TVC_TOKEN": "forbidden",
            "ZEROEX_API_KEY": "forbidden", "WALLET_PRIVATE_KEY": "forbidden", "AWS_SECRET_ACCESS_KEY": "forbidden",
        }
        clean = worker.clean_exec_env(env)
        self.assertEqual(clean["HOME"], "/tmp/home")
        self.assertEqual(clean["XDG_STATE_HOME"], "/tmp/state")
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "TVC_TOKEN", "ZEROEX_API_KEY", "WALLET_PRIVATE_KEY", "AWS_SECRET_ACCESS_KEY"):
            self.assertNotIn(name, clean)

    def test_execute_state_transition_invokes_bounded_producer_without_predeclared_node(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            producer = root / "scripts" / "advance_heartbeat_transition.py"
            producer.parent.mkdir(parents=True)
            producer.write_text("# bounded transition producer\n", encoding="utf-8")
            contract = root / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json"
            contract.parent.mkdir(parents=True)
            contract.write_text("{}", encoding="utf-8")
            receipt = root / "receipts" / "heartbeat-transition-continuity" / "latest.json"
            captured = {}

            def fake_run(command, **kwargs):
                captured["command"] = list(command)
                captured["env"] = dict(kwargs.get("env") or {})
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({
                    "state": "CARRIER_TRANSITION_COMPLETE",
                    "reason": "HB29_TO_V12_SUCCESSOR_TRANSITION_VERIFIED",
                    "carrier_epoch_before": 29,
                    "carrier_epoch_after": 30,
                }), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with mock.patch.object(worker, "ROOT", root), \
                 mock.patch.object(worker, "TRANSITION_CONTRACT", contract), \
                 mock.patch.object(worker, "TRANSITION_RECEIPT", receipt), \
                 mock.patch.object(worker, "third_party_hosted_environment", return_value=False), \
                 mock.patch.object(worker.subprocess, "run", side_effect=fake_run), \
                 mock.patch.dict(os.environ, {"HOME": str(root), "PATH": "/usr/bin", "GITHUB_TOKEN": "forbidden", "TVC_TOKEN": "forbidden"}, clear=True):
                result = worker.execute_state_transition_solution()

            self.assertTrue(result["attempted"])
            self.assertEqual(result["state"], "CARRIER_TRANSITION_COMPLETE")
            self.assertEqual(result["carrier_epoch_before"], 29)
            self.assertEqual(result["carrier_epoch_after"], 30)
            self.assertFalse(result["physical_additional_machine_required"])
            self.assertFalse(result["always_on_external_host_required"])
            self.assertEqual(result["credential_authority"], "TV/TVC")
            self.assertIn("advance_heartbeat_transition.py", captured["command"][1])
            self.assertNotIn("GITHUB_TOKEN", captured["env"])
            self.assertNotIn("TVC_TOKEN", captured["env"])

    def test_hosted_environment_never_attempts_state_transition(self):
        with mock.patch.object(worker, "third_party_hosted_environment", return_value=True), mock.patch.object(worker.subprocess, "run") as run:
            result = worker.execute_state_transition_solution()
        self.assertFalse(result["attempted"])
        self.assertEqual(result["reason"], "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_TRANSITION_EVIDENCE")
        run.assert_not_called()

    def test_resolution_contract_forbids_extra_machine_and_always_on_host(self):
        contract = worker.unresolved_transition_contract({"reason": "CARRIER_TRANSITION_EXECUTION_FAILED"})
        self.assertEqual(contract["dependency_class"], "EXECUTION_OPPORTUNITY")
        self.assertTrue(contract["resolvable_by_current_worker"])
        self.assertFalse(contract["physical_additional_machine_required"])
        self.assertFalse(contract["always_on_external_host_required"])
        self.assertIn("Another physical machine", contract["problem_statement"])
        self.assertEqual(contract["next_solution_action"], "EXECUTE_BOUNDED_V12_STATE_TRANSITION")

    def test_process_adapter_remains_secret_free_and_has_sufficient_envelope(self):
        registry = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text(encoding="utf-8"))
        adapter = next(row for row in registry["adapters"] if row["adapter_ref"] == "process:sovereign-runtime-activation-v1")
        self.assertGreaterEqual(adapter["timeout_seconds"], 1200)
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "TVC_TOKEN"):
            self.assertNotIn(name, adapter["env_allowlist"])


if __name__ == "__main__":
    unittest.main()
