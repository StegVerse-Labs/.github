from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_tvc_runtime_boundary_reusable.py"
PRIMARY_ID = "RT-TVC-PRIMARY-RUNTIME-BINDING-001"
PREDICATES = [
    "CURRENT_CANONICAL_TVC_SOURCE_VERIFIED",
    "EXISTING_TV_TVC_VAULT_BROKER_SOCKET_VERIFIED",
    "EXISTING_PRIMARY_RUNTIME_BOUND",
    "APPROVED_SERVICE_DELIVERY_REUSED",
    "NO_DUPLICATE_RUNTIME_OR_HOST_CREATED",
]


def load_subject():
    spec = importlib.util.spec_from_file_location("tvc_runtime_reusable", WRAPPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_primary_binding_uses_bounded_same_service_delivery_and_emits_result(tmp_path, monkeypatch):
    subject = load_subject()
    tvc = tmp_path / "TVC"
    (tvc / "tools").mkdir(parents=True)
    (tvc / "scripts").mkdir(parents=True)
    for rel in (
        "tools/task_dispatcher.py",
        "scripts/observe_tvc_runtime_boundary.py",
        "scripts/install_tvc_primary_runtime_service.py",
    ):
        (tvc / rel).write_text("# fixture\n", encoding="utf-8")

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"manifest_hash": "sha256:test"}), encoding="utf-8")
    result = tmp_path / "runner-result.json"
    monkeypatch.setenv("STEGVERSE_REPO_ROOTS_JSON", json.dumps({"StegVerse-Labs/TVC": str(tvc)}))
    monkeypatch.setenv("STEGVERSE_REUSABLE_TASK_ID", PRIMARY_ID)
    monkeypatch.setenv("STEGVERSE_REUSABLE_TASK_INVOCATION_ID", "sv002-test-invocation")
    monkeypatch.setenv("STEGVERSE_REUSABLE_TASK_MANIFEST", str(manifest))
    monkeypatch.setenv("STEGVERSE_REUSABLE_TASK_RESULT_PATH", str(result))
    monkeypatch.setenv("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", json.dumps(PREDICATES))
    monkeypatch.setenv("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "{}")

    calls: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: Path, timeout: int = 300):
        calls.append(list(command))
        if "task_dispatcher.py" in command[1]:
            report = {
                "status": "ok",
                "result": {
                    "state": "READY_FOR_TV_TVC_PRIMARY_RUNTIME_SERVE",
                    "task_id": "TVC-PRIMARY-RUNTIME-BINDER-005",
                    "runtime_id": "stegtvc-primary-runtime",
                    "local_binding_proof": {"state": "PRIMARY_RUNTIME_LOCAL_BINDING_PROOF_VERIFIED"},
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                },
            }
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(report), stderr="")
        if "install_tvc_primary_runtime_service.py" in command[1]:
            return subprocess.CompletedProcess(command, 0, stdout="/etc/systemd/system/stegtvc-primary-runtime.service\n", stderr="")
        if "observe_tvc_runtime_boundary.py" in command[1]:
            output = Path(command[command.index("--output") + 1])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({
                "state": "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "provider_secret_used": False,
                "provider_secret_exported": False,
            }), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"state": "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND"}), stderr="")
        raise AssertionError(command)

    monkeypatch.setattr(subject, "run", fake_run)
    assert subject.main() == 0

    flattened = [" ".join(command) for command in calls]
    assert not any("tvc.primary_runtime_binder.activate" in command for command in flattened)
    delivery = [command for command in calls if "install_tvc_primary_runtime_service.py" in command[1]]
    assert len(delivery) == 1
    assert "--activate" in delivery[0]

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["schema"] == "stegverse.reusable-task-runner-result/v1"
    assert payload["reusable_task_id"] == PRIMARY_ID
    assert payload["completion_predicates_satisfied"] == PREDICATES
    assert payload["runtime_observed"] is True
    assert payload["completion_evidence_observed"] is True
    assert payload["evidence"]["same_service_restarted"] is True
    assert payload["evidence"]["duplicate_runtime_or_host_created"] is False
    assert payload["authority_effect"] == "NONE"
