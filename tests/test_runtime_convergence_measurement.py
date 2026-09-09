import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT = ROOT / "workers/runtime_convergence_measurement.py"
BOUNDARIES = ROOT / "workers/runtime_failure_boundaries.py"
RUNNER = ROOT / "scripts/run_global_runtime_node_profile_convergence.py"
VACC = ROOT / "workers/vacc_profiled_resident_execution.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_measurement_context_freezes_run_and_before_after_evidence(tmp_path):
    m = load(MEASUREMENT, "measurement")
    source = tmp_path / "source"; runtime = tmp_path / "runtime"
    source.mkdir(); runtime.mkdir()
    profile_registry = source / "profiles.json"; projection = source / "projection.json"
    profile_registry.write_text("{}\n", encoding="utf-8"); projection.write_text("{}\n", encoding="utf-8")
    receipt = runtime / "receipts/test.json"; receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({"node_ref":"N1","source_device_hb_reference":"heartbeat_epoch:1","transition_commitment":"aaa"}), encoding="utf-8")
    profiles = [{"task_id":"T1","profile_id":"P1","execution_binding":{"receipt":"receipts/test.json"}}]
    ctx = m.freeze_context(source, runtime, profile_registry, projection, profiles)
    assert ctx["measurement_only"] is True
    assert ctx["same_run_remediation_allowed"] is False
    assert ctx["automatic_retry_after_first_failure"] is False
    assert ctx["baseline"][0]["tracked"]["transition_commitment"] == "aaa"
    receipt.write_text(json.dumps({"node_ref":"N1","source_device_hb_reference":"heartbeat_epoch:1","transition_commitment":"bbb"}), encoding="utf-8")
    done = m.finish_context(ctx, runtime, profiles)
    assert done["after"][0]["tracked"]["transition_commitment"] == "bbb"
    assert done["run_id"] == ctx["run_id"]


def test_run_ids_are_unique_and_timestamped():
    m = load(MEASUREMENT, "measurement_ids")
    now = datetime(2026, 9, 9, 17, 30, tzinfo=timezone.utc)
    a, b = m.new_run_id(now), m.new_run_id(now)
    assert a.startswith("global-runtime-20260909T173000Z-")
    assert a != b


def test_readiness_and_live_verified_do_not_suppress_failure():
    b = load(BOUNDARIES, "boundaries_readiness")
    for state in ("PROFILE_BOUND_PARENT_CHAIN_PRESENT_REEXECUTION_READY", "PROFILE_BOUND_RUNTIME_LIVE_VERIFIED"):
        row = b.annotate_lane_outcome({"lane":"X","task_id":"T","resume_stage":"AUTHENTIC_BROWSER_INVOCATION","state":state})
        assert row["first_failure_stage_index"] == 7
        assert row["first_failure"] is not None


def test_noncontiguous_explicit_observation_fails_at_missing_earlier_stage():
    b = load(BOUNDARIES, "boundaries_contiguous")
    row = b.annotate_lane_outcome({"lane":"X","task_id":"T","state":"FAILED","stage_observations":{"RUNTIME_PROFILE_RESOLUTION":{"state":"PASS_CURRENT_RUN"},"EPHEMERAL_REQUEST_CONSUMPTION":{"state":"FAILED_CURRENT_RUN"}}})
    assert row["first_failure_stage_index"] == 2
    assert row["first_failure_code"] == "RUNTIME_STAGE_02_NODE_CONTINUITY_UNOBSERVED"


def test_not_reached_is_not_itself_failure():
    b = load(BOUNDARIES, "boundaries_not_reached")
    row = b.annotate_lane_outcome({"lane":"X","task_id":"T","state":"FAILED","stage_observations":{"RUNTIME_PROFILE_RESOLUTION":{"state":"PASS_CURRENT_RUN"},"PERSISTENT_NODE_CONTINUITY":{"state":"FAILED_CURRENT_RUN"},"EPHEMERAL_REQUEST_CONSUMPTION":{"state":"NOT_REACHED"}}})
    assert row["first_failure_stage_index"] == 2
    assert sum(1 for item in row["boundary_trace"] if item["failed"]) == 1


def test_runner_and_vacc_enforce_measurement_only_behavior():
    runner = RUNNER.read_text(encoding="utf-8")
    vacc = VACC.read_text(encoding="utf-8")
    assert 'STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY' in runner
    assert 'same_run_remediation_allowed' not in runner or 'MEASUREMENT_RUN_DOES_NOT_REPAIR_OR_RETRY_AFTER_FIRST_FAILURE' in runner
    assert 'if live is None and not measurement_only:' in vacc
    assert 'same_run_parent_repair_attempted' in vacc
    assert 'PASS_HISTORICAL_EVIDENCE' in vacc
