import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001"
VECTOR = "71000000100110"


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_worker_registry_binds_existing_goal_task_and_cosv():
    registry = load("control/worker-registry.d/shared-docs-provider-content-integrity-001.json")
    assert registry["schema"] == "stegverse.worker-registry-fragment/v0.1"
    assert registry["authority_effect"] == "NONE_REGISTRATION_ONLY"
    assert registry["credential_authority"] == "TV/TVC"
    assert registry["provider_mutation_allowed"] is False
    assert len(registry["tasks"]) == 1
    task = registry["tasks"][0]
    assert task["task_id"] == TASK_ID
    assert task["state"] == "HANDOFF_READY"
    assert task["machine_readable_state"]["cosv"]["vector"] == VECTOR
    assert task["source_state_vector_ref"] == "control/task-vectors/SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001.json"


def test_process_adapter_reuses_existing_consumer_without_new_authority_plane():
    adapter = load("control/process-worker-adapters.d/shared-docs-provider-content-integrity-001.json")["adapters"][0]
    assert adapter["adapter_ref"] == "process:shared-docs-provider-content-integrity-v1"
    assert adapter["type"] == "process_json_v0.1"
    assert adapter["command"] == ["python", "workers/shared_docs_provider_content_integrity_worker.py"]
    assert "STEGVERSE_TVC_ROOT" in adapter["env_allowlist"]
    assert "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET" in adapter["env_allowlist"]
    notes = " ".join(adapter["notes"])
    assert "TV/TVC remains credential and provider-operation authority" in notes
    assert "No static resident dispatcher" in notes


def test_handoff_preserves_authority_and_fenced_scope():
    handoff = load("handoffs/SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001.json")
    assert handoff["task"]["task_id"] == TASK_ID
    assert handoff["machine_readable_state"]["cosv"]["vector"] == VECTOR
    authority = handoff["authority"]
    assert authority["credential_authority"] == "TV/TVC"
    assert authority["provider_operation_authority"] == "TV/TVC"
    assert authority["transition_authority"] == "Interlock/InTr"
    assert authority["user_verification_authority"] == "KV/SKAP Vault"
    assert authority["execution_authority_created"] is False
    assert authority["provider_mutation_allowed"] is False
    assert handoff["execution"]["allowed_paths"] == ["receipts/sovereign-host/shared-docs-provider-content-integrity.latest.json"]


def test_existing_exact_provider_request_remains_read_only():
    request = load("control/resident-execution-request.d/shared-docs-provider-content-integrity-001.json")
    assert request["task_id"] == TASK_ID
    assert request["selector"] == "shared_docs_provider_content_integrity"
    provider = request["provider_request"]
    assert provider["content_profile"] == "google-drive.downloaded-bytes.v1"
    assert provider["read_only"] is True
    assert provider["provider_mutation_allowed"] is False


def test_worker_wrapper_is_translation_only_and_emits_worker_protocol():
    source = (ROOT / "workers/shared_docs_provider_content_integrity_worker.py").read_text(encoding="utf-8")
    assert 'TASK_ID = "SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001"' in source
    assert '"schema": "stegverse.worker-response/v0.1"' in source
    assert '"state": "COMPLETED" if observed else "ACTIVE"' in source
    assert 'module.consume(root, root, environ=os.environ)' in source
    assert "provider_mutation_performed" in source
    assert "credential_authority" in source
