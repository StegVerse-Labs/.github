import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "run_device_kv_skap_roundtrip_worker.py"
CONTINUATION = ROOT / "scripts" / "continue_device_kv_skap_from_tvc_custody.py"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "device-kv-skap-roundtrip-001.json"


def _load_worker():
    spec = importlib.util.spec_from_file_location("device_kv_skap_roundtrip_worker", WORKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("worker module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _invocation(*, claim_id="CLAIM-DEVICE-KV-SKAP-G7", fence=7):
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 42,
        "task": {
            "task_id": "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
            "claim_id": claim_id,
            "heartbeat_timing": {"fencing_token": fence},
        },
        "handoff": {
            "goal": {"goal_id": "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"},
            "task": {"task_id": "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"},
            "authority": {
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "transition_authority": "Interlock/InTr",
            },
        },
        "scope": {
            "claim_id": claim_id,
            "fencing_token": fence,
            "allowed_paths": ["StegVerse-Labs/.github"],
            "required_capabilities": ["bounded_process_execution"],
        },
    }


class DeviceKVSKAPRoundTripWorkerSourceTests(unittest.TestCase):
    def test_worker_supports_tvc_single_writer_continuation(self):
        text = WORKER.read_text(encoding="utf-8")
        for marker in (
            "STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR",
            "STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT",
            "STEGVERSE_STEGOS_ROOT",
            "continue_device_kv_skap_from_tvc_custody.py",
            "continue_roundtrip(",
            "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED",
            "manifest_or_tvc_continuation_required",
        ):
            self.assertIn(marker, text)

    def test_worker_consumes_process_adapter_invocation_and_emits_response_protocol(self):
        text = WORKER.read_text(encoding="utf-8")
        for marker in (
            "stegverse.worker-invocation/v0.1",
            "stegverse.worker-response/v0.1",
            "worker_claim_binding_mismatch",
            "worker_fence_binding_mismatch",
            "claim_or_fence_minted_by_worker",
            '"transition_authority": "Interlock/InTr"',
            '"credential_authority": "TV/TVC"',
        ):
            self.assertIn(marker, text)

    def test_valid_fenced_invocation_is_bound_without_minting_authority(self):
        worker = _load_worker()
        epoch, claim_id, fence = worker._validate_invocation(_invocation())
        self.assertEqual(epoch, 42)
        self.assertEqual(claim_id, "CLAIM-DEVICE-KV-SKAP-G7")
        self.assertEqual(fence, 7)

    def test_claim_fence_mismatch_fails_closed(self):
        worker = _load_worker()
        with self.assertRaisesRegex(SystemExit, "worker_claim_fence_invalid"):
            worker._validate_invocation(_invocation(claim_id="CLAIM-DEVICE-KV-SKAP-G6", fence=7))

    def test_task_claim_binding_mismatch_fails_closed(self):
        worker = _load_worker()
        invocation = _invocation()
        invocation["task"]["claim_id"] = "CLAIM-OTHER-G7"
        with self.assertRaisesRegex(SystemExit, "worker_claim_binding_mismatch"):
            worker._validate_invocation(invocation)

    def test_worker_fails_closed_on_partial_continuation_inputs(self):
        text = WORKER.read_text(encoding="utf-8")
        self.assertIn("if any(continuation_inputs) and not all(continuation_inputs)", text)
        self.assertIn("incomplete_tvc_continuation_inputs", text)

    def test_adapter_allows_only_nonsecret_continuation_paths(self):
        adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))["adapters"][0]
        allow = set(adapter["env_allowlist"])
        self.assertTrue({
            "STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT",
            "STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR",
            "STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT",
            "STEGVERSE_STEGOS_ROOT",
            "STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT",
        }.issubset(allow))
        forbidden_tokens = ("TOKEN", "SECRET", "PASSWORD", "PRIVATE_KEY", "CREDENTIAL_VALUE")
        for name in allow:
            self.assertFalse(any(token in name for token in forbidden_tokens), name)

    def test_continuation_preserves_tvc_as_single_custody_writer(self):
        text = CONTINUATION.read_text(encoding="utf-8")
        self.assertIn("TVC remains the only ciphertext custody writer", text)
        self.assertIn("custody_path,custody_bytes,tvc_digest=_validate_tvc_outcome", text)
        self.assertIn("tvc_single_custody_writer_preserved\":True", text)
        self.assertNotIn("write_bytes(custody_bytes)", text)
        self.assertNotIn("atomic_bytes(custody_path", text)

    def test_continuation_requires_exact_skap_readback_and_first_hop_binding(self):
        text = CONTINUATION.read_text(encoding="utf-8")
        self.assertIn("tvc_skap_exact_readback_mismatch", text)
        self.assertIn("tvc_custody_first_hop_binding_mismatch", text)
        self.assertIn("canonical_roundtrip_eligible", text)
        self.assertIn("exact_ciphertext_readback_verified\":True", text)


if __name__ == "__main__":
    unittest.main()
