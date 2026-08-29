from __future__ import annotations

import json
import os
import tempfile
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


    def test_evaluator_route_projection_is_disabled_without_materialized_config(self) -> None:
        old = dict(os.environ)
        try:
            os.environ.pop(mod.EVALUATOR_CONFIG_ENV, None)
            with tempfile.TemporaryDirectory() as td:
                mod.EVALUATOR_CONFIG_DEFAULT = Path(td) / "missing.json"
                projection = mod.evaluator_gateway_projection()
        finally:
            os.environ.clear()
            os.environ.update(old)
        self.assertEqual(projection["STEGVERSE_EVALUATOR_INTR_ENABLED"], "false")
        self.assertEqual(projection["STEGVERSE_EVALUATOR_INTR_UPSTREAM"], "")

    def test_evaluator_route_projection_uses_exact_materialized_loopback_only(self) -> None:
        old = dict(os.environ)
        try:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "evaluator.json"
                path.write_text(json.dumps({
                    "schema": "stegverse.evaluator-intr-route-config/v1",
                    "host": "127.0.0.1",
                    "port": 8765,
                    "credential_authority": "TV/TVC",
                    "github_token_runtime_authority": "NONE",
                    "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
                }) + "\n", encoding="utf-8")
                os.environ[mod.EVALUATOR_CONFIG_ENV] = str(path)
                projection = mod.evaluator_gateway_projection()
                self.assertEqual(projection["STEGVERSE_EVALUATOR_INTR_ENABLED"], "true")
                self.assertEqual(projection["STEGVERSE_EVALUATOR_INTR_UPSTREAM"], "http://127.0.0.1:8765/intr/evaluator")

                value = json.loads(path.read_text(encoding="utf-8"))
                value["host"] = "192.0.2.10"
                path.write_text(json.dumps(value) + "\n", encoding="utf-8")
                disabled = mod.evaluator_gateway_projection()
                self.assertEqual(disabled["STEGVERSE_EVALUATOR_INTR_ENABLED"], "false")
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_healer_child_env_carries_only_nonsecret_evaluator_projection(self) -> None:
        old = dict(os.environ)
        try:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "evaluator.json"
                path.write_text(json.dumps({
                    "schema": "stegverse.evaluator-intr-route-config/v1",
                    "host": "127.0.0.1",
                    "port": 8765,
                    "credential_authority": "TV/TVC",
                    "github_token_runtime_authority": "NONE",
                    "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
                }) + "\n", encoding="utf-8")
                os.environ[mod.EVALUATOR_CONFIG_ENV] = str(path)
                env = mod.build_healer_child_env(Path("/healer/targets.json"), "{}")
        finally:
            os.environ.clear()
            os.environ.update(old)
        self.assertEqual(env["STEGVERSE_EVALUATOR_INTR_ENABLED"], "true")
        self.assertEqual(env["STEGVERSE_EVALUATOR_INTR_UPSTREAM"], "http://127.0.0.1:8765/intr/evaluator")
        self.assertNotIn(mod.EVALUATOR_CONFIG_ENV, env)

    def test_required_scheduler_inputs_still_cross_boundary(self) -> None:
        env = mod.build_healer_child_env(Path("/healer/targets.json"), "{}")
        self.assertEqual(env["RUN_SCOPE"], "all")
        self.assertEqual(env["DISPATCH_MODE"], "schedule")
        self.assertEqual(env["TARGETS_FILE"], "/healer/targets.json")
        self.assertEqual(env["STEGVERSE_REPO_ROOTS_JSON"], "{}")


if __name__ == "__main__":
    unittest.main()
