#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
from typing import Any

ROOT=Path.cwd().resolve()
TASK="SHWP-STEGFIN-SOVEREIGN-TRADING-001"
RECEIPT=ROOT/"receipts"/"stegfin-sovereign-trading"/f"{TASK}.json"

def atomic_write(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h:
        json.dump(value,h,indent=2,sort_keys=True); h.write("\n"); name=h.name
    os.replace(name,path)

def roots()->list[Path]:
    values:list[Path]=[]
    explicit=os.environ.get("STEGVERSE_STEGFIN_SOURCE_ROOT")
    if explicit:
        values.append(Path(explicit))
    values.extend([
        ROOT/"workloads"/"stegfin-governance",
        Path.home()/".stegverse"/"workloads"/"stegfin-governance",
        Path.home()/".stegverse"/"source"/"stegfin-governance",
        Path("/var/lib/stegverse/workloads/stegfin-governance"),
        Path("/var/lib/stegverse/source/stegfin-governance"),
    ])
    return values

def find_root()->Path|None:
    for p in roots():
        try:r=p.expanduser().resolve()
        except Exception:continue
        if (r/"scripts"/"run_sovereign_trading_activation_round.py").is_file() and (r/"docs"/"STEGFIN_MIRROR_HANDOFF.md").is_file(): return r
    return None

def env(root:Path)->dict[str,str]:
    return {"PATH":os.environ.get("PATH","/usr/bin:/bin"),"PYTHONPATH":str(root),"LANG":"C.UTF-8","LC_ALL":"C.UTF-8"}

def blocker(problem:str,action:str,condition:str)->dict[str,Any]:
    return {"dependency_class":"INTERNAL_CAPABILITY","problem_statement":problem,"solution_required":True,"may_remain_blocked":False,"workaround_candidates":["Resolve the already-released StegFin workload from STEGVERSE_STEGFIN_SOURCE_ROOT or canonical local StegVerse workload/source locations; do not use network source checkout.","Retry on the next admitted heartbeat without widening financial or credential authority."],"next_solution_action":action,"machine_observable_release_condition":condition,"github_token_required":False,"third_party_blocker":False,"human_action_required":False}

def response(state:str,transition:str,seq:int,next_transition:str|None,block:dict[str,Any]|None=None)->dict[str,Any]:
    out={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":seq,"expected_next_transition":next_transition,"expected_next_earliest_epoch":None,"expected_next_latest_epoch":None,"checkpoint_ref":str(RECEIPT.relative_to(ROOT)),"evidence_refs":[str(RECEIPT.relative_to(ROOT)),"StegVerse-Labs/stegfin-governance:scripts/run_sovereign_trading_activation_round.py","master-records/orchestration#23"]}
    if block is not None: out["blocker"]=block
    return out

def main()->int:
    inv=json.load(sys.stdin); task=inv.get("task") or {}; handoff=inv.get("handoff") or {}; epoch=inv.get("heartbeat_epoch")
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK or not isinstance(epoch,int): return 2
    timing=task.get("heartbeat_timing") or {}; claim=task.get("claim_id"); fence=timing.get("fencing_token")
    if not isinstance(claim,str) or not claim or not isinstance(fence,int): return 3
    caps=set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if not {"runtime_observation","bounded_process_execution","durable_state_reconstruction","stegfin_sovereign_internal_trading_activation"}.issubset(caps): return 4
    root=find_root()
    if root is None:
        b=blocker("The released StegFin activation capsule is not locally materialized on the sovereign carrier.","Resolve/materialize the released StegFin workload through canonical local StegVerse source/workload storage.","find_root resolves run_sovereign_trading_activation_round.py and the canonical StegFin handoff")
        durable={"schema":"stegverse.stegfin-sovereign-trading-worker-receipt/v0.2","task_id":TASK,"heartbeat_epoch":epoch,"claim_id":claim,"fencing_token":fence,"state":"BLOCKED","transition_id":"STEGFIN_SOVEREIGN_CAPSULE_NOT_MATERIALIZED","github_token_required":False,"non_tv_tvc_secret_or_token_used":False,"wallet_signing_authority":False,"transaction_broadcast_authority":False,"custody_authority":False,"scale_up_authority":False,"blocker":b}; atomic_write(RECEIPT,durable); json.dump(response("BLOCKED",durable["transition_id"],1,"STEGFIN_SOVEREIGN_TRADING_ACTIVATED",b),sys.stdout); print(); return 0
    with tempfile.TemporaryDirectory(prefix="stegfin-sovereign-worker-") as td:
        output=Path(td)/"result.json"
        cp=subprocess.run([sys.executable,str(root/"scripts"/"run_sovereign_trading_activation_round.py"),"--worker-mode","--output",str(output)],cwd=root,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=180,check=False,env=env(root))
        result=json.loads(output.read_text()) if output.is_file() else None
    completed=cp.returncode==0 and isinstance(result,dict) and result.get("state")=="COMPLETED" and result.get("terminal_result")=="STEGFIN_SOVEREIGN_TRADING_ACTIVATED" and result.get("master_records_reconstruction_pass") is True and result.get("e2_reconstruction_proof_observed") is True
    if completed:
        durable={"schema":"stegverse.stegfin-sovereign-trading-worker-receipt/v0.2","task_id":TASK,"heartbeat_epoch":epoch,"claim_id":claim,"fencing_token":fence,"state":"COMPLETED","transition_id":"STEGFIN_SOVEREIGN_TRADING_ACTIVATED","round_id":result.get("round_id"),"packet_hash":result.get("packet_hash"),"reconstruction_hash":result.get("reconstruction_hash"),"reconstruction_binding_hash":result.get("reconstruction_binding_hash"),"internal_settlement_pass":True,"master_records_reconstruction_pass":True,"e2_reconstruction_proof_observed":True,"github_token_required":False,"non_tv_tvc_secret_or_token_used":False,"wallet_signing_authority":False,"transaction_broadcast_authority":False,"custody_authority":False,"scale_up_authority":False}; atomic_write(RECEIPT,durable); json.dump(response("COMPLETED",durable["transition_id"],2,None),sys.stdout); print(); return 0
    reason=(result or {}).get("terminal_result") if isinstance(result,dict) else "ACTIVATION_RUNNER_FAILED"
    b=blocker("The internal sovereign activation round has not yet produced exact Master Records reconstruction and E2 binding.","Materialize the released Master Records reconstruction workload locally and retry the same fenced activation task.","runner exits 0 with STEGFIN_SOVEREIGN_TRADING_ACTIVATED and exact reconstruction/E2 hashes")
    durable={"schema":"stegverse.stegfin-sovereign-trading-worker-receipt/v0.2","task_id":TASK,"heartbeat_epoch":epoch,"claim_id":claim,"fencing_token":fence,"state":"BLOCKED","transition_id":"STEGFIN_SOVEREIGN_RECONSTRUCTION_REQUIRED","runner_result":reason,"github_token_required":False,"non_tv_tvc_secret_or_token_used":False,"wallet_signing_authority":False,"transaction_broadcast_authority":False,"custody_authority":False,"scale_up_authority":False,"blocker":b}; atomic_write(RECEIPT,durable); json.dump(response("BLOCKED",durable["transition_id"],1,"STEGFIN_SOVEREIGN_TRADING_ACTIVATED",b),sys.stdout); print(); return 0

if __name__=="__main__": raise SystemExit(main())
