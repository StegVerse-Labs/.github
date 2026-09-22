#!/usr/bin/env python3
"""Consume the SV002 organization-runtime activation request on a sovereign resident.

This consumer is executed by the existing native HeartBeat-separated
WorkerCoordinator resident runtime. It does not create or require a second
resident executor or resident request. It invokes the current StegVerse-002 rerun
callable from that resident substrate; StegVerse-002 remains the execution owner
and canonical Master Records remains custody/reconstruction authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
REQUEST_REL=Path("control/resident-execution-request.d/sv002-org-runtime-activation-001.json")
RECEIPT_REL=Path("receipts/sovereign-host/sv002-org-runtime-activation.latest.json")
TASK_ID="SHWP-SV002-ORG-RUNTIME-ACTIVATION-001"

def load(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError(f"expected object: {path}")
    return v

def sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def candidates(env_name:str,org:str,repo:str)->list[Path]:
    out=[]
    raw=str(os.getenv(env_name) or "").strip()
    if raw: out.append(Path(raw).expanduser())
    home=Path.home()
    out += [
      home/".stegverse"/"repos"/org/repo,
      Path("/var/lib/stegverse/source")/org/repo,
      Path("/srv/stegverse/repos")/org/repo,
      Path("/opt/stegverse/repos")/org/repo,
    ]
    return [p.resolve() for p in out]

def resolve(env_name:str,org:str,repo:str,required:tuple[str,...])->Path:
    for root in candidates(env_name,org,repo):
        if root.is_dir() and all((root/r).is_file() for r in required):
            return root
    raise RuntimeError(f"local source not materialized: {org}/{repo}")

def parse_last(stdout:str)->dict[str,Any]|None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:v=json.loads(line)
        except Exception:continue
        if isinstance(v,dict):return v
    return None

def consume(source_root:Path,runtime_root:Path,*,runner=subprocess.run)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    request_path=runtime/REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.sv002-org-runtime-activation-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    req=load(request_path)
    expected={
      "schema":"stegverse.resident-execution-request/v1","state":"REQUESTED",
      "request_id":"RESIDENT-EXEC-SV002-ORG-RUNTIME-ACTIVATION-001",
      "task_id":TASK_ID,
      "goal_task_id":"STEGVERSE-002-EXPERIMENT-RERUN-001",
      "cosv_task_vector":"50000000107000",
      "operation":"REQUEST_SELF_CHARACTERIZATION",
      "deterministic_packet_id":"SV002-RERUN-C796D0BFD181CEC5D99E4C23",
      "current_callable_ref":"StegVerse-002/.github:resident-runtime/invoke_sv002_experiment_rerun.py",
      "request_bound_master_records_required":True,
      "request_bound_required_evidence_exact_bytes":True,
      "credential_authority":"TV/TVC",
      "github_token_required":False,"github_token_runtime_authority":"NONE",
      "heartbeat_grants_execution_authority":False,"request_granted_authority":False,
      "network_source_fetch_allowed":False,"authority_effect":"NONE_REQUEST_ONLY",
    }
    for k,v in expected.items():
        if req.get(k)!=v: raise RuntimeError(f"request {k} mismatch")
    request_hash=sha(req)
    receipt_path=runtime/RECEIPT_REL
    if receipt_path.is_file():
        prior=load(receipt_path)
        if prior.get("request_sha256")==request_hash and prior.get("terminal_round_trip_observed") is True:
            return {"schema":prior["schema"],"state":"ALREADY_CONSUMED","request_sha256":request_hash,"runtime_execution_attempted":False,"authority_effect":"NONE"}

    source=source_root.expanduser().resolve()
    if not (source/"workers/canonical_state_transition_custody.py").is_file():
        raise RuntimeError("canonical Master Records custody client not materialized in resident source")
    target_org=resolve(
        "STEGVERSE_SV002_ORG_ROOT","StegVerse-002",".github",
        ("resident-runtime/invoke_sv002_experiment_rerun.py","resident-runtime/activation-manifest.json"),
    )

    env=dict(os.environ)
    for name in ("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","STEGVERSE_GITHUB_TOKEN"):
        env.pop(name,None)
    roots_raw=str(env.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    try:
        roots=json.loads(roots_raw) if roots_raw else {}
    except Exception as exc:
        raise RuntimeError("resident repository roots invalid") from exc
    if not isinstance(roots,dict):
        raise RuntimeError("resident repository roots must be object")
    roots["StegVerse-Labs/.github"]=str(source)
    roots["StegVerse-002/.github"]=str(target_org)
    mr_root=str(env.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT") or "").strip()
    if mr_root:
        roots["master-records/orchestration"]=str(Path(mr_root).expanduser().resolve())
    env["STEGVERSE_REPO_ROOTS_JSON"]=json.dumps(roots,sort_keys=True,separators=(",",":"))
    env["STEGVERSE_SV002_ORG_ROOT"]=str(target_org)
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"

    cmd=[sys.executable,str(target_org/"resident-runtime/invoke_sv002_experiment_rerun.py")]
    completed=runner(cmd,cwd=target_org,capture_output=True,text=True,check=False,env=env,timeout=2300)
    result=parse_last(completed.stdout)
    request_bound_custodied=bool(
      isinstance(result,dict)
      and result.get("goal_task_id")=="STEGVERSE-002-EXPERIMENT-RERUN-001"
      and result.get("cosv_id")=="50000000107000"
      and result.get("packet_id")=="SV002-RERUN-C796D0BFD181CEC5D99E4C23"
      and result.get("experiment_id")=="STEGVERSE-002-SELF-CHARACTERIZATION-001"
      and result.get("operation")=="REQUEST_SELF_CHARACTERIZATION"
      and result.get("invocation_count")==1
      and result.get("manifest_sha256")=="29222a589eb4c2958d2787743e266f067ee07e1373c51f60b553f1f359789828"
      and isinstance(result.get("packet_sha256"),str) and bool(result.get("packet_sha256"))
      and isinstance(result.get("request_sha256"),str) and bool(result.get("request_sha256"))
      and isinstance(result.get("frame_sha256"),str) and bool(result.get("frame_sha256"))
      and result.get("request_bound_claimed") is True
      and result.get("request_bound_master_records_state")=="RECORDED"
      and result.get("request_bound_master_records_reconstruction_status")=="PASS"
      and result.get("request_bound_master_records_required_evidence_validation_status")=="PASS"
      and result.get("request_bound_master_records_required_evidence_count")==1
      and isinstance(result.get("request_bound_master_records_receipt_sha256"),str)
      and result.get("request_bound_master_records_receipt_sha256")
      == result.get("request_bound_master_records_reconstructed_receipt_sha256")
    )
    terminal=False
    receipt={
      "schema":"stegverse.sv002-org-runtime-activation-consumption/v1",
      "state":"ATTEMPT_RECORDED",
      "task_id":TASK_ID,
      "goal_task_id":"STEGVERSE-002-EXPERIMENT-RERUN-001",
      "cosv_task_vector":"50000000107000",
      "request_sha256":request_hash,
      "target_org_root":str(target_org),
      "callable_ref":"resident-runtime/invoke_sv002_experiment_rerun.py",
      "deterministic_packet_id":"SV002-RERUN-C796D0BFD181CEC5D99E4C23",
      "runtime_execution_attempted":True,
      "execution_returncode":completed.returncode,
      "execution_result":result,
      "request_bound_custodied":request_bound_custodied,
      "request_bound_master_records_state":result.get("request_bound_master_records_state") if isinstance(result,dict) else None,
      "request_bound_master_records_reconstruction_status":result.get("request_bound_master_records_reconstruction_status") if isinstance(result,dict) else None,
      "request_bound_master_records_required_evidence_validation_status":result.get("request_bound_master_records_required_evidence_validation_status") if isinstance(result,dict) else None,
      "request_bound_master_records_receipt_sha256":result.get("request_bound_master_records_receipt_sha256") if isinstance(result,dict) else None,
      "request_bound_master_records_reconstructed_receipt_sha256":result.get("request_bound_master_records_reconstructed_receipt_sha256") if isinstance(result,dict) else None,
      "request_bound_master_record_ref":result.get("request_bound_master_record_ref") if isinstance(result,dict) else None,
      "terminal_round_trip_observed":terminal,
      "runtime_substrate":"HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR",
      "second_resident_executor_required":False,
      "second_request_required":False,
      "cross_org_principal_execution":False,
      "github_token_runtime_authority":"NONE",
      "credential_authority":"TV/TVC",
      "master_records_custody_authority":"MASTER_RECORDS",
      "authority_effect":"NONE_REQUEST_CONSUMPTION_ONLY",
    }
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--source-root",type=Path,default=ROOT);ap.add_argument("--runtime-root",type=Path,required=True)
    a=ap.parse_args();r=consume(a.source_root,a.runtime_root);print(json.dumps(r,sort_keys=True));return 0

if __name__=="__main__":raise SystemExit(main())
