from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workers import healer_sovereign_scheduler_worker as mod


class HealerUniversalInTrProjectionTests(unittest.TestCase):
    def config(self):
        return {
            "schema": "stegverse.hil-intr-route-config/v1",
            "runtime_root": "/var/lib/stegverse/runtime",
            "loopback_url": "http://127.0.0.1:8765",
            "public_origin": "https://stegverse.org",
            "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
            "boundary_identity_ref": "node:test",
            "event_triggered": True,
            "always_on_receiver_required": False,
            "second_user_device_required": False,
            "g18_completion_required": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "execution_authority": "NONE",
            "authority_effect": "NONE_CONFIG_ONLY",
        }

    def project(self, value):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hil-intr-runtime.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with patch.dict("os.environ", {mod.HIL_INTR_CONFIG_ENV: str(path)}, clear=False):
                return mod.hil_intr_gateway_projection()

    def test_valid_route_projects_exact_materialization_upstream(self):
        self.assertEqual(
            self.project(self.config()),
            {
                "STEGVERSE_HIL_INTR_ENABLED": "true",
                "STEGVERSE_HIL_INTR_UPSTREAM": "http://127.0.0.1:8765/intr/materialization",
            },
        )

    def test_missing_config_fails_closed(self):
        with patch.dict("os.environ", {mod.HIL_INTR_CONFIG_ENV: "/definitely/missing.json"}, clear=False):
            self.assertEqual(
                mod.hil_intr_gateway_projection(),
                {"STEGVERSE_HIL_INTR_ENABLED": "false", "STEGVERSE_HIL_INTR_UPSTREAM": ""},
            )

    def test_authority_drift_fails_closed(self):
        value = self.config()
        value["github_token_runtime_authority"] = "FULL"
        self.assertEqual(self.project(value)["STEGVERSE_HIL_INTR_ENABLED"], "false")

    def test_non_loopback_route_fails_closed(self):
        value = self.config()
        value["loopback_url"] = "https://remote.example"
        self.assertEqual(self.project(value)["STEGVERSE_HIL_INTR_ENABLED"], "false")

    def test_g18_dependency_drift_fails_closed(self):
        value = self.config()
        value["g18_completion_required"] = True
        self.assertEqual(self.project(value)["STEGVERSE_HIL_INTR_ENABLED"], "false")


if __name__ == "__main__":
    unittest.main()
