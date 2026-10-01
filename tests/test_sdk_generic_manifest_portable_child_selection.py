from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_test5_sdk_portable_dispatch_is_goal_and_child_scoped():
    definition=json.loads((ROOT/"source-bundles/reusable-task-registry.d/RT-SDK-GENERIC-MANIFEST-PORTABLE-DISPATCH-001.json").read_text())
    assert "request_id" in definition["parameter_keys"]
    assert "EXACT_CHILD_REQUEST_ID_BOUND" in definition["completion_predicates"]

    bridge=(ROOT/"scripts/refresh_and_dispatch_resident_requests.py").read_text()
    dispatcher=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
    consumer=(ROOT/"scripts/consume_sdk_generic_manifest_execution_request.py").read_text()

    assert 'SDK_GENERIC_MANIFEST_CONSUMER' in bridge
    assert 'command.extend(["--request-id", request_id])' in bridge
    assert '("sdk_generic_manifest_execution",)' in dispatcher
    assert 'command.extend(["--request-id", request_id])' in dispatcher
    assert 'command.extend(["--goal-task-id", current_goal_task_id])' in dispatcher
    assert 'requests=[item for item in requests if item.get("request_id")==request_id]' in consumer
    assert 'raise RuntimeError("exact SDK generic manifest child request not found or not unique")' in consumer
    assert 'p.add_argument("--request-id")' in consumer
    assert 'p.add_argument("--goal-task-id")' in consumer

def test_test5_shared_bundle_still_preserves_a_before_b():
    req=json.loads((ROOT/"control/resident-execution-request.d/sdk-generic-manifest-execution.json").read_text())
    ids=[row["request_id"] for row in req["requests"]]
    assert ids[:2]==["test5-a","test5-b"]
