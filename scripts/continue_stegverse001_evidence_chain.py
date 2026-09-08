#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, subprocess
from pathlib import Path
from typing import Any

REQUIRED_SV002_ANCESTOR="786323f16e36346c69b2215894086515d7b1d58e"
DEFAULT_SOURCE_RECEIPT=Path.home()/".stegverse/state/stegverse001-bounded-autonomy/receipts/latest.json"
DEFAULT_SITE_CUSTODY_PROOF=Path.home()/".stegverse/state/stegverse001-evidence-chain/site-master-records-custody.latest.json"
DEFAULT_SV002_STATE=Path.home()/".stegverse/state/sv002-adversarial-observation"
SV002_REQUIRED_FILES=(
  "scripts/evaluate_sv002_adversarial_observation.py",
  "fixtures/sv002-adversarial-observation/cases.v1.json",
)
CANONICAL_CURRENT_IPHONE_AUTHORIZATION_SOURCE="EXTERNAL_WORKERCOORDINATOR_TVC_BOUND_ENVELOPE"
CANONICAL_G23_SHA="sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35"
SITE_CUSTODY_SCHEMA="stegos.master-records.portable-sv001-custody-proof/v1"

def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("expected JSON object")
    return v

def authorized_execution_state(source:dict[str,Any])->bool|str:
    legacy=source.get("authorized_execution","NOT_ESTABLISHED")
    if legacy is True: return True
    if legacy is False: return False
    if source.get("authorized_execution_source")==CANONICAL_CURRENT_IPHONE_AUTHORIZATION_SOURCE: return True
    return "NOT_ESTABLISHED"

def _git(root:Path,*args:str)->subprocess.CompletedProcess[str]:
    return subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=False,timeout=20)

def validate_sv002_source(source_root:Path)->dict[str,Any]:
    root=source_root.resolve()
    head=_git(root,"rev-parse","HEAD")
    ancestor=_git(root,"merge-base","--is-ancestor",REQUIRED_SV002_ANCESTOR,"HEAD")
    clean=_git(root,"status","--porcelain")
    files=all((root/p).is_file() for p in SV002_REQUIRED_FILES)
    return {
      "path":str(root),
      "head":head.stdout.strip() if head.returncode==0 else "",
      "clean_worktree":clean.returncode==0 and clean.stdout.strip()=="",
      "required_ancestor_present":ancestor.returncode==0,
      "required_files_present":files,
      "valid":head.returncode==0 and ancestor.returncode==0 and clean.returncode==0 and clean.stdout.strip()=="" and files
    }

def validate_site_custody_proof(proof:dict[str,Any], source_hash:str)->None:
    required={
      "schema":SITE_CUSTODY_SCHEMA,
      "state":"PASS",
      "execution_surface":"CURRENT_USER_IPHONE",
      "source_receipt_sha256":source_hash,
      "intr_governance_admission_observed":True,
      "reconstruction_state":"PASS",
      "canonical_owner":"master-records/orchestration",
      "site_custody_authority":False,
      "site_execution_authority":False,
      "heartbeat_granted_authority":False,
      "human_approval_checkpoint_inserted":False,
      "prior_receipt_authorizes_transition":False,
      "historical_state_retroactively_authorized":False,
    }
    for key, expected in required.items():
        if proof.get(key)!=expected:
            raise RuntimeError(f"invalid governed Site custody proof field {key}")
    for key in (
      "intr_admission_receipt_sha256","intr_admission_journal_entry_sha256",
      "custody_hash","reconstruction_hash","custody_journal_entry_sha256",
      "reconstruction_journal_entry_sha256","final_replay_tail_sha256",
    ):
        if not proof.get(key): raise RuntimeError(f"missing governed Site custody proof field {key}")

