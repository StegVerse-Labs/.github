#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess, sys, tempfile
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

def _nonsecret_readiness(value:Any)->bool:
    if not isinstance(value,dict): return False
    if value.get("schema")!="stegverse.tvc.bea-credential-readiness/v1": return False
    if value.get("provider")!="bea" or value.get("credential_authority")!="TV/TVC": return False
    if value.get("secret_ref")!="vault://tvc/providers/bea/api-key": return False
    for key in ("secret_material_read","secret_material_returned","secret_material_logged",
                "secret_material_hashed","provider_contacted"):
        if value.get(key) is not False: return False
    return value.get("decision") in {"READY","UNAVAILABLE"}


def _census_evidence(output_dir:Path)->dict[str,Any]:
    raw=output_dir/"census_acs_housing_cost_burden.raw"
    candidate_path=output_dir/"census_acs_housing_cost_burden.candidate.json"
    if not raw.is_file() or not candidate_path.is_file():
        raise ValueError("CENSUS_EXACT_CAPTURE_MISSING")
    value=json.loads(candidate_path.read_text(encoding="utf-8"))
    digest=hashlib.sha256(raw.read_bytes()).hexdigest()
    if (value.get("schema")!="stegverse.erl.household-economic-source-candidate/v1"
        or value.get("goal_task_id")!=TASK
        or value.get("inventory_series_id")!="CENSUS_ACS_HOUSING_COST_BURDEN"
        or value.get("required_cost_scope")!="HOUSING_COST_BURDEN_ONLY"
        or value.get("status")!="NORMALIZED_SOURCE_OBSERVATIONS"
        or value.get("finding_authority") is not False
        or value.get("public_activation_authorized") is not False
        or value.get("raw_sha256")!=digest):
        raise ValueError("CENSUS_EXACT_CAPTURE_INVALID")
    observations=value.get("observations")
    if not isinstance(observations,list) or len(observations)!=16:
        raise ValueError("CENSUS_EXPECTED_OBSERVATION_SET_MISSING")
    direct=sum(x.get("evidence_class")=="DIRECT_OBSERVATION" for x in observations if isinstance(x,dict))
    derived=sum(x.get("evidence_class")=="DERIVED_FROM_DIRECT_OBSERVATIONS" for x in observations if isinstance(x,dict))
    if (direct,derived)!=(10,6):raise ValueError("CENSUS_DIRECT_DERIVED_COUNTS_MISMATCH")
    return {"candidate_ref":str(candidate_path.relative_to(ROOT)),"raw_ref":str(raw.relative_to(ROOT)),
            "raw_sha256":digest,"source_vintage":value.get("source_vintage"),
            "acquired_at":value.get("acquired_at"),"direct_count":direct,"derived_count":derived,
            "required_cost_scope":"HOUSING_COST_BURDEN_ONLY","finding_authority":False}


