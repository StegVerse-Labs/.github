from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_kv_ai_workercoordinator_claim_fence_observation.py"

spec = importlib.util.spec_from_file_location("kv_ai_claim_fence_observer", SCRIPT)
assert spec and spec.loader
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def _write_positive_fixture(root: Path) -> None:
    (root / "receipts/sovereign-host").mkdir(parents=True, exist_ok=True)
    (root / "control").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)

    event = {
        "event_type": "worker_assignment_bound_from_independent_task_control",
        "task_id": "SV-KV-AI-PERSISTENCE-001",
        "worker_id": "kv-ai-memory-resident-worker",
        "claim_id": "SHWP-SV-KV-AI-PERSISTENCE-001-G42",
        "fencing_token": 42,
        "packet_id": "INDEPENDENT-SV-KV-AI-PERSISTENCE-001-HB31",
        "master_records_binding_ref": "events/master-records-worker-assignment.jsonl#packet_id=INDEPENDENT-SV-KV-AI-PERSISTENCE-001-HB31",
        "authority_effect": False,
    }
    receipt = {
        "schema": "stegverse.resident-refresh-targeted-execution/v3",
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "task_id": "SV-KV-AI-PERSISTENCE-001",
        "cosv_task_pointer": {
            "profile": "task.v1",
            "task_id": "SV-KV-AI-PERSISTENCE-001",
            "vector": "20111110110000",
            "binding_verified": True,
            "authority_effect": "NONE",
        },
        "runtime_execution_attempted": True,
        "execution_result_observed": True,
        "execution_result": {"events": [event]},
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
    }
    (root / observer.DEFAULT_RECEIPT_REL).write_text(json.dumps(receipt), encoding="utf-8")

    task = {
        "task_id": "SV-KV-AI-PERSISTENCE-001",
        "state": "ACTIVE",
        "worker_id": "kv-ai-memory-resident-worker",
        "worker_instance_id": "kv-ai-memory-resident-worker-HB31-G42",
        "claim_id": "SHWP-SV-KV-AI-PERSISTENCE-001-G42",
        "assignment_timer": {
            "schema": "stegverse.worker-assignment-timer/v1",
            "task_id": "SV-KV-AI-PERSISTENCE-001",
            "worker_id": "kv-ai-memory-resident-worker",
            "worker_instance_id": "kv-ai-memory-resident-worker-HB31-G42",
            "claim_id": "SHWP-SV-KV-AI-PERSISTENCE-001-G42",
            "fencing_token": 42,
            "allocated_hb_units": 5,
            "remaining_hb_units": 5,
        },
    }
    (root / observer.REGISTRY_REL).write_text(json.dumps({"schema": "stegverse.worker-registry/v0.1", "tasks": [task]}), encoding="utf-8")

    assignment = {
        "task_id": "SV-KV-AI-PERSISTENCE-001",
        "worker_id": "kv-ai-memory-resident-worker",
        "worker_instance_id": "kv-ai-memory-resident-worker-HB31-G42",
        "claim_id": "SHWP-SV-KV-AI-PERSISTENCE-001-G42",
        "fencing_token": 42,
        "packet_id": "INDEPENDENT-SV-KV-AI-PERSISTENCE-001-HB31",
    }
    (root / observer.ASSIGNMENT_RECORD_REL).write_text(json.dumps(assignment) + "\n", encoding="utf-8")


def test_accepts_only_same_execution_claim_fence_tuple(tmp_path: Path) -> None:
    _write_positive_fixture(tmp_path)
    result = observer.evaluate(tmp_path)
    assert result["observed"] is True
    assert result["status"] == "AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED"
    assert result["claim_id"] == "SHWP-SV-KV-AI-PERSISTENCE-001-G42"
    assert result["worker_instance_id"] == "kv-ai-memory-resident-worker-HB31-G42"
    assert result["fencing_token"] == 42
    assert result["authority_effect"] == "NONE_OBSERVATION_ONLY"
    assert "OBSERVER_DOES_NOT_COMPLETE_SV_KV_AI_PERSISTENCE_001" in result["nonclaims"]


def test_rejects_missing_master_records_assignment(tmp_path: Path) -> None:
    _write_positive_fixture(tmp_path)
    (tmp_path / observer.ASSIGNMENT_RECORD_REL).unlink()
    result = observer.evaluate(tmp_path)
    assert result["observed"] is False
    assert result["status"] == "AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED"
    assert "master_records_worker_assignment_record" in result["missing_predicates"]
    assert result["claim_id"] is None


def test_rejects_wrong_cosv_vector_even_with_claim_like_data(tmp_path: Path) -> None:
    _write_positive_fixture(tmp_path)
    receipt_path = tmp_path / observer.DEFAULT_RECEIPT_REL
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["cosv_task_pointer"]["vector"] = "20111110110001"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    result = observer.evaluate(tmp_path)
    assert result["observed"] is False
    assert "exact_cosv_task_pointer_binding" in result["missing_predicates"]


def test_rejects_registry_tuple_mismatch(tmp_path: Path) -> None:
    _write_positive_fixture(tmp_path)
    registry_path = tmp_path / observer.REGISTRY_REL
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["tasks"][0]["assignment_timer"]["fencing_token"] = 43
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    result = observer.evaluate(tmp_path)
    assert result["observed"] is False
    assert "assignment_timer_fencing_token_match" in result["missing_predicates"]
