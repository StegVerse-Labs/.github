import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cosv import encode_task, validate_record  # noqa: E402

TASK_ID = "ERL-RC-TRUMP-FAMILY-CRYPTO-MARKET-2026"
VECTOR = "60200000112012"
ERL = "StegVerse-Labs/Executive_Rhetoric_Ledger"
RECORD = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"
TASK_VECTOR = ROOT / "control" / "task-vectors" / f"{TASK_ID}.json"
INDEX = ROOT / "control" / "task-vector-index.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_identity_states_and_lane():
    record = load(RECORD)
    assert record["schema"] == "stegverse.canonical-task-record/v1"
    assert record["task_id"] == record["correlation_id"] == record["root_correlation_id"] == TASK_ID
    assert record["parent_task_id"] is None
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "UNCLAIMED"
    assert record["repository"] == ERL
    assert record["issue_ref"] == f"{ERL}#223"
    assert "runtime_requirements" not in record
    lane = record["lane"]
    assert lane["lane_id"] == TASK_ID
    assert lane["producer"] == "StegVerse-Labs/Trumpality:.github/workflows/erl-active-research.yml"
    assert lane["consumer"] == f"{ERL}:.github/workflows/trumpality-research-intake.yml"
    assert lane["artifacts"] == f"{ERL}:research-data/trumpality-acquisition/{TASK_ID}/"
    assert lane["owning_goals"] == ["StegVerse-Labs/Trumpality#8", f"{ERL}#60", f"{ERL}#223"]


def test_vector_is_encoded_from_exact_metrics_and_agrees_everywhere():
    task_vector = load(TASK_VECTOR)
    assert task_vector["identity"] == f"StegVerse-Labs/.github:task:{TASK_ID}"
    assert task_vector["profile"] == "task.v1" and task_vector["level"] == "task"
    assert task_vector["authority_effect"] == "NONE"
    assert encode_task(task_vector["exact_metrics"]) == task_vector["vector"] == VECTOR
    assert validate_record(task_vector)
    record = load(RECORD)
    assert record["cosv_task_vector"] == VECTOR
    assert record["cosv_exact_metrics"] == task_vector["exact_metrics"]
    rows = [r for r in load(REGISTRY)["tasks"] if r["task_id"] == TASK_ID]
    assert len(rows) == 1 and rows[0] == record
    entries = [e for e in load(INDEX)["tasks"] if e["task_id"] == TASK_ID]
    assert len(entries) == 1
    assert entries[0]["vector"] == VECTOR and entries[0]["vector_state"] == "EMITTED"


def test_authority_separation_and_no_completion_claim():
    record = load(RECORD)
    assert record["worker_claim"]["authority"] == "WORKERCOORDINATOR"
    assert record["worker_claim"]["claim_ref"] is None
    assert record["worker_claim"]["projection_only"] is True
    model = record["authority_model"]
    assert model["task_registry_mints_execution_authority"] is False
    assert model["credential_authority"] == "TV/TVC"
    assert model["github_runtime_authority"] == "NONE"
    assert model["producer_evaluation_authority"] is False
    assert record["completion"] == {"claimed": False, "validated": False, "runtime_observed": False}
    assert {b["disposition"] for b in record["blockers"]} == {"FAIL_CLOSED", "DENY"}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("OK")
