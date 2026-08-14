from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "activate_stegfin_after_sovereign_bootstrap.py"

spec = importlib.util.spec_from_file_location("post_bootstrap", SCRIPT)
post_bootstrap = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(post_bootstrap)


class FakeInstaller:
    def __init__(self, receipt: Path, *, returncode: int = 0, active: bool = True):
        self.receipt = receipt
        self.returncode = returncode
        self.active = active
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(self, command, **kwargs):
        env = dict(kwargs.get("env") or {})
        self.calls.append((list(command), env))
        if self.returncode == 0:
            body = {
                "active": self.active,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": False,
                "non_tv_tvc_secret_or_token_embedded": False,
                "wallet_signing_authority": "USER_ONLY",
                "broadcast_authority": "USER_ONLY",
                "execution_authority_created": False,
            }
            self.receipt.parent.mkdir(parents=True, exist_ok=True)
            self.receipt.write_text(json.dumps(body) + "\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, self.returncode, stdout="", stderr="")


class SovereignStegFinPostBootstrapTests(unittest.TestCase):
    def create_root(self, base: Path) -> Path:
        root = base / "repo"
        for rel in (
            "scripts/install_stegfin_continuity_machine_service.py",
            "scripts/run_stegfin_continuity_machine_executor.py",
        ):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# source\n", encoding="utf-8")
        return root

    def proof(self, path: Path, *, complete: bool = True) -> None:
        body = {name: True for name in post_bootstrap.REQUIRED_PREDICATES}
        if not complete:
            body[post_bootstrap.REQUIRED_PREDICATES[-1]] = False
        body["all_predicates_pass"] = complete
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body) + "\n", encoding="utf-8")

    def node(self, path: Path, *, authority: str = "TV/TVC") -> None:
        body = {
            "declared": True,
            "credential_authority": authority,
            "github_token_required": False,
            "third_party_runtime_required": False,
            "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body) + "\n", encoding="utf-8")

    def paths(self, base: Path):
        return (
            base / "activation.latest.json",
            base / "node.json",
            base / "executor-activation.latest.json",
            base / "integration.latest.json",
        )

    def test_hosted_environment_fails_closed_before_installer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self.create_root(base)
            proof, node, executor_receipt, integration = self.paths(base)
            self.proof(proof)
            self.node(node)
            runner = FakeInstaller(executor_receipt)
            result = post_bootstrap.activate(
                root,
                proof_path=proof,
                node_marker=node,
                executor_activation_receipt=executor_receipt,
                integration_receipt=integration,
                env={"GITHUB_ACTIONS": "true"},
                runner=runner,
            )
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "HOSTED_ENVIRONMENT_IS_NOT_AUTHORIZED_LOCAL_INTEGRATION_SURFACE")
            self.assertEqual(runner.calls, [])

    def test_incomplete_sovereign_proof_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self.create_root(base)
            proof, node, executor_receipt, integration = self.paths(base)
            self.proof(proof, complete=False)
            self.node(node)
            runner = FakeInstaller(executor_receipt)
            result = post_bootstrap.activate(
                root,
                proof_path=proof,
                node_marker=node,
                executor_activation_receipt=executor_receipt,
                integration_receipt=integration,
                env={},
                runner=runner,
            )
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "SOVEREIGN_NINE_PREDICATE_PROOF_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_invalid_node_authority_boundary_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self.create_root(base)
            proof, node, executor_receipt, integration = self.paths(base)
            self.proof(proof)
            self.node(node, authority="OTHER")
            runner = FakeInstaller(executor_receipt)
            result = post_bootstrap.activate(
                root,
                proof_path=proof,
                node_marker=node,
                executor_activation_receipt=executor_receipt,
                integration_receipt=integration,
                env={},
                runner=runner,
            )
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "SOVEREIGN_NODE_DECLARATION_AUTHORITY_BOUNDARY_INVALID")
            self.assertEqual(runner.calls, [])

    def test_success_activates_only_released_service_with_clean_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self.create_root(base)
            proof, node, executor_receipt, integration = self.paths(base)
            self.proof(proof)
            self.node(node)
            runner = FakeInstaller(executor_receipt)
            result = post_bootstrap.activate(
                root,
                proof_path=proof,
                node_marker=node,
                executor_activation_receipt=executor_receipt,
                integration_receipt=integration,
                env={
                    "HOME": str(base),
                    "PATH": "/usr/bin",
                    "GITHUB_TOKEN": "forbidden",
                    "TVC_TOKEN": "not-required",
                    "WALLET_KEY": "forbidden",
                    "PROVIDER_SECRET": "forbidden",
                },
                runner=runner,
            )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["executor_service_active"])
            self.assertFalse(result["wallet_handoff_ready_claimed"])
            self.assertFalse(result["provider_contacted"])
            self.assertFalse(result["wallet_contacted"])
            self.assertFalse(result["signed"])
            self.assertFalse(result["broadcast"])
            self.assertEqual(len(runner.calls), 1)
            command, env = runner.calls[0]
            self.assertIn("install_stegfin_continuity_machine_service.py", command[1])
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertNotIn("TVC_TOKEN", env)
            self.assertNotIn("WALLET_KEY", env)
            self.assertNotIn("PROVIDER_SECRET", env)
            self.assertEqual(env["STEGVERSE_POST_BOOTSTRAP_INTEGRATION"], "1")

    def test_installer_success_without_authoritative_activation_receipt_does_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self.create_root(base)
            proof, node, executor_receipt, integration = self.paths(base)
            self.proof(proof)
            self.node(node)
            runner = FakeInstaller(executor_receipt, active=False)
            result = post_bootstrap.activate(
                root,
                proof_path=proof,
                node_marker=node,
                executor_activation_receipt=executor_receipt,
                integration_receipt=integration,
                env={},
                runner=runner,
            )
            self.assertEqual(result["state"], "REVIEW_REQUIRED")
            self.assertFalse(result["executor_service_active"])
            self.assertFalse(result["wallet_handoff_ready_claimed"])


if __name__ == "__main__":
    unittest.main()
