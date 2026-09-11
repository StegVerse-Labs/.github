import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "workers" / "run_device_kv_skap_canonical_runtime_worker.py"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "device-kv-skap-roundtrip-001.json"


class DeviceKVSKAPCanonicalRuntimeBindingTests(unittest.TestCase):
    def test_registered_adapter_uses_canonical_runtime_wrapper(self):
        cfg = json.loads(ADAPTER.read_text(encoding="utf-8"))["adapters"][0]
        self.assertEqual(cfg["command"], ["python", "workers/run_device_kv_skap_canonical_runtime_worker.py"])
        required = {
            "STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT",
            "STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT",
            "STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR",
            "STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT",
            "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
            "STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE",
            "STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT",
            "STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT",
            "STEGVERSE_STEGOS_ROOT",
        }
        self.assertTrue(required.issubset(set(cfg["env_allowlist"])))
        forbidden_tokens = ("TOKEN", "SECRET", "PASSWORD", "PRIVATE_KEY", "CREDENTIAL_VALUE")
        for name in cfg["env_allowlist"]:
            self.assertFalse(any(token in name for token in forbidden_tokens), name)

    def test_wrapper_consumes_merged_stegos_domain_binding(self):
        text = WRAPPER.read_text(encoding="utf-8")
        for marker in (
            "stegos.device_kv_skap_canonical_runtime",
            "DeviceKVSKAPCanonicalRuntimeCapability",
            "execute_bound_device_kv_skap_roundtrip",
            "worker_claim_from_invocation",
            "build_runtime_admission_from_lease_snapshot",
            "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
            "STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE",
            "STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT",
            "STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT",
            "canonical_worker_response_hash_mismatch",
            "canonical_runtime_lease_binding_mismatch",
        ):
            self.assertIn(marker, text)

    def test_wrapper_does_not_reimplement_parallel_bridge_or_authority(self):
        text = WRAPPER.read_text(encoding="utf-8")
        forbidden = (
            "LeaseMachine(",
            "CapabilityAdapter(",
            "Bridge()",
            "def _worker_claim(",
            "CLAIM_GRANT_OBSERVED",
            "WORKERCOORDINATOR_CLAIM_ONLY",
            "claim_id = f\"",
            "credential_material",
            "cloudflared",
            "Render",
        )
        for marker in forbidden:
            self.assertNotIn(marker, text)

    def test_bridge_receipt_is_an_output_not_a_preexisting_input(self):
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn('_output_path("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT")', text)
        self.assertNotIn('_required_path("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT")', text)
        self.assertIn("domain_worker._write_once(bridge_receipt_path, dict(receipt))", text)


if __name__ == "__main__":
    unittest.main()
