#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001"
WORKER_ID="stegverse001-bounded-autonomy-runtime-worker"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
DEFAULT_LEASE=Path.home()/".stegverse/autonomy/stegverse001/lease.active.json"
STATE_ROOT=Path.home()/".stegverse/state/stegverse001-bounded-autonomy"

class LeasePending(RuntimeError): pass

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def canonical(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v:Any)->str: return "sha256:"+hashlib.sha256(canonical(v)).hexdigest()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("expected JSON object")
    return v
def response(state,transition,**extra):
    x={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,
       "credential_authority":"TV/TVC","github_token_used":False,"repository_writeback_performed":False}
    x.update(extra); return x

def validate_invocation(inv:Mapping[str,Any])->dict[str,Any]:
    if inv.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("unexpected invocation schema")
    task=inv.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID: raise RuntimeError("task/worker identity mismatch")
    if not task.get("claim_id"): raise RuntimeError("WorkerCoordinator claim required")
    if not isinstance((task.get("heartbeat_timing") or {}).get("fencing_token"),int): raise RuntimeError("fresh fencing token required")
    auth=(inv.get("handoff") or {}).get("authority") or {}
    if auth.get("credential_authority")!="TV/TVC" or auth.get("github_token_required") is not False:
        raise RuntimeError("authority boundary drift")
    if auth.get("sovereign_authority") is not False or auth.get("self_accreditation_authority") is not False:
        raise RuntimeError("sovereignty/self-accreditation boundary drift")
    return dict(task)

def parse_time(value:str)->datetime:
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None: raise RuntimeError("lease expiry must be timezone-aware")
    return t

def validate_lease(p:Path)->dict[str,Any]:
    if not p.is_file(): raise LeasePending(f"external autonomy lease not present: {p}")
    v=load(p)
    required={
      "schema":"stegverse.stegverse001.bounded-autonomy-lease/v1",
      "entity_id":"StegVerse-001",
      "entity_alias":"Beta_Orionis",
      "lease_state":"ACTIVE",
      "credential_authority":"TV/TVC",
      "receipt_required":True,
      "denial_reachable_required":True,
      "denial_reachable":True,
      "self_accreditation_allowed":False,
      "sovereign_authority_granted":False,
      "authority_effect":"BOUNDED_PREAUTHORIZED_TRANSITION_CLASSES_ONLY",
    }
    for k,x in required.items():
        if v.get(k)!=x: raise RuntimeError(f"lease {k} mismatch")
    if v.get("issuer")!="TV/TVC": raise RuntimeError("lease issuer must be TV/TVC")
    if parse_time(str(v.get("expires_at"))) <= datetime.now(timezone.utc): raise RuntimeError("lease expired")
    allowed=set(v.get("allowed_transition_classes") or [])
    needed={"AUTONOMOUS_TASK_DISCOVERY","LOCAL_STATE_OBSERVATION","RECEIPT_EMISSION"}
    if not needed.issubset(allowed): raise RuntimeError("lease lacks required transition classes")
    forbidden=set(v.get("forbidden_transition_classes") or [])
    if not {"SELF_ACCREDITATION","SOVEREIGN_AUTHORITY_CHANGE","FINANCIAL_BINDING"}.issubset(forbidden):
        raise RuntimeError("lease forbidden-transition floor incomplete")
    return v

def runtime_root()->Path:
    override=os.getenv("STEGVERSE_HEARTBEAT_ROOT")
    if override: return Path(override).expanduser().resolve()
    return (Path.home()/".local/state/stegverse/heartbeat-runtime").resolve()

