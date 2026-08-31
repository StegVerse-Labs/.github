#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = Path("scripts/run_worker_runtime.py")
REGISTRY_REL = Path("control/worker-registry.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
RECEIPT_REL = Path("receipts/sovereign-host/sv-dn1-publication-continuation.latest.json")

TASKS = (
    "SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001",
    "SV-DN1-PUBLICATION-OBSERVER-001",
)

HOSTED_ENV = (
    "GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN",
)
NONSECRET_ENV = (
    "PATH","HOME","LANG","LC_ALL","SSL_CERT_FILE","SSL_CERT_DIR","XDG_STATE_HOME","XDG_CONFIG_HOME",
    "STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_SV_DN1_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION",
)
Runner = Callable[..., subprocess.CompletedProcess[str]]

def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"","0","false","no"}

def clean_exec_env(values: Mapping[str,str] | None = None) -> dict[str,str]:
    source = dict(os.environ if values is None else values)
    hosted=[n for n in HOSTED_ENV if truthy(source.get(n))]
    creds=[n for n in FORBIDDEN_CREDENTIAL_ENV if truthy(source.get(n))]
    if hosted:
        raise RuntimeError("hosted execution cannot continue SV-DN-1 publication: "+",".join(sorted(hosted)))
    if creds:
        raise RuntimeError("credential-bearing environment forbidden for SV-DN-1 publication continuation: "+",".join(sorted(creds)))
    env={n:source[n] for n in NONSECRET_ENV if source.get(n)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env

def default_runtime_root(values: Mapping[str,str] | None = None) -> Path:
    env=os.environ if values is None else values
    override=str(env.get("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    base=Path(str(env.get("XDG_STATE_HOME") or (Path.home()/".local"/"state")))
    return (base/"stegverse"/"heartbeat-runtime").expanduser().resolve()

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value

def task_row(registry:Mapping[str,Any],task_id:str)->dict[str,Any]|None:
    rows=[r for r in registry.get("tasks",[]) if isinstance(r,dict) and r.get("task_id")==task_id]
    if len(rows)>1:
        raise RuntimeError(f"duplicate runtime task: {task_id}")
    return dict(rows[0]) if rows else None

def bound(name:str,default:Path,env:Mapping[str,str])->Path:
    raw=str(env.get(name) or "").strip()
    return Path(raw).expanduser().resolve() if raw else default.expanduser().resolve()

def validate_receipt(task_id:str, env:Mapping[str,str])->dict[str,Any]:
    if task_id=="SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001":
        root=Path.home()/".stegverse"/"transport"/"sv-dn1-repository-persistence"
        path=root/"receipts/latest.json"
        expected={
            "schema":"stegverse.sv-dn1.repository-persistence-dispatch-receipt/v1",
            "state":"COMPLETE",
            "transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED",
            "credential_used":False,
            "repository_mutation_performed_by_worker":False,
            "merge_performed":False,
            "deployment_performed":False,
            "authority_effect":"NONE_REQUEST_STAGING_ONLY",
        }
    else:
        root=Path.home()/".stegverse"/"state"/"sv-dn1-publication-observer"
        path=root/"receipts/latest.json"
        expected={
            "schema":"stegverse.sv-dn1.publication-observation/v1",
            "state":"COMPLETE",
            "transition_id":"SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED",
            "all_public_artifacts_observed":True,
            "exact_bytes_preserved":True,
            "credential_used":False,
            "repository_writeback_performed":False,
            "deployment_performed":False,
            "authority_effect":"NONE_PUBLICATION_OBSERVATION_ONLY",
        }
    if not path.is_file():
        raise RuntimeError(f"{task_id}: durable receipt missing: {path}")
    receipt=load(path)
    bad=[f"{k}={receipt.get(k)!r}, expected {v!r}" for k,v in expected.items() if receipt.get(k)!=v]
    if bad:
        raise RuntimeError(f"{task_id}: durable receipt mismatch: "+"; ".join(bad))
    return {"task_id":task_id,"receipt_path":str(path)}

def atomic(path:Path,value:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name("."+path.name+".tmp")
    tmp.write_text(json.dumps(dict(value),indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def execute(runtime_root:Path,*,runner:Runner=subprocess.run,env:Mapping[str,str]|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    safe=clean_exec_env(values)
    runtime=runtime_root.expanduser().resolve()
    if not (runtime/CARRIER_REL).is_file():
        return {"schema":"stegverse.sv-dn1.publication-continuation/v1","state":"HANDOFF_READY","transition_id":"SV_DN1_PUBLICATION_CARRIER_REFERENCE_PENDING","next_task":TASKS[0],"authority_effect":"NONE"}
    runner_path=runtime/RUNNER_REL; registry_path=runtime/REGISTRY_REL
    if not runner_path.is_file() or not registry_path.is_file():
        raise RuntimeError("targeted WorkerCoordinator runtime surfaces missing")
    completed_tasks=[]; results=[]
    for task_id in TASKS:
        registry=load(registry_path); row=task_row(registry,task_id)
        if row is not None and row.get("state")=="COMPLETED":
            validated=validate_receipt(task_id,values)
            completed_tasks.append(task_id);results.append({"task_id":task_id,"execution_attempted":False,"registry_state":"COMPLETED","durable_receipt":validated})
            continue
        if row is not None and row.get("state") in {"ACTIVE","BLOCKED"}:
            return {"schema":"stegverse.sv-dn1.publication-continuation/v1","state":"HANDOFF_READY","transition_id":"SV_DN1_PUBLICATION_EXISTING_TASK_LIFECYCLE_MUST_RESOLVE","completed_tasks":completed_tasks,"next_task":task_id,"task_state":row.get("state"),"authority_effect":"NONE"}
        command=[sys.executable,str(runner_path),"--root",str(runtime),"--task-id",task_id]
        proc=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=safe,timeout=1200)
        registry=load(registry_path); row=task_row(registry,task_id); state=None if row is None else row.get("state")
        result={"task_id":task_id,"execution_attempted":True,"returncode":proc.returncode,"registry_state":state,"stderr_tail":(proc.stderr or "")[-1200:]}
        results.append(result)
        if proc.returncode!=0 or state!="COMPLETED":
            return {"schema":"stegverse.sv-dn1.publication-continuation/v1","state":"HANDOFF_READY","transition_id":"SV_DN1_PUBLICATION_STEP_NOT_TERMINAL","completed_tasks":completed_tasks,"next_task":task_id,"task_state":state,"task_results":results,"authority_effect":"NONE"}
        try:
            result["durable_receipt"]=validate_receipt(task_id,values)
        except Exception as exc:
            result["durable_receipt_error"]=str(exc)
            return {"schema":"stegverse.sv-dn1.publication-continuation/v1","state":"BLOCKED","transition_id":"SV_DN1_PUBLICATION_DURABLE_RECEIPT_MISMATCH","completed_tasks":completed_tasks,"next_task":task_id,"task_results":results,"authority_effect":"NONE"}
        completed_tasks.append(task_id)
    receipt={
        "schema":"stegverse.sv-dn1.publication-continuation/v1",
        "state":"COMPLETE",
        "transition_id":"SV_DN1_PUBLICATION_CONTINUATION_COMPLETE",
        "completed_tasks":completed_tasks,
        "next_task":None,
        "credential_authority":"TV/TVC",
        "github_token_required":False,
        "repository_mutation_performed_by_continuation":False,
        "merge_performed":False,
        "deployment_performed":False,
        "public_exact_bytes_observed":True,
        "authority_effect":"NONE_ORCHESTRATION_ONLY",
    }
    atomic(runtime/RECEIPT_REL,receipt)
    return receipt

def main()->int:
    parser=argparse.ArgumentParser(description="Run the bounded SV-DN-1 post-analysis publication continuation.")
    parser.add_argument("--runtime-root",type=Path,default=default_runtime_root())
    args=parser.parse_args()
    try:
        result=execute(args.runtime_root)
    except Exception as exc:
        result={"schema":"stegverse.sv-dn1.publication-continuation/v1","state":"BLOCKED","transition_id":"SV_DN1_PUBLICATION_CONTINUATION_BLOCKED","error":str(exc),"authority_effect":"NONE"}
    print(json.dumps(result,sort_keys=True))
    return 0 if result.get("state") in {"COMPLETE","HANDOFF_READY"} else 1

if __name__=="__main__":
    raise SystemExit(main())
