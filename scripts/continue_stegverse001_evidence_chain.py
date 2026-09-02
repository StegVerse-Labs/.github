#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, os, subprocess, sys
from pathlib import Path
from typing import Any

REQUIRED_MASTER_RECORDS_ANCESTOR="d593c920c1630aa5da20cc2622196f8676a74afd"
REQUIRED_SV002_ANCESTOR="786323f16e36346c69b2215894086515d7b1d58e"
DEFAULT_SOURCE_RECEIPT=Path.home()/".stegverse/state/stegverse001-bounded-autonomy/receipts/latest.json"
DEFAULT_MASTER_RECORDS_STATE=Path.home()/".stegverse/master-records/stegverse001-bounded-autonomy"
DEFAULT_SV002_STATE=Path.home()/".stegverse/state/sv002-adversarial-observation"
MASTER_RECORDS_REQUIRED_FILES=(
  "scripts/watch_stegverse001_autonomy_receipt.py",
  "scripts/import_stegverse001_autonomy_receipt.py",
)
SV002_REQUIRED_FILES=(
  "scripts/evaluate_sv002_adversarial_observation.py",
  "fixtures/sv002-adversarial-observation/cases.v1.json",
)

def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("expected JSON object")
    return v

def _git(root:Path,*args:str)->subprocess.CompletedProcess[str]:
    return subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=False,timeout=20)

def _locate(candidates:list[Path], required_ancestor:str, required_files:tuple[str,...])->tuple[Path|None,list[dict[str,Any]]]:
    seen=[]
    for root in candidates:
        root=root.expanduser()
        if not (root/".git").is_dir(): continue
        head=_git(root,"rev-parse","HEAD")
        clean=_git(root,"status","--porcelain")
        ancestor=_git(root,"merge-base","--is-ancestor",required_ancestor,"HEAD")
        row={
          "path":str(root),
          "head":head.stdout.strip() if head.returncode==0 else "",
          "clean_worktree":clean.returncode==0 and clean.stdout.strip()=="",
          "required_ancestor_present":ancestor.returncode==0,
          "required_files_present":all((root/p).is_file() for p in required_files)
        }
        seen.append(row)
        if row["head"] and row["clean_worktree"] and row["required_ancestor_present"] and row["required_files_present"]:
            row["selected"]=True
            return root.resolve(),seen
    return None,seen

def locate_master_records()->tuple[Path|None,list[dict[str,Any]]]:
    raw=(os.getenv("STEGVERSE_MASTER_RECORDS_ROOT") or os.getenv("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT") or os.getenv("STEGVERSE_MASTER_RECORDS_SOURCE_ROOT") or "").strip()
    c=[]
    if raw: c.append(Path(raw))
    c.extend([
      Path.home()/".stegverse/repos/master-records/orchestration",
      Path("/var/lib/stegverse/source/master-records/orchestration"),
      Path("/srv/stegverse/repos/master-records/orchestration"),
      Path("/opt/stegverse/repos/master-records/orchestration"),
    ])
    return _locate(c,REQUIRED_MASTER_RECORDS_ANCESTOR,MASTER_RECORDS_REQUIRED_FILES)

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

def _load_evaluator(source_root:Path):
    path=source_root/"scripts/evaluate_sv002_adversarial_observation.py"
    spec=importlib.util.spec_from_file_location("sv002_runtime_evaluator",path)
    if spec is None or spec.loader is None: raise RuntimeError("SV002 evaluator import unavailable")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def continue_chain(source_root:Path, source_receipt:Path=DEFAULT_SOURCE_RECEIPT, master_records_state:Path=DEFAULT_MASTER_RECORDS_STATE, sv002_state:Path=DEFAULT_SV002_STATE, runner=subprocess.run)->dict[str,Any]:
    if not source_receipt.is_file():
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"SV001_RECEIPT_NOT_OBSERVED","retry_allowed":True,"authority_effect":"NONE"}
    source=load(source_receipt)
    mr_root,mr_seen=locate_master_records()
    if mr_root is None:
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"MASTER_RECORDS_SOURCE_NOT_MATERIALIZED","retry_allowed":True,"master_records_candidates":mr_seen,"authority_effect":"NONE"}
    cmd=[sys.executable,str(mr_root/"scripts/watch_stegverse001_autonomy_receipt.py"),"--source",str(source_receipt),"--root",str(master_records_state)]
    completed=runner(cmd,cwd=mr_root,capture_output=True,text=True,check=False,timeout=180)
    intake_path=master_records_state/"receipts/stegverse001-bounded-autonomy/resident-intake.latest.json"
    recon_path=master_records_state/"receipts/stegverse001-bounded-autonomy/reconstruction.latest.json"
    if completed.returncode!=0 or not intake_path.is_file():
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"MASTER_RECORDS_INTAKE_FAILED","retry_allowed":True,"returncode":completed.returncode,"authority_effect":"NONE"}
    intake=load(intake_path)
    if intake.get("state")!="PASS" or not recon_path.is_file():
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"MASTER_RECORDS_RECONSTRUCTION_PENDING","retry_allowed":True,"master_records_intake":intake,"authority_effect":"NONE"}
    reconstruction=load(recon_path)
    sv_source=validate_sv002_source(source_root)
    if not sv_source["valid"]:
        return {"schema":"stegverse.sv001-evidence-chain-continuation/v1","state":"SV002_SOURCE_NOT_CURRENT","retry_allowed":True,"sv002_source":sv_source,"authority_effect":"NONE"}
    evaluator=_load_evaluator(source_root)
    observation_valid=(reconstruction.get("state")=="PASS" and reconstruction.get("source_receipt_sha256")==source.get("receipt_hash"))
    baseline_inputs={
      "master_records_custody":"PASS",
      "reconstruction_state":"PASS" if reconstruction.get("state")=="PASS" else "MISMATCH",
      "observation_valid":observation_valid,
      "output_correct":source.get("state")=="COMPLETED",
      "authorized_execution":source.get("authorized_execution","NOT_ESTABLISHED")
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
      "source_receipt_sha256":source.get("receipt_hash"),
      "master_records_reconstruction_hash":reconstruction.get("reconstruction_hash"),
      "master_records_reconstruction_state":reconstruction.get("state"),
      "sv002_baseline_disposition":baseline,
      "adversarial_fixture_results":fixture_results,
      "adversarial_fixture_suite_pass":fixtures_pass,
      "target_property":"ADVERSARIALLY_CREDIBLE_OBSERVATION",
      "target_property_established":target_established,
      "frozen_experiment_condition":"v0.3 FROZEN",
      "frozen_findings_modified":False,
      "principal_runtime_required_for_reconstruction":False,
      "network_source_fetch_performed":False,
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
    p.add_argument("--master-records-state",type=Path,default=DEFAULT_MASTER_RECORDS_STATE)
    p.add_argument("--sv002-state",type=Path,default=DEFAULT_SV002_STATE)
    a=p.parse_args()
    r=continue_chain(a.source_root,a.source_receipt,a.master_records_state,a.sv002_state)
    print(json.dumps(r,sort_keys=True))
    return 0 if r["state"] in {"PASS","SV001_RECEIPT_NOT_OBSERVED","MASTER_RECORDS_SOURCE_NOT_MATERIALIZED","MASTER_RECORDS_RECONSTRUCTION_PENDING","SV002_SOURCE_NOT_CURRENT"} else 2
if __name__=="__main__": raise SystemExit(main())
