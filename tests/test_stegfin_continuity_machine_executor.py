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


executor = load("stegfin_machine_executor", ROOT / "scripts" / "run_stegfin_continuity_machine_executor.py")
installer = load("stegfin_machine_installer", ROOT / "scripts" / "install_stegfin_continuity_machine_service.py")


class StegFinContinuityMachineExecutorTests(unittest.TestCase):
    def fixture(self, temp: Path):
        (temp / "handoffs").mkdir(parents=True)
        (temp / "control" / "worker-registry.d").mkdir(parents=True)
        (temp / "workers").mkdir(parents=True)
        handoff = {
            "state": "HANDOFF_READY_MACHINE_OWNED_TRANSPORT_SELECTION_AT_EXECUTION",
            "task": {"task_id": executor.TASK_ID, "manual_execution_allowed": False},
            "authority": {
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "non_tv_tvc_secret_or_token_allowed": False,
            },
            "execution": {"allowed_paths": ["reports/continuity_pretrade/**"]},
            "activation": {
                "executor_binding": "MACHINE_SCHEDULER_ONLY",
                "claim_issuer": "scripts/acquire_stegfin_continuity_claim.py",
            },
        }
        registry = {
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "tasks": [{"task_id": executor.TASK_ID, "state": "HANDOFF_READY", "claim_id": None}],
            "workers": [{"worker_id": executor.WORKER_ID, "status": "AVAILABLE", "adapter_ref": "process:stegfin-continuity-carrier-v1"}],
        }
        (temp / executor.HANDOFF_REL).write_text(json.dumps(handoff))
        (temp / executor.REGISTRY_REL).write_text(json.dumps(registry))
        (temp / executor.WORKER_REL).write_text("print('fixture')\n")
        node = temp / "node.json"
        node.write_text(json.dumps({
            "schema": "stegverse.sovereign-node-declaration/v0.2",
            "declared": True,
            "declaration_source": "DERIVED_LOCAL_RUNTIME_ELIGIBILITY",
            "credential_authority": "TV/TVC",
            "github_token_required": False,
        }))
        return node

    def test_hosted_environment_fails_closed(self):
        self.assertTrue(executor.hosted_environment({"GITHUB_ACTIONS": "true"}))
        self.assertTrue(executor.hosted_environment({"RENDER": "1"}))
        self.assertFalse(executor.hosted_environment({}))

    def test_node_declaration_requires_tvtvc_and_no_github_token(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "node.json"
            path.write_text(json.dumps({"schema": "stegverse.sovereign-node-declaration/v0.2", "declared": True, "credential_authority": "OTHER", "github_token_required": False}))
            with self.assertRaises(RuntimeError):
                executor.validate_node_declaration(path)
            path.write_text(json.dumps({"schema": "stegverse.sovereign-node-declaration/v0.2", "declared": True, "credential_authority": "TV/TVC", "github_token_required": True}))
            with self.assertRaises(RuntimeError):
                executor.validate_node_declaration(path)

    def test_contract_requires_claim_free_available_machine_worker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            executor.validate_contract(root)
            registry_path = root / executor.REGISTRY_REL
            registry = json.loads(registry_path.read_text())
            registry["tasks"][0]["claim_id"] = "foreign-claim"
            registry_path.write_text(json.dumps(registry))
            with self.assertRaises(RuntimeError):
                executor.validate_contract(root)

    def test_child_environment_strips_all_credential_inputs(self):
        child = executor.child_environment({
            "PATH": "/bin",
            "HOME": "/tmp/home",
            "STEGVERSE_TVC_SOURCE_ROOT": "/source/TVC",
            "STEGVERSE_TV_TVC_BROKER_ENDPOINT": "/run/stegverse/vault-broker.sock",
            "GITHUB_TOKEN": "x",
            "GH_TOKEN": "x",
            "PROVIDER_API_KEY": "x",
            "WALLET_KEY": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
        })
        self.assertEqual(child["STEGVERSE_TVC_SOURCE_ROOT"], "/source/TVC")
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertNotIn("GH_TOKEN", child)
        self.assertNotIn("PROVIDER_API_KEY", child)
        self.assertNotIn("WALLET_KEY", child)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", child)

    def test_executor_invokes_existing_worker_without_minting_claim_or_fence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            node = self.fixture(root)
            seen = {}

            def fake_runner(command, **kwargs):
                seen["command"] = command
                seen["env"] = kwargs["env"]
                seen["invocation"] = json.loads(kwargs["input"])
                response = {
                    "schema": "stegverse.worker-response/v0.1",
                    "state": "BLOCKED",
                    "transition_id": "WAIT_FOR_CANONICAL_TRANSPORT",
                    "evidence_refs": [],
                }
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(response), stderr="")

            receipt = executor.execute_once(root, node_declaration=node, env={"HOME": str(root)}, runner=fake_runner)
            self.assertEqual(receipt["state"], "BLOCKED")
            self.assertFalse(receipt["executor_minted_claim_or_fence"])
            self.assertTrue(receipt["worker_self_claims"])
            task = seen["invocation"]["task"]
            self.assertIsNone(task["claim_id"])
            self.assertIsNone(task["heartbeat_timing"])
            self.assertTrue(str(seen["command"][1]).endswith("workers/stegfin_continuity_carrier_worker_v3.py"))

    def test_complete_requires_exact_wallet_handoff_durable_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            node = self.fixture(root)

            def fake_runner(command, **kwargs):
                target = root / executor.DURABLE_WORKER_RECEIPT_REL
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps({
                    "state": "COMPLETE",
                    "transition_id": "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY",
                    "credential_authority": "TV/TVC",
                    "non_tv_tvc_secret_or_token_used": False,
                    "provider_secret_exported": False,
                    "signed": False,
                    "broadcast": False,
                }))
                response = {"schema": "stegverse.worker-response/v0.1", "state": "COMPLETE", "transition_id": "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY", "evidence_refs": []}
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(response), stderr="")

            receipt = executor.execute_once(root, node_declaration=node, env={"HOME": str(root)}, runner=fake_runner)
            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertFalse(receipt["signed"])
            self.assertFalse(receipt["broadcast"])

    def test_false_complete_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            node = self.fixture(root)

            def fake_runner(command, **kwargs):
                response = {"schema": "stegverse.worker-response/v0.1", "state": "COMPLETE", "transition_id": "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY", "evidence_refs": []}
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(response), stderr="")

            with self.assertRaises(RuntimeError):
                executor.execute_once(root, node_declaration=node, env={"HOME": str(root)}, runner=fake_runner)

    def test_rootless_service_is_native_non_authorizing_and_secret_free(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "scripts" / "run_stegfin_continuity_machine_executor.py").write_text("# fixture\n")
            service = installer.materialize_service(root, system="linux", env={"XDG_CONFIG_HOME": str(root / "config")})
            text = service["content"]
            self.assertIn("systemd", service["registration_kind"])
            self.assertIn("NoNewPrivileges=yes", text)
            self.assertIn("Restart=on-failure", text)
            self.assertFalse(service["heartbeat_replacement"])
            self.assertFalse(service["execution_authority_created"])
            self.assertFalse(service["github_token_runtime_authority"])
            for marker in installer.FORBIDDEN_TEXT:
                self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
