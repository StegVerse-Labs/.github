import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "run_device_kv_skap_roundtrip_worker.py"
CONTINUATION = ROOT / "scripts" / "continue_device_kv_skap_from_tvc_custody.py"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "device-kv-skap-roundtrip-001.json"


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
