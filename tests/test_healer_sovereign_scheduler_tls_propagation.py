from __future__ import annotations

import os
import unittest
from pathlib import Path

from workers import healer_sovereign_scheduler_worker as mod


class HealerSovereignSchedulerTlsPropagationTests(unittest.TestCase):
    def test_only_tls_locator_and_config_values_cross_worker_boundary(self) -> None:
        old = dict(os.environ)
        try:
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_CERT_FILE"] = "/runtime/tvc/cert.pem"
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_KEY_FILE"] = "/runtime/tvc/key.pem"
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_BIND_ADDRESS"] = "0.0.0.0"
            os.environ["STEGVERSE_SERVICE_GATEWAY_TLS_PORT"] = "443"
            os.environ["STEGVERSE_PROVIDER_TOKEN"] = "must-not-propagate"
            os.environ["STEGVERSE_MASTER_RECORDS_TOKEN"] = "must-not-propagate"
            env = mod.build_healer_child_env(Path("/healer/targets.json"), '{"StegVerse-org/LLM-adapter":"/llm"}')
        finally:
            os.environ.clear()
            os.environ.update(old)

        self.assertEqual(env["STEGVERSE_SERVICE_GATEWAY_TLS_CERT_FILE"], "/runtime/tvc/cert.pem")
        self.assertEqual(env["STEGVERSE_SERVICE_GATEWAY_TLS_KEY_FILE"], "/runtime/tvc/key.pem")
        self.assertEqual(env["STEGVERSE_SERVICE_GATEWAY_TLS_BIND_ADDRESS"], "0.0.0.0")
        self.assertEqual(env["STEGVERSE_SERVICE_GATEWAY_TLS_PORT"], "443")
        self.assertNotIn("STEGVERSE_PROVIDER_TOKEN", env)
        self.assertNotIn("STEGVERSE_MASTER_RECORDS_TOKEN", env)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("must-not-propagate", repr(env))

    def test_empty_tls_locators_are_not_injected(self) -> None:
        old = dict(os.environ)
        try:
            for name in mod.TLS_LOCATOR_ENV:
                os.environ.pop(name, None)
            env = mod.build_healer_child_env(Path("/healer/targets.json"), "{}")
        finally:
            os.environ.clear()
            os.environ.update(old)

        for name in mod.TLS_LOCATOR_ENV:
            self.assertNotIn(name, env)


if __name__ == "__main__":
    unittest.main()
