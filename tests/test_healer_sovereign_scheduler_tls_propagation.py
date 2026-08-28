from __future__ import annotations

import os
import unittest
from pathlib import Path

from workers import healer_sovereign_scheduler_worker as mod


class HealerSovereignSchedulerTlsAutodiscoveryTests(unittest.TestCase):
    def test_worker_does_not_propagate_tls_or_secret_locators(self) -> None:
        old = dict(os.environ)
        try:
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_CERT_FILE"] = "/runtime/tvc/cert.pem"
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_KEY_FILE"] = "/runtime/tvc/key.pem"
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_BIND_ADDRESS"] = "0.0.0.0"
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_PORT"] = "443"
            os.environ["STEGVERSE_TVC_SERVICE_GATEWAY_TLS_ADOPTION_RECEIPT"] = "/var/lib/stegverse/tvc/service-gateway-tls/latest.json"
            os.environ["STEGVERSE_PROVIDER_TOKEN"] = "must-not-propagate"
            os.environ["STEGVERSE_MASTER_RECORDS_TOKEN"] = "must-not-propagate"
            env = mod.build_healer_child_env(Path("/healer/targets.json"), '{"StegVerse-org/LLM-adapter":"/llm"}')
        finally:
            os.environ.clear()
            os.environ.update(old)

        for name in (
            "STEGVERSE_SERVICE_GATEWAY_TLS_CERT_FILE",
            "STEGVERSE_SERVICE_GATEWAY_TLS_KEY_FILE",
            "STEGVERSE_SERVICE_GATEWAY_TLS_BIND_ADDRESS",
            "STEGVERSE_SERVICE_GATEWAY_TLS_PORT",
            "STEGVERSE_TVC_SERVICE_GATEWAY_TLS_ADOPTION_RECEIPT",
            "STEGVERSE_PROVIDER_TOKEN",
            "STEGVERSE_MASTER_RECORDS_TOKEN",
            "GITHUB_TOKEN",
            "GH_TOKEN",
        ):
            self.assertNotIn(name, env)
        self.assertNotIn("must-not-propagate", repr(env))

    def test_required_scheduler_inputs_still_cross_boundary(self) -> None:
        env = mod.build_healer_child_env(Path("/healer/targets.json"), "{}")
        self.assertEqual(env["RUN_SCOPE"], "all")
        self.assertEqual(env["DISPATCH_MODE"], "schedule")
        self.assertEqual(env["TARGETS_FILE"], "/healer/targets.json")
        self.assertEqual(env["STEGVERSE_REPO_ROOTS_JSON"], "{}")


if __name__ == "__main__":
    unittest.main()
