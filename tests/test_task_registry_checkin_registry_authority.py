import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
spec = importlib.util.spec_from_file_location("registry_checkin", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def record(task_id, *, root_goal="GOAL-A", state="PROPOSED"):
    return {
        "schema": "stegverse.canonical-task-record/v1",
        "task_id": task_id,
        "correlation_id": task_id,
        "root_correlation_id": root_goal,
        "parent_task_id": root_goal if task_id != root_goal else None,
        "goal": "test",
        "coordination_state": state,
        "source_refs": [],
        "targets": {"organizations": ["StegVerse-Labs"], "repositories": ["StegVerse-Labs/.github"], "components": [task_id]},
        "dependencies": [],
        "blockers": [],
        "adjacent_task_refs": [],
        "expected_evidence_predicates": [],
        "worker_claim": {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
        "completion": {"claimed": False, "validated": False, "reconciliation_ref": None},
        "allowed_next_transitions": ["INGRESS_ADMITTED"],
        "authority_model": {
            "task_registry_mints_execution_authority": False,
            "source_state_proves_execution": False,
            "worker_claim_authority": "WORKERCOORDINATOR",
            "master_records_reality_authority": True,
            "interlock_intr_required_for_governed_ingress_egress": True,
        },
    }


def test_registry_only_identity_is_loaded_without_shard():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records = root / "records"
        records.mkdir()
        registry = root / "registry.json"
        registry.write_text(json.dumps({"tasks": [record("A-001")]}), encoding="utf-8")
        old_registry, old_records = module.REGISTRY, module.RECORDS
        module.REGISTRY, module.RECORDS = registry, records
        try:
            loaded = module.load_records()
        finally:
            module.REGISTRY, module.RECORDS = old_registry, old_records
        assert set(loaded) == {"A-001"}


def test_shard_only_identity_is_not_registered_work():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records = root / "records"
        records.mkdir()
        registry = root / "registry.json"
        registry.write_text(json.dumps({"tasks": [record("A-001")]}), encoding="utf-8")
        (records / "GHOST-001.json").write_text(json.dumps(record("GHOST-001")), encoding="utf-8")
        old_registry, old_records = module.REGISTRY, module.RECORDS
        module.REGISTRY, module.RECORDS = registry, records
        try:
            loaded = module.load_records()
        finally:
            module.REGISTRY, module.RECORDS = old_registry, old_records
        assert set(loaded) == {"A-001"}


def test_shard_cannot_override_registry_state():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records = root / "records"
        records.mkdir()
        registry = root / "registry.json"
        registry.write_text(json.dumps({"tasks": [record("A-001", state="INGRESS_ADMITTED")]}), encoding="utf-8")
        (records / "A-001.json").write_text(json.dumps(record("A-001", state="PROPOSED")), encoding="utf-8")
        old_registry, old_records = module.REGISTRY, module.RECORDS
        module.REGISTRY, module.RECORDS = registry, records
        try:
            loaded = module.load_records()
        finally:
            module.REGISTRY, module.RECORDS = old_registry, old_records
        assert loaded["A-001"]["coordination_state"] == "INGRESS_ADMITTED"


def test_same_goal_progression_controller_is_not_collision_owner():
    candidate = record("CHILD-001", root_goal="GOAL-A")
    controller = record(module.PROGRESSION_CONTROLLER_TASK_ID, root_goal="GOAL-A")
    controller["worker_claim"]["projection_only"] = True
    assert module.progression_controller_for_same_goal(candidate, controller) is True
    assert module.progression_controller_for_same_goal(candidate, record("OTHER-001", root_goal="GOAL-A")) is False
