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


class G18SelfBootstrapWorkerTests(unittest.TestCase):
    def test_clean_bootstrap_env_forwards_no_secret_or_token_material(self):
        with tempfile.TemporaryDirectory() as td:
            env = {
                "HOME": td,
                "PATH": "/usr/bin:/bin",
                "XDG_STATE_HOME": str(Path(td) / "state"),
                "GITHUB_TOKEN": "forbidden",
                "GH_TOKEN": "forbidden",
                "TVC_TOKEN": "forbidden",
                "ZEROEX_API_KEY": "forbidden",
                "WALLET_PRIVATE_KEY": "forbidden",
                "AWS_SECRET_ACCESS_KEY": "forbidden",
            }
            clean = worker.clean_bootstrap_env(env)
            self.assertEqual(clean["HOME"], td)
            self.assertIn("STEGVERSE_HEARTBEAT_ROOT", clean)
            for name in env:
                if name not in {"HOME", "PATH", "XDG_STATE_HOME"}:
                    self.assertNotIn(name, clean)

    def test_execute_native_solution_invokes_released_bootstrap_without_predeclared_node(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            bootstrap = source / "scripts" / "bootstrap_sovereign_runtime.py"
            bootstrap.parent.mkdir(parents=True)
            bootstrap.write_text("# canonical released bootstrap\n", encoding="utf-8")
            receipt = root / "bootstrap.latest.json"
            runtime = root / "runtime"
            captured = {}

            def fake_run(command, **kwargs):
                captured["command"] = list(command)
                captured["env"] = dict(kwargs.get("env") or {})
                receipt.write_text(json.dumps({
                    "schema": "stegverse.sovereign-runtime-self-bootstrap-receipt/v1",
                    "state": "COMPLETE",
                    "reason": "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED",
                    "node_declaration_ref": str(root / "home" / ".stegverse" / "node.json"),
                    "node_eligibility": {"eligible": True},
                    "credential_requirement": "NONE",
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "post_bootstrap_stegfin": {
                        "attempted": True,
                        "state": "COMPLETE",
                        "executor_service_active": True,
                        "wallet_handoff_ready_claimed": False,
                    },
                }) + "\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            env = {
                "HOME": str(root / "home"),
                "PATH": "/usr/bin:/bin",
                "XDG_STATE_HOME": str(root / "state"),
                "GITHUB_TOKEN": "forbidden",
                "TVC_TOKEN": "forbidden",
            }
            with mock.patch.object(worker, "ROOT", source), \
                 mock.patch.object(worker, "bootstrap_receipt_path", return_value=receipt), \
                 mock.patch.object(worker, "default_runtime_root", return_value=runtime), \
                 mock.patch.object(worker, "third_party_hosted_environment", return_value=False), \
                 mock.patch.object(worker.subprocess, "run", side_effect=fake_run), \
                 mock.patch.dict(os.environ, env, clear=True):
                result = worker.execute_native_solution()

            self.assertTrue(result["attempted"])
            self.assertFalse(result["pre_existing_node_declaration_required"])
            self.assertEqual(result["reason"], "SOVEREIGN_SELF_BOOTSTRAP_VERIFIED")
            self.assertTrue(result["eligible_node"])
            self.assertEqual(result["credential_authority"], "TV/TVC")
            self.assertFalse(result["github_token_required"])
            self.assertFalse(result["non_tv_tvc_secret_or_token_forwarded"])
            self.assertIn("bootstrap_sovereign_runtime.py", captured["command"][1])
            self.assertNotIn("GITHUB_TOKEN", captured["env"])
            self.assertNotIn("TVC_TOKEN", captured["env"])

    def test_hosted_environment_never_attempts_self_bootstrap(self):
        with mock.patch.object(worker, "third_party_hosted_environment", return_value=True), \
             mock.patch.object(worker.subprocess, "run") as run:
            result = worker.execute_native_solution()
        self.assertFalse(result["attempted"])
        self.assertTrue(result["hosted_environment_rejected"])
        self.assertEqual(result["reason"], "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE")
        run.assert_not_called()

    def test_resolution_contract_explicitly_removes_predeclared_node_requirement(self):
        contract = worker.unresolved_node_resolution_contract({"reason": "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN"})
        self.assertEqual(contract["dependency_class"], "PHYSICAL_RESOURCE")
        self.assertFalse(contract["resolvable_by_current_worker"])
        self.assertIn("pre-existing node declaration is not required", contract["problem_statement"])
        self.assertIn("scripts/bootstrap_sovereign_runtime.py", contract["next_solution_action"])


if __name__ == "__main__":
    unittest.main()
