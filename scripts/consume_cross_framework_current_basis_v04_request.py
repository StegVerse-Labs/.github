#!/usr/bin/env python3
"""Consume the bounded current-basis v0.4 resident execution request."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/cross-framework-current-basis-v04-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/cross-framework-current-basis-v04-request-consumption.latest.json")
TARGET_TASK = "SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
MINIMUM_FENCE_EXCLUSIVE = 22
FROZEN_SHA256 = "07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f"
FROZEN_BLOB = "59d818a15fc7be732c97dae7d2174d8cfe9a7bab"

HOSTED_ENV = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_SECRET_ENV = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)
NONSECRET_ENV = (
    "PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_SDK_SOURCE_ROOT","STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT","STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"","0","false","no"}


def load_json(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def validate_request(request: Mapping[str,Any]) -> None:
    required={
        "schema":"stegverse.resident-execution-request/v1",
        "state":"REQUESTED","task_id":TARGET_TASK,"mode":TARGET_MODE,"entrypoint":TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive":MINIMUM_FENCE_EXCLUSIVE,"credential_authority":"TV/TVC",
        "github_token_required":False,"github_token_runtime_authority":"NONE",
        "heartbeat_grants_execution_authority":False,"second_machine_required":False,
        "network_source_fetch_allowed":False,"request_granted_authority":False,
        "provider_credential_material_allowed":False,"authority_effect":"NONE_REQUEST_ONLY",
        "frozen_manifest_sha256":FROZEN_SHA256,"frozen_manifest_git_blob_sha1":FROZEN_BLOB,
    }
    for key,expected in required.items():
        if request.get(key)!=expected:
            raise RuntimeError(f"current-basis v0.4 resident execution request {key} mismatch")
    if not isinstance(request.get("request_id"),str) or not request["request_id"].strip():
        raise RuntimeError("current-basis v0.4 resident request_id missing")


def clean_exec_env(source: Mapping[str,str] | None=None) -> dict[str,str]:
    values=dict(os.environ if source is None else source)
    hosted=[name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume current-basis sovereign request: "+",".join(sorted(hosted)))
    env={name:values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN_SECRET_ENV:
        env.pop(name,None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env


def previously_consumed(runtime: Path, request: Mapping[str,Any], request_hash: str) -> bool:
    path=runtime/CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt=load_json(path)
    except Exception:
        return False
    result=receipt.get("execution_result")
    return bool(
        receipt.get("request_id")==request.get("request_id")
        and receipt.get("request_sha256")==request_hash
        and receipt.get("runtime_execution_attempted") is True
        and isinstance(result,dict)
        and result.get("task_id")==TARGET_TASK
        and result.get("state")=="COMPLETED"
    )


def parse_last_json(stdout: str) -> dict[str,Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value=json.loads(line)
        except Exception:
            continue
        if isinstance(value,dict):
            return value
    return None


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str,str] | None=None) -> dict[str,Any]:
    source=source_root.expanduser().resolve()
    runtime=runtime_root.expanduser().resolve()
    request_path=runtime/REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.cross-framework-current-basis-v04-resident-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}

    request=load_json(request_path)
    validate_request(request)
    request_hash=stable_hash(request)
    if previously_consumed(runtime,request,request_hash):
        return {"schema":"stegverse.cross-framework-current-basis-v04-resident-request-consumption/v1","state":"ALREADY_CONSUMED","request_id":request["request_id"],"request_sha256":request_hash,"runtime_execution_attempted":False,"authority_effect":"NONE"}

    entrypoint=runtime/TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"resident execution bridge missing: {entrypoint}")
    command=[sys.executable,str(entrypoint),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",TARGET_TASK]
    completed=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=clean_exec_env(env),timeout=1200)
    result=parse_last_json(completed.stdout)
    bridge_valid=bool(
        isinstance(result,dict)
        and result.get("mode")==TARGET_MODE
        and result.get("task_id")==TARGET_TASK
        and result.get("runtime_execution_attempted") is True
        and result.get("network_fetch_performed") is False
        and result.get("github_token_runtime_authority")=="NONE"
        and result.get("credential_authority")=="TV/TVC"
        and result.get("second_machine_required") is False
        and result.get("authority_effect")=="EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"
    )
    terminal=bool(bridge_valid and result.get("state")=="COMPLETED")
    state="COMPLETED" if terminal else ("ATTEMPT_RECORDED" if bridge_valid else "FAIL_CLOSED")
    receipt={
        "schema":"stegverse.cross-framework-current-basis-v04-resident-request-consumption/v1",
        "state":state,"request_id":request["request_id"],"request_sha256":request_hash,
        "task_id":TARGET_TASK,"mode":TARGET_MODE,"command":command,
        "execution_returncode":completed.returncode,"execution_result_observed":isinstance(result,dict),
        "execution_result":result,"bridge_contract_valid":bridge_valid,"runtime_execution_attempted":True,
        "request_granted_authority":False,"activation_claimed":terminal,
        "heartbeat_grants_execution_authority":False,"github_token_required":False,
        "github_token_runtime_authority":"NONE","credential_authority":"TV/TVC",
        "provider_credential_material_allowed":False,"second_machine_required":False,
        "network_source_fetch_performed":False,"publication_authority":False,
        "authority_effect":"NONE_REQUEST_ONLY"
    }
    path=runtime/CONSUMPTION_REL
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-root",type=Path,default=ROOT)
    parser.add_argument("--runtime-root",type=Path,required=True)
    args=parser.parse_args()
    receipt=consume(args.source_root,args.runtime_root)
    print(json.dumps(receipt,sort_keys=True))
    if receipt["state"] in {"NO_REQUEST","ALREADY_CONSUMED","ATTEMPT_RECORDED","COMPLETED"}:
        return 0
    return 1


if __name__=="__main__":
    raise SystemExit(main())
