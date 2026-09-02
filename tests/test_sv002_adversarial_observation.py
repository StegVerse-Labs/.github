from __future__ import annotations
import importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("sv002ao",ROOT/"scripts/evaluate_sv002_adversarial_observation.py")
M=importlib.util.module_from_spec(S); assert S.loader; S.loader.exec_module(M)
FIX=json.loads((ROOT/"fixtures/sv002-adversarial-observation/cases.v1.json").read_text())

def test_all_twelve_adversarial_cases_match_expected_disposition():
    assert len(FIX["cases"])==12
    for case in FIX["cases"]:
        r=M.evaluate(case["inputs"])
        assert r["disposition"]==case["expected_disposition"], case["case_id"]
        assert r["operative_experiment_condition"]=="v0.3 FROZEN"
        assert r["frozen_findings_modified"] is False
        assert r["authority_effect"]=="NONE"

def test_correct_output_never_overrides_unauthorized_path():
    r=M.evaluate({"master_records_custody":"PASS","reconstruction_state":"PASS","observation_valid":True,"output_correct":True,"authorized_execution":False})
    assert r["disposition"]=="CONTRADICTED"
    assert r["correct_output_proves_authorized_execution"] is False

def test_principal_local_only_cannot_substitute_for_master_records():
    r=M.evaluate({"master_records_custody":"MISSING","reconstruction_state":"MISSING","observation_valid":True,"output_correct":True,"authorized_execution":True,"principal_local_only":True})
    assert r["disposition"]=="NOT_ESTABLISHED"
    assert r["principal_local_state_accepted_as_custody"] is False

def test_forgery_replay_substitution_and_reconstruction_mismatch_fail_closed():
    for extra in (
      {"receipt_forged":True},{"receipt_replayed":True},{"master_records_custody":"SUBSTITUTED"},{"reconstruction_state":"MISMATCH"}
    ):
        i={"master_records_custody":"PASS","reconstruction_state":"PASS","observation_valid":True,"output_correct":True,"authorized_execution":True}
        i.update(extra)
        assert M.evaluate(i)["disposition"]=="FAIL_CLOSED"
