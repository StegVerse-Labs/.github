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
        worker_presence: bool = True,
    ):
        self.proof_path = proof_path
        self.integration_receipt = integration_receipt
        self.install_returncode = install_returncode
        self.verify_returncode = verify_returncode
        self.post_bootstrap_returncode = post_bootstrap_returncode
        self.write_proof = write_proof
        self.executor_service_active = executor_service_active
        self.worker_presence = worker_presence
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    @staticmethod
    def _write_json(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def _materialize_carrier_evidence(self, runtime_root: Path) -> None:
        self._write_json(runtime_root / "receipts/sovereign-host/carrier-activation.latest.json", {
            "schema": "stegverse.sovereign-heartbeat-carrier-activation/v1",
            "activation_scope": "CARRIER_ONLY",
            "carrier_active": self.install_returncode == 0,
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
        })
        if not self.worker_presence:
            return
        self._write_json(runtime_root / "control/worker-runtime-state.json", {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 7,
            "observation_mode": "TASK_CAPABLE",
        })
        self._write_json(runtime_root / "receipts/sovereign-host/ephemeral-process.latest.json", {
            "schema": "stegverse.ephemeral-sovereign-process/v3",
            "active": True,
            "carrier_active": True,
            "worker_active": True,
            "worker_task_capable_cycle_observed": True,
            "separate_carrier_and_worker_processes": True,
            "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
            "third_party_process_host_required": False,
            "heartbeat_grants_execution_authority": False,
            "authority_effect": "NONE_SUPERVISION_ONLY",
        })

    def __call__(self, command, **kwargs):
        env = dict(kwargs.get("env") or {})
        self.calls.append((list(command), env))
        executable = str(command[1]) if len(command) > 1 else ""
        if "install_sovereign_heartbeat_carrier.py" in executable:
            runtime_root = Path(command[command.index("--runtime-root") + 1])
            self._materialize_carrier_evidence(runtime_root)
            return subprocess.CompletedProcess(command, self.install_returncode, stdout="", stderr="")
        if "install_sovereign_worker_source_refresh_service.py" in executable:
            runtime_root = Path(command[command.index("--runtime-root") + 1])
            self._write_json(runtime_root / "receipts/sovereign-host/worker-source-refresh-installation.latest.json", {
                "activated": True,
                "filesystem_event_driven": True,
                "intr_materialization_event_driven": True,
                "source_package_event_driven": True,
                "worker_service": "stegverse-worker-runtime.service",
            })
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if "dispatch_resident_execution_requests.py" in executable:
            runtime_root = Path(command[command.index("--runtime-root") + 1])
            self._write_json(runtime_root / "receipts/sovereign-host/resident-request-dispatch.latest.json", {
                "state": "DISPATCH_COMPLETE",
                "request_failures": [],
                "request_dispatch_grants_authority": False,
            })
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if "run_worker_runtime.py" in executable:
            result = {
                "state": "ACTIVE",
                "task_id": "TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001",
                "claim_state": "CLAIMED",
            }
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(result) + "\n", stderr="")
        if "verify_sovereign_runtime_activation.py" in executable:
            if self.write_proof:
                proof = {name: True for name in bootstrap_module.REQUIRED_PREDICATES}
                proof.update({
                    "schema": "stegverse.sovereign-runtime-activation-proof/v4",
                    "all_predicates_pass": True,
                    "activation_order": "CARRIER_ONLY_THEN_INDEPENDENT_WORKER_SELF_HEAL",
                    "detail": {"runtime_root": str(self.proof_path.parent / "runtime-placeholder")},
                })
                self._write_json(self.proof_path, proof)
            return subprocess.CompletedProcess(command, self.verify_returncode, stdout="", stderr="")
        if "activate_stegfin_after_sovereign_bootstrap.py" in executable:
            self._write_json(self.integration_receipt, {
                "schema": "stegverse.sovereign-stegfin-post-bootstrap/v1",
                "state": "COMPLETE" if self.post_bootstrap_returncode == 0 and self.executor_service_active else "REVIEW_REQUIRED",
                "reason": "BOUNDED_STEGFIN_EXECUTOR_SERVICE_ACTIVE_AFTER_CANONICAL_SOVEREIGN_BOOTSTRAP"
                if self.executor_service_active else "STEGFIN_EXECUTOR_SERVICE_ACTIVATION_NOT_PROVEN",
                "executor_service_active": self.executor_service_active,
                "credential_authority": "TV/TVC",
                "non_tv_tvc_secret_or_token_used": False,
                "wallet_handoff_ready_claimed": False,
            })
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
            path.write_text("{}\n" if path.suffix == ".json" else "# test canonical source\n", encoding="utf-8")
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

    def test_incomplete_source_fails_closed_without_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, complete=False)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN")
            self.assertEqual(runner.calls, [])

    def test_eligible_local_source_derives_non_authorizing_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, _proof, _receipt, _post = self.paths(root)
            declared, ref, eligibility = bootstrap_module.derive_node_declaration(source, runtime, marker, {})
            self.assertTrue(declared)
            self.assertEqual(ref, str(marker.resolve()))
            self.assertTrue(eligibility["eligible"])
            body = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(body["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
            self.assertEqual(body["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertEqual(body["credential_authority"], "TV/TVC")
            self.assertFalse(body["github_token_required"])

    def test_publish_runtime_locator_is_nonsecret_and_uid_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            runtime = root / "state" / "stegverse" / "heartbeat-runtime"
            source.mkdir()
            runtime.mkdir(parents=True)
            xdg = root / "run-user"
            with mock.patch.object(bootstrap_module.platform, "system", return_value="Linux"):
                result = bootstrap_module.publish_runtime_locator(source, runtime, env={"XDG_RUNTIME_DIR": str(xdg)})
            self.assertEqual(result["state"], "PUBLISHED")
            body = json.loads((xdg / "stegverse" / "sovereign-runtime.json").read_text(encoding="utf-8"))
            self.assertFalse(body["credential_material_present"])
            self.assertFalse(body["heartbeat_grants_authority"])
            self.assertEqual(body["github_token_runtime_authority"], "NONE")

    def test_successful_bootstrap_uses_carrier_first_then_independent_worker_presence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["carrier_activation_valid"])
            self.assertTrue(result["worker_presence_after_carrier_start"]["observed"])
            executables = [Path(call[0][1]).name for call in runner.calls]
            self.assertEqual(executables[0], "install_sovereign_heartbeat_carrier.py")
            self.assertNotIn("install_sovereign_heartbeat_service.py", executables)
            self.assertLess(executables.index("install_sovereign_heartbeat_carrier.py"), executables.index("verify_sovereign_runtime_activation.py"))

    def test_successful_bootstrap_retains_locator_without_making_it_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            xdg = root / "run-user"
            with mock.patch.object(bootstrap_module.platform, "system", return_value="Linux"):
                result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={"XDG_RUNTIME_DIR": str(xdg)}, runner=runner)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["runtime_locator"]["published"])
            self.assertEqual(result["runtime_locator"]["authority_effect"], "NONE_LOCATOR_ONLY")

    def test_successful_bootstrap_automatically_attempts_released_stegfin_service_activation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(
                source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt,
                env={"GITHUB_TOKEN": "forbidden", "GH_TOKEN": "forbidden", "STEGVERSE_GITHUB_TOKEN": "forbidden", "TVC_TOKEN": "forbidden"}, runner=runner,
            )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(result["reason"], "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED")
            self.assertIn("activate_stegfin_after_sovereign_bootstrap.py", runner.calls[-1][0][1])
            for _command, child_env in runner.calls:
                for name in bootstrap_module.CREDENTIAL_ENV_VARS:
                    self.assertEqual(child_env[name], "")
            self.assertTrue(result["post_bootstrap_stegfin"]["executor_service_active"])

    def test_post_bootstrap_failure_does_not_erase_sovereign_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt, post_bootstrap_returncode=1, executor_service_active=False)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(result["activation_all_predicates_pass"])
            self.assertEqual(result["post_bootstrap_stegfin"]["state"], "REVIEW_REQUIRED")

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

    def test_missing_worker_self_heal_evidence_keeps_bootstrap_active_for_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            runner = FakeRunner(proof, post_receipt, worker_presence=False)
            with mock.patch.object(bootstrap_module, "_wait_for_worker_presence", return_value={"observed": False, "state": "INDEPENDENT_WORKER_PRESENCE_NOT_YET_OBSERVED", "authority_effect": "NONE_OBSERVATION_ONLY"}):
                result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner)
            self.assertEqual(result["state"], "RETRY")
            self.assertEqual(result["reason"], "INDEPENDENT_WORKER_SELF_HEAL_NOT_YET_OBSERVED")
            self.assertTrue(result["carrier_activation_valid"])

    def test_explicit_skip_preserves_post_bootstrap_integration_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, with_post_bootstrap=True)
            runtime, marker, proof, receipt, post_receipt = self.paths(root)
            self.patch_post_receipt(post_receipt)
            runner = FakeRunner(proof, post_receipt)
            result = bootstrap_module.bootstrap(source, runtime, node_marker=marker, proof_path=proof, receipt_path=receipt, env={}, runner=runner, activate_downstream=False)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertFalse(result["post_bootstrap_stegfin"]["attempted"])
            self.assertEqual(result["post_bootstrap_stegfin"]["state"], "NOT_ELIGIBLE")

    def test_tvc_skap_successor_is_independent_of_g18_terminalization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            worker = runtime / "scripts" / "run_worker_runtime.py"
            worker.parent.mkdir(parents=True, exist_ok=True)
            worker.write_text("# worker runner\n", encoding="utf-8")
            proof = root / "proof.json"
            calls = []
            def runner(command, **kwargs):
                calls.append((list(command), dict(kwargs.get("env") or {})))
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"state": "ACTIVE", "task_id": "TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001", "claim_state": "CLAIMED"}) + "\n", stderr="")
            result = bootstrap_module._advance_tvc_skap_successor(root / "source", runtime, proof_path=proof, env={"GITHUB_TOKEN": "must-be-scrubbed"}, runner=runner)
            self.assertTrue(result["attempted"])
            self.assertTrue(result["fresh_independent_claim_required"])
            self.assertTrue(result["parent_claim_reuse_prohibited"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertEqual(calls[0][1]["GITHUB_TOKEN"], "")

    def test_source_dispatches_tvc_skap_before_verification_without_g18_gate(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        dispatch_pos = source.index('body["post_bootstrap_tvc_skap_successor"] = _advance_tvc_skap_successor(')
        verify_pos = source.index('verify_sovereign_runtime_activation.py')
        self.assertLess(dispatch_pos, verify_pos)
        self.assertNotIn('"reason": "G18_NOT_TERMINAL"', source)


if __name__ == "__main__":
    unittest.main()
