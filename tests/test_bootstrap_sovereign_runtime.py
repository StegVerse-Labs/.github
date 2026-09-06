from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"

spec = importlib.util.spec_from_file_location("bootstrap_sovereign_runtime", SCRIPT)
bootstrap_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(bootstrap_module)


class FakeRunner:
    def __init__(
        self,
        proof_path: Path,
        integration_receipt: Path,
        *,
        install_returncode: int = 0,
        verify_returncode: int = 0,
        post_bootstrap_returncode: int = 0,
        write_proof: bool = True,
        executor_service_active: bool = True,
        valid_carrier_receipt: bool = True,
    ):
        self.proof_path = proof_path
        self.integration_receipt = integration_receipt
        self.install_returncode = install_returncode
        self.verify_returncode = verify_returncode
        self.post_bootstrap_returncode = post_bootstrap_returncode
        self.write_proof = write_proof
        self.executor_service_active = executor_service_active
        self.valid_carrier_receipt = valid_carrier_receipt
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(self, command, **kwargs):
        env = dict(kwargs.get("env") or {})
        self.calls.append((list(command), env))
        if "install_sovereign_heartbeat_carrier.py" in str(command[1]):
            runtime_root = Path(command[command.index("--runtime-root") + 1])
            path = runtime_root / "receipts/sovereign-host/carrier-activation.latest.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "schema": "stegverse.sovereign-heartbeat-carrier-activation/v1",
                "activation_scope": "CARRIER_ONLY",
                "carrier_active": self.install_returncode == 0 and self.valid_carrier_receipt,
                "worker_start_attempted": False,
                "worker_runtime_dependency_for_carrier_start": False,
                "network_fetch_required": False,
                "third_party_process_host_required": False,
                "third_party_scheduler_required": False,
                "github_runtime_dependency": False,
                "credential_authority": "TV/TVC",
                "credential_requirement": "NONE",
                "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
                "heartbeat_period_ms": 10.0,
                "heartbeat_reference_frequency_hz": 100.0,
                "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
                "canonical_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
                "carrier_progression_observation": {
                    "observed": self.valid_carrier_receipt,
                    "first_epoch": 32,
                    "last_epoch": 33,
                },
            }) + "\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, self.install_returncode, stdout="", stderr="")
        if "install_sovereign_heartbeat_service.py" in str(command[1]):
            raise AssertionError("combined heartbeat+worker installer must not be a carrier startup prerequisite")
        if "install_sovereign_worker_source_refresh_service.py" in str(command[1]):
            runtime_root = Path(command[command.index("--runtime-root") + 1])
            path = runtime_root / "receipts/sovereign-host/worker-source-refresh-installation.latest.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "activated": True,
                "filesystem_event_driven": True,
                "intr_materialization_event_driven": True,
                "source_package_event_driven": True,
                "worker_service": "stegverse-worker-runtime.service",
            }) + "\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if "verify_sovereign_runtime_activation.py" in str(command[1]):
            if self.write_proof:
                proof = {name: True for name in bootstrap_module.REQUIRED_PREDICATES}
                proof.update({
                    "schema": "stegverse.sovereign-runtime-activation-proof/v4",
                    "all_predicates_pass": True,
                    "detail": {"runtime_root": str(self.proof_path.parent / "runtime-placeholder")},
                })
                self.proof_path.parent.mkdir(parents=True, exist_ok=True)
                self.proof_path.write_text(json.dumps(proof) + "\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, self.verify_returncode, stdout="", stderr="")
        if "activate_stegfin_after_sovereign_bootstrap.py" in str(command[1]):
            self.integration_receipt.parent.mkdir(parents=True, exist_ok=True)
            self.integration_receipt.write_text(json.dumps({
                "schema": "stegverse.sovereign-stegfin-post-bootstrap/v1",
                "state": "COMPLETE" if self.post_bootstrap_returncode == 0 and self.executor_service_active else "REVIEW_REQUIRED",
                "reason": "BOUNDED_STEGFIN_EXECUTOR_SERVICE_ACTIVE_AFTER_CANONICAL_SOVEREIGN_BOOTSTRAP"
                if self.executor_service_active else "STEGFIN_EXECUTOR_SERVICE_ACTIVATION_NOT_PROVEN",
                "executor_service_active": self.executor_service_active,
                "credential_authority": "TV/TVC",
                "non_tv_tvc_secret_or_token_used": False,
                "wallet_handoff_ready_claimed": False,
            }) + "\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, self.post_bootstrap_returncode, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")


class SovereignRuntimeSelfBootstrapTests(unittest.TestCase):
    def make_source(self, root: Path, *, complete: bool = True, with_post_bootstrap: bool = False) -> Path:
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
        if with_post_bootstrap:
            path = source / "scripts" / "activate_stegfin_after_sovereign_bootstrap.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# released post-bootstrap bridge\n", encoding="utf-8")
        return source

    def paths(self, root: Path):
        return (
            root / "runtime",
            root / "node.json",
            root / "activation.latest.json",
            root / "bootstrap.latest.json",
            root / "sovereign-post-bootstrap.latest.json",
        )

    def patch_post_receipt(self, path: Path):
        original = bootstrap_module.default_post_bootstrap_receipt
        bootstrap_module.default_post_bootstrap_receipt = lambda: path.resolve()
        self.addCleanup(setattr, bootstrap_module, "default_post_bootstrap_receipt", original)

    def test_hosted_environment_fails_closed_before_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(
                source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt,
                env={"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": "should-not-matter"}, runner=runner,
            )
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_BOOTSTRAP_SURFACE")
            self.assertEqual(runner.calls, [])
            self.assertFalse(marker.exists())
            self.assertFalse(result["post_bootstrap_stegfin"]["attempted"])

    def test_incomplete_source_fails_closed_without_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, complete=False, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN")
            self.assertFalse(marker.exists())
            self.assertEqual(runner.calls, [])
            self.assertFalse(result["post_bootstrap_stegfin"]["attempted"])

    def test_eligible_local_source_derives_non_authorizing_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, _proof, _receipt, _post_receipt = self.paths(root)
            declared, ref, eligibility = bootstrap_module.derive_node_declaration(source, runtime, marker, {})
            self.assertTrue(declared)
            self.assertEqual(ref, str(marker.resolve()))
            self.assertTrue(eligibility["eligible"])
            body = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(body["schema"], "stegverse.sovereign-node-declaration/v0.4")
            self.assertEqual(body["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
            self.assertEqual(body["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertEqual(body["credential_requirement"], "NONE")
            self.assertEqual(body["credential_authority"], "TV/TVC")
            self.assertFalse(body["github_token_required"])
            self.assertEqual(body["authority_effect"], "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY")

    def test_publish_runtime_locator_is_nonsecret_and_uid_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            runtime = root / "state" / "stegverse" / "heartbeat-runtime"
            source.mkdir()
            runtime.mkdir(parents=True)
            xdg = root / "run-user"
            env = {"XDG_RUNTIME_DIR": str(xdg)}
            with mock.patch.object(bootstrap_module.platform, "system", return_value="Linux"):
                result = bootstrap_module.publish_runtime_locator(source, runtime, env=env)
            self.assertEqual(result["state"], "PUBLISHED")
            self.assertTrue(result["published"])
            marker = xdg / "stegverse" / "sovereign-runtime.json"
            self.assertTrue(marker.is_file())
            body = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(body["schema"], "stegverse.sovereign-runtime-locator/v1")
            self.assertEqual(body["uid"], bootstrap_module.os.getuid())
            self.assertEqual(body["runtime_root"], str(runtime.resolve()))
            self.assertEqual(body["source_root"], str(source.resolve()))
            self.assertFalse(body["credential_material_present"])
            self.assertFalse(body["request_grants_authority"])
            self.assertFalse(body["heartbeat_grants_authority"])
            self.assertEqual(body["github_token_runtime_authority"], "NONE")
            self.assertEqual(body["authority_effect"], "NONE_LOCATOR_ONLY")

    def test_successful_bootstrap_retains_locator_result_without_making_it_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            xdg = root / "run-user"
            with mock.patch.object(bootstrap_module.platform, "system", return_value="Linux"):
                result = bootstrap_module.bootstrap(
                    source,
                    runtime,
                    node_marker=marker,
                    proof_path=proof,
                    receipt_path=receipt,
                    env={"XDG_RUNTIME_DIR": str(xdg)},
                    runner=runner,
                )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["carrier_activation_valid"])
            self.assertTrue(result["runtime_locator"]["published"])
            self.assertEqual(result["runtime_locator"]["authority_effect"], "NONE_LOCATOR_ONLY")
            locator = json.loads((xdg / "stegverse" / "sovereign-runtime.json").read_text(encoding="utf-8"))
            self.assertFalse(locator["credential_material_present"])
            self.assertFalse(locator["heartbeat_grants_authority"])

    def test_successful_bootstrap_automatically_attempts_released_stegfin_service_activation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(
                source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt,
                env={
                    "GITHUB_TOKEN": "forbidden-value",
                    "GH_TOKEN": "forbidden-value",
                    "STEGVERSE_GITHUB_TOKEN": "forbidden-value",
                    "TVC_TOKEN": "not-required-for-bootstrap",
                }, runner=runner,
            )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(result["reason"], "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED")
            executables = [Path(call[0][1]).name for call in runner.calls]
            self.assertEqual(executables[0], "install_sovereign_heartbeat_carrier.py")
            self.assertNotIn("install_sovereign_heartbeat_service.py", executables)
            self.assertIn("activate_stegfin_after_sovereign_bootstrap.py", executables)
            for _command, child_env in runner.calls:
                for name in bootstrap_module.CREDENTIAL_ENV_VARS:
                    self.assertEqual(child_env[name], "")
            downstream = result["post_bootstrap_stegfin"]
            self.assertTrue(downstream["attempted"])
            self.assertEqual(downstream["state"], "COMPLETE")
            self.assertTrue(downstream["executor_service_active"])
            self.assertEqual(downstream["credential_authority"], "TV/TVC")
            self.assertFalse(downstream["non_tv_tvc_secret_or_token_used"])
            self.assertFalse(downstream["wallet_handoff_ready_claimed"])
            persisted = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(persisted["state"], "COMPLETE")
            self.assertTrue(persisted["activation_all_predicates_pass"])
            self.assertTrue(persisted["carrier_activation_valid"])

    def test_post_bootstrap_failure_does_not_forge_or_erase_sovereign_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt, post_bootstrap_returncode=1, executor_service_active=False)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["activation_all_predicates_pass"])
            self.assertTrue(result["post_bootstrap_stegfin"]["attempted"])
            self.assertEqual(result["post_bootstrap_stegfin"]["state"], "REVIEW_REQUIRED")
            self.assertFalse(result["post_bootstrap_stegfin"]["executor_service_active"])
            self.assertFalse(result["post_bootstrap_stegfin"]["wallet_handoff_ready_claimed"])

    def test_missing_or_failed_activation_proof_never_attempts_stegfin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt, verify_returncode=1, write_proof=False)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "REVIEW_REQUIRED")
            self.assertFalse(result["activation_all_predicates_pass"])
            self.assertEqual(set(result["missing_predicates"]), set(bootstrap_module.REQUIRED_PREDICATES))
            self.assertFalse(result["post_bootstrap_stegfin"]["attempted"])

    def test_invalid_carrier_activation_receipt_stops_before_worker_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            runner = FakeRunner(proof, post_receipt, valid_carrier_receipt=False)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "RETRY")
            self.assertEqual(result["reason"], "CARRIER_ONLY_ACTIVATION_PROOF_RETRY_REQUIRED")
            self.assertFalse(result["carrier_activation_valid"])
            executables = [Path(call[0][1]).name for call in runner.calls]
            self.assertEqual(executables, ["install_sovereign_heartbeat_carrier.py"])

    def test_explicit_skip_preserves_heartbeat_only_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(
                source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt,
                env={}, runner=runner, activate_downstream=False,
            )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertFalse(result["post_bootstrap_stegfin"]["attempted"])
            self.assertEqual(result["post_bootstrap_stegfin"]["state"], "NOT_ELIGIBLE")

    def test_tvc_skap_successor_is_independent_of_g18_terminalization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            runtime = root / "runtime"
            worker = runtime / "scripts" / "run_worker_runtime.py"
            worker.parent.mkdir(parents=True, exist_ok=True)
            worker.write_text("# worker runner\n", encoding="utf-8")
            proof = root / "proof.json"
            calls = []

            def runner(command, **kwargs):
                calls.append((list(command), dict(kwargs.get("env") or {})))
                result = {
                    "state": "ACTIVE",
                    "task_id": "TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001",
                    "claim_state": "CLAIMED",
                }
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(result) + "\n", stderr="")

            result = bootstrap_module._advance_tvc_skap_successor(
                source, runtime, proof_path=proof, env={"GITHUB_TOKEN": "must-be-scrubbed"}, runner=runner
            )
            self.assertTrue(result["attempted"])
            self.assertEqual(result["task_id"], "TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001")
            self.assertEqual(result["returncode"], 0)
            self.assertTrue(result["fresh_independent_claim_required"])
            self.assertTrue(result["parent_claim_reuse_prohibited"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertEqual(result["credential_authority"], "TV/TVC")
            self.assertEqual(len(calls), 1)
            command, child_env = calls[0]
            self.assertIn("--task-id", command)
            self.assertIn("TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001", command)
            self.assertEqual(child_env["GITHUB_TOKEN"], "")

    def test_source_dispatches_tvc_skap_before_g18_verification_gate(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        dispatch_pos = source.index('body["post_bootstrap_tvc_skap_successor"] = _advance_tvc_skap_successor(')
        verify_pos = source.index('verify = runner([sys.executable, str(source_root / "scripts" / "verify_sovereign_runtime_activation.py")')
        self.assertLess(dispatch_pos, verify_pos)
        self.assertNotIn('"reason": "G18_NOT_TERMINAL"', source)


if __name__ == "__main__":
    unittest.main()
