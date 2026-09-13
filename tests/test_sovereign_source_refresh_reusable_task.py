import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_refresh_reusable_task_resolves_from_shard():
    constructor = load_module(ROOT / "scripts/materialize_reusable_task_construct.py", "rt_constructor_source_refresh")
    registry = constructor.load_registry()
    definition = constructor.resolve_reusable_task(registry, "RT-SOVEREIGN-SOURCE-REFRESH-001")
    assert definition["runner_templates"] == ["scripts/refresh_sovereign_worker_runtime_source.py"]
    assert "runtime availability is an execution boundary" in definition["reuse_instructions"].lower()


def test_trigger_parameterizes_existing_source_refresh_runner():
    trigger = load_module(ROOT / "scripts/trigger_reusable_task.py", "rt_trigger_source_refresh")
    runner = ROOT / "scripts/refresh_sovereign_worker_runtime_source.py"
    command = trigger.build_runner_command(
        trigger.SOURCE_REFRESH_PRIMARY,
        runner,
        {"source_root": str(ROOT), "runtime_root": "/tmp/stegverse-runtime"},
    )
    assert command[-4:] == ["--source-root", str(ROOT.resolve()), "--runtime-root", "/tmp/stegverse-runtime"]


def test_component_consumes_reusable_task_without_manual_device_gate():
    component = json.loads((ROOT / "data/reusable-sovereign-source-refresh-component-contract.json").read_text())
    profile = json.loads((ROOT / "data/goal-task-component-profiles/SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001.json").read_text())
    selected = profile["selected_components"][0]
    assert component["reusable_task_id"] == "RT-SOVEREIGN-SOURCE-REFRESH-001"
    assert selected["reusable_task_id"] == "RT-SOVEREIGN-SOURCE-REFRESH-001"
    assert "authorized_sovereign_runtime_surface_is_available" not in component["preconditions"]
    assert "task-specific prerequisite" in selected["execution_boundary_semantics"]


def test_registry_shard_is_carried_by_existing_source_bundle_refresh():
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    assert 'Path("source-bundles")' in refresh
