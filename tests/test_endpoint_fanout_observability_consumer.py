import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control" / "runtime-observability-consumers" / "endpoint-fanout-sovereign-runtime-001.json"
CONTRACT = ROOT / "management" / "HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json"


def test_endpoint_fanout_shared_observability_binding_is_non_authorizing():
    consumer = json.loads(CONSUMER.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert consumer["shared_contract"] == "management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json"
    assert consumer["canonical_projector"] == contract["canonical_projector"]
    assert consumer["resident_projection_module"] == contract["canonical_module"]
    assert consumer["first_unresolved_shared_runtime_predicate"] == "resident_process_alive_supervised"
    assert consumer["predicate_map"]["authentic_device_kv_parent_observed"]["observed"] is False
    assert consumer["predicate_map"]["runtime_execution_completed"]["observed"] is False
    assert consumer["predicate_map"]["replay_reconstruction_proven"]["observed"] is False
    assert consumer["heartbeat_grants_authority"] is False
    assert consumer["hb_derived_signal_grants_authority"] is False
    assert consumer["workercoordinator_retains_claim_fence_authority"] is True
    assert consumer["credential_authority"] == "TV/TVC"
    assert consumer["github_token_runtime_authority"] == "NONE"
    assert consumer["authority_effect"] == "NONE_OBSERVATION_ONLY"
