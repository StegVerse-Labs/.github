from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "stegfin_continuity_carrier_worker_v3.py"

spec = importlib.util.spec_from_file_location("stegfin_continuity_v3", WORKER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class StegFinContinuityLocalBrokerFastPathTests(unittest.TestCase):
    def test_absolute_live_unix_socket_is_selected_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.sock"
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                server.bind(str(path))
                with mock.patch.dict(os.environ, {"STEGVERSE_TV_TVC_BROKER_ENDPOINT": str(path)}, clear=False):
                    self.assertEqual(module.local_broker_endpoint(), str(path.resolve()))
            finally:
                server.close()

    def test_https_endpoint_preserves_existing_primary_runtime_path(self) -> None:
        with mock.patch.dict(os.environ, {"STEGVERSE_TV_TVC_BROKER_ENDPOINT": "https://tvc.stegverse.org/v1/provider-operation"}, clear=False):
            self.assertIsNone(module.local_broker_endpoint())

    def test_regular_file_is_not_accepted_as_unix_broker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-a-socket"
            path.write_text("no\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"STEGVERSE_TV_TVC_BROKER_ENDPOINT": str(path)}, clear=False):
                self.assertIsNone(module.local_broker_endpoint())

    def test_adapter_contains_no_secret_environment_allowlist(self) -> None:
        import json
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/stegfin-continuity-carrier-007.json").read_text(encoding="utf-8"))["adapters"][0]
        self.assertEqual(adapter["command"], ["python", "workers/stegfin_continuity_carrier_worker_v3.py"])
        forbidden = {"GITHUB_TOKEN", "GH_TOKEN", "ZEROEX_API_KEY", "WALLET_PRIVATE_KEY", "API_KEY", "PRIVATE_KEY"}
        self.assertTrue(forbidden.isdisjoint(set(adapter["env_allowlist"])))


if __name__ == "__main__":
    unittest.main()
