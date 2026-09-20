import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "scripts" / "refresh_and_dispatch_resident_requests.py"
SHARD = ROOT / "source-bundles" / "reusable-task-registry.d" / "RT-SDK-TT-PURPOSE-BOUND-RESIDENT-CONSUMPTION-001.json"
RT_ID = "RT-SDK-TT-PURPOSE-BOUND-RESIDENT-CONSUMPTION-001"
SELECTOR = "stegagents_governed_runtime_targeted"


def load_bridge():
    spec = importlib.util.spec_from_file_location("sdk_tt_purpose_reusable_bridge", BRIDGE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_reusable_identity_binds_only_existing_stegagents_targeted_selector(tmp_path):
    mod = load_bridge()
    env = {
        mod.REUSABLE_TASK_ID_ENV: RT_ID,
        mod.REUSABLE_TASK_PARAMETERS_ENV: json.dumps({
            "source_root": str(ROOT),
            "runtime_root": str(tmp_path),
            "only_consumer": SELECTOR,
        }),
    }
    params = mod.reusable_canonical_work_parameters(env)
    assert params["only_consumer"] == SELECTOR
    assert params["goal_task_id"] is None
    args = argparse.Namespace(source_root=None, runtime_root=None, only_consumer=None, goal_task_id=None)
    source, runtime, target, goal = mod.resolve_main_inputs(args, env)
    assert source == ROOT.resolve()
    assert runtime == tmp_path.resolve()
    assert target == SELECTOR
    assert goal is None


def test_reusable_identity_rejects_selector_or_goal_context_drift(tmp_path):
    mod = load_bridge()
    base = {"source_root": str(ROOT), "runtime_root": str(tmp_path)}
    for payload in (
        {**base, "only_consumer": "canonical_work_coordination"},
        {**base, "only_consumer": SELECTOR, "goal_task_id": "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"},
    ):
        env = {
            mod.REUSABLE_TASK_ID_ENV: RT_ID,
            mod.REUSABLE_TASK_PARAMETERS_ENV: json.dumps(payload),
        }
        try:
            mod.reusable_canonical_work_parameters(env)
        except RuntimeError:
            pass
        else:
            raise AssertionError("SDK TT reusable binding must fail closed on selector/context drift")


def test_registered_runner_reuses_existing_bridge_only():
    shard = json.loads(SHARD.read_text())
    assert shard["runner_templates"] == ["scripts/refresh_and_dispatch_resident_requests.py"]
    assert shard["authority_effect"] == "NONE_ORCHESTRATION_ONLY"
