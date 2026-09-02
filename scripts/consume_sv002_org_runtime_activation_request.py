#!/usr/bin/env python3
"""Consume the SV002 organization-runtime activation request on a sovereign resident.

This consumer is executed by the existing native HeartBeat-separated
WorkerCoordinator resident runtime. It does not create or require a second
resident executor. It invokes the bounded StegVerse-org SV002 round-trip
entrypoint directly from that resident substrate; the source org boundary remains
StegVerse-org and the target StegVerse-002 org still owns principal execution.
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
      "task_id":TASK_ID,"credential_authority":"TV/TVC",
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

    source_org=resolve("STEGVERSE_ORG_CONTROL_ROOT","StegVerse-org",".github",("resident-runtime/run_sv002_self_characterization_roundtrip.py",))
    target_org=resolve("STEGVERSE_SV002_ORG_ROOT","StegVerse-002",".github",("resident-runtime/self_characterization_surface.py",))
    sdk=resolve("STEGVERSE_SDK_SOURCE_ROOT","StegVerse-org","StegVerse-SDK",("stegverse/external_interlock_bootstrap.py",))
    principal=resolve("STEGVERSE_MICRO_NODE_RUNTIME_ROOT","StegVerse-002","micro-node-runtime",("tools/run_self_characterization_principal.py","experiments/self-characterization-001/EXPERIMENT_CONTRACT.v0.3.json"))

    env=dict(os.environ)
    for name in ("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","STEGVERSE_GITHUB_TOKEN"):
        env.pop(name,None)
    env["STEGVERSE_ORG_CONTROL_ROOT"]=str(source_org)
    env["STEGVERSE_SV002_ORG_ROOT"]=str(target_org)
    env["STEGVERSE_SDK_SOURCE_ROOT"]=str(sdk)
    env["STEGVERSE_MICRO_NODE_RUNTIME_ROOT"]=str(principal)
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"

    cmd=[sys.executable,str(source_org/"resident-runtime/run_sv002_self_characterization_roundtrip.py"),"--authority-ref","SDK_EXTERNAL_EVALUATOR"]
    completed=runner(cmd,cwd=source_org,capture_output=True,text=True,check=False,env=env,timeout=2300)
    result=parse_last(completed.stdout)
    terminal=bool(
      completed.returncode==0
      and isinstance(result,dict)
      and result.get("experiment_id")=="STEGVERSE-002-SELF-CHARACTERIZATION-001"
      and result.get("principal_execution_owner")=="StegVerse-002/.github"
      and result.get("cross_organization_principal_execution") is False
    )
    receipt={
      "schema":"stegverse.sv002-org-runtime-activation-consumption/v1",
      "state":"COMPLETED" if terminal else "ATTEMPT_RECORDED",
      "task_id":TASK_ID,
      "request_sha256":request_hash,
      "source_org_root":str(source_org),
      "target_org_root":str(target_org),
      "sdk_root":str(sdk),
      "principal_root":str(principal),
      "runtime_execution_attempted":True,
      "execution_returncode":completed.returncode,
      "execution_result":result,
      "terminal_round_trip_observed":terminal,
      "runtime_substrate":"HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR",
      "second_resident_executor_required":False,
      "cross_org_principal_execution":False,
      "github_token_runtime_authority":"NONE",
      "credential_authority":"TV/TVC",
      "authority_effect":"NONE_REQUEST_CONSUMPTION_ONLY",
    }
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--source-root",type=Path,default=ROOT);ap.add_argument("--runtime-root",type=Path,required=True)
    a=ap.parse_args();r=consume(a.source_root,a.runtime_root);print(json.dumps(r,sort_keys=True));return 0

if __name__=="__main__":raise SystemExit(main())
