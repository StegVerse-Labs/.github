import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / "control/manifold-lineage.d/governed-multilane-manifold-activation-001.json"
REQUEST = ROOT / "control/resident-execution-request.d/governed-multilane-manifold-activation-001.json"


def test_source_discovery_is_declared_before_source_reading_formalism_lanes() -> None:
    lineage = json.loads(LINEAGE.read_text())
    request = json.loads(REQUEST.read_text())

    discovery = "SHWP-FORMALISM-SOURCE-DISCOVERY-001"
    lanes = {
        "SHWP-FORMALISM-INVENTORY-001",
        "SHWP-FORMALISM-HANDOFF-NORMALIZATION-001",
        "SHWP-FORMALISM-MATHEMATICAL-CROSSWALK-001",
        "SHWP-MANIFOLD-GOVERNANCE-MAPPING-001",
    }

    node_ids = {node["task_id"] for node in lineage["nodes"]}
    assert discovery in node_ids
    assert node_ids == set(request["subordinate_task_ids"])
    assert request["execution_dispositions"][discovery] == "EXECUTE_IF_NOT_ALREADY_QUALIFYING"
    assert "control/worker-registry.d/formalism-source-discovery-001.json" in request["worker_registry_refs"]
    assert "control/process-worker-adapters.d/formalism-source-discovery-001.json" in request["process_adapter_refs"]

    depends = {(edge["from"], edge["to"]) for edge in lineage["edges"] if edge["kind"] == "DEPENDS_ON"}
    for lane in lanes:
        assert (lane, discovery) in depends

    sequence = "\n".join(request["execution_sequence"])
    assert sequence.index(discovery) < sequence.index("four prerequisite formalism evidence lanes")
