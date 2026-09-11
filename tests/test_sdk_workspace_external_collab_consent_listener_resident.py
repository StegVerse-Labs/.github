from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control/resident-execution-request.d/consume-sdk-workspace-external-collab-consent-listener.py"
REQUEST = ROOT / "control/resident-execution-request.d/sdk-workspace-external-collab-consent-listener-001.json"

spec = importlib.util.spec_from_file_location("consent_listener_consumer", CONSUMER)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class FakeHealthResponse:
    status = 200
    def __init__(self, body):
        self._body = json.dumps(body).encode()
    def read(self, _limit):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False


def healthy():
    return {
        "state": "HEALTHY",
        "client_secret_purpose": "google_drive.external_collaboration.client_secret",
        "credential_material_present": False,
        "provider_contact_performed": False,
        "runtime_activation_claimed": False,
    }


class ConsentListenerResidentTests(unittest.TestCase):
    def _runtime(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        target = root / mod.REQUEST_REL
        target.parent.mkdir(parents=True)
        target.write_text(REQUEST.read_text(), encoding="utf-8")
        return tmp, root

    def test_request_is_exact_non_authorizing_machine_owned_control(self):
        request = json.loads(REQUEST.read_text())
        self.assertEqual(request["selector"], "sdk_workspace_external_collab_consent_listener")
        self.assertEqual(request["task_id"], "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003")
        self.assertEqual(request["expected_tvc_installer_git_blob"], "dae00dbec1a79d611a3184e185e04e6f29110348")
        self.assertEqual(request["loopback_health_url"], "http://127.0.0.1:8786/tvc/external-collaboration/google-drive/consent/health")
        self.assertFalse(request["credential_material_allowed"])
        self.assertFalse(request["public_https_binding_allowed"])
        self.assertFalse(request["google_owner_consent_allowed"])
        self.assertFalse(request["provider_contact_allowed"])
        self.assertFalse(request["gateway_authority"])
        self.assertFalse(request["second_machine_required"])

    def test_dispatcher_registration_and_nonsecret_env_are_exact(self):
        text = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
        self.assertIn('(\"sdk_workspace_external_collab_consent_listener\", \"control/resident-execution-request.d/consume-sdk-workspace-external-collab-consent-listener.py\")', text)
        for name in mod.NONSECRET_REQUIRED:
            self.assertIn(f'\"{name}\"', text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", text)

    def test_already_healthy_returns_terminal_secret_free_observation_without_installer(self):
        tmp, runtime = self._runtime()
        self.addCleanup(tmp.cleanup)
        result = mod.consume(runtime, environ={"PATH": "/usr/bin"}, opener=lambda *_a, **_k: FakeHealthResponse(healthy()))
        self.assertEqual(result["state"], "SERVICE_ALREADY_HEALTHY")
        self.assertTrue(result["loopback_health_verified"])
        self.assertFalse(result["installer_invoked"])
        self.assertFalse(result["provider_contact_performed"])
        self.assertFalse(result["public_https_binding_performed"])
        self.assertFalse(result["google_owner_consent_performed"])

    def test_missing_nonsecret_config_blocks_without_installer(self):
        tmp, runtime = self._runtime()
        self.addCleanup(tmp.cleanup)
        result = mod.consume(runtime, environ={"PATH": "/usr/bin"}, opener=lambda *_a, **_k: (_ for _ in ()).throw(OSError("closed")))
        self.assertEqual(result["state"], "BLOCKED")
        self.assertTrue(result["reason"].startswith("REQUIRED_NONSECRET_CONFIGURATION_ABSENT:"))
        self.assertFalse(result["installer_invoked"])

    def test_hosted_environment_fails_closed(self):
        tmp, runtime = self._runtime()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            mod.consume(runtime, environ={"PATH": "/usr/bin", "GITHUB_ACTIONS": "true"})

    def test_install_completion_requires_exact_health_contract(self):
        tmp, runtime = self._runtime()
        self.addCleanup(tmp.cleanup)
        stegfin = runtime / "stegfin"
        stegfin.mkdir()
        env = {
            "PATH": "/usr/bin",
            "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID": "example.apps.googleusercontent.com",
            "STEGVERSE_OWNER_BINDING_DIGEST": "sha256:" + "a" * 64,
            "STEGVERSE_STEGFIN_SOURCE_ROOT": str(stegfin),
        }
        responses = iter([None, healthy()])
        def fake_health(_url, *, opener=None):
            return next(responses)
        completed = SimpleNamespace(returncode=0, stdout="TVC_EXTERNAL_COLLAB_GOOGLE_DRIVE_CONSENT_SERVICE_INSTALLED\n", stderr="")
        with (
            patch.object(mod, "_health", side_effect=fake_health),
            patch.object(mod, "_locate_tvc_root", return_value=(runtime, "synthetic:INSTALLER_BLOB=dae00dbec1a79d611a3184e185e04e6f29110348")),
            patch.object(mod.os, "geteuid", return_value=0),
        ):
            result = mod.consume(runtime, environ=env, runner=lambda *_a, **_k: completed)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertTrue(result["loopback_health_verified"])
        self.assertTrue(result["installer_invoked"])
        self.assertFalse(result["credential_material_present"])
        self.assertFalse(result["gateway_authority"])

    def test_wrong_health_purpose_never_counts_as_ready(self):
        bad = healthy()
        bad["client_secret_purpose"] = "google_drive.personal_kv.client_secret"
        request = json.loads(REQUEST.read_text())
        self.assertFalse(mod._health_valid(bad, request))


if __name__ == "__main__":
    unittest.main()
