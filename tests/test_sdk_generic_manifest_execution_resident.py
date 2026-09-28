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
    assert [x["build"]["processor_request"]["provider"] for x in req["requests"]]==["openai","anthropic"]
    portable=(ROOT/"scripts/refresh_and_dispatch_resident_requests.py").read_text()
    assert 'SDK_GENERIC_MANIFEST_CONSUMER = "sdk_generic_manifest_execution"' in portable
    assert "STEG_BROWSER_TVC_CONSUMER, SDK_GENERIC_MANIFEST_CONSUMER)" in portable
    consumer=(ROOT/"scripts/consume_sdk_generic_manifest_execution_request.py").read_text()
    assert "process=\"stegbrowser\"" not in consumer
    assert "build_manifest(**item[\"build\"])" in consumer
    assert "CAPABILITY_WORKAROUND_REQUIRED" in consumer
    assert "CAPABILITY_DEVELOPMENT_REQUESTED" in consumer
