from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "source-bundles/reusable-task-registry.d/RT-CANONICAL-WORK-PORTABLE-DISPATCH-001.json"
TRIGGER = ROOT / "scripts/trigger_reusable_task.py"
BRIDGE = ROOT / "scripts/refresh_and_dispatch_resident_requests.py"
RT_ID = "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001"


def load_trigger():
    spec = importlib.util.spec_from_file_location("reusable_trigger_canonical_work_test", TRIGGER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reusable_identity_resolves_once_and_reuses_existing_bridge() -> None:
    trigger = load_trigger()
    definition = trigger.resolve_definition(RT_ID)
    assert definition["reusable_task_id"] == RT_ID
    assert definition["runner_templates"] == ["scripts/refresh_and_dispatch_resident_requests.py"]
    assert definition["parameter_keys"] == ["source_root", "runtime_root", "only_consumer", "goal_task_id"]
    assert definition["authority_effect"] == "NONE_ORCHESTRATION_ONLY"


def test_reusable_definition_requires_exact_goal_scoped_canonical_work_semantics() -> None:
    definition = json.loads(DEFINITION.read_text(encoding="utf-8"))
    assert "EXACT_CANONICAL_WORK_COORDINATION_SELECTOR_BOUND" in definition["completion_predicates"]
    assert "EXACT_CURRENT_GOAL_CONTEXT_BOUND" in definition["completion_predicates"]
    assert "TASK_REGISTRY_PREFLIGHT_RETAINED" in definition["completion_predicates"]
    source = BRIDGE.read_text(encoding="utf-8")
    assert 'REUSABLE_CANONICAL_WORK_TASK_ID = "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001"' in source
    assert 'normalized["only_consumer"] != "canonical_work_coordination"' in source
    assert 'portable bridge reusable invocation requires goal_task_id' in source
    assert 'raise RuntimeError("portable bridge reusable invocation conflicts with explicit CLI: " + ",".join(sorted(mismatches)))' in source
