from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worker = load("sdk_mcp_canonical_validation_worker", ROOT / "workers" / "sdk_mcp_canonical_validation_worker.py")


class SDKMCPCanonicalValidationWorkerTests(unittest.TestCase):
    def fixture_roots(self, root: Path) -> dict[str, str]:
        layout = {
            "STEGVERSE_SDK_SOURCE_ROOT": ("sdk", "stegverse/mcp_governance.py"),
            "STEGVERSE_STEGCORE_SOURCE_ROOT": ("stegcore", "src/stegcore/transaction_lifecycle.py"),
            "STEGVERSE_CORE_LITE_SOURCE_ROOT": ("core-lite", "core_lite/transaction_route.py"),
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": ("master-records", "services/manifest_receipt_custody.py"),
        }
        env = {"HOME": str(root), "PATH": "/bin"}
        for key, (dirname, required) in layout.items():
            base = root / dirname
            target = base / required
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# fixture\n", encoding="utf-8")
            env[key] = str(base)
        return env

    def node(self, root: Path) -> Path:
        path = root / "node.json"
        path.write_text(json.dumps({
            "schema": "stegverse.sovereign-node-declaration/v0.2",
            "declared": True,
            "declaration_source": "DERIVED_LOCAL_RUNTIME_ELIGIBILITY",
            "credential_authority": "TV/TVC",
            "github_token_required": False,
        }), encoding="utf-8")
        return path

    def invocation(self) -> dict:
        return {
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "CLAIM-EXACT-MCP-1",
            },
            "handoff": {
                "authority": {
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "non_tv_tvc_secret_or_token_allowed": False,
                }
            },
        }

    def test_hosted_environment_fails_closed(self):
        self.assertTrue(worker.hosted_environment({"GITHUB_ACTIONS": "true"}))
        self.assertTrue(worker.hosted_environment({"RENDER": "1"}))
        self.assertFalse(worker.hosted_environment({}))

    def test_invocation_requires_scheduler_claim(self):
        value = self.invocation()
        worker.validate_invocation(value)
        value["task"]["claim_id"] = None
        with self.assertRaises(RuntimeError):
            worker.validate_invocation(value)

    def test_node_requires_tvtvc_and_no_github_token(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self.node(root)
            worker.validate_node_declaration(path)
            data = json.loads(path.read_text())
            data["credential_authority"] = "OTHER"
            path.write_text(json.dumps(data))
            with self.assertRaises(RuntimeError):
                worker.validate_node_declaration(path)

    def test_roots_are_local_nonsecret_locators_and_required_files_must_exist(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = self.fixture_roots(root)
            roots = worker.resolve_roots(env)
            self.assertEqual(set(roots), {"sdk", "stegcore", "core_lite", "master_records"})
            Path(env["STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"]) .joinpath("services/manifest_receipt_custody.py").unlink()
            with self.assertRaises(RuntimeError):
                worker.resolve_roots(env)

    def test_child_environment_strips_inherited_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = self.fixture_roots(root)
            env.update({
                "GITHUB_TOKEN": "bad",
                "GH_TOKEN": "bad",
                "PROVIDER_API_KEY": "bad",
                "WALLET_KEY": "bad",
            })
            child = worker.child_environment(worker.resolve_roots(env), env)
            self.assertNotIn("GITHUB_TOKEN", child)
            self.assertNotIn("GH_TOKEN", child)
            self.assertNotIn("PROVIDER_API_KEY", child)
            self.assertNotIn("WALLET_KEY", child)
            self.assertIn("PYTHONPATH", child)

    def test_execute_requires_unskipped_suite_and_complete_exact_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = self.fixture_roots(root)
            node = self.node(root)
            calls = []

            def fake_runner(command, **kwargs):
                calls.append(command)
                if "unittest" in command:
                    return subprocess.CompletedProcess(command, 0, stdout="Ran 1 test\nOK\n", stderr="")
                result = {
                    "schema": "stegverse.sdk-mcp-canonical-validation-result/v1",
                    "state": "COMPLETE",
                    "inspect": {"manifest_receipt_id": "MR-EXAMPLE", "route_receipt_ids": ["MRR-X"]},
                    "replay": {"consequence_reexecuted": False, "operation_receipt_ids": ["MRO-R"]},
                    "reconstruction": {"consequence_reexecuted": False, "operation_receipt_ids": ["MRO-C"]},
                    "bounded_write": {"status": "UPDATED", "bounded_value": 42},
                }
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(result) + "\n", stderr="")

            receipt = worker.execute(self.invocation(), env=env, node_declaration=node, runner=fake_runner)
            self.assertEqual("COMPLETE", receipt["state"])
            self.assertEqual("TV/TVC", receipt["credential_authority"])
            self.assertFalse(receipt["github_token_runtime_authority"])
            self.assertFalse(receipt["non_tv_tvc_secret_or_token_used"])
            self.assertFalse(receipt["signed"])
            self.assertFalse(receipt["broadcast"])
            self.assertEqual(2, len(calls))

    def test_skipped_exact_suite_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = self.fixture_roots(root)
            node = self.node(root)

            def fake_runner(command, **kwargs):
                return subprocess.CompletedProcess(command, 0, stdout="OK (skipped=1)\n", stderr="")

            with self.assertRaises(RuntimeError):
                worker.execute(self.invocation(), env=env, node_declaration=node, runner=fake_runner)


if __name__ == "__main__":
    unittest.main()