def _load_evaluator(source_root:Path):
    path=source_root/"scripts/evaluate_sv002_adversarial_observation.py"
    spec=importlib.util.spec_from_file_location("sv002_runtime_evaluator",path)
    if spec is None or spec.loader is None: raise RuntimeError("SV002 evaluator import unavailable")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def continue_chain(source_root:Path, source_receipt:Path=DEFAULT_SOURCE_RECEIPT, site_custody_proof:Path=DEFAULT_SITE_CUSTODY_PROOF, sv002_state:Path=DEFAULT_SV002_STATE)->dict[str,Any]:
    if not source_receipt.is_file():
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"SV001_RECEIPT_NOT_OBSERVED","retry_allowed":True,"authority_effect":"NONE"}
    source=load(source_receipt)
    source_hash=str(source.get("receipt_hash") or "")
    if source_hash!=CANONICAL_G23_SHA or source.get("transition_id")!="SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED":
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"CANONICAL_G23_SOURCE_MISMATCH","retry_allowed":False,"authority_effect":"NONE_FAIL_CLOSED"}
    authorized_execution=authorized_execution_state(source)

    # The independent WorkerCoordinator continuation must never create Master Records
    # custody itself. The current-iPhone Site carrier owns the fresh root-InTr request
    # and canonical Master Records mutation. This worker only consumes the resulting
    # governed proof after that authoritative path has completed.
    if not site_custody_proof.is_file():
        return {
          "schema":"stegverse.sv001-evidence-chain-continuation/v1",
          "state":"SITE_GOVERNED_CUSTODY_PENDING",
          "retry_allowed":True,
          "required_producer":"StegOSWebBootstrap.executeMasterRecordsSv001Custody",
          "required_transition":"MasterRecords:SV001Custody",
          "source_receipt_sha256":source_hash,
          "master_records_mutation_performed":False,
          "authority_effect":"NONE_OBSERVATION_ONLY"
        }
    proof=load(site_custody_proof)
    try:
        validate_site_custody_proof(proof,source_hash)
    except Exception as exc:
        return {
          "schema":"stegverse.sv001-evidence-chain-continuation/v1",
          "state":"SITE_GOVERNED_CUSTODY_PROOF_INVALID",
          "retry_allowed":True,
          "reason":str(exc),
          "source_receipt_sha256":source_hash,
          "master_records_mutation_performed":False,
          "authority_effect":"NONE_FAIL_CLOSED"
        }

    sv_source=validate_sv002_source(source_root)
    if not sv_source["valid"]:
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"SV002_SOURCE_NOT_CURRENT","retry_allowed":True,"sv002_source":sv_source,"authority_effect":"NONE"}
    evaluator=_load_evaluator(source_root)
    observation_valid=(proof.get("reconstruction_state")=="PASS" and proof.get("source_receipt_sha256")==source_hash and proof.get("intr_governance_admission_observed") is True)
    baseline_inputs={
      "master_records_custody":"PASS",
      "reconstruction_state":"PASS",
      "observation_valid":observation_valid,
      "output_correct":source.get("state")=="COMPLETED",
      "authorized_execution":authorized_execution
    }
    baseline=evaluator.evaluate(baseline_inputs)
    fixture_set=load(source_root/"fixtures/sv002-adversarial-observation/cases.v1.json")
    fixture_results=[]
    for case in fixture_set.get("cases",[]):
        actual=evaluator.evaluate(case["inputs"])["disposition"]
        fixture_results.append({"case_id":case["case_id"],"expected":case["expected_disposition"],"actual":actual,"pass":actual==case["expected_disposition"]})
    fixtures_pass=len(fixture_results)==12 and all(x["pass"] for x in fixture_results)
    target_established=(baseline["disposition"]=="OBSERVED" and fixtures_pass and observation_valid)
    out={
      "schema":"stegverse.sv001-evidence-chain-continuation/v1",
      "state":"PASS" if target_established else "REVIEW_REQUIRED",
      "source_receipt_sha256":source_hash,
      "intr_governance_admission_observed":True,
      "intr_admission_receipt_sha256":proof.get("intr_admission_receipt_sha256"),
      "master_records_custody_hash":proof.get("custody_hash"),
      "master_records_reconstruction_hash":proof.get("reconstruction_hash"),
      "master_records_reconstruction_state":"PASS",
      "retained_same_execution_chain_tail":proof.get("final_replay_tail_sha256"),
      "sv002_baseline_disposition":baseline,
      "adversarial_fixture_results":fixture_results,
      "adversarial_fixture_suite_pass":fixtures_pass,
      "target_property":"ADVERSARIALLY_CREDIBLE_OBSERVATION",
      "target_property_established":target_established,
      "frozen_experiment_condition":"v0.3 FROZEN",
      "frozen_findings_modified":False,
      "principal_runtime_required_for_reconstruction":False,
      "network_source_fetch_performed":False,
      "master_records_mutation_performed":False,
      "repository_writeback_performed":False,
      "credential_authority":"NONE",
      "authority_effect":"NONE_OBSERVATION_AND_DISPOSITION_ONLY",
      "retry_allowed":not target_established
    }
    target=sv002_state/"receipts/stegverse001.latest.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--source-receipt",type=Path,default=DEFAULT_SOURCE_RECEIPT)
    p.add_argument("--site-custody-proof",type=Path,default=DEFAULT_SITE_CUSTODY_PROOF)
    p.add_argument("--sv002-state",type=Path,default=DEFAULT_SV002_STATE)
    a=p.parse_args()
    r=continue_chain(a.source_root,a.source_receipt,a.site_custody_proof,a.sv002_state)
    print(json.dumps(r,sort_keys=True))
    return 0 if r["state"] in {"PASS","SV001_RECEIPT_NOT_OBSERVED","SITE_GOVERNED_CUSTODY_PENDING","SITE_GOVERNED_CUSTODY_PROOF_INVALID","SV002_SOURCE_NOT_CURRENT"} else 2
if __name__=="__main__": raise SystemExit(main())
