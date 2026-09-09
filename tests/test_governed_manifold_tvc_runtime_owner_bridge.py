from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "consume_governed_multilane_manifold_activation_request.py"
CONTROL = ROOT / "control" / "resident-execution-request.d" / "consume-governed-multilane-manifold-activation.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GovernedManifoldTVCRuntimeOwnerBridgeTests(unittest.TestCase):
    def test_tvc_runtime_owner_bridge_is_present_in_both_consumers(self) -> None:
        for path in (SCRIPT, CONTROL):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertIn("execute_existing_tvc_runtime_owner_path", source)
                self.assertIn("tvc.primary_runtime_binder.preflight", source)
                self.assertIn("tvc.primary_runtime_binder.activate", source)
                self.assertIn("observe_tvc_runtime_boundary.py", source)
                self.assertIn("TVC-PROVIDER-OPERATION-BROKER-003", source)
                self.assertIn("TVC-CAPABILITY-RUNTIME-002", source)

    def test_bridge_fails_closed_without_tvtvc_activation_declaration(self) -> None:
        module = _load(SCRIPT)
        env = dict(os.environ)
        for name in module.HOSTED_ENV:
            env.pop(name, None)
        env.pop("STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY", None)
        env.pop("STEGVERSE_TVC_ROOT", None)
        env.pop("STEGVERSE_REPO_ROOTS_JSON", None)
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, env, clear=True):
            result = module.execute_existing_tvc_runtime_owner_path(Path(temp))
        self.assertEqual(result["state"], "BLOCKED_TV_TVC_RUNTIME_ACTIVATION_DECLARATION_REQUIRED")
        self.assertEqual(result["authority_effect"], "NONE_FAIL_CLOSED")

    def test_bridge_rejects_hosted_execution_before_owner_dispatch(self) -> None:
        module = _load(SCRIPT)
        env = dict(os.environ)
        for name in module.HOSTED_ENV:
            env.pop(name, None)
        env["GITHUB_ACTIONS"] = "true"
        env["STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY"] = "TV/TVC"
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, env, clear=True):
            result = module.execute_existing_tvc_runtime_owner_path(Path(temp))
        self.assertEqual(result["state"], "BLOCKED_HOSTED_SURFACE_REJECTED")
        self.assertIn("GITHUB_ACTIONS", result["hosted"])


if __name__ == "__main__":
    unittest.main()
