from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_erl_household_runtime_binding_preserves_authority_boundaries():
    task=json.loads((ROOT/"data/canonical-task-records/ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001.json").read_text())
    reg=json.loads((ROOT/"control/worker-registry.d/erl-household-economic-conditions-site-001.json").read_text())
    adapter=json.loads((ROOT/"control/process-worker-adapters.d/erl-household-economic-conditions-site-001.json").read_text())
    req=json.loads((ROOT/"control/resident-execution-request.d/canonical-work-erl-household-economic-conditions-site-001.json").read_text())
    assert task["coordination_state"]=="PROPOSED"
    assert task["allowed_next_transitions"]==["INGRESS_ADMITTED"]
    assert task["worker_claim"]["authority"]=="WORKERCOORDINATOR"
    assert task["worker_claim"]["projection_only"] is True
    assert req["request_granted_authority"] is False
    assert req["credential_authority"]=="TV/TVC"
    assert reg["tasks"][0]["admission"]["fresh_fence_required"] is True
    assert reg["tasks"][0]["admission"]["heartbeat_grants_execution_authority"] is False
    assert adapter["adapters"][0]["env_allowlist"]
    assert all("API_KEY" not in x and "TOKEN" not in x for x in adapter["adapters"][0]["env_allowlist"])

def test_no_device_inventory_gate_or_new_runtime_plane():
    text=(ROOT/"workers/erl_household_economic_conditions_worker.py").read_text()
    forbidden=["connected_device","device_inventory","remote_computer","BEA_API_KEY","api_key =","api_key="]
    for term in forbidden:
        assert term not in text
    assert "check_tvc_bea_credential_readiness.py" in text
    assert "tvc_execute_bea_readonly.py" in text
    assert "--source\",\"census" in text or '"--source","census"' in text
    assert "public_activation_authorized\":False" in text or '"public_activation_authorized":False' in text
