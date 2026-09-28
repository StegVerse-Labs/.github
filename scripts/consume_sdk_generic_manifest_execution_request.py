#!/usr/bin/env python3
"""Generic resident consumer for SDK evaluator manifests and capability requests."""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
REQUEST_REL=Path("control/resident-execution-request.d/sdk-generic-manifest-execution.json")
RECEIPT_REL=Path("receipts/sovereign-host/sdk-generic-manifest-execution.latest.json")

def load(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("JSON object required")
    return v

def consume(source_root:Path,runtime_root:Path,*,env:dict[str,str]|None=None)->dict[str,Any]:
    source=source_root.expanduser().resolve(); runtime=runtime_root.expanduser().resolve()
    request_path=runtime/REQUEST_REL
    if not request_path.is_file(): request_path=source/REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.sdk-generic-manifest-execution-result/v1","state":"NO_REQUEST","runtime_execution_attempted":False}
    req=load(request_path)
    expected={"schema":"stegverse.sdk-generic-manifest-execution-request/v1","state":"REQUESTED",
      "entrypoint":"stegverse.manifest_execution.execute_manifest","credential_authority":"TV/TVC",
      "transition_authority":"Interlock/InTr","request_granted_authority":False,"second_machine_required":False}
    for k,v in expected.items():
        if req.get(k)!=v: raise RuntimeError(f"generic SDK request {k} mismatch")
    values=dict(os.environ if env is None else env)
    sdk=Path(values.get("STEGVERSE_SDK_SOURCE_ROOT","")).expanduser() if values.get("STEGVERSE_SDK_SOURCE_ROOT") else None
    if sdk is None or not sdk.is_dir():
        return {"schema":"stegverse.sdk-generic-manifest-execution-result/v1","state":"FAIL_CLOSED",
          "disposition":"FAIL_CLOSED","failed_predicate":"SDK_SOURCE_NOT_MATERIALIZED","runtime_execution_attempted":True}
    sys.path.insert(0,str(sdk.resolve()))
    from stegverse.manifest_builder import build_manifest
    from stegverse.manifest_execution import execute_manifest
    results=[]
    for item in req.get("requests") or []:
        build=build_manifest(**item["build"])
        state=build.get("state") if isinstance(build,dict) else None
        if state in {"CAPABILITY_WORKAROUND_REQUIRED","CAPABILITY_DEVELOPMENT_REQUESTED"}:
            results.append({"request_id":item["request_id"],"manifest_build_resolution":build})
            continue
        result=execute_manifest(build)
        results.append({"request_id":item["request_id"],"manifest":build,"result":result})
        if result.get("disposition") in {"DENY","FAIL_CLOSED"}: break
    receipt={"schema":"stegverse.sdk-generic-manifest-execution-result/v1","state":"ATTEMPT_RECORDED",
      "runtime_execution_attempted":True,"results":results,"authority_effect":"NONE_EVIDENCE_ONLY"}
    out=runtime/RECEIPT_REL; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,default=ROOT); p.add_argument("--runtime-root",type=Path,required=True)
    a=p.parse_args(); print(json.dumps(consume(a.source_root,a.runtime_root),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
