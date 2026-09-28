import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_test5_resident_request_uses_existing_dispatcher_and_run_manifest():
    req=json.loads((ROOT/"control/resident-execution-request.d/sdk-test5-stegbrowser-llm-profile-001.json").read_text())
    assert req["task_id"]=="EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001"
    assert req["entrypoint"]=="stegverse.manifest_execution.execute_manifest"
    assert req["second_machine_required"] is False
    assert [w["response_marker"] for w in req["workers"]]==["TEST5_A","TEST5_B"]
    dispatcher=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
    assert '("sdk_test5_stegbrowser_llm_profile", "scripts/consume_sdk_test5_stegbrowser_llm_profile_request.py")' in dispatcher
    consumer=(ROOT/"scripts/consume_sdk_test5_stegbrowser_llm_profile_request.py").read_text()
    assert 'from stegverse.manifest_execution import execute_manifest' in consumer
    assert 'process="stegbrowser"' in consumer
    assert '"stegbrowser.llm-profile-request.v1"' in consumer
    assert "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL" not in consumer
