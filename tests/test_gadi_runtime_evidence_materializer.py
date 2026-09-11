from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
MAT_PATH = ROOT / "scripts" / "materialize_gadi_resident_runtime_bundle.py"
DISPATCH_PATH = ROOT / "scripts" / "dispatch_gadi_resident_execution.py"

mspec = importlib.util.spec_from_file_location("gadi_materializer", MAT_PATH)
materializer = importlib.util.module_from_spec(mspec)
assert mspec.loader is not None
mspec.loader.exec_module(materializer)

dspec = importlib.util.spec_from_file_location("gadi_dispatch", DISPATCH_PATH)
dispatcher = importlib.util.module_from_spec(dspec)
assert dspec.loader is not None
dspec.loader.exec_module(dispatcher)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def populate_sources(root: Path) -> None:
    base = root / materializer.SOURCE_DIR
    write_json(base / "stegos-command.json", {
        "schema": "stegos.gadi-native-defensive-command.v1",
        "task_id": materializer.PARENT_TASK_ID,
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_admission_observed": True,
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:1",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "authorization_evidence_ref": "tvtvc:capability:1",
        "credential_authority": "TV/TVC",
    })
    write_json(base / "intr-admission.json", {
        "schema": "stegos.defensive_intervention_request.v1",
        "task_id": materializer.PARENT_TASK_ID,
        "admission": {
            "state": "ADMITTED",
            "intr_decision_ref": "intr:decision:1",
        },
    })
    write_json(base / "worker-claim.json", {
        "schema": "stegverse.worker-registry-fragment/v0.1",
        "tasks": [{
            "task_id": materializer.TASK_ID,
            "goal_id": materializer.PARENT_TASK_ID,
            "state": "IN_PROGRESS",
            "claim_id": "wc:claim:1",
            "worker_id": "gadi-resident-execution-worker",
            "worker_instance_id": "gadi-worker-instance-1",
            "assignment_timer": {"fencing_token": 17},
        }],
    })
    write_json(base / "actuator-observation.json", {
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "execution_subject": "stegverse:gadi:test-subject",
        "runtime_binding_ref": "runtime:binding:1",
        "intr_decision_ref": "intr:decision:1",
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
    })


def materialized_tools(root: Path) -> None:
    for rel in (dispatcher.RESOLVER, dispatcher.MATERIALIZER, dispatcher.PREFLIGHT, dispatcher.CONSUMER):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# stub\n", encoding="utf-8")


def resolver_success():
    return SimpleNamespace(returncode=0, stdout='{"state":"SOURCE_RESOLUTION_COMPLETE","blockers":[]}\n')


def test_materializer_fails_closed_when_sources_missing(tmp_path):
    result = materializer.materialize(tmp_path)
    assert result["state"] == "MATERIALIZATION_BLOCKED_FAIL_CLOSED"
    assert result["ready"] is False
    assert "COMMAND_SOURCE_MISSING" in result["blockers"]
    assert not (tmp_path / materializer.COMMAND_OUT).exists()


def test_materializer_projects_authentic_workercoordinator_claim_and_canonical_intr(tmp_path):
    populate_sources(tmp_path)
    result = materializer.materialize(tmp_path)
    assert result["state"] == "MATERIALIZED_READY_FOR_PREFLIGHT"
    assert result["ready"] is True
    assert result["blockers"] == []
    assert result["intr_admission_shape"] == "NESTED_CANONICAL"
    assert result["intr_runtime_binding_required"] is False
    assert result["worker_claim_shape"] == "WORKERCOORDINATOR_REGISTRY"
    assert result["worker_claim_owns_runtime_binding"] is False
    assert result["worker_claim_owns_gadi_target_binding"] is False
    context = json.loads((tmp_path / materializer.CONTEXT_OUT).read_text())
    assert context["worker_claim_ref"] == "wc:claim:1"
    assert context["fence_ref"] == "17"
    assert context["runtime_binding_ref"] == "runtime:binding:1"
    assert context["control_surface"] == "safe-state-control"
    assert context["target_class"] == "CONTROLLED_SIMULATION"
    assert context["execution_subject"] == "stegverse:gadi:test-subject"
    assert context["worker_id"] == "gadi-resident-execution-worker"
    assert context["worker_instance_id"] == "gadi-worker-instance-1"
    assert context["source_intr_admission_sha256"] == result["source_sha256"]["intr"]
    assert result["authority_minted"] is False


