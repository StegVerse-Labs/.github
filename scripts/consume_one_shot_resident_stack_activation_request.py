#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any, Callable, Mapping

REQUEST_REL=Path("control/resident-execution-request.d/one-shot-resident-stack-activation-001.json")
RECEIPT_REL=Path("receipts/sovereign-host/one-shot-resident-stack-activation-request-consumption.latest.json")
TASK_ID="SHWP-ONE-SHOT-RESIDENT-STACK-ACTIVATION-001"
Runner=Callable[...,subprocess.CompletedProcess[str]]

ENV_KEYS={
  "llm":"STEGVERSE_LLM_ADAPTER_ROOT",
  "stegos":"STEGVERSE_STEGOS_ROOT",
  "kv":"STEGVERSE_KV_SOURCE_ROOT",
  "healer":"STEGVERSE_HEALER_ROOT",
  "tv":"STEGVERSE_TV_ROOT",
  "tvc":"STEGVERSE_TVC_ROOT",
  "master_records":"STEGVERSE_MASTER_RECORDS_ROOT",
  "micro_node":"STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
  "tt":"STEGVERSE_TT_ROOT",
  "rtg":"STEGVERSE_RTG_ROOT",
  "gtg":"STEGVERSE_GTG_ROOT",
  "ae":"STEGVERSE_AE_ROOT",
}
REPO_KEYS={
  "llm":"StegVerse-org/LLM-adapter",
  "stegos":"StegVerse-Labs/StegOS",
  "healer":"StegVerse-Labs/StegVerse-Healer",
  "tv":"StegVerse-Labs/TV",
  "tvc":"StegVerse-Labs/TVC",
  "master_records":"master-records/orchestration",
  "micro_node":"StegVerse-002/micro-node-runtime",
  "tt":"Admissible-Existence/TT",
  "rtg":"Admissible-Existence/RTG",
  "gtg":"Admissible-Existence/GTG",
  "ae":"Admissible-Existence/AE",
}
REQUIRED_FILES={
  "llm":"scripts/stegdeploy_bootstrap.py",
  "stegos":"stegos/intr_backbone.py",
  "kv":"runtime/kv_interlock_endpoint.py",
  "healer":"app/dispatch_orchestrators.py",
  "tv":"scripts/tv_run_resident_operational_proof.py",
  "tvc":"tools/hil_intr_lifecycle_intake.py",
  "master_records":"scripts/watch_stegverse001_autonomy_receipt.py",
  "micro_node":"tools/run_self_characterization_principal.py",
}

