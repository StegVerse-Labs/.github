from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "execute_device_kv_skap_roundtrip_event.py"
SPEC = importlib.util.spec_from_file_location("device_kv_skap_event_execution", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class DeviceKVSKAPEventExecutionTests(unittest.TestCase):
    def test_safe_env_forwards_only_nonsecret_roundtrip_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            stegos = root / "stegos"
            sidecar = root / "gateway.json"
            tvc = root / "tvc.json"
            output = root / "out.json"
            env = mod._safe_env(
                {
                    "PATH": "/usr/bin",
                    "HOME": "/tmp/home",
                    "GITHUB_TOKEN": "must-not-pass",
                    "TVC_TOKEN": "must-not-pass",
                    "OPENAI_API_KEY": "must-not-pass",
                },
                runtime=runtime,
                stegos=stegos,
                sidecar=sidecar,
                tvc_receipt=tvc,
                output=output,
            )
            self.assertEqual(env["STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT"], str(runtime))
            self.assertEqual(env["STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR"], str(sidecar))
            self.assertEqual(env["STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT"], str(tvc))
            self.assertEqual(env["STEGVERSE_STEGOS_ROOT"], str(stegos))
            self.assertEqual(env["STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT"], str(output))
            self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
            self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertNotIn("TVC_TOKEN", env)
            self.assertNotIn("OPENAI_API_KEY", env)

    def test_safe_env_rejects_hosted_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(mod.RoundtripEventExecutionError, "hosted_runtime_forbidden"):
                mod._safe_env(
                    {"PATH": "/usr/bin", "GITHUB_ACTIONS": "true"},
                    runtime=root / "runtime",
                    stegos=root / "stegos",
                    sidecar=root / "gateway.json",
                    tvc_receipt=root / "tvc.json",
                    output=root / "out.json",
                )

    def test_event_executor_binds_canonical_task_and_cosv(self) -> None:
        self.assertEqual(mod.TASK_ID, "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001")
        self.assertEqual(mod.COSV_VECTOR, "50000000102000")
        self.assertEqual(mod.TERMINAL_TRANSITION, "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED")
        self.assertEqual(mod.RUNNER_REL.as_posix(), "scripts/run_worker_runtime.py")

    def _terminal_fixture(self, root: Path):
        runtime = root / "runtime"
        runtime.mkdir(parents=True)
        checkpoint_ref = "checkpoints/workers/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001/HB31-G7.json"
        checkpoint_path = runtime / checkpoint_ref
        checkpoint_path.parent.mkdir(parents=True)
        checkpoint = {
            "schema": "stegverse.worker-checkpoint/v0.1",
            "checkpoint_id": "CP-STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001-HB31-G7",
            "heartbeat_epoch": 31,
            "task_id": mod.TASK_ID,
            "goal_id": mod.TASK_ID,
            "worker_id": "worker-1",
            "worker_instance_id": "worker-1-HB31-G7",
            "claim_id": "SHWP-STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001-G7",
            "fencing_token": 7,
            "current_state": "COMPLETED",
            "completed_transitions": [{
                "heartbeat_epoch": 31,
                "transition_id": mod.TERMINAL_TRANSITION,
                "transition_sequence": 1,
                "response_state": "COMPLETED",
            }],
            "unresolved_work": [],
            "evidence_refs": ["receipts/roundtrip.json"],
            "next_authorized_action": "No additional action authorized",
            "policy_version": "test",
            "authority_source": "test",
            "handoff_ref": "handoffs/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json",
            "handoff_sha256": "a" * 64,
            "worker_checkpoint_ref": "receipts/roundtrip.json",
            "resource_budget": {},
            "execution_authority": False,
        }
        checkpoint["checkpoint_sha256"] = mod._checkpoint_digest(checkpoint)
        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

        registry_path = runtime / mod.REGISTRY_REL
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps({
            "tasks": [{
                "task_id": mod.TASK_ID,
                "state": "COMPLETED",
                "last_checkpoint_ref": checkpoint_ref,
                "heartbeat_timing": {
                    "current_transition": mod.TERMINAL_TRANSITION,
                    "fencing_token": 7,
                },
            }]
        }), encoding="utf-8")

        result_path = runtime / "receipts/roundtrip.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps({
            "state": mod.TERMINAL_TRANSITION,
            "credential_authority": "TV/TVC",
        }), encoding="utf-8")

        cycle = {
            "schema": "stegverse.worker-runtime-cycle-result/v1",
            "target_task_id": mod.TASK_ID,
            "targeted_independent_task_control": True,
            "unrelated_worker_execution_suppressed": True,
            "carrier_packet_execution_suppressed": True,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "events": [
                {
                    "event_type": "worker_response",
                    "task_id": mod.TASK_ID,
                    "response_state": "COMPLETED",
                    "transition_id": mod.TERMINAL_TRANSITION,
                    "transition_sequence": 1,
                },
                {
                    "event_type": "canonical_worker_checkpoint_written",
                    "task_id": mod.TASK_ID,
                    "checkpoint_ref": checkpoint_ref,
                    "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                    "fencing_token": 7,
                },
            ],
        }
        return runtime, result_path, cycle

    def test_terminal_verification_uses_workercoordinator_cycle_checkpoint_registry_and_readback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime, result_path, cycle = self._terminal_fixture(Path(tmp))
            evidence = mod._validate_targeted_terminal_evidence(
                runtime=runtime,
                cycle=cycle,
                result_path=result_path,
            )
            self.assertEqual(evidence["state"], mod.TERMINAL_TRANSITION)
            self.assertEqual(evidence["fencing_token"], 7)
            self.assertTrue(evidence["canonical_checkpoint_ref"].startswith("checkpoints/workers/"))
            self.assertEqual(evidence["worker_result"]["state"], mod.TERMINAL_TRANSITION)

    def test_terminal_verification_rejects_old_direct_stdout_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime, result_path, _cycle = self._terminal_fixture(Path(tmp))
            with self.assertRaisesRegex(mod.RoundtripEventExecutionError, "worker_cycle_schema_invalid"):
                mod._validate_targeted_terminal_evidence(
                    runtime=runtime,
                    cycle={"state": mod.TERMINAL_TRANSITION},
                    result_path=result_path,
                )

    def test_terminal_verification_rejects_missing_canonical_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime, result_path, cycle = self._terminal_fixture(Path(tmp))
            cycle["events"] = [cycle["events"][0]]
            with self.assertRaisesRegex(mod.RoundtripEventExecutionError, "canonical_worker_checkpoint_event_not_observed"):
                mod._validate_targeted_terminal_evidence(
                    runtime=runtime,
                    cycle=cycle,
                    result_path=result_path,
                )

    def test_terminal_verification_rejects_unverified_worker_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime, result_path, cycle = self._terminal_fixture(Path(tmp))
            result_path.write_text(json.dumps({"state": "INCOMPLETE"}), encoding="utf-8")
            with self.assertRaisesRegex(mod.RoundtripEventExecutionError, "roundtrip_worker_result_not_verified"):
                mod._validate_targeted_terminal_evidence(
                    runtime=runtime,
                    cycle=cycle,
                    result_path=result_path,
                )


if __name__ == "__main__":
    unittest.main()