def test_materializer_accepts_legacy_top_level_intr_and_bridge_claim_projection(tmp_path):
    populate_sources(tmp_path)
    intr_path = tmp_path / materializer.INTR_SOURCE
    write_json(intr_path, {"state": "ADMITTED", "intr_decision_ref": "intr:decision:1"})
    claim_path = tmp_path / materializer.CLAIM_SOURCE
    write_json(claim_path, {
        "task_id": materializer.TASK_ID,
        "parent_task_id": materializer.PARENT_TASK_ID,
        "state": "CLAIMED",
        "worker_claim_ref": "wc:claim:legacy",
        "fence_ref": "wc:fence:legacy",
    })
    result = materializer.materialize(tmp_path)
    assert result["ready"] is True
    assert result["intr_admission_shape"] == "TOP_LEVEL_COMPATIBILITY"
    assert result["worker_claim_shape"] == "BRIDGE_COMPATIBILITY"


def test_materializer_rejects_intr_decision_mismatch(tmp_path):
    populate_sources(tmp_path)
    intr_path = tmp_path / materializer.INTR_SOURCE
    intr = json.loads(intr_path.read_text())
    intr["admission"]["intr_decision_ref"] = "intr:decision:other"
    write_json(intr_path, intr)
    result = materializer.materialize(tmp_path)
    assert result["ready"] is False
    assert "INTR_DECISION_REF_MISMATCH" in result["blockers"]


def test_materializer_rejects_missing_workercoordinator_fence(tmp_path):
    populate_sources(tmp_path)
    claim_path = tmp_path / materializer.CLAIM_SOURCE
    claim = json.loads(claim_path.read_text())
    claim["tasks"][0]["assignment_timer"] = {}
    write_json(claim_path, claim)
    result = materializer.materialize(tmp_path)
    assert result["ready"] is False
    assert "FENCE_REF_MISSING" in result["blockers"]


def test_materializer_rejects_command_actuator_runtime_binding_mismatch(tmp_path):
    populate_sources(tmp_path)
    actuator_path = tmp_path / materializer.ACTUATOR_SOURCE
    actuator = json.loads(actuator_path.read_text())
    actuator["runtime_binding_ref"] = "runtime:binding:other"
    write_json(actuator_path, actuator)
    result = materializer.materialize(tmp_path)
    assert result["ready"] is False
    assert "ACTUATOR_RUNTIME_BINDING_MISMATCH" in result["blockers"]


def test_materializer_rejects_command_actuator_target_mismatch(tmp_path):
    populate_sources(tmp_path)
    actuator_path = tmp_path / materializer.ACTUATOR_SOURCE
    actuator = json.loads(actuator_path.read_text())
    actuator["control_surface"] = "other-surface"
    write_json(actuator_path, actuator)
    result = materializer.materialize(tmp_path)
    assert result["ready"] is False
    assert "COMMAND_ACTUATOR_CONTROL_SURFACE_MISMATCH" in result["blockers"]


def test_dispatch_stops_before_materializer_when_source_resolution_blocks(tmp_path):
    materialized_tools(tmp_path)
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=2, stdout='{"state":"SOURCE_RESOLUTION_BLOCKED_FAIL_CLOSED","blockers":["NETWORK_SOURCE_FETCH_FORBIDDEN"]}\n')
    result = dispatcher.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "SOURCE_RESOLUTION_BLOCKED_FAIL_CLOSED"
    assert result["materializer_attempted"] is False
    assert result["preflight_attempted"] is False
    assert result["consumer_attempted"] is False
    assert len(calls) == 1


def test_dispatch_stops_before_preflight_when_materialization_blocks(tmp_path):
    materialized_tools(tmp_path)
    calls = []
    outputs = [resolver_success(), SimpleNamespace(returncode=2, stdout='{"state":"MATERIALIZATION_BLOCKED_FAIL_CLOSED","ready":false,"blockers":["INTR_NOT_ADMITTED"]}\n')]
    def runner(command, **kwargs):
        calls.append(command)
        return outputs.pop(0)
    result = dispatcher.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "MATERIALIZATION_BLOCKED_FAIL_CLOSED"
    assert result["preflight_attempted"] is False
    assert result["consumer_attempted"] is False
    assert len(calls) == 2


def test_dispatch_order_is_resolve_materialize_preflight_consume(tmp_path):
    materialized_tools(tmp_path)
    outputs = [
        resolver_success(),
        SimpleNamespace(returncode=0, stdout='{"state":"MATERIALIZED_READY_FOR_PREFLIGHT","ready":true,"blockers":[]}\n'),
        SimpleNamespace(returncode=0, stdout='{"state":"READY_FOR_RESIDENT_CONSUMPTION","ready":true,"blocker_count":0}\n'),
        SimpleNamespace(returncode=0, stdout='{"state":"AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"}\n'),
    ]
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        return outputs.pop(0)
    result = dispatcher.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    assert result["consumer_attempted"] is True
    assert result["activation_claimed"] is False
    assert dispatcher.RESOLVER.name in calls[0][1]
    assert dispatcher.MATERIALIZER.name in calls[1][1]
    assert dispatcher.PREFLIGHT.name in calls[2][1]
    assert dispatcher.CONSUMER.name in calls[3][1]