def main()->int:
    inv=json.load(sys.stdin); task=inv.get("task") or {}; epoch=inv.get("heartbeat_epoch")
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK or not isinstance(epoch,int):return 2
    claim=task.get("claim_id"); fence=(task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim,str) or not claim or not isinstance(fence,int):return 3
    rr=roots(); sg=rr.get("StegVerse-Labs/stegfin-governance")
    tvc=rr.get("StegVerse-Labs/TVC"); erl=rr.get("StegVerse-Labs/Executive_Rhetoric_Ledger")
    common={"schema":"stegverse.erl-household-economic-conditions-worker-receipt/v1",
            "task_id":TASK,"heartbeat_epoch":epoch,"claim_id":claim,"fencing_token":fence,
            "credential_authority":"TV/TVC","finding_authority":False,
            "public_activation_authorized":False,"credential_material_present":False,
            "github_token_runtime_authority":"NONE"}
    def finish(state:str,transition:str,seq:int,evidence:dict[str,Any],blocker:dict[str,Any]|None=None)->int:
        record={**common,**evidence,"state":state,"transition_id":transition}
        if blocker:record["blocker"]=blocker
        atomic_write(RECEIPT,record)
        json.dump(response(state,transition,seq,None if state=="COMPLETED" else "HOUSEHOLD_SOURCE_CAPTURE_RETRY",blocker),sys.stdout)
        print()
        return 0
    if not erl or not (erl/"scripts"/"acquire_census_b25140.py").is_file():
        blocker={"dependency_class":"INTERNAL_CAPABILITY","problem_statement":"Existing ERL census acquisition source not locally materialized",
                 "solution_required":True,"may_remain_blocked":False,
                 "workaround_candidates":["refresh already-local canonical source roots"],
                 "next_solution_action":"reconcile existing source-root materialization",
                 "machine_observable_release_condition":"ERL acquire_census_b25140.py exists locally",
                 "github_token_required":False,"non_tv_tvc_secret_or_token_required":False,
                 "third_party_blocker":False,"human_action_required":False}
        return finish("BLOCKED","ERL_CENSUS_SOURCE_NOT_MATERIALIZED",1,{},blocker)
    census_dir=ROOT/"receipts"/"erl-household-economic-conditions"/"census-acs-2024"
    census_dir.mkdir(parents=True,exist_ok=True)
    completed=subprocess.run([sys.executable,str(erl/"scripts"/"acquire_census_b25140.py"),
                 "--year","2024","--output-dir",str(census_dir)],cwd=erl,capture_output=True,text=True,
                 check=False,timeout=600,env=dict(os.environ))
    try:
        if completed.returncode!=0:raise ValueError("CENSUS_ACQUISITION_NONZERO_EXIT")
        census=_census_evidence(census_dir)
    except (ValueError,OSError,json.JSONDecodeError) as exc:
        blocker={"dependency_class":"PUBLIC_SOURCE_EVIDENCE","problem_statement":str(exc),
                 "solution_required":True,"may_remain_blocked":False,
                 "next_solution_action":"inspect exact existing Census source acquisition failure receipt and retest",
                 "machine_observable_release_condition":"Census raw SHA and 10+6 direct/derived candidate validated",
                 "github_token_required":False,"non_tv_tvc_secret_or_token_required":False,
                 "third_party_blocker":False,"human_action_required":False}
        return finish("BLOCKED","CENSUS_EVIDENCE_CAPTURE_FAILED",2,
                      {"census_returncode":completed.returncode},blocker)
    # BEA is optional to the independent Census result. Only fresh same-invocation
    # metadata can trigger the already-existing single-use lease.
    readiness=None
    readiness_state="UNKNOWN_NOT_OBSERVED"
    bea_execution=None
    if sg and (sg/"scripts"/"check_tvc_bea_credential_readiness.py").is_file():
        readiness_path=ROOT/"receipts"/"erl-household-economic-conditions"/"bea-readiness.json"
        readiness_path.unlink(missing_ok=True) # never reuse a prior READY result
        observed=subprocess.run([sys.executable,str(sg/"scripts"/"check_tvc_bea_credential_readiness.py"),
                         "--out",str(readiness_path)],cwd=sg,capture_output=True,text=True,
                         check=False,timeout=60,env=dict(os.environ))
        if readiness_path.is_file():
            try:
                candidate=json.loads(readiness_path.read_text(encoding="utf-8"))
                if _nonsecret_readiness(candidate) and (
                    (observed.returncode==0 and candidate["decision"]=="READY") or
                    (observed.returncode==2 and candidate["decision"]=="UNAVAILABLE")
                ):
                    readiness=candidate
                    readiness_state=candidate["decision"]
            except (ValueError,OSError,json.JSONDecodeError):pass
        if readiness_state=="READY":
            if tvc and (tvc/"scripts"/"tvc_execute_bea_readonly.py").is_file():
                bea_out=ROOT/"receipts"/"erl-household-economic-conditions"/"bea-readonly-result.json"
                bea_out.unlink(missing_ok=True)
                rc,result=run_json([sys.executable,str(tvc/"scripts"/"tvc_execute_bea_readonly.py"),
                            "--readiness-receipt",str(readiness_path),"--out",str(bea_out)],tvc,900)
                if rc==0 and bea_out.is_file():
                    body=json.loads(bea_out.read_text(encoding="utf-8"))
                    if (body.get("schema")=="stegverse.tvc.bea-readonly-execution/v1"
                        and body.get("public_activation_authorized") is False
                        and body.get("credential_material_returned") is False):
                        bea_execution={"state":"NON_AUTHORIZING_RESULT_RETAINED",
                                       "result_ref":str(bea_out.relative_to(ROOT)),
                                       "raw_sha256":(body.get("provider_result") or {}).get("raw_sha256"),
                                       "source_vintage":(body.get("provider_result") or {}).get("source_vintage")}
                    else:bea_execution={"state":"RESULT_INVALID"}
                else:bea_execution={"state":"PROVIDER_USE_FAILED","returncode":rc}
            else:bea_execution={"state":"LOCAL_TVC_EXECUTOR_NOT_MATERIALIZED"}
    return finish("COMPLETED","HOUSEHOLD_ECONOMIC_SOURCE_OBSERVATION_COMPLETE",2,
                  {"census_credential_free":census,"bea_readiness_state":readiness_state,
                   "bea_readiness":readiness,"bea_execution":bea_execution,
                   "authority_effect":"NONE_CANDIDATE_EVIDENCE_ONLY"})

if __name__=="__main__":raise SystemExit(main())
