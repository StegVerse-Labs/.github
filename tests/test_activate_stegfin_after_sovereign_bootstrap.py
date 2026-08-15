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
        self.receipt = receipt; self.returncode = returncode; self.active = active; self.calls = []
    def __call__(self, command, **kwargs):
        env = dict(kwargs.get("env") or {}); self.calls.append((list(command), env))
        if self.returncode == 0:
            body = {"active": self.active, "credential_authority": "TV/TVC", "github_token_runtime_authority": False,
                    "non_tv_tvc_secret_or_token_embedded": False, "wallet_signing_authority": "USER_ONLY",
                    "broadcast_authority": "USER_ONLY", "execution_authority_created": False}
            self.receipt.parent.mkdir(parents=True, exist_ok=True)
            self.receipt.write_text(json.dumps(body) + "\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, self.returncode, stdout="", stderr="")

class SovereignStegFinPostBootstrapTests(unittest.TestCase):
    def create_root(self, base: Path) -> Path:
        root = base / "repo"
        for rel in ("scripts/install_stegfin_continuity_machine_service.py", "scripts/run_stegfin_continuity_machine_executor.py"):
            path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("# source\n", encoding="utf-8")
        return root
    def proof(self, path: Path, *, complete: bool = True) -> None:
        body = {name: True for name in post_bootstrap.REQUIRED_PREDICATES}
        if not complete: body[post_bootstrap.REQUIRED_PREDICATES[-1]] = False
        body["all_predicates_pass"] = complete; path.write_text(json.dumps(body) + "\n", encoding="utf-8")
    def node(self, path: Path, *, authority: str = "TV/TVC") -> None:
        body = {"declared": True, "credential_authority": authority, "github_token_required": False,
                "third_party_runtime_required": False, "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY"}
        path.write_text(json.dumps(body) + "\n", encoding="utf-8")
    def paths(self, base: Path):
        return base / "activation.latest.json", base / "node.json", base / "executor-activation.latest.json", base / "integration.latest.json"
    def test_hosted_environment_fails_closed_before_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); r=self.create_root(b); p,n,e,i=self.paths(b); self.proof(p); self.node(n); runner=FakeInstaller(e)
            out=post_bootstrap.activate(r, proof_path=p, node_marker=n, executor_activation_receipt=e, integration_receipt=i, env={"GITHUB_ACTIONS":"true"}, runner=runner)
            self.assertEqual(out["state"],"FAIL_CLOSED"); self.assertEqual(runner.calls,[])
    def test_incomplete_sovereign_proof_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); r=self.create_root(b); p,n,e,i=self.paths(b); self.proof(p,complete=False); self.node(n); runner=FakeInstaller(e)
            out=post_bootstrap.activate(r, proof_path=p, node_marker=n, executor_activation_receipt=e, integration_receipt=i, env={}, runner=runner)
            self.assertEqual(out["reason"],"SOVEREIGN_NINE_PREDICATE_PROOF_NOT_ESTABLISHED"); self.assertEqual(runner.calls,[])
    def test_invalid_node_authority_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); r=self.create_root(b); p,n,e,i=self.paths(b); self.proof(p); self.node(n,authority="OTHER"); runner=FakeInstaller(e)
            out=post_bootstrap.activate(r, proof_path=p, node_marker=n, executor_activation_receipt=e, integration_receipt=i, env={}, runner=runner)
            self.assertEqual(out["reason"],"SOVEREIGN_NODE_DECLARATION_AUTHORITY_BOUNDARY_INVALID"); self.assertEqual(runner.calls,[])
    def test_success_activates_only_released_service_with_clean_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); r=self.create_root(b); p,n,e,i=self.paths(b); self.proof(p); self.node(n); runner=FakeInstaller(e)
            out=post_bootstrap.activate(r, proof_path=p, node_marker=n, executor_activation_receipt=e, integration_receipt=i,
                env={"HOME":str(b),"PATH":"/usr/bin","GITHUB_TOKEN":"forbidden","TVC_TOKEN":"not-required","WALLET_KEY":"forbidden","PROVIDER_SECRET":"forbidden"}, runner=runner)
            self.assertEqual(out["state"],"COMPLETE"); self.assertTrue(out["executor_service_active"]); self.assertFalse(out["wallet_handoff_ready_claimed"])
            _, env = runner.calls[0]
            for key in ("GITHUB_TOKEN","TVC_TOKEN","WALLET_KEY","PROVIDER_SECRET"): self.assertNotIn(key,env)
    def test_installer_success_without_authoritative_activation_receipt_does_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp); r=self.create_root(b); p,n,e,i=self.paths(b); self.proof(p); self.node(n); runner=FakeInstaller(e,active=False)
            out=post_bootstrap.activate(r, proof_path=p, node_marker=n, executor_activation_receipt=e, integration_receipt=i, env={}, runner=runner)
            self.assertEqual(out["state"],"REVIEW_REQUIRED"); self.assertFalse(out["executor_service_active"])

if __name__ == "__main__": unittest.main()
