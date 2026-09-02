import importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p",ROOT/"scripts/project_stegverse001_runtime_observability.py")
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

def test_profile_points_only_to_canonical_observability_module():
    cfg=json.loads((ROOT/"control/runtime-observability-bindings.d/stegverse001-bounded-autonomy.json").read_text())
    assert cfg["canonical_module"]=="org-kernel/runtime_observability.py"
    assert cfg["authority_effect"]=="NONE_OBSERVATION_ONLY"
    assert set(cfg["predicates"])=={"resident_request_consumption","runtime_execution_completed","reconstruction_proven","sv002_adversarial_disposition"}
