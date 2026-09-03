import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001.json"
CONTRACT = ROOT / "management" / "HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json"


def test_sv001_uses_current_canonical_runtime_presence_projection():
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    binding = handoff["observability_binding"]

    assert binding["contract_ref"] == "management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json"
    assert binding["canonical_module"] == contract["canonical_module"]
    assert binding["canonical_projector"] == contract["canonical_projector"]
    assert binding["canonical_validation"] == contract["canonical_validation"]
    assert binding["heartbeat_or_projection_grants_authority"] is False
    assert binding["authority_effect"] == "NONE_OBSERVATION_ONLY"

    superseded = set(contract.get("superseded_local_experiment") or [])
    assert binding["canonical_module"] not in superseded
    assert binding["canonical_projector"] not in superseded
