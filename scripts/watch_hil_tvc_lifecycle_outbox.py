#!/usr/bin/env python3
"""Bounded lease-scoped watcher for HIL custody→TVC lifecycle events."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable, Mapping

WATCH_RECEIPT_REL=Path("receipts/hil-sovereign-receiver/tvc-lifecycle-watch.latest.json")
CONSUMER_REL=Path("scripts/consume_hil_tvc_lifecycle_outbox.py")
CREDENTIAL_AUTHORITY="TV/TVC"

Runner=Callable[..., subprocess.CompletedProcess[str]]

def _last_json(stdout:str)->dict[str,Any]|None:
    for line in reversed([v.strip() for v in stdout.splitlines() if v.strip()]):
        try: value=json.loads(line)
        except Exception: continue
        if isinstance(value,dict): return value
    return None

def _safe_env(source:Mapping[str,str]|None=None)->dict[str,str]:
    values=dict(os.environ if source is None else source)
    blocked=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    for key in blocked: values.pop(key,None)
    values["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    values["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    values["PYTHONDONTWRITEBYTECODE"]="1"
    return values

def _write(runtime:Path,value:Mapping[str,Any])->None:
    path=runtime/WATCH_RECEIPT_REL
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(value),indent=2,sort_keys=True)+"\n",encoding="utf-8")

def watch(
    runtime_root:Path,
    *,
    window_seconds:float=900.0,
    poll_seconds:float=0.5,
    runner:Runner=subprocess.run,
    env:Mapping[str,str]|None=None,
    monotonic=time.monotonic,
    sleeper=time.sleep,
)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    consumer=runtime/CONSUMER_REL
    if not consumer.is_file():
        result={"schema":"stegverse.hil.tvc-lifecycle-watch/v1","state":"FAIL_CLOSED","reason":"CONSUMER_NOT_MATERIALIZED","authority_effect":"NONE"}
        _write(runtime,result); return result
    if window_seconds<=0 or poll_seconds<=0:
        raise ValueError("watch_window_and_poll_must_be_positive")
    safe=_safe_env(env)
    started=monotonic()
    attempts=0
    last:dict[str,Any]|None=None
    while monotonic()-started < window_seconds:
        attempts+=1
        completed=runner(
            [sys.executable,str(consumer),"--runtime-root",str(runtime)],
            cwd=runtime,capture_output=True,text=True,check=False,timeout=120,env=safe,
        )
        last=_last_json(completed.stdout)
        state=last.get("state") if isinstance(last,dict) else None
        if completed.returncode==0 and state=="ADMITTED_TO_TVC_HIL_LIFECYCLE":
            result={
                "schema":"stegverse.hil.tvc-lifecycle-watch/v1",
                "state":"TVC_LIFECYCLE_ADMITTED",
                "attempts":attempts,
                "consumer_state":state,
                "consumer_receipt_ref":str((runtime/Path("receipts/hil-sovereign-receiver/tvc-lifecycle-outbox-consumption.latest.json")).relative_to(runtime)),
                "credential_authority":CREDENTIAL_AUTHORITY,
                "credential_value_exposed":False,
                "github_token_runtime_authority":"NONE",
                "private_review_completed":False,
                "publication_authorized":False,
                "authority_effect":"NONE_EVENT_WATCH_ONLY",
            }
            _write(runtime,result); return result
        if state=="FAIL_CLOSED" or completed.returncode not in {0,1}:
            result={
                "schema":"stegverse.hil.tvc-lifecycle-watch/v1","state":"FAIL_CLOSED",
                "attempts":attempts,"consumer_state":state,"consumer_returncode":completed.returncode,
                "credential_authority":CREDENTIAL_AUTHORITY,"authority_effect":"NONE",
            }
            _write(runtime,result); return result
        sleeper(poll_seconds)
    result={
        "schema":"stegverse.hil.tvc-lifecycle-watch/v1","state":"LEASE_WINDOW_EXPIRED_NO_TVC_ADMISSION",
        "attempts":attempts,"last_consumer_state":last.get("state") if isinstance(last,dict) else None,
        "credential_authority":CREDENTIAL_AUTHORITY,"credential_value_exposed":False,
        "github_token_runtime_authority":"NONE","authority_effect":"NONE_EVENT_WATCH_ONLY",
    }
    _write(runtime,result); return result

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--runtime-root",type=Path,required=True)
    p.add_argument("--window-seconds",type=float,default=float(os.environ.get("STEGVERSE_HIL_TVC_WATCH_SECONDS","900")))
    p.add_argument("--poll-seconds",type=float,default=float(os.environ.get("STEGVERSE_HIL_TVC_POLL_SECONDS","0.5")))
    args=p.parse_args()
    result=watch(args.runtime_root,window_seconds=args.window_seconds,poll_seconds=args.poll_seconds)
    print(json.dumps(result,sort_keys=True))
    return 0 if result["state"] in {"TVC_LIFECYCLE_ADMITTED","LEASE_WINDOW_EXPIRED_NO_TVC_ADMISSION"} else 1

if __name__=="__main__": raise SystemExit(main())
