#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
from typing import Any

ROOT=Path.cwd().resolve()
TASK="ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001"
RECEIPT=ROOT/"receipts"/"erl-household-economic-conditions"/"latest.json"

def atomic_write(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h:
        json.dump(value,h,indent=2,sort_keys=True); h.write("\n"); name=h.name
    os.replace(name,path)

def roots()->dict[str,Path]:
    out={}
    raw=os.environ.get("STEGVERSE_REPO_ROOTS_JSON","").strip()
    if raw:
        try:
            v=json.loads(raw)
            if isinstance(v,dict):
                for k,p in v.items():
                    if isinstance(p,str) and p.strip(): out[k]=Path(p).expanduser().resolve()
        except Exception:
            pass
    explicit={
      "StegVerse-Labs/TVC":os.environ.get("STEGVERSE_TVC_ROOT"),
      "StegVerse-Labs/stegfin-governance":os.environ.get("STEGVERSE_STEGFIN_GOVERNANCE_ROOT"),
      "StegVerse-Labs/Executive_Rhetoric_Ledger":os.environ.get("STEGVERSE_ERL_SOURCE_ROOT")
    }
    for k,p in explicit.items():
        if p: out[k]=Path(p).expanduser().resolve()
    for k,name in [("StegVerse-Labs/TVC","TVC"),("StegVerse-Labs/stegfin-governance","stegfin-governance"),("StegVerse-Labs/Executive_Rhetoric_Ledger","Executive_Rhetoric_Ledger")]:
        if k not in out:
            for base in [ROOT/"workloads",Path.home()/".stegverse"/"workloads",Path.home()/".stegverse"/"source",Path("/var/lib/stegverse/workloads"),Path("/var/lib/stegverse/source")]:
                p=(base/name)
                if p.is_dir(): out[k]=p.resolve(); break
    return out

def run_json(argv:list[str],cwd:Path,timeout:int=600)->tuple[int,dict[str,Any]|None]:
    p=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,check=False,timeout=timeout,env=dict(os.environ))
    value=None
    for line in reversed([x.strip() for x in p.stdout.splitlines() if x.strip()]):
        try:
            x=json.loads(line)
            if isinstance(x,dict): value=x; break
        except Exception: pass
    return p.returncode,value

def response(state:str,transition:str,seq:int,next_transition:str|None,blocker:dict[str,Any]|None=None)->dict[str,Any]:
    x={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":seq,
       "expected_next_transition":next_transition,"expected_next_earliest_epoch":None,"expected_next_latest_epoch":None,
       "checkpoint_ref":str(RECEIPT.relative_to(ROOT)),"evidence_refs":[str(RECEIPT.relative_to(ROOT))]}
    if blocker:x["blocker"]=blocker
    return x

def main()->int:
    inv=json.load(sys.stdin); task=inv.get("task") or {}; epoch=inv.get("heartbeat_epoch")
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK or not isinstance(epoch,int): return 2
    claim=task.get("claim_id"); fence=(task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim,str) or not claim or not isinstance(fence,int): return 3
    rr=roots(); sg=rr.get("StegVerse-Labs/stegfin-governance"); tvc=rr.get("StegVerse-Labs/TVC"); erl=rr.get("StegVerse-Labs/Executive_Rhetoric_Ledger")
    missing=[k for k,v in [("stegfin-governance",sg),("TVC",tvc),("Executive_Rhetoric_Ledger",erl)] if v is None]
    if missing:
        blocker={"dependency_class":"INTERNAL_CAPABILITY","problem_statement":"Required already-local source root missing: "+",".join(missing),
          "solution_required":True,"may_remain_blocked":False,"workaround_candidates":["refresh existing local canonical source only"],
          "next_solution_action":"refresh existing local source and retry same fenced task","machine_observable_release_condition":"all three existing local roots resolve",
          "github_token_required":False,"non_tv_tvc_secret_or_token_required":False,"third_party_blocker":False,"human_action_required":False}
        d={"schema":"stegverse.erl-household-economic-conditions-worker-receipt/v1","task_id":TASK,"state":"BLOCKED","transition_id":"LOCAL_SOURCE_ROOT_PENDING",
           "heartbeat_epoch":epoch,"claim_id":claim,"fencing_token":fence,"blocker":blocker,"credential_authority":"TV/TVC","public_activation_authorized":False}
        atomic_write(RECEIPT,d); json.dump(response("BLOCKED",d["transition_id"],1,"BEA_READINESS_OBSERVED",blocker),sys.stdout); print(); return 0

    # Independently advance one exact credential-free required-cost source.
    census_dir=ROOT/"receipts"/"erl-household-economic-conditions"/"census-acs-2024"
    census_rc,census_summary=run_json([sys.executable,str(erl/"scripts"/"acquire_household_economic_conditions.py"),"--source","census","--census-year","2024","--output-dir",str(census_dir)],erl,600)

    # Re-observe only metadata; this script does not read/hash secret bytes or contact BEA.
    readiness_path=ROOT/"receipts"/"erl-household-economic-conditions"/"bea-readiness.json"
    p=subprocess.run([sys.executable,str(sg/"scripts"/"check_tvc_bea_credential_readiness.py"),"--out",str(readiness_path)],cwd=sg,capture_output=True,text=True,check=False,timeout=60,env=dict(os.environ))
    readiness=json.loads(readiness_path.read_text()) if readiness_path.is_file() else None
    bea_execution=None
    if isinstance(readiness,dict) and readiness.get("decision")=="READY":
        bea_out=ROOT/"receipts"/"erl-household-economic-conditions"/"bea-readonly-result.json"
        rc,res=run_json([sys.executable,str(tvc/"scripts"/"tvc_execute_bea_readonly.py"),"--readiness-receipt",str(readiness_path),"--out",str(bea_out)],tvc,900)
        bea_execution={"returncode":rc,"summary":res,"result_ref":str(bea_out.relative_to(ROOT)) if bea_out.is_file() else None}
    durable={"schema":"stegverse.erl-household-economic-conditions-worker-receipt/v1","task_id":TASK,"state":"COMPLETED",
      "transition_id":"HOUSEHOLD_ECONOMIC_SOURCE_OBSERVATION_COMPLETE","heartbeat_epoch":epoch,"claim_id":claim,"fencing_token":fence,
      "census_credential_free":{"returncode":census_rc,"output_dir":str(census_dir.relative_to(ROOT)),"candidate_only":True},
      "bea_readiness":readiness,"bea_execution":bea_execution,"credential_authority":"TV/TVC","credential_material_present":False,
      "finding_authority":False,"public_activation_authorized":False,"github_token_runtime_authority":"NONE","authority_effect":"NONE_CANDIDATE_EVIDENCE_ONLY"}
    atomic_write(RECEIPT,durable)
    json.dump(response("COMPLETED",durable["transition_id"],2,None),sys.stdout); print(); return 0

if __name__=="__main__": raise SystemExit(main())
