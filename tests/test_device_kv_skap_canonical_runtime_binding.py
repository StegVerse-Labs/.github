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
            "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
            "STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE",
            "STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT",
            "STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT",
            "STEGVERSE_STEGOS_ROOT",
        }
        self.assertTrue(required.issubset(set(cfg["env_allowlist"])))

    def test_wrapper_binds_existing_authority_layers(self):
        text = WRAPPER.read_text(encoding="utf-8")
        for marker in (
            "WorkerCoordinatorCanonicalRuntimeBridge",
            "build_runtime_admission_from_lease_snapshot",
            "CLAIM_GRANT_OBSERVED",
            "WORKERCOORDINATOR_CLAIM_ONLY",
            "device-kv-skap-roundtrip",
            "50000000102000",
            "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
            "STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE",
            "STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT",
            "STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT",
        ):
            self.assertIn(marker, text)

    def test_wrapper_does_not_create_parallel_authority(self):
        text = WRAPPER.read_text(encoding="utf-8")
        forbidden = (
            "LeaseMachine(",
            "claim_id = f\"",
            "credential_material",
            "cloudflared",
            "Render",
        )
        for marker in forbidden:
            self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
