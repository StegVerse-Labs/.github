from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sv002_obs",ROOT/"scripts/serve_sv002_observation_intr_runtime.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

def genesis():
    body={
      "schema":"stegos.node_handoff_receipt.v1",
      "receipt_number":1,
      "transition":"NODE_REGISTERED",
      "prior_state":"UNREGISTERED",
      "resulting_state":"REGISTERED",
      "continuity_parent":"GENESIS",
      "node_id":"SV-NODE-test",
      "interlock_id":"SV-IL-test",
      "device_binding_sha256":"a"*64,
      "authority_effect":"NONE",
      "heartbeat_authority":"StegVerse-Labs/.github",
      "credential_authority":"TV/TVC",
    }
    return {**body,"receipt_sha256":mod.sha256_hex(body)}

def request():
    g=genesis()
    body={
      "schema_version":"stegverse.sv002.public_observation.interlock_request.v1",
      "request_class":"SV002_PUBLIC_OBSERVE",
      "operation":"READ_OBSERVATION",
      "authority_ref":"PUBLIC_READ",
      "transport":"InTr",
      "observer":{"node_id":g["node_id"],"interlock_id":g["interlock_id"],"registration_receipt_sha256":g["receipt_sha256"],"genesis_receipt":g},
      "bindings":{"experiment_id":"STEGVERSE-002-SELF-CHARACTERIZATION-001","observation_projection":"PUBLIC_READ_ONLY"},
      "payload":{},
      "authority_transfer":False,
    }
    return {**body,"request_sha256":mod.sha256_hex(body)}

def test_node_genesis_and_request_binding_are_independently_validated():
    r=request()
    g=mod._validate_request(r,"PUBLIC_READ")
    assert g["node_id"]=="SV-NODE-test"
    broken=json.loads(json.dumps(r))
    broken["observer"]["genesis_receipt"]["receipt_sha256"]="0"*64
    try:
        mod._validate_request(broken,"PUBLIC_READ")
    except mod.ObservationRuntimeError as exc:
        assert "digest_mismatch" in str(exc)
    else:
        raise AssertionError("invalid genesis receipt was accepted")

def test_projection_preserves_not_observed_and_then_real_artifacts():
    with tempfile.TemporaryDirectory() as td:
        base=Path(td); runtime=base/"runtime"; micro=base/"micro"; state=base/"state"
        runtime.mkdir(); state.mkdir(); (micro/"experiments/self-characterization-001").mkdir(parents=True)
        provenance={"source_organization":{"organization":"Admissible-Existence","availability_known":True,"interlock_connected":False}}
        (micro/mod.PROVENANCE_REL).write_text(json.dumps(provenance))
        p=mod.build_projection(runtime,micro)
        assert p["state"]["worker_receipt"]=="NOT_OBSERVED"
        assert p["topology"]["admissible_existence_interlock"]=="NOT_CONNECTED"
        assert p["reconstruction"]["state"]=="NOT_OBSERVED"
        receipt_path=runtime/mod.WORKER_RECEIPT_REL; receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(json.dumps({"state":"COMPLETED","state_root":str(state)}))
        (state/"EXPERIMENT_EXECUTION_RECEIPT.json").write_text(json.dumps({"state":"COMPLETED"}))
        (state/"SELF_CHARACTERIZATION.md").write_text("Observed result")
        (state/"SELF_CHARACTERIZATION_FORMAL.json").write_text(json.dumps({"representation":"observed"}))
        (state/"INTERACTION_RECEIPT_CHAIN.json").write_text(json.dumps({"events":[{"kind":"EXTERNAL_INTERACTION"}]}))
        p=mod.build_projection(runtime,micro)
        assert p["state"]["worker_receipt"]=="OBSERVED"
        assert p["state"]["principal_execution"]=="OBSERVED"
        assert p["artifacts"]["self_characterization"]=="Observed result"
        assert any(e["event"]=="INTERACTION_EVIDENCE" for e in p["events"])
        assert p["topology"]["observer_direct_relation_to_stegverse_002"] is False
