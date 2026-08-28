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


class G18V13RuntimeWorkerTests(unittest.TestCase):
    def test_clean_exec_env_forwards_no_secret_or_token_material(self):
        env = {
            "HOME": "/tmp/home",
            "PATH": "/usr/bin:/bin",
            "XDG_STATE_HOME": "/tmp/state",
            "STEGVERSE_HEARTBEAT_SOURCE_ROOT": "/tmp/source",
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "TVC_TOKEN": "forbidden",
            "ZEROEX_API_KEY": "forbidden",
            "WALLET_PRIVATE_KEY": "forbidden",
            "AWS_SECRET_ACCESS_KEY": "forbidden",
        }
        clean = worker.clean_exec_env(env)
        self.assertEqual(clean["HOME"], "/tmp/home")
        self.assertEqual(clean["XDG_STATE_HOME"], "/tmp/state")
        self.assertEqual(clean["STEGVERSE_HEARTBEAT_SOURCE_ROOT"], "/tmp/source")
        for name in (
            "GITHUB_TOKEN", "GH_TOKEN", "TVC_TOKEN", "ZEROEX_API_KEY",
            "WALLET_PRIVATE_KEY", "AWS_SECRET_ACCESS_KEY",
        ):
            self.assertNotIn(name, clean)

    def test_v13_self_bootstrap_invokes_existing_canonical_path_without_downstream_activation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bootstrap = root / "scripts" / "bootstrap_sovereign_runtime.py"
            bootstrap.parent.mkdir(parents=True)
            bootstrap.write_text("# canonical bootstrap\n", encoding="utf-8")
            runtime_root = root / "runtime"
            proof_path = root / "activation.latest.json"
            bootstrap_receipt = root / "bootstrap.latest.json"
            node_marker = root / "node.json"
            captured = {}

            def fake_run(command, **kwargs):
                captured["command"] = list(command)
                captured["env"] = dict(kwargs.get("env") or {})
                bootstrap_receipt.write_text(json.dumps({
                    "schema": "stegverse.sovereign-runtime-self-bootstrap-receipt/v2",
                    "state": "COMPLETE",
                    "reason": "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED",
                    "node_declaration_ref": str(node_marker),
                    "node_eligibility": {"eligible": True},
                }) + "\n", encoding="utf-8")
                proof = {name: True for name in worker.REQUIRED_PREDICATES}
                proof.update({
                    "schema": "stegverse.sovereign-runtime-activation-proof/v1",
                    "all_predicates_pass": True,
                })
                proof_path.write_text(json.dumps(proof) + "\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with mock.patch.object(worker, "ROOT", root), \
                 mock.patch.object(worker, "BOOTSTRAP", bootstrap), \
                 mock.patch.object(worker, "default_runtime_root", return_value=runtime_root), \
                 mock.patch.object(worker, "default_proof_path", return_value=proof_path), \
                 mock.patch.object(worker, "default_bootstrap_receipt", return_value=bootstrap_receipt), \
                 mock.patch.object(worker, "default_node_marker", return_value=node_marker), \
                 mock.patch.object(worker, "third_party_hosted_environment", return_value=False), \
                 mock.patch.object(worker.subprocess, "run", side_effect=fake_run), \
                 mock.patch.dict(os.environ, {
                     "HOME": str(root),
                     "PATH": "/usr/bin",
                     "GITHUB_TOKEN": "forbidden",
                     "TVC_TOKEN": "forbidden",
                 }, clear=True):
                result = worker.execute_v13_self_bootstrap()

            self.assertTrue(result["attempted"])
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["activation_all_predicates_pass"])
            self.assertEqual(result["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(result["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
            self.assertEqual(result["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertFalse(result["heartbeat_dependency"])
            self.assertIn("--skip-post-bootstrap-stegfin", captured["command"])
            self.assertNotIn("advance_heartbeat_transition.py", " ".join(captured["command"]))
            self.assertNotIn("GITHUB_TOKEN", captured["env"])
            self.assertNotIn("TVC_TOKEN", captured["env"])

    def test_hosted_environment_never_attempts_sovereign_bootstrap(self):
        with mock.patch.object(worker, "third_party_hosted_environment", return_value=True), \
             mock.patch.object(worker.subprocess, "run") as run:
            result = worker.execute_v13_self_bootstrap()
        self.assertFalse(result["attempted"])
        self.assertEqual(result["reason"], "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE")
        run.assert_not_called()

    def test_blocker_preserves_no_second_machine_and_no_heartbeat_dependency(self):
        contract = worker.blocker_for({"reason": "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN"})
        self.assertEqual(contract["dependency_class"], "PHYSICAL_RESOURCE_SOVEREIGN_NODE_ELIGIBILITY")
        self.assertFalse(contract["physical_additional_machine_required"])
        self.assertFalse(contract["always_on_external_host_required"])
        self.assertFalse(contract["heartbeat_activation_blocked"])
        self.assertEqual(
            contract["next_solution_action"],
            "EXECUTE_CANONICAL_V13_SOVEREIGN_RUNTIME_SELF_BOOTSTRAP",
        )
        self.assertTrue(any("worker_task_capable_cycle_observed" in row for row in contract["completion_evidence"]))

    def test_process_adapter_remains_secret_free_and_has_sufficient_envelope(self):
        registry = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text(encoding="utf-8"))
        adapter = next(
            row for row in registry["adapters"]
            if row["adapter_ref"] == "process:sovereign-runtime-activation-v1"
        )
        self.assertGreaterEqual(adapter["timeout_seconds"], 1200)
        self.assertEqual(
            adapter["command"],
            ["python", "workers/sovereign_runtime_activation_entrypoint.py"],
        )
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "TVC_TOKEN"):
            self.assertNotIn(name, adapter["env_allowlist"])


if __name__ == "__main__":
    unittest.main()
