#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
TASK_ID="SHWP-SV002-SELF-CHARACTERIZATION-001"
CHECKPOINT=f"receipts/sv002-self-characterization/{TASK_ID}.json"
PINS={"TT":"ab60b42934222a2cb5335a5a8194f258a491fc57","RTG":"ca69954cb3dc4ad073c9244e003bc8f0ef3837e2","GTG":"8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225","AE":"53c8eedddc4e54d8fa0660039d65ab9ac63057a1"}

def git_head(p:Path)->str:
    return subprocess.check_output(["git","-C",str(p),"rev-parse","HEAD"],text=True).strip()

def git_commit_exists(p:Path, commit:str)->bool:
    return subprocess.run(["git","-C",str(p),"cat-file","-e",f"{commit}^{commit}"],capture_output=True,text=True,check=False).returncode==0

def candidates(org:str,repo:str,override:str|None=None):
    out=[]
    if override: out.append(Path(override).expanduser())
    home=Path(os.environ.get("HOME",str(Path.home())))
    out += [home/".stegverse/repos"/org/repo,Path("/var/lib/stegverse/source")/org/repo,Path("/srv/stegverse/repos")/org/repo,Path("/opt/stegverse/repos")/org/repo]
    return [p.resolve() for p in out]

def find_repo(org,repo,expected=None,override=None,required=()):
    seen=[]
    for p in candidates(org,repo,override):
        rec={"path":str(p),"present":p.is_dir()}
        if p.is_dir() and all((p/x).is_file() for x in required) and (p/".git").exists():
            try: h=git_head(p)
            except Exception: h=None
            rec["head"]=h
            commit_ok=True if expected is None else git_commit_exists(p,expected)
            if expected is not None: rec["pinned_commit_available"]=commit_ok
            if commit_ok:
                rec["selected"]=True; seen.append(rec); return p,seen
        seen.append(rec)
    return None,seen

def response(state,transition,epoch):
    return {"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,"expected_next_transition":None if state=="COMPLETED" else "SV002_SELF_CHARACTERIZATION_RECHECK","expected_next_earliest_epoch":None if state=="COMPLETED" else epoch+1,"expected_next_latest_epoch":None if state=="COMPLETED" else epoch+1,"checkpoint_ref":CHECKPOINT,"evidence_refs":[CHECKPOINT],"cost_observation":{"hb_transition_count":1,"compute_units":2,"external_cost_usd":0,"task_class":"sv002_self_characterization"}}

def main():
    inv=json.load(sys.stdin); epoch=inv.get("heartbeat_epoch"); task=inv.get("task") or {}; handoff=inv.get("handoff") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or not isinstance(epoch,int): return 2
    if any(str(os.environ.get(x,"")).lower() in {"1","true","yes"} for x in ("GITHUB_ACTIONS","CI","RENDER","VERCEL","CF_PAGES")): return 3
    out=(ROOT/CHECKPOINT); out.parent.mkdir(parents=True,exist_ok=True)
    micro, micro_seen=find_repo("StegVerse-002","micro-node-runtime",override=os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT"),required=("tools/run_self_characterization_principal.py",))
    formal={}; observed={}
    for repo,sha in PINS.items():
        p,seen=find_repo("Admissible-Existence",repo,sha,os.environ.get(f"STEGVERSE_{repo}_ROOT"))
        observed[repo]=seen
        if p: formal[f"Admissible-Existence/{repo}"]=str(p)
    endpoint=os.environ.get("STEGVERSE_SELF_CHAR_MODEL_ENDPOINT","").strip()
    model=os.environ.get("STEGVERSE_SELF_CHAR_MODEL_ID","").strip()
    if not endpoint and os.environ.get("STEGVERSE_OLLAMA_MODEL"):
        endpoint="http://127.0.0.1:11434"; model=os.environ["STEGVERSE_OLLAMA_MODEL"]
    blockers=[]
    if micro is None: blockers.append("MICRO_NODE_RUNTIME_NOT_MATERIALIZED")
    if len(formal)!=4: blockers.append("PINNED_FORMAL_COMMITS_NOT_LOCALLY_AVAILABLE")
    if not endpoint or not model: blockers.append("QUALIFYING_LOCAL_REASONING_ENDPOINT_NOT_OBSERVED")
    if model=="stegverse-reference-lm-v1" or "reference" in model.lower(): blockers.append("REFERENCE_MODEL_NOT_QUALIFYING_PRINCIPAL")
    if blockers:
        receipt={"schema":"stegverse.sv002-self-characterization-worker-receipt/v0.1","task_id":TASK_ID,"state":"BLOCKED","blockers":blockers,"micro_node_candidates":micro_seen,"formal_candidates":observed,"model_id":model or None,"endpoint":endpoint or None,"network_fetch_performed":False,"authority_effect":"NONE"}
        out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print(json.dumps(response("BLOCKED","SV002_SELF_CHARACTERIZATION_BLOCKED",epoch),sort_keys=True)); return 0
    env={"PATH":os.environ.get("PATH",""),"HOME":os.environ.get("HOME",str(Path.home())),"STEGVERSE_FORMAL_ROOTS_JSON":json.dumps(formal),"STEGVERSE_SELF_CHAR_MODEL_ENDPOINT":endpoint,"STEGVERSE_SELF_CHAR_MODEL_ID":model,"STEGVERSE_SELF_CHAR_STATE_ROOT":str(Path(os.environ.get("HOME",str(Path.home())))/".stegverse/self-characterization-001")}
    proc=subprocess.run([sys.executable,str(micro/"tools/run_self_characterization_principal.py")],cwd=micro,env=env,capture_output=True,text=True,timeout=1800)
    state_root=Path(env["STEGVERSE_SELF_CHAR_STATE_ROOT"])
    execution=state_root/"EXPERIMENT_EXECUTION_RECEIPT.json"
    result=json.loads(execution.read_text()) if execution.is_file() else {}
    completed=proc.returncode==0 and result.get("state")=="COMPLETED"
    receipt={"schema":"stegverse.sv002-self-characterization-worker-receipt/v0.1","task_id":TASK_ID,"state":"COMPLETED" if completed else "BLOCKED","principal_returncode":proc.returncode,"principal_result":result,"model_id":model,"endpoint":endpoint,"formal_roots":formal,"state_root":str(state_root),"self_characterization_path":str(state_root/"SELF_CHARACTERIZATION.md") if completed else None,"formal_result_path":str(state_root/"SELF_CHARACTERIZATION_FORMAL.json") if completed else None,"interaction_receipt_chain_path":str(state_root/"INTERACTION_RECEIPT_CHAIN.json") if completed else None,"network_fetch_performed":False,"authority_effect":"NONE"}
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(response("COMPLETED" if completed else "BLOCKED","SV002_SELF_CHARACTERIZATION_COMPLETED" if completed else "SV002_SELF_CHARACTERIZATION_EXECUTION_BLOCKED",epoch),sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
