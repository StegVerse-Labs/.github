from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py"
INSTALLER = ROOT / "scripts/install_and_run_canonical_work_event_bootstrap.py"
REQUEST = ROOT / "control/resident-execution-request.d/canonical-work-global-runtime-evidence-measurement-001.json"
TASK = ROOT / "data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_measurement_request_is_registered_and_measurement_only():
    consumer = load(CONSUMER, "measurement_consumer")
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    task = json.loads(TASK.read_text(encoding="utf-8"))
    assert consumer.GLOBAL_MEASUREMENT_SPEC in consumer.REQUEST_SPECS
    assert consumer.GLOBAL_MEASUREMENT_SPEC["task_id"] == "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001"
    consumer.validate_request(request, consumer.GLOBAL_MEASUREMENT_SPEC)
    assert request["measurement_only"] is True
    assert request["same_run_remediation_allowed"] is False
    assert request["automatic_retry_after_first_failure"] is False
    assert task["coordination_state"] == "PROPOSED"
    assert "INGRESS_ADMITTED" in task["allowed_next_transitions"]


def test_new_task_can_materialize_from_source_shard_when_monolithic_registry_is_stale(tmp_path):
    consumer = load(CONSUMER, "measurement_shard_fallback")
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    (source / "data/canonical-task-records").mkdir(parents=True)
    (runtime / "data").mkdir(parents=True)
    (source / "data/canonical-task-registry.json").write_text(
        json.dumps({"schema": "stegverse.canonical-task-registry/v1", "tasks": []}), encoding="utf-8"
    )
    (runtime / "data/canonical-task-registry.json").write_text(
        json.dumps({"schema": "stegverse.canonical-task-registry/v1", "tasks": []}), encoding="utf-8"
    )
    source_task = json.loads(TASK.read_text(encoding="utf-8"))
    (source / "data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001.json").write_text(
        json.dumps(source_task), encoding="utf-8"
    )
    result = consumer.ensure_task_identity_materialized(source, runtime, "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001")
    assert result["state"] == "SOURCE_TASK_SHARD_MATERIALIZED"
    assert result["source_kind"] == "SOURCE_TASK_SHARD"
    materialized = json.loads((runtime / "data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001.json").read_text(encoding="utf-8"))
    assert materialized["task_id"] == "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001"


def test_measurement_child_triggers_global_convergence_runner():
    installer = load(INSTALLER, "measurement_installer")
    assert installer.GLOBAL_MEASUREMENT_TASK_ID == "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001"
    assert installer.GLOBAL_MEASUREMENT_TASK_ID in installer.GLOBAL_CONVERGENCE_TASK_IDS
    assert installer.RUNTIME_PROFILE_MAP_TASK_ID in installer.GLOBAL_CONVERGENCE_TASK_IDS
