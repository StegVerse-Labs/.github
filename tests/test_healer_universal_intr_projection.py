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


def test_hil_receiver_gateway_projection_requires_fresh_machine_claim_over_retained_g25_predecessor(tmp_path, monkeypatch):
    runtime = tmp_path
    receipt = runtime / mod.HIL_RECEIVER_WORKER_RECEIPT_REL
    receipt.parent.mkdir(parents=True)
    durable = tmp_path / "hil-durable"
    durable.mkdir()
    receipt.write_text(json.dumps({
        "schema": "stegverse.hil.sovereign-receiver-worker-receipt/v0.1",
        "task_id": mod.HIL_RECEIVER_TASK_ID,
        "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G26",
        "fencing_token": 26,
        "predecessor_claim_id": mod.HIL_RECEIVER_PREDECESSOR_CLAIM_ID,
        "predecessor_fencing_token": mod.HIL_RECEIVER_PREDECESSOR_FENCE,
        "receiver_ready": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "base_url": "http://127.0.0.1:8877",
        "durable_state_root": str(durable),
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "ROOT", runtime)
    assert mod.hil_receiver_gateway_projection() == {
        "STEGVERSE_HIL_RECEIVER_PROXY_ENABLED": "true",
        "STEGVERSE_HIL_RECEIVER_UPSTREAM": "http://127.0.0.1:8877",
    }


def test_hil_receiver_gateway_projection_rejects_wrong_fence_or_intr_path(tmp_path, monkeypatch):
    runtime = tmp_path
    receipt = runtime / mod.HIL_RECEIVER_WORKER_RECEIPT_REL
    receipt.parent.mkdir(parents=True)
    durable = tmp_path / "hil-durable"
    durable.mkdir()
    base = {
        "schema": "stegverse.hil.sovereign-receiver-worker-receipt/v0.1",
        "task_id": mod.HIL_RECEIVER_TASK_ID,
        "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G26",
        "fencing_token": 26,
        "predecessor_claim_id": mod.HIL_RECEIVER_PREDECESSOR_CLAIM_ID,
        "predecessor_fencing_token": 24,
        "receiver_ready": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "base_url": "http://127.0.0.1:8877",
        "durable_state_root": str(durable),
    }
    receipt.write_text(json.dumps(base) + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "ROOT", runtime)
    assert mod.hil_receiver_gateway_projection()["STEGVERSE_HIL_RECEIVER_PROXY_ENABLED"] == "false"
    base["predecessor_fencing_token"] = mod.HIL_RECEIVER_PREDECESSOR_FENCE
    base["base_url"] = "http://127.0.0.1:8877/intr/materialization"
    receipt.write_text(json.dumps(base) + "\n", encoding="utf-8")
    assert mod.hil_receiver_gateway_projection()["STEGVERSE_HIL_RECEIVER_PROXY_ENABLED"] == "false"


def test_healer_hil_receiver_gateway_source_requires_merged_contract(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    path = app / "coinbase_stegdeploy_gateway.py"
    path.write_text(
        'HIL_RECEIVER_PROXY_ENABLED_ENV = "STEGVERSE_HIL_RECEIVER_PROXY_ENABLED"\n'
        'HIL_RECEIVER_UPSTREAM_ENV = "STEGVERSE_HIL_RECEIVER_UPSTREAM"\n'
        f'MINIMUM_HIL_RECEIVER_GATEWAY_COMMIT = "{mod.LLM_HIL_RECEIVER_GATEWAY_MERGE}"\n'
        'def validate_hil_receiver_gateway_readiness(): pass\n'
        'LLM_ADAPTER_HIL_RECEIVER_GATEWAY_SOURCE_STALE\n',
        encoding="utf-8",
    )
    result = mod.verify_healer_hil_receiver_gateway_source(tmp_path)
    assert result["state"] == "CURRENT"
    assert result["required_healer_merge"] == mod.HEALER_HIL_RECEIVER_GATEWAY_MERGE


def test_healer_hil_receiver_gateway_source_fails_stale_contract(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "coinbase_stegdeploy_gateway.py").write_text("# stale\n", encoding="utf-8")
    result = mod.verify_healer_hil_receiver_gateway_source(tmp_path)
    assert result["state"] == "STALE_OR_INCOMPLETE"
    assert result["missing_markers"]
