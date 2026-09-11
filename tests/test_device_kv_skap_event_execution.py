from __future__ import annotations

import importlib.util
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
        self.assertEqual(mod.RUNNER_REL.as_posix(), "scripts/run_worker_runtime.py")


if __name__ == "__main__":
    unittest.main()
