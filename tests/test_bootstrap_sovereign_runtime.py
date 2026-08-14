from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"

spec = importlib.util.spec_from_file_location("bootstrap_sovereign_runtime", SCRIPT)
bootstrap_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(bootstrap_module)


class FakeRunner:
    def __init__(self, proof_path: Path, *, install_returncode: int = 0, verify_returncode: int = 0, write_proof: bool = True):
        self.proof_path = proof_path
        self.install_returncode = install_returncode
        self.verify_returncode = verify_returncode
        self.write_proof = write_proof
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(self, command, **kwargs):
        env = dict(kwargs.get("env") or {})
        self.calls.append((list(command), env))
        if "install_sovereign_heartbeat_service.py" in str(command[1]):
            return subprocess.CompletedProcess(command, self.install_returncode, stdout="", stderr="")
        if "verify_sovereign_runtime_activation.py" in str(command[1]):
            if self.write_proof:
                proof = {name: True for name in bootstrap_module.REQUIRED_PREDICATES}
                proof.update({"schema": "stegverse.sovereign-runtime-activation-proof/v1", "all_predicates_pass": True})
                self.proof_path.parent.mkdir(parents=True, exist_ok=True)
                self.proof_path.write_text(json.dumps(proof) + "\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, self.verify_returncode, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")


class SovereignRuntimeSelfBootstrapTests(unittest.TestCase):
    def make_source(self, root: Path, *, complete: bool = True) -> Path:
        source = root / "source"
        required = list(bootstrap_module.REQUIRED_SOURCE_FILES)
        if not complete:
            required = required[:-1]
        for rel in required:
            path = source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                path.write_text("{}\n", encoding="utf-8")
            else:
                path.write_text("# test canonical source\n", encoding="utf-8")
        return source

    def paths(self, root: Path):
        return (
            root / "runtime",
            root / "node.json",
            root / "activation.latest.json",
            root / "bootstrap.latest.json",
        )

    def test_hosted_environment_fails_closed_before_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, proof, receipt = self.paths(root)
            runner = FakeRunner(proof)
            result = bootstrap_module.bootstrap(
                source,
                runtime,
                node_marker=marker,
                proof_path=proof,
                receipt_path=receipt,
                env={"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": "should-not-matter"},
                runner=runner,
            )
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_BOOTSTRAP_SURFACE")
            self.assertEqual(runner.calls, [])
            self.assertFalse(marker.exists())

    def test_incomplete_source_fails_closed_without_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, complete=False)
            runtime, marker, proof, receipt = self.paths(root)
            runner = FakeRunner(proof)
            result = bootstrap_module.bootstrap(
                source,
                runtime,
                node_marker=marker,
                proof_path=proof,
                receipt_path=receipt,
                env={},
                runner=runner,
            )
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN")
            self.assertFalse(marker.exists())
            self.assertEqual(runner.calls, [])

    def test_eligible_local_source_derives_non_authorizing_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, proof, receipt = self.paths(root)
            declared, ref, eligibility = bootstrap_module.derive_node_declaration(source, runtime, marker, {})
            self.assertTrue(declared)
            self.assertEqual(ref, str(marker.resolve()))
            self.assertTrue(eligibility["eligible"])
            body = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(body["schema"], "stegverse.sovereign-node-declaration/v0.3")
            self.assertEqual(body["credential_requirement"], "NONE")
            self.assertEqual(body["credential_authority"], "TV/TVC")
            self.assertFalse(body["github_token_required"])
            self.assertEqual(body["authority_effect"], "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY")

    def test_successful_bootstrap_orchestrates_installer_and_verifier_and_scrubs_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, proof, receipt = self.paths(root)
            runner = FakeRunner(proof)
            result = bootstrap_module.bootstrap(
                source,
                runtime,
                node_marker=marker,
                proof_path=proof,
                receipt_path=receipt,
                env={
                    "GITHUB_TOKEN": "forbidden-value",
                    "GH_TOKEN": "forbidden-value",
                    "STEGVERSE_GITHUB_TOKEN": "forbidden-value",
                    "TVC_TOKEN": "not-required-for-bootstrap",
                },
                runner=runner,
            )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(result["reason"], "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED")
            self.assertEqual(len(runner.calls), 2)
            for _command, child_env in runner.calls:
                for name in bootstrap_module.CREDENTIAL_ENV_VARS:
                    self.assertEqual(child_env[name], "")
                self.assertEqual(child_env["STEGVERSE_SOVEREIGN_NODE"], "1")
                self.assertEqual(child_env["STEGVERSE_SOVEREIGN_PROOF_PATH"], str(proof.resolve()))
            persisted = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(persisted["state"], "COMPLETE")
            self.assertTrue(persisted["activation_all_predicates_pass"])
            self.assertEqual(persisted["credential_authority"], "TV/TVC")
            self.assertFalse(persisted["github_token_required"])

    def test_missing_or_failed_activation_proof_never_completes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, proof, receipt = self.paths(root)
            runner = FakeRunner(proof, verify_returncode=1, write_proof=False)
            result = bootstrap_module.bootstrap(
                source,
                runtime,
                node_marker=marker,
                proof_path=proof,
                receipt_path=receipt,
                env={},
                runner=runner,
            )
            self.assertEqual(result["state"], "REVIEW_REQUIRED")
            self.assertFalse(result["activation_all_predicates_pass"])
            self.assertEqual(set(result["missing_predicates"]), set(bootstrap_module.REQUIRED_PREDICATES))


if __name__ == "__main__":
    unittest.main()
