from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFRESH = ROOT / "scripts/refresh_sovereign_worker_runtime_source.py"
REFRESH_BASE = ROOT / "scripts/refresh_sovereign_worker_runtime_source_base.py"

REQUIRED_MARKERS = (
    'Path("scripts/build_runtime_profile_map.py")',
    'Path("scripts/run_global_runtime_evidence_convergence.py")',
    'Path("scripts/run_global_runtime_node_profile_convergence.py")',
    'Path("control/runtime-node-profiles.json")',
    'Path("control/runtime-profile-sources.json")',
    'Path("control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json")',
    'Path("control/runtime-observability-consumers")',
)


def load_refresh(path: Path):
    spec = importlib.util.spec_from_file_location("runtime_refresh_test_module", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_active_and_base_refresh_lists_include_profile_convergence_sources():
    for path in (REFRESH, REFRESH_BASE):
        text = path.read_text(encoding="utf-8")
        for marker in REQUIRED_MARKERS:
            assert marker in text, f"missing {marker} from {path.name}"


def test_active_refresh_materializes_profile_convergence_without_overwriting_runtime_state():
    module = load_refresh(REFRESH)
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Path(tmp) / "runtime"
        receipt = module.refresh(ROOT, runtime)
        for relative in (
            "scripts/build_runtime_profile_map.py",
            "scripts/run_global_runtime_evidence_convergence.py",
            "scripts/run_global_runtime_node_profile_convergence.py",
            "control/runtime-node-profiles.json",
            "control/runtime-profile-sources.json",
            "control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json",
            "control/runtime-observability-consumers/stegbrowser-ephemeral-runtime-binding-001.json",
            "control/runtime-observability-consumers/data-continuation-stegclaw-p4.json",
            "control/runtime-observability-consumers/decision-envelope-de006.json",
        ):
            assert (runtime / relative).is_file(), relative
        assert receipt["mutable_runtime_state_preserved"] is True
        assert receipt["network_fetch_performed"] is False
        assert receipt["credential_read_or_acquired"] is False
        assert receipt["github_token_required"] is False
        assert receipt["authority_effect"] == "NONE_LOCAL_SOURCE_REFRESH"
