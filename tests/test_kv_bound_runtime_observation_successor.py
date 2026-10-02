import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_ID = "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001"
SUCCESSOR_ID = "KV-BOUND-AUTHENTIC-STEGOS-RUNTIME-OBSERVATION-001"
OWNER_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "50000010100000"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_parent_is_prompt_limit_decomposed_without_runtime_completion():
    parent = load(f"data/canonical-task-records/{PARENT_ID}.json")
    assert parent["coordination_state"] == "RETIRED"
    assert parent["checkout_state"] == "DECOMPOSED_AT_PROMPT_LIMIT"
    assert parent["prompt_budget"]["goal_prompt_count"] == "20/20"
    assert parent["prompt_budget"]["continuation_task_id"] == SUCCESSOR_ID
    assert parent["completion"]["claimed"] is False
    assert parent["completion"]["validated"] is False
    assert parent["decomposition"]["first_unresolved_successor_predicate"] == "AUTHENTIC_RETAINED_STEGOS_STEGBROWSER_RUNTIME_OBSERVED"


def test_successor_reuses_existing_owner_and_does_not_authorize_attempt():
    successor = load(f"data/canonical-task-records/{SUCCESSOR_ID}.json")
    assert successor["cosv_task_vector"] == COSV
    assert successor["existing_execution_owner"]["task_id"] == OWNER_ID
    assert successor["existing_execution_owner"]["reusable_task_id"] == "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001"
    assert successor["existing_execution_owner"]["requested_invocation_count"] == 1
    assert successor["existing_execution_owner"]["second_request_allowed"] is False
    assert successor["runtime_resolution"]["attempt_cardinality"] == "EXACTLY_ONE_FUTURE_INDEPENDENTLY_AUTHORIZED_ATTEMPT"
    assert successor["runtime_resolution"]["invocation_authorized_by_this_record"] is False
    assert successor["runtime_resolution"]["unresolved_predicate"] == "AUTHENTIC_RETAINED_STEGOS_STEGBROWSER_RUNTIME_OBSERVED"
    assert successor["authority_model"]["task_registry_mints_execution_authority"] is False
    assert successor["device_invariants"]["physical_device_identity_gate"] == "NONE_PROHIBITED"
    assert successor["device_invariants"]["second_user_operated_device_allowed"] is False


def test_registry_and_cosv_index_project_successor():
    registry = load("data/canonical-task-registry.json")
    rows = [x for x in registry["tasks"] if x["task_id"] == SUCCESSOR_ID]
    assert len(rows) == 1
    assert rows[0]["coordination_state"] == "PROPOSED"
    vector = load(f"control/task-vectors/{SUCCESSOR_ID}.json")
    index = load(f"control/task-vector-index.d/{SUCCESSOR_ID}.json")
    assert vector["vector"] == COSV
    assert index["vector"] == COSV
    assert index["registry_ref"].endswith(f"{SUCCESSOR_ID}.json")
