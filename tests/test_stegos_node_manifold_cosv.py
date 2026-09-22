from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGOS-NODE-MANIFOLD-001"
VECTOR = "40000100100000"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)

def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_stegos_node_manifold_cosv_is_derived_from_exact_metrics():
    record = load(f"control/task-vectors/{TASK_ID}.json")
    assert cosv.encode_task(record["exact_metrics"]) == VECTOR
    assert cosv.validate_record(record)

def test_canonical_task_and_index_shard_bind_exact_vector():
    task = load(f"data/canonical-task-records/{TASK_ID}.json")
    shard = load(f"control/task-vector-index.d/{TASK_ID}.json")
    assert task["coordination_state"] == "ACTIVE"
    assert task["checkout_state"] == "CHECKED_OUT"
    assert task["cosv_task_vector"] == VECTOR
    assert task["source_state_vector_ref"] == f"control/task-vectors/{TASK_ID}.json"
    assert shard["registry_ref"] == f"data/canonical-task-records/{TASK_ID}.json"
    assert shard["source_state_vector_ref"] == task["source_state_vector_ref"]
    assert shard["vector"] == VECTOR
    assert shard["vector_state"] == "EMITTED"
    assert shard["authority_effect"] == "NONE"
