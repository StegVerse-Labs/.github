from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def test_request_is_non_authorizing_and_pins_tvc_reseal_source():
    request = canonical_request()
    assert request["task_id"] == "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003"
    assert request["selector"] == "sdk_workspace_external_collab_client_secret_reseal"
    assert request["credential_authority"] == "TV/TVC"
    assert request["expected_tvc_reseal_script_git_blob"] == "fba3f668e08dba300cd994e85b3c70872fc1f8e6"
    assert request["target_purpose"] == "google_drive.external_collaboration.client_secret"
    assert request["personal_kv_source_purpose"] == "google_drive.personal_kv.client_secret"
    assert request["credential_material_allowed"] is False
    assert request["network_source_fetch_allowed"] is False
    assert request["request_granted_authority"] is False
    assert request["second_machine_required"] is False


def test_dispatcher_registers_source_refresh_carried_consumer():
    text = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    expected = '("sdk_workspace_external_collab_client_secret_reseal", "control/resident-execution-request.d/consume-sdk-workspace-external-collab-client-secret-reseal.py")'
    assert expected in text
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    assert 'Path("control/resident-execution-request.d")' in refresh


def test_hosted_environment_fails_before_execution():
    module = load_consumer()
    with pytest.raises(RuntimeError, match="hosted environment may not consume"):
        module._clean_env({"PATH": "/usr/bin", "GITHUB_ACTIONS": "true"})


def test_existing_target_is_observed_not_overwritten(tmp_path: Path, monkeypatch):
    module = load_consumer()
    runtime = tmp_path / "runtime"
    tvc = tmp_path / "tvc"
    tvc.mkdir()
    request = canonical_request()
    source = tmp_path / "source.json"; source.write_text("{}")
    target = tmp_path / "target.json"; target.write_text('{"existing":true}\n')
    activation = tmp_path / "activation.json"; activation.write_text("{}")
    private = tmp_path / "private.pem"; private.write_text("private-placeholder")
    request.update({
        "source_custody_receipt": str(source),
        "target_custody_receipt": str(target),
        "resident_seal_activation_receipt": str(activation),
        "resident_private_key": str(private),
    })
    write_request(runtime, request)
    monkeypatch.setattr(module, "_locate_tvc_root", lambda request, environ: (tvc, "TEST_TVC_ROOT"))
    result = module.consume(runtime, environ={"PATH": "/usr/bin", "HOME": str(tmp_path)})
    assert result["state"] == "TARGET_ALREADY_PRESENT"
    assert result["reason"] == "VALIDATE_EXISTING_TARGET_DO_NOT_OVERWRITE"
    assert target.read_text() == '{"existing":true}\n'


def test_root_resident_execution_accepts_only_secret_free_reseal_result(tmp_path: Path, monkeypatch):
    module = load_consumer()
    runtime = tmp_path / "runtime"
    tvc = tmp_path / "tvc"
    script = tvc / "scripts/reseal_google_drive_external_collaboration_client_secret.py"
    script.parent.mkdir(parents=True)
    script.write_text("# pinned by mocked locator\n")
    source = tmp_path / "source.json"; source.write_text("{}")
    target = tmp_path / "target.json"
    activation = tmp_path / "activation.json"; activation.write_text("{}")
    private = tmp_path / "private.pem"; private.write_text("private-placeholder")
    request = canonical_request()
    request.update({
        "source_custody_receipt": str(source),
        "target_custody_receipt": str(target),
        "resident_seal_activation_receipt": str(activation),
        "resident_private_key": str(private),
    })
    write_request(runtime, request)
    monkeypatch.setattr(module, "_locate_tvc_root", lambda request, environ: (tvc, "TEST_TVC_ROOT"))
    monkeypatch.setattr(module.os, "geteuid", lambda: 0)

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

    result = module.consume(runtime, environ={"PATH": "/usr/bin", "HOME": str(tmp_path)}, runner=runner)
    assert result["state"] == "COMPLETED"
    assert result["credential_material_present"] is False
    assert result["provider_contact_performed"] is False
    assert result["secret_free_reseal_result"]["plaintext_returned"] is False
    assert result["target_custody_receipt_present_after"] is True
    assert result["stdout_secret_material_retained"] is False
    assert result["stderr_secret_material_retained"] is False
