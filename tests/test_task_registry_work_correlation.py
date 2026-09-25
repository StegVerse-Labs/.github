"""Regression tests for nonblocking Task Registry source-work correlation."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "resolve_task_work_correlation.py"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
TASK = "MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001"


def load_module():
    spec = importlib.util.spec_from_file_location("work_correlation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_task_id_resolves_source_work_without_runtime_gate():
    result = load_module().resolve(TASK, json.loads(REGISTRY.read_text()))
    assert result["task_id"] == TASK
    assert result["source_work_allowed_without_runtime_disposition"] is True
    assert result["cosv_lineage"] == "40000100100000"
    assert result["cosv_is_exclusive_task_identity"] is False
    assert result["worker_claim_issued"] is False
    assert result["intr_admission_issued"] is False
    assert result["master_records_closure_claimed"] is False
    assert result["authority_effect"] == "NONE_CORRELATION_ONLY"
    assert result["work_identity_digest"].startswith("sha256:")


def test_shared_cosv_lineage_does_not_alias_distinct_task_id():
    registry = json.loads(REGISTRY.read_text())
    result = load_module().resolve(TASK, registry)
    other = next(x for x in registry["tasks"]
                 if x["task_id"] != TASK and x.get("cosv_task_vector") == "40000100100000")
    if other.get("correlation_id") == other["task_id"]:
        other_result = load_module().resolve(other["task_id"], registry)
        assert result["work_identity_digest"] != other_result["work_identity_digest"]


def test_missing_or_duplicate_canonical_id_fails_closed():
    module = load_module()
    registry = json.loads(REGISTRY.read_text())
    try:
        module.resolve("NOT-A-REAL-TASK", registry)
        assert False, "unknown task was accepted"
    except ValueError:
        pass
    registry["tasks"].append(dict(next(x for x in registry["tasks"] if x["task_id"] == TASK)))
    try:
        module.resolve(TASK, registry)
        assert False, "duplicate task was accepted"
    except ValueError:
        pass


def test_forged_work_correlation_cannot_override_canonical_identity():
    module = load_module()
    registry = json.loads(REGISTRY.read_text())
    row = next(x for x in registry["tasks"] if x["task_id"] == TASK)
    row["work_correlation"]["primary_key"] = "FORGED"
    try:
        module.resolve(TASK, registry)
        assert False, "forged correlation accepted"
    except ValueError:
        pass


def test_cli_reads_canonical_registry():
    result = subprocess.run([sys.executable, str(SCRIPT), "--task-id", TASK],
                            text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)["task_id"] == TASK
