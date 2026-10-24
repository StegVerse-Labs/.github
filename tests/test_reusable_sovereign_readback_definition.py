"""Read-only reusable sovereign receipt definition must reuse existing native owners."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARD = ROOT / "source-bundles/reusable-task-registry.d/RT-AUTHENTICATED-SOVEREIGN-READBACK-001.json"

def test_sovereign_readback_reusable_identity_is_non_authorizing():
    row = json.loads(SHARD.read_text())
    assert row["reusable_task_id"] == "RT-AUTHENTICATED-SOVEREIGN-READBACK-001"
    assert row["runner_templates"] == []
    assert row["authority_effect"] == "NONE_READBACK_ONLY"
    assert "RECORDING_PROOF_NOT_TREATED_AS_GOVERNANCE_AUTHORIZATION" in row["completion_predicates"]
    assert "resident-runtime/organization_ledger_readback.py" in row["existing_implementation_refs"]
    assert "workers/canonical_state_transition_custody.py" in row["existing_implementation_refs"]

def test_sovereign_readback_reusable_identity_is_not_duplicated():
    aggregate = json.loads((ROOT / "data/reusable-task-registry.json").read_text())
    rows = aggregate["tasks"]
    shards = ROOT / "source-bundles/reusable-task-registry.d"
    for path in shards.glob("*.json"):
        rows.append(json.loads(path.read_text()))
    identities = [r["reusable_task_id"] for r in rows]
    assert identities.count("RT-AUTHENTICATED-SOVEREIGN-READBACK-001") == 1
    assert len(identities) == len(set(identities))
