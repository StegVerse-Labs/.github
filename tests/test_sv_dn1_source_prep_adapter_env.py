import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "control/process-worker-adapters.d/sv-dn1-production-source-prep-001.json"


def test_source_prep_adapter_forwards_all_canonical_local_root_locators():
    doc = json.loads(ADAPTER.read_text())
    adapter = doc["adapters"][0]
    allowlist = set(adapter["env_allowlist"])

    required = {
        "STEGVERSE_SDK_SOURCE_ROOT",
        "STEGVERSE_STEGCORE_SOURCE_ROOT",
        "STEGVERSE_CORE_LITE_SOURCE_ROOT",
        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    }

    assert required <= allowlist
    assert adapter["enabled"] is True
    assert adapter["type"] == "process_json_bound_state_v0.1"