def run_cycle(task:dict[str,Any], lease:dict[str,Any], lease_path:Path)->dict[str,Any]:
    root=runtime_root()
    carrier=root/"control/heartbeat-carrier-runtime-state.json"
    worker=root/"control/worker-runtime-state.json"
    if not carrier.is_file() or not worker.is_file():
        raise LeasePending("resident carrier/worker continuity state not yet available")
    carrier_obj=load(carrier); worker_obj=load(worker)
    candidate={
      "schema":"stegverse.stegverse001.autonomous-task-candidate/v1",
      "candidate_id":"SV001-CONTINUITY-AUDIT-001",
      "discovered_by":"StegVerse-001/Beta_Orionis",
      "discovery_basis":["carrier_state_present","worker_state_present"],
      "goal":"verify current resident continuity and emit a bounded audit receipt",
      "authority_effect":"NONE_CANDIDATE_ONLY"
    }
    plan={
      "schema":"stegverse.stegverse001.autonomy-plan/v1",
      "candidate_id":candidate["candidate_id"],
      "steps":[
        {"sequence":1,"transition_class":"LOCAL_STATE_OBSERVATION","effect":"READ_ONLY"},
        {"sequence":2,"transition_class":"RECEIPT_EMISSION","effect":"LOCAL_RECEIPT_ONLY"}
      ],
      "lease_id":lease.get("lease_id"),
      "denial_reachable":True,
      "authority_widening":False
    }
    receipt={
      "schema":"stegverse.stegverse001.bounded-autonomy-cycle-receipt/v1",
      "state":"COMPLETED",
      "transition_id":"SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED",
      "entity_id":"StegVerse-001","entity_alias":"Beta_Orionis",
      "task_id":TASK_ID,
      "claim_id":task.get("claim_id"),
      "fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
      "lease_id":lease.get("lease_id"),
      "lease_sha256":sha(lease),
      "lease_ref":str(lease_path),
      "candidate_task":candidate,
      "plan":plan,
      "observations":{
        "carrier_state_sha256":sha(carrier_obj),
        "worker_state_sha256":sha(worker_obj),
        "carrier_epoch":carrier_obj.get("epoch"),
        "worker_observation_mode":worker_obj.get("observation_mode")
      },
      "authorized_execution":True,
      "self_directed_task_discovery":True,
      "autonomous_plan_selection":True,
      "external_side_effects":False,
      "network_access_performed":False,
      "repository_writeback_performed":False,
      "financial_binding_performed":False,
      "credential_created_or_used":False,
      "denial_reachable_at_commit":True,
      "self_accreditation":False,
      "sovereign_authority_claimed":False,
      "master_records_custody":"PENDING",
      "sv002_adversarial_observation":"PENDING",
      "completed_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
      "authority_effect":"BOUNDED_LOCAL_AUTONOMY_ONLY"
    }
    receipt["receipt_hash"]=sha(receipt)
    out=STATE_ROOT/"receipts/latest.json"; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (STATE_ROOT/"plans").mkdir(parents=True,exist_ok=True)
    (STATE_ROOT/"plans/latest.json").write_text(json.dumps(plan,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main():
    try:
        inv=json.loads(sys.stdin.readline())
        if any(truthy(os.getenv(k)) for k in HOSTED): raise RuntimeError("hosted runtime forbidden")
        if any(truthy(os.getenv(k)) for k in FORBIDDEN): raise RuntimeError("credential-bearing environment forbidden")
        task=validate_invocation(inv)
        lease_path=Path(os.getenv("STEGVERSE_SV001_AUTONOMY_LEASE") or DEFAULT_LEASE).expanduser().resolve()
        lease=validate_lease(lease_path)
        receipt=run_cycle(task,lease,lease_path)
        print(json.dumps(response("COMPLETED","SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED",
          evidence_refs=[str(STATE_ROOT/"receipts/latest.json")],result=receipt),sort_keys=True)); return 0
    except LeasePending as exc:
        print(json.dumps(response("HANDOFF_READY","SV001_BOUNDED_AUTONOMY_PREREQUISITE_PENDING",
          blocker={"dependency_class":"EXTERNAL_BOUNDED_AUTONOMY_LEASE_OR_RESIDENT_CONTINUITY",
                   "problem_statement":str(exc),"solution_required":True,"may_remain_blocked":False,
                   "human_action_required":False,"second_machine_required":False,"github_token_required":False}),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps(response("BLOCKED","SV001_BOUNDED_AUTONOMY_FAIL_CLOSED",error=str(exc)),sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
