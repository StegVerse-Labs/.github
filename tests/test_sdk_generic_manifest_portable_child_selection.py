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


def _fake_runner(captured):
    class _Result:
        returncode = 0
        stdout = '{"state":"OK"}'
        stderr = ""

    def run(command, **_kwargs):
        captured.append([str(part) for part in command])
        return _Result()

    return run


def _dispatcher():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_disp", ROOT / "scripts/dispatch_resident_execution_requests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_goal_context_without_a_request_id_is_refused_and_runs_nothing():
    """The consumer filters its bundle only when given a request_id; without one
    it runs every entry. The source-text assertions above cannot see this."""
    module = _dispatcher()
    captured = []
    try:
        module.dispatch(ROOT, ROOT, runner=_fake_runner(captured),
                        only_consumers=("sdk_generic_manifest_execution",),
                        goal_task_id="RT-SDK-GENERIC-MANIFEST-PORTABLE-DISPATCH-001")
    except RuntimeError as error:
        assert "exact child request_id required" in str(error)
    else:
        raise AssertionError("goal context without a request_id was accepted")
    assert captured == [], "nothing may execute when the exact child is unbound"


def test_goal_context_with_a_request_id_forwards_it():
    module = _dispatcher()
    captured = []
    module.dispatch(ROOT, ROOT, runner=_fake_runner(captured),
                    only_consumers=("sdk_generic_manifest_execution",),
                    goal_task_id="RT-SDK-GENERIC-MANIFEST-PORTABLE-DISPATCH-001",
                    request_id="test5-a")
    assert captured, "the consumer should have been invoked"
    command = captured[0]
    assert "--request-id" in command and command[command.index("--request-id") + 1] == "test5-a"


def test_portable_bridge_also_refuses_goal_context_without_a_request_id():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_bridge", ROOT / "scripts/refresh_and_dispatch_resident_requests.py")
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    try:
        bridge.refresh_and_dispatch(
            ROOT, ROOT, target_consumer="sdk_generic_manifest_execution",
            goal_task_id="RT-SDK-GENERIC-MANIFEST-PORTABLE-DISPATCH-001")
    except RuntimeError as error:
        assert "exact child request_id required" in str(error)
    else:
        raise AssertionError("portable bridge accepted goal context with no request_id")
