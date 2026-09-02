#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

VOCAB={"OBSERVED","NOT_OBSERVED","INFERRED","NOT_ESTABLISHED","OUTSIDE_EXPERIMENT_SCOPE","CONTRADICTED","FAIL_CLOSED"}

def canonical(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v:Any)->str: return "sha256:"+hashlib.sha256(canonical(v)).hexdigest()

def evaluate(inputs:dict[str,Any])->dict[str,Any]:
    custody=inputs.get("master_records_custody")
    recon=inputs.get("reconstruction_state")
    authorized=inputs.get("authorized_execution","NOT_ESTABLISHED")
    if inputs.get("receipt_forged") or inputs.get("receipt_replayed") or custody=="SUBSTITUTED" or recon=="MISMATCH":
        disposition="FAIL_CLOSED"
    elif custody!="PASS" or recon!="PASS" or inputs.get("principal_local_only"):
        disposition="NOT_ESTABLISHED"
    elif inputs.get("history_fork"):
        disposition="CONTRADICTED"
    elif authorized is False:
        disposition="CONTRADICTED"
    elif authorized=="NOT_ESTABLISHED":
        disposition="NOT_ESTABLISHED"
    elif inputs.get("observation_valid") is not True:
        disposition="NOT_OBSERVED"
    else:
        disposition="OBSERVED"
    out={
      "schema":"stegverse.sv002-adversarial-observation-disposition/v1",
      "operative_experiment_condition":"v0.3 FROZEN",
      "frozen_findings_modified":False,
      "disposition":disposition,
      "execution_integrity":"ESTABLISHED" if authorized is True else ("CONTRADICTED" if authorized is False else "NOT_ESTABLISHED"),
      "observation_integrity":"ESTABLISHED" if inputs.get("observation_valid") is True and custody=="PASS" and recon=="PASS" else "NOT_ESTABLISHED",
      "evidentiary_integrity":"ESTABLISHED" if custody=="PASS" and recon=="PASS" and not inputs.get("receipt_forged") and not inputs.get("receipt_replayed") else "NOT_ESTABLISHED",
      "disposition_integrity":"BOUNDED",
      "correct_output":bool(inputs.get("output_correct")),
      "correct_output_proves_authorized_execution":False,
      "principal_local_state_accepted_as_custody":False,
      "evaluator_secrecy_required":False,
      "authority_effect":"NONE"
    }
    out["disposition_hash"]=sha(out)
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("fixture",type=Path); p.add_argument("--output",type=Path)
    a=p.parse_args(); f=json.loads(a.fixture.read_text())
    r=evaluate(f["inputs"])
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
