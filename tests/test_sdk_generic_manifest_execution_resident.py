import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_generic_sdk_manifest_consumer_replaces_test5_selector():
    dispatch=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
    assert '("sdk_generic_manifest_execution", "scripts/consume_sdk_generic_manifest_execution_request.py")' in dispatch
    assert "sdk_test5_stegbrowser_llm_profile" not in dispatch
    req=json.loads((ROOT/"control/resident-execution-request.d/sdk-generic-manifest-execution.json").read_text())
    assert req["schema"]=="stegverse.sdk-generic-manifest-execution-request/v1"
    assert [x["build"]["process"] for x in req["requests"]]==["stegbrowser","stegbrowser"]
    assert [x["build"]["processor_request"]["response_marker"] for x in req["requests"]]==["TEST5_A","TEST5_B"]
    assert [x["build"]["processor_request"]["provider"] for x in req["requests"]]==["credential-free-huggingface-space","credential-free-huggingface-space"]
    assert all(x["build"]["processor_request"]["secure_url"].startswith("https://") for x in req["requests"])
    assert all(x["build"]["processor_request"]["model"]=="Qwen3" for x in req["requests"])
    assert all(x["build"]["processor_request"]["browser_actions"] for x in req["requests"])
    portable=(ROOT/"scripts/refresh_and_dispatch_resident_requests.py").read_text()
    assert 'SDK_GENERIC_MANIFEST_CONSUMER = "sdk_generic_manifest_execution"' in portable
    assert "STEG_BROWSER_TVC_CONSUMER, SDK_GENERIC_MANIFEST_CONSUMER)" in portable
    consumer=(ROOT/"scripts/consume_sdk_generic_manifest_execution_request.py").read_text()
    assert "process=\"stegbrowser\"" not in consumer
    assert "build_manifest(**item[\"build\"])" in consumer
    assert "CAPABILITY_WORKAROUND_REQUIRED" in consumer
    assert "CAPABILITY_DEVELOPMENT_REQUESTED" in consumer


def test_universal_intr_binds_stegbrowser_llm_to_existing_browser_owner():
    source=(ROOT/"workers/manifest_state_transition_intr_ingress.py").read_text()
    assert 'capability == "stegbrowser"' in source
    assert 'graph.get("profile") == "llm.v1"' in source
    assert "execute_manifested_llm_browser_operation" in source
    assert 'roots.get(name)' in source
    assert 'build_state_receipt' in source and 'submit_state_receipt' in source
    assert 'organization_records_before_master_records' in source
