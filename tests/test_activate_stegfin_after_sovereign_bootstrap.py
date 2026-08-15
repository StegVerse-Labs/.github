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
        self.calls = []

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

    def paths(self, base: Path):
        return (
            base / "activation.latest.json",
            base / "bootstrap.latest.json",
            base / "node.json",
            base / "executor-activation.latest.json",
            base / "integration.latest.json",
            base / "runtime",
        )

    def proof(self, path: Path, runtime_root: Path, *, complete: bool = True, schema: str | None = None) -> None:
        body = {name: True for name in post_bootstrap.REQUIRED_PREDICATES}
        if not complete:
            body[post_bootstrap.REQUIRED_PREDICATES[-1]] = False
        body.update({
            "schema": schema or post_bootstrap.ACTIVATION_PROOF_SCHEMA,
            "all_predicates_pass": complete,
            "third_party_runtime_required": False,
            "detail": {"runtime_root": str(runtime_root.resolve())},
        })
        path.write_text(json.dumps(body) + "\n", encoding="utf-8")

    def node(self, path: Path, root: Path, *, authority: str = "TV/TVC") -> None:
        body = {
            "schema": "stegverse.sovereign-node-declaration/v0.3",
            "declared": True,
            "source_root": str(root.resolve()),
            "credential_authority": authority,
            "github_token_required": False,
            "third_party_runtime_required": False,
            "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
        }
        path.write_text(json.dumps(body) + "\n", encoding="utf-8")

    def bootstrap(self, path: Path, root: Path, runtime_root: Path, proof: Path, node: Path, *, state: str = "COMPLETE") -> None:
        body = {
            "schema": post_bootstrap.BOOTSTRAP_RECEIPT_SCHEMA,
            "task_id": "SHWP-SOVEREIGN-RUNTIME-SELF-BOOTSTRAP-001",
            "source_root": str(root.resolve()),
            "runtime_root": str(runtime_root.resolve()),
            "node_declaration_ref": str(node.resolve()),
            "credential_requirement": "NONE",
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "third_party_runtime_required": False,
            "proof_path": str(proof.resolve()),
            "activation_all_predicates_pass": state == "COMPLETE",
            "state": state,
            "reason": "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED" if state == "COMPLETE" else "SOVEREIGN_ACTIVATION_PROOF_INCOMPLETE",
        }
        path.write_text(json.dumps(body) + "\n", encoding="utf-8")

    def valid_fixture(self, base: Path):
        root = self.create_root(base)
        proof, bootstrap, node, executor_receipt, integration, runtime_root = self.paths(base)
        runtime_root.mkdir(parents=True, exist_ok=True)
        self.proof(proof, runtime_root)
        self.node(node, root)
        self.bootstrap(bootstrap, root, runtime_root, proof, node)
        return root, proof, bootstrap, node, executor_receipt, integration, runtime_root

    def activate(self, root, proof, bootstrap, node, executor_receipt, integration, runner, *, env=None):
        return post_bootstrap.activate(
            root,
            proof_path=proof,
            bootstrap_receipt=bootstrap,
            node_marker=node,
            executor_activation_receipt=executor_receipt,
            integration_receipt=integration,
            env={} if env is None else env,
            runner=runner,
        )

    def test_hosted_environment_fails_closed_before_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, _ = self.valid_fixture(b)
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner, env={"GITHUB_ACTIONS": "true"})
            self.assertEqual(out["state"], "FAIL_CLOSED")
            self.assertEqual(runner.calls, [])

    def test_incomplete_sovereign_proof_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, runtime_root = self.valid_fixture(b)
            self.proof(p, runtime_root, complete=False)
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_NINE_PREDICATE_PROOF_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_forged_boolean_complete_proof_with_wrong_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, runtime_root = self.valid_fixture(b)
            self.proof(p, runtime_root, schema="forged/proof")
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_NINE_PREDICATE_PROOF_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_invalid_node_authority_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, _ = self.valid_fixture(b)
            self.node(n, r, authority="OTHER")
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_NODE_DECLARATION_AUTHORITY_BOUNDARY_INVALID")
            self.assertEqual(runner.calls, [])

    def test_mismatched_bootstrap_proof_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, runtime_root = self.valid_fixture(b)
            other = b / "other-proof.json"
            self.bootstrap(br, r, runtime_root, other, n)
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_BOOTSTRAP_PROVENANCE_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_mismatched_bootstrap_node_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, runtime_root = self.valid_fixture(b)
            self.bootstrap(br, r, runtime_root, p, b / "other-node.json")
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_BOOTSTRAP_PROVENANCE_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_wrong_source_root_or_runtime_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, runtime_root = self.valid_fixture(b)
            self.bootstrap(br, b / "other-source", runtime_root, p, n)
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_BOOTSTRAP_PROVENANCE_NOT_ESTABLISHED")
            self.bootstrap(br, r, b / "other-runtime", p, n)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_BOOTSTRAP_PROVENANCE_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_noncomplete_bootstrap_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, runtime_root = self.valid_fixture(b)
            self.bootstrap(br, r, runtime_root, p, n, state="REVIEW_REQUIRED")
            runner = FakeInstaller(e)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["reason"], "SOVEREIGN_BOOTSTRAP_PROVENANCE_NOT_ESTABLISHED")
            self.assertEqual(runner.calls, [])

    def test_success_activates_only_released_service_with_clean_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, _ = self.valid_fixture(b)
            runner = FakeInstaller(e)
            out = self.activate(
                r, p, br, n, e, i, runner,
                env={"HOME": str(b), "PATH": "/usr/bin", "GITHUB_TOKEN": "forbidden", "TVC_TOKEN": "not-required", "WALLET_KEY": "forbidden", "PROVIDER_SECRET": "forbidden"},
            )
            self.assertEqual(out["state"], "COMPLETE")
            self.assertTrue(out["executor_service_active"])
            self.assertFalse(out["wallet_handoff_ready_claimed"])
            _, env = runner.calls[0]
            for key in ("GITHUB_TOKEN", "TVC_TOKEN", "WALLET_KEY", "PROVIDER_SECRET"):
                self.assertNotIn(key, env)

    def test_installer_success_without_authoritative_activation_receipt_does_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp)
            r, p, br, n, e, i, _ = self.valid_fixture(b)
            runner = FakeInstaller(e, active=False)
            out = self.activate(r, p, br, n, e, i, runner)
            self.assertEqual(out["state"], "REVIEW_REQUIRED")
            self.assertFalse(out["executor_service_active"])


if __name__ == "__main__":
    unittest.main()
