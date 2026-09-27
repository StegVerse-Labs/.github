"""Regression: the existing SHWP task has exactly one canonical Registry projection."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_existing_shwp_task_is_projected_once_with_original_cosv():
    registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
    shard = json.loads((ROOT / "data/canonical-task-records/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json").read_text())
    matches = [t for t in registry["tasks"] if t["task_id"] == shard["task_id"]]
    assert len(matches) == 1
    assert matches[0] == shard
    assert shard["cosv_tracking"]["vector"] == "50000000100000"
    assert shard["authority_model"]["source_projection_grants_execution_authority"] is False
    assert shard["completion"]["validated"] is False


def test_external_ai_acceptance_requires_original_envelope_reconstruction():
    handoff = (ROOT / "docs/EPHEMERAL_STEGBROWSER_EXTERNAL_AI_ACTIVATION_MIRROR_HANDOFF.md").read_text()
    assert "original retained canonical receipt" in handoff
    assert "A second invocation is a **new execution**" in handoff
    assert "RECEIPT_SHA256_EQUALS_RECONSTRUCTED_RECEIPT_SHA256" in handoff
