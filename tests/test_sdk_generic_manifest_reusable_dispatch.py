import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_generic_sdk_manifest_has_neutral_reusable_addressability():
    d=json.loads((ROOT/"source-bundles/reusable-task-registry.d/RT-SDK-GENERIC-MANIFEST-PORTABLE-DISPATCH-001.json").read_text())
    assert d["runner_templates"]==["scripts/refresh_and_dispatch_resident_requests.py"]
    assert d["authority_effect"]=="NONE_ORCHESTRATION_ONLY"
    s=(ROOT/"scripts/refresh_and_dispatch_resident_requests.py").read_text()
    assert 'REUSABLE_SDK_GENERIC_MANIFEST_TASK_ID = "RT-SDK-GENERIC-MANIFEST-PORTABLE-DISPATCH-001"' in s
    assert 'REUSABLE_SDK_GENERIC_MANIFEST_TASK_ID: SDK_GENERIC_MANIFEST_CONSUMER' in s
    assert 'normalized["only_consumer"] != allowed_reusable[reusable_task_id]' in s

# Exact-head validation touch: deterministic suite retry after cancelled run.