def stable(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError("expected JSON object")
    return value

def parse_last_json(stdout:str)->dict[str,Any]|None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try: value=json.loads(line)
        except Exception: continue
        if isinstance(value,dict): return value
    return None

def repo_roots(values:Mapping[str,str])->dict[str,Path]:
    raw=str(values.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if not raw: return {}
    try: obj=json.loads(raw)
    except Exception: return {}
    if not isinstance(obj,dict): return {}
    out={}
    for key,val in obj.items():
        if isinstance(key,str) and isinstance(val,str) and val.strip():
            out[key]=Path(val).expanduser().resolve()
    return out

def resolve_roots(values:Mapping[str,str]|None=None)->tuple[dict[str,Path],list[str]]:
    env=dict(os.environ if values is None else values)
    mapped=repo_roots(env)
    roots={}
    missing=[]
    for name,env_key in ENV_KEYS.items():
        raw=str(env.get(env_key) or "").strip()
        if not raw and name=="master_records":
            raw=str(env.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT") or "").strip()
        if raw:
            candidate=Path(raw).expanduser().resolve()
        elif name in REPO_KEYS and REPO_KEYS[name] in mapped:
            candidate=mapped[REPO_KEYS[name]]
        else:
            missing.append(name); continue
        required_rel=REQUIRED_FILES.get(name)
        if required_rel:
            required=candidate/required_rel
            if not required.is_file():
                missing.append(name); continue
        else:
            if not (candidate/".git").is_dir():
                missing.append(name); continue
        roots[name]=candidate
    return roots,missing

def consume(source_root:Path,runtime_root:Path,runner:Runner=subprocess.run,env:Mapping[str,str]|None=None)->dict[str,Any]:
    source=source_root.resolve(); runtime=runtime_root.resolve()
    request_path=runtime/REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.resident-execution-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    req=load(request_path)
    if req.get("schema")!="stegverse.resident-execution-request/v1" or req.get("task_id")!=TASK_ID or req.get("state")!="REQUESTED":
        raise RuntimeError("one-shot resident stack request contract mismatch")
    rh=stable(req)
    receipt_path=runtime/RECEIPT_REL
    if receipt_path.is_file():
        old=load(receipt_path)
        if old.get("request_sha256")==rh and old.get("activation_complete") is True:
            return {
              "schema":"stegverse.resident-execution-request-consumption/v1",
              "state":"ALREADY_CONSUMED","request_id":req.get("request_id"),"request_sha256":rh,
              "task_id":TASK_ID,"runtime_execution_attempted":False,"activation_complete":True,
              "exactly_once_after_complete":True,"request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"
            }
    roots,missing=resolve_roots(env)
    if missing:
        out={
          "schema":"stegverse.resident-execution-request-consumption/v1","state":"SOURCE_ROOTS_PENDING",
          "request_id":req.get("request_id"),"request_sha256":rh,"task_id":TASK_ID,
          "runtime_execution_attempted":False,"activation_complete":False,"retry_allowed":True,
          "missing_source_roots":sorted(missing),"network_source_fetch_performed":False,
          "request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"
        }
        receipt_path.parent.mkdir(parents=True,exist_ok=True)
        receipt_path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        return out
    script=runtime/"scripts/activate_resident_stack.py"
    if not script.is_file():
        raise RuntimeError("one-shot resident stack activator not materialized")
    command=[
      sys.executable,str(script),
      "--source-root",str(source),
      "--llm-adapter-root",str(roots["llm"]),
      "--stegos-root",str(roots["stegos"]),
      "--kv-source-root",str(roots["kv"]),
      "--healer-root",str(roots["healer"]),
      "--tv-root",str(roots["tv"]),
      "--tvc-root",str(roots["tvc"]),
      "--master-records-root",str(roots["master_records"]),
      "--micro-node-root",str(roots["micro_node"]),
      "--tt-root",str(roots["tt"]),
      "--rtg-root",str(roots["rtg"]),
      "--gtg-root",str(roots["gtg"]),
      "--ae-root",str(roots["ae"]),
      "--receipt-path",str(runtime/"receipts/sovereign-host/resident-stack-activation.latest.json"),
    ]
    completed=runner(command,cwd=runtime,capture_output=True,text=True,check=False,timeout=7200,env=dict(os.environ if env is None else env))
    result=parse_last_json(completed.stdout)
    done=isinstance(result,dict) and result.get("state")=="COMPLETE"
    out={
      "schema":"stegverse.resident-execution-request-consumption/v1",
      "state":"COMPLETED" if done else "ATTEMPT_RECORDED",
      "request_id":req.get("request_id"),"request_sha256":rh,"task_id":TASK_ID,
      "runtime_execution_attempted":True,"execution_returncode":completed.returncode,
      "execution_result":result,"activation_complete":done,"retry_allowed":not done,
      "exactly_once_after_complete":True,"network_source_fetch_performed":False,
      "request_granted_authority":False,"github_token_runtime_authority":"NONE",
      "credential_authority":"TV/TVC","authority_effect":"NONE_REQUEST_ONLY"
    }
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    return out

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--runtime-root",type=Path,required=True)
    a=p.parse_args()
    try: out=consume(a.source_root,a.runtime_root)
    except Exception as exc:
        print(json.dumps({"schema":"stegverse.resident-execution-request-consumption/v1","state":"BLOCKED","reason":str(exc),"runtime_execution_attempted":False,"authority_effect":"NONE"},sort_keys=True)); return 2
    print(json.dumps(out,sort_keys=True))
    return 0 if out["state"] in {"NO_REQUEST","SOURCE_ROOTS_PENDING","ATTEMPT_RECORDED","COMPLETED","ALREADY_CONSUMED"} else 1

if __name__=="__main__": raise SystemExit(main())
