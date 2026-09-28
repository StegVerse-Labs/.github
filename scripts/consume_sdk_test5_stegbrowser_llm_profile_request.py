#!/usr/bin/env python3
"""Consume Test 5 through the existing SDK run-manifest + Universal InTr path."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
REQUEST_REL=Path("control/resident-execution-request.d/sdk-test5-stegbrowser-llm-profile-001.json")
RECEIPT_REL=Path("receipts/sovereign-host/sdk-test5-stegbrowser-llm-profile.latest.json")
TASK_ID="EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001"

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError("JSON object required")
    return value

def _digest(label:str)->str:
    return "sha256:"+hashlib.sha256(label.encode()).hexdigest()

def consume(source_root:Path,runtime_root:Path,*,env:dict[str,str]|None=None)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    req_path=runtime/REQUEST_REL
    if not req_path.is_file():
        req_path=source_root.expanduser().resolve()/REQUEST_REL
    if not req_path.is_file():
        return {"schema":"stegverse.sdk-test5-resident-result/v1","state":"NO_REQUEST","runtime_execution_attempted":False}
    req=load(req_path)
    expected={"schema":"stegverse.resident-execution-request/v1","state":"REQUESTED","task_id":TASK_ID,
              "mode":"SDK_TEST5_STEGBROWSER_LLM_PROFILE","entrypoint":"stegverse.manifest_execution.execute_manifest",
              "credential_authority":"TV/TVC","transition_authority":"Interlock/InTr",
              "github_token_runtime_authority":"NONE","second_machine_required":False,"request_granted_authority":False}
    for k,v in expected.items():
        if req.get(k)!=v: raise RuntimeError(f"Test 5 request {k} mismatch")
    values=dict(os.environ if env is None else env)
    sdk=Path(values.get("STEGVERSE_SDK_SOURCE_ROOT","")).expanduser() if values.get("STEGVERSE_SDK_SOURCE_ROOT") else None
    if sdk is None or not sdk.is_dir():
        return {"schema":"stegverse.sdk-test5-resident-result/v1","state":"FAIL_CLOSED","disposition":"FAIL_CLOSED",
                "failed_predicate":"SDK_SOURCE_NOT_MATERIALIZED","runtime_execution_attempted":True}
    sys.path.insert(0,str(sdk.resolve()))
    from stegverse.manifest_builder import build_manifest
    from stegverse.manifest_execution import execute_manifest
    results=[]
    for spec in req.get("workers") or []:
        wid=str(spec["worker_id"])
        outbound=_digest("test5:"+wid+":outbound")
        returned=_digest("test5:"+wid+":return")
        profile={
          "schema":"stegbrowser.llm-profile-request.v1","profile":"llm.v1",
          "prompt":spec["prompt"],"response_marker":spec["response_marker"],"provider":spec["provider"],
          "journey":{"schema":"stegverse.packet-carried-endpoint-receipt-journey/v1",
            "journey_id":"test5-"+wid.lower(),"origin_endpoint":"stegverse:test5-origin",
            "ephemeral_endpoint":"stegbrowser:ephemeral:"+wid.lower(),
            "outbound_manifest_sha256":outbound,"return_manifest_sha256":returned,
            "return_predecessor_manifest_sha256":outbound}}
        manifest=build_manifest(data={"test":5,"worker":wid},data_class="stegverse.sdk-test.v1",
          source_framework="StegVerse-SDK-Evaluator",source_output_id="test5-"+wid.lower(),
          processor_request=profile,process="stegbrowser",return_depth="full-trace",publisher_required=False)
        result=execute_manifest(manifest)
        results.append({"worker_id":wid,"manifest":manifest,"result":result})
        if result.get("disposition") in {"DENY","FAIL_CLOSED"}:
            break
    receipt={"schema":"stegverse.sdk-test5-resident-result/v1","task_id":TASK_ID,
      "state":"COMPLETE" if len(results)==2 and all(x["result"].get("state")=="COMPLETE" for x in results) else "ATTEMPT_RECORDED",
      "runtime_execution_attempted":True,"results":results,"authority_effect":"NONE_EVIDENCE_ONLY"}
    out=runtime/RECEIPT_REL; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,default=ROOT); ap.add_argument("--runtime-root",type=Path,required=True)
    a=ap.parse_args(); print(json.dumps(consume(a.source_root,a.runtime_root),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
