#!/usr/bin/env python3
"""Refresh the existing resident source and run only the admitted Kimi task.

This is a thin task-specific environment-preservation wrapper around the same
canonical source refresher and `run_worker_runtime.py`. It creates no scheduler,
carrier, WorkerCoordinator, claim/fence, credential, transport, or governance
authority.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from refresh_sovereign_worker_runtime_source import refresh

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "KIMI-INTR-RESIDENT-ACTIVATION-001"
RUNNER_REL = Path("scripts/run_worker_runtime.py")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
RECEIPT_REL = Path("receipts/sovereign-host/kimi-intr-resident-targeted-execution.latest.json")
HOSTED = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY","ANTHROPIC_API_KEY","DEEPSEEK_API_KEY","MOONSHOT_API_KEY","KIMI_API_KEY",
    "MASTER_RECORDS_AUTH_TOKEN","MASTER_RECORDS_RECEIPT_KEY","STEGVERSE_MASTER_RECORDS_TOKEN",
)
SAFE = (
    "PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT","STEGVERSE_TVC_ROOT","STEGVERSE_STEGOS_ROOT",
    "STEGVERSE_GOVERNANCE_ROOT","STEGVERSE_STEGCORE_SOURCE_ROOT","STEGVERSE_TEST_LANES_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT","STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_VAULT_BROKER_SOCKET","STEGVERSE_MASTER_RECORDS_PROVIDER_USAGE_SOCKET",
)


def truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() not in {"","0","false","no"}


def clean_env(source: Mapping[str,str] | None = None) -> dict[str,str]:
    values=dict(os.environ if source is None else source)
    hosted=[k for k in HOSTED if truthy(values.get(k))]
    if hosted:
        raise RuntimeError("hosted runtime may not execute Kimi resident task: "+",".join(sorted(hosted)))
    leaked=[k for k in FORBIDDEN if values.get(k)]
    if leaked:
        raise RuntimeError("credential-bearing Kimi wrapper environment prohibited: "+",".join(sorted(leaked)))
    env={k:values[k] for k in SAFE if values.get(k)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env


def last_json(stdout: str) -> dict[str,Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try: value=json.loads(line)
        except Exception: continue
        if isinstance(value,dict): return value
    return None


def execute(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str,str] | None = None) -> dict[str,Any]:
    source=source_root.expanduser().resolve(); runtime=runtime_root.expanduser().resolve()
    refresh_receipt=refresh(source,runtime)
    runner_path=runtime/RUNNER_REL
    if not runner_path.is_file(): raise RuntimeError("refreshed WorkerCoordinator runner missing")
    if not (runtime/CARRIER_REL).is_file(): raise RuntimeError("separated carrier reference missing")
    command=[sys.executable,str(runner_path),"--root",str(runtime),"--task-id",TASK_ID]
    done=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=clean_env(env),timeout=1800)
    result=last_json(done.stdout)
    receipt={
        "schema":"stegverse.kimi-resident-refresh-targeted-execution/v1",
        "source_root":str(source),"runtime_root":str(runtime),
        "mode":"TARGETED_INDEPENDENT_TASK_CONTROL","task_id":TASK_ID,
        "command":command,"refresh_receipt":refresh_receipt,
        "execution_returncode":done.returncode,"execution_result":result,
        "execution_result_observed":isinstance(result,dict),"runtime_execution_attempted":True,
        "source_refresh_is_runtime_execution":False,"network_fetch_performed":False,
        "third_party_scheduler_required":False,"second_machine_required":False,
        "github_token_required":False,"github_token_runtime_authority":"NONE",
        "credential_authority":"TV/TVC","credential_value_exposed":False,
        "authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
    }
    target=runtime/RECEIPT_REL; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,default=ROOT); p.add_argument("--runtime-root",type=Path,required=True); a=p.parse_args()
    receipt=execute(a.source_root,a.runtime_root); print(json.dumps(receipt,sort_keys=True))
    return 0 if receipt["execution_result_observed"] else 1

if __name__=="__main__": raise SystemExit(main())
