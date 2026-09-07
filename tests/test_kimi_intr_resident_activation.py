import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "kimi_intr_resident_activation_worker_v2.py"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "kimi-intr-resident-activation-001.json"
HANDOFF = ROOT / "docs" / "KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md"


def load_worker():
    spec = importlib.util.spec_from_file_location("kimi_intr_resident_activation_worker_v2", WORKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_adapter_uses_exact_wire_v2_worker_only():
    value = json.loads(ADAPTER.read_text(encoding="utf-8"))
    adapters = value["adapters"]
    assert len(adapters) == 1
    adapter = adapters[0]
    assert adapter["enabled"] is True
    assert adapter["adapter_ref"] == "process:kimi-intr-resident-activation-v2"
    assert adapter["command"] == ["python", "workers/kimi_intr_resident_activation_worker_v2.py"]
    assert "STEGVERSE_VAULT_BROKER_SOCKET" in adapter["env_allowlist"]
    assert "STEGVERSE_MASTER_RECORDS_PROVIDER_USAGE_SOCKET" in adapter["env_allowlist"]
    for secret in ("KIMI_API_KEY", "MOONSHOT_API_KEY", "MASTER_RECORDS_AUTH_TOKEN", "MASTER_RECORDS_RECEIPT_KEY", "GITHUB_TOKEN"):
        assert secret not in adapter["env_allowlist"]


def test_worker_imports_exact_tvc_provider_wire_not_legacy_wire():
    source = WORKER.read_text(encoding="utf-8")
    assert "canonical_kimi_tvc_provider_wire_bytes" in source
    assert "canonical_kimi_tvc_provider_request_hash" in source
    assert "from llm_adapter.kimi_intr_transport import kimi_wire_bytes" not in source
    assert "MAX_OUTPUT_TOKENS = 4096" in source
    assert 'RESPONSE_FORMAT = "json"' in source


def test_worker_requires_exact_hash_at_ingress_tvc_and_llm_adapter_boundaries():
    source = WORKER.read_text(encoding="utf-8")
    for guard in (
        "UNIVERSAL_INTR_INGRESS_PAYLOAD_HASH_NOT_EXACT_TVC_WIRE",
        "TVC_BROKER_OPERATION_NOT_BOUND_TO_ADMITTED_EXACT_PROVIDER_WIRE",
        "LLM_ADAPTER_ADMISSION_HASH_NOT_EXACT_TVC_PROVIDER_WIRE",
        "LLM_ADAPTER_EXECUTION_ENVELOPE_DRIFT",
        "UNIVERSAL_INTR_EGRESS_PAYLOAD_HASH_NOT_EXACT_RESPONSE_BYTES",
        "TERMINAL_SAME_EXECUTION_PREDICATES_NOT_ALL_PROVEN",
    ):
        assert guard in source


def test_worker_forbids_provider_master_records_and_github_secret_environment():
    module = load_worker()
    forbidden = set(module.FORBIDDEN_SECRET_ENV)
    assert {"KIMI_API_KEY", "MOONSHOT_API_KEY", "MASTER_RECORDS_AUTH_TOKEN", "MASTER_RECORDS_RECEIPT_KEY", "GITHUB_TOKEN"}.issubset(forbidden)


def test_blocked_receipt_claims_no_activation_or_secret_authority(tmp_path, monkeypatch):
    module = load_worker()
    monkeypatch.setattr(module, "RECEIPT", tmp_path / "receipt.json")
    response = module.blocked("TEST_BLOCK", epoch=32)
    assert response["state"] == "BLOCKED"
    saved = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    result = saved["result"]
    assert result["credential_authority"] == "TV/TVC"
    assert result["provider_credential_material_present"] is False
    assert result["master_records_credential_material_present"] is False
    assert result["heartbeat_grants_execution_authority"] is False
    assert result["transport_grants_execution_authority"] is False
    assert result["governance_grants_execution_authority"] is False
    assert result["execution_authorized_by_request"] is False
    assert result["publication_authorized"] is False


def test_handoff_keeps_runtime_proof_separate_from_source_completion():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "AUTHENTIC_RUNTIME_ROUND_TRIP_NOT_YET_OBSERVED" in text
    assert "No source merge, CI result" in text
