import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "control/resident-execution-request.d/governed-multilane-manifold-activation-001.json"
LINEAGE = ROOT / "control/manifold-lineage.d/governed-multilane-manifold-activation-001.json"

RECOVERY_TASK = "SHWP-FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001"
DISCOVERY_TASK = "SHWP-FORMALISM-SOURCE-DISCOVERY-001"
RECOVERY_REGISTRY = "control/worker-registry.d/formalism-tvc-repository-transport-consumers-001.json"
RECOVERY_ADAPTER = "control/process-worker-adapters.d/formalism-tvc-repository-transport-consumers-001.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_missing_source_recovery_is_reachable_from_umbrella():
    request = load(REQUEST)
    lineage = load(LINEAGE)

    assert RECOVERY_TASK in request["subordinate_task_ids"]
    assert RECOVERY_REGISTRY in request["worker_registry_refs"]
    assert RECOVERY_ADAPTER in request["process_adapter_refs"]
    assert request["execution_dispositions"][RECOVERY_TASK] == "EXECUTE_IF_SOURCE_DISCOVERY_REPORTS_MISSING_OR_INVALID_ROOT"

    node_ids = {node["task_id"] for node in lineage["nodes"]}
    assert RECOVERY_TASK in node_ids

    edges = {(edge["from"], edge["to"], edge["kind"]) for edge in lineage["edges"]}
    assert (DISCOVERY_TASK, RECOVERY_TASK, "RECOVERS_MISSING_OR_INVALID_SOURCE_THROUGH_TVC") in edges
    assert (RECOVERY_TASK, DISCOVERY_TASK, "RERUNS_AFTER_MATERIALIZATION_RECEIPT") in edges


def test_source_reading_lanes_remain_fail_closed_until_rediscovery():
    request = load(REQUEST)
    sequence = "\n".join(request["execution_sequence"])
    assert "rerun source discovery" in sequence
    assert "do not execute source-reading formalism lanes" in sequence
