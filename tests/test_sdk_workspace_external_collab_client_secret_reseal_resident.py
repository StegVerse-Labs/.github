from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_PATH = ROOT / "control/resident-execution-request.d/consume-sdk-workspace-external-collab-client-secret-reseal.py"
REQUEST_PATH = ROOT / "control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json"


def load_consumer():
    spec = importlib.util.spec_from_file_location("sdk_workspace_reseal_consumer", CONSUMER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_request() -> dict:
    return json.loads(REQUEST_PATH.read_text())


def write_request(runtime: Path, request: dict) -> None:
    path = runtime / "control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(request) + "\n")


class SDKWorkspaceExternalCollabResealResidentTests(unittest.TestCase):
    def test_request_is_non_authorizing_and_pins_tvc_reseal_source(self):
        request = canonical_request()
        self.assertEqual(request["task_id"], "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003")
        self.assertEqual(request["selector"], "sdk_workspace_external_collab_client_secret_reseal")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["expected_tvc_reseal_script_git_blob"], "fba3f668e08dba300cd994e85b3c70872fc1f8e6")
        self.assertEqual(request["target_purpose"], "google_drive.external_collaboration.client_secret")
        self.assertEqual(request["personal_kv_source_purpose"], "google_drive.personal_kv.client_secret")
        self.assertIs(request["credential_material_allowed"], False)
        self.assertIs(request["network_source_fetch_allowed"], False)
        self.assertIs(request["request_granted_authority"], False)
        self.assertIs(request["second_machine_required"], False)

    def test_dispatcher_registers_source_refresh_carried_consumer(self):
        text = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
        expected = '("sdk_workspace_external_collab_client_secret_reseal", "control/resident-execution-request.d/consume-sdk-workspace-external-collab-client-secret-reseal.py")'
        self.assertIn(expected, text)
        refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
        self.assertIn('Path("control/resident-execution-request.d")', refresh)

    def test_hosted_environment_fails_before_execution(self):
        module = load_consumer()
        with self.assertRaisesRegex(RuntimeError, "hosted environment may not consume"):
            module._clean_env({"PATH": "/usr/bin", "GITHUB_ACTIONS": "true"})

    def test_existing_target_is_observed_not_overwritten(self):
        module = load_consumer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            tvc = root / "tvc"
            tvc.mkdir()
            request = canonical_request()
            source = root / "source.json"
            source.write_text("{}")
            target = root / "target.json"
            target.write_text('{"existing":true}\n')
            activation = root / "activation.json"
            activation.write_text("{}")
            private = root / "private.pem"
            private.write_text("private-placeholder")
            request.update({
                "source_custody_receipt": str(source),
                "target_custody_receipt": str(target),
                "resident_seal_activation_receipt": str(activation),
                "resident_private_key": str(private),
            })
            write_request(runtime, request)
            with patch.object(module, "_locate_tvc_root", return_value=(tvc, "TEST_TVC_ROOT")):
                result = module.consume(runtime, environ={"PATH": "/usr/bin", "HOME": str(root)})
            self.assertEqual(result["state"], "TARGET_ALREADY_PRESENT")
            self.assertEqual(result["reason"], "VALIDATE_EXISTING_TARGET_DO_NOT_OVERWRITE")
            self.assertEqual(target.read_text(), '{"existing":true}\n')

    def test_root_resident_execution_accepts_only_secret_free_reseal_result(self):
        module = load_consumer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            tvc = root / "tvc"
            script = tvc / "scripts/reseal_google_drive_external_collaboration_client_secret.py"
            script.parent.mkdir(parents=True)
            script.write_text("# pinned by mocked locator\n")
            source = root / "source.json"
            source.write_text("{}")
            target = root / "target.json"
            activation = root / "activation.json"
            activation.write_text("{}")
            private = root / "private.pem"
            private.write_text("private-placeholder")
            request = canonical_request()
            request.update({
                "source_custody_receipt": str(source),
                "target_custody_receipt": str(target),
                "resident_seal_activation_receipt": str(activation),
                "resident_private_key": str(private),
            })
            write_request(runtime, request)

            secret_free = {
                "state": "PURPOSE_SPECIFIC_CIPHERTEXT_CUSTODY_MATERIALIZED",
                "target_purpose": "google_drive.external_collaboration.client_secret",
                "credential_authority": "TV/TVC",
                "plaintext_returned": False,
                "plaintext_persisted": False,
                "plaintext_logged": False,
                "plaintext_hashed": False,
                "provider_operation_authority": False,
            }

            def runner(command, **kwargs):
                target.write_text('{"schema":"stegverse.tvc.skap_resident_sealed_custody_receipt/v1"}\n')
                return SimpleNamespace(returncode=0, stdout=json.dumps(secret_free) + "\n", stderr="")

            with patch.object(module, "_locate_tvc_root", return_value=(tvc, "TEST_TVC_ROOT")), patch.object(module.os, "geteuid", return_value=0):
                result = module.consume(runtime, environ={"PATH": "/usr/bin", "HOME": str(root)}, runner=runner)
            self.assertEqual(result["state"], "COMPLETED")
            self.assertIs(result["credential_material_present"], False)
            self.assertIs(result["provider_contact_performed"], False)
            self.assertIs(result["secret_free_reseal_result"]["plaintext_returned"], False)
            self.assertIs(result["target_custody_receipt_present_after"], True)
            self.assertIs(result["stdout_secret_material_retained"], False)
            self.assertIs(result["stderr_secret_material_retained"], False)


if __name__ == "__main__":
    unittest.main()
