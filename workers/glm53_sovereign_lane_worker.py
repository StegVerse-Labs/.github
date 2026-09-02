#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path.cwd().resolve()
TASK_ID="SHWP-GLM53-SOVEREIGN-LANE-001"
CAPABILITY="glm53_sovereign_lane_evidence"
MICRO_MERGE="07e4388eda92d99a8feb220f28265b147551242d"
RECEIPT=ROOT/"receipts/glm53-sovereign-lane/SHWP-GLM53-SOVEREIGN-LANE-001.json"
CONSUMER_EVIDENCE=ROOT/"receipts/glm53-sovereign-lane/runtime-evidence.glm-sovereign.json"
PRODUCER_RECEIPT=ROOT/"receipts/glm53-sovereign-lane/micro-node-producer-receipt.json"
EXPECTED_BLOBS={
    "tools/run_glm53_sovereign_lane_evidence.py":"d17c9567b3c77b271407c19383dda9e793e3b7de",
    "tools/evaluate_glm53_sovereign_eligibility.py":"11e0e051be402314db416928fd595bf05926e65e",
    "tasks/SV-COST-ELEVEN-LANE-GLM-SOVEREIGN-001.prompt.md":"693a1c09c93e85ab23f240a8df9292c3f06ccfc7",
}
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","ZAI_API_KEY","PRIVATE_KEY","SEED","MNEMONIC")


def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}

def measurement(name: str):
    raw=os.environ.get(name)
    if raw is None or not str(raw).strip(): return None
    try: value=float(raw)
    except ValueError as exc: raise RuntimeError(f"{name} must be a finite nonnegative number") from exc
    if not math.isfinite(value) or value < 0: raise RuntimeError(f"{name} must be a finite nonnegative number")
    return value

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def verify_micro(root: Path) -> dict:
    observed={}
    blobs_ok=True
    for rel,expected in EXPECTED_BLOBS.items():
        p=root/rel
        actual=git_blob(p.read_bytes()) if p.is_file() else "MISSING"
        observed[rel]=actual
        blobs_ok=blobs_ok and actual==expected
    ancestor=False
    head=None
    if (root/".git").exists():
        h=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True,check=False,timeout=20)
        a=subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",MICRO_MERGE,"HEAD"],capture_output=True,text=True,check=False,timeout=20)
        head=h.stdout.strip() if h.returncode==0 else None
        ancestor=a.returncode==0
    return {"root":str(root),"git_head":head,"required_ancestor_present":ancestor,"exact_git_blobs_verified":blobs_ok,"observed_blobs":observed,"verified":bool(blobs_ok and (ancestor or not (root/".git").exists()))}

def child_env():
    allow={"PATH","HOME","USER","LOGNAME","SHELL","PYTHONPATH","LANG","LC_ALL","TMPDIR","XDG_CONFIG_HOME","XDG_STATE_HOME"}
    env={k:os.environ[k] for k in allow if os.environ.get(k)}
    for k in FORBIDDEN: env.pop(k,None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env

def write(path: Path,value: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main() -> int:
    try: invocation=json.load(sys.stdin)
    except Exception: return 2
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1": return 3
    task=invocation.get("task") or {}
    handoff=invocation.get("handoff") or {}
    if task.get("task_id")!=TASK_ID: return 4
    if CAPABILITY not in set((handoff.get("execution") or {}).get("required_capabilities") or []): return 5

    hosted=[k for k in HOSTED if truthy(os.environ.get(k))]
    micro_raw=os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT")
    result={}
    state="BLOCKED"
    transition="GLM53_SOVEREIGN_EVIDENCE_BLOCKED"

    if hosted:
        result={"reason":"HOSTED_RUNTIME_PROHIBITED","hosted_markers":hosted}
    elif not micro_raw:
        result={"reason":"MICRO_NODE_RUNTIME_ROOT_NOT_DECLARED"}
    else:
        micro=Path(micro_raw).expanduser().resolve()
        source=verify_micro(micro) if micro.is_dir() else {"root":str(micro),"verified":False}
        if not source.get("verified"):
            result={"reason":"MICRO_NODE_GLM53_EVIDENCE_SOURCE_NOT_VERIFIED","source":source}
        else:
            tool=micro/"tools/run_glm53_sovereign_lane_evidence.py"
            endpoint=os.environ.get("STEGVERSE_GLM53_ENDPOINT")
            model_path=os.environ.get("STEGVERSE_GLM53_MODEL_PATH")
            runtime_id=os.environ.get("STEGVERSE_GLM53_RUNTIME_IDENTITY") or "stegverse-sovereign-glm53"
            measurements={
                "--energy-kwh":measurement("STEGVERSE_GLM53_ENERGY_KWH"),
                "--hardware-amortization-usd":measurement("STEGVERSE_GLM53_HARDWARE_AMORTIZATION_USD"),
                "--energy-cost-usd":measurement("STEGVERSE_GLM53_ENERGY_COST_USD"),
                "--storage-network-runtime-overhead-usd":measurement("STEGVERSE_GLM53_STORAGE_NETWORK_RUNTIME_OVERHEAD_USD"),
            }
            command=[sys.executable,str(tool),"--receipt",str(PRODUCER_RECEIPT)]
            if endpoint:
                command += ["--endpoint",endpoint,"--runtime-identity",runtime_id,"--write",str(CONSUMER_EVIDENCE)]
            if model_path:
                command += ["--model-path",model_path]
            for flag,value in measurements.items():
                if value is not None:
                    command += [flag,str(value)]
            done=subprocess.run(command,cwd=micro,capture_output=True,text=True,check=False,env=child_env(),timeout=900)
            producer=json.loads(PRODUCER_RECEIPT.read_text(encoding="utf-8")) if PRODUCER_RECEIPT.is_file() else None
            evidence=json.loads(CONSUMER_EVIDENCE.read_text(encoding="utf-8")) if CONSUMER_EVIDENCE.is_file() else None
            success=bool(
                done.returncode==0 and isinstance(producer,dict)
                and producer.get("state")=="EVIDENCE_READY"
                and isinstance(evidence,dict)
                and evidence.get("model")=="GLM-5.3-Flash"
                and evidence.get("vendor_api_credential_used") is False
            )
            state="COMPLETED" if success else "BLOCKED"
            transition="GLM53_SOVEREIGN_EVIDENCE_READY" if success else "GLM53_SOVEREIGN_RUNTIME_BLOCKER_OBSERVED"
            result={
                "reason":"GLM53_SOVEREIGN_EVIDENCE_READY" if success else (producer.get("state") if isinstance(producer,dict) else "GLM53_PRODUCER_FAILED"),
                "source":source,
                "producer_returncode":done.returncode,
                "producer_receipt_ref":"receipts/glm53-sovereign-lane/micro-node-producer-receipt.json",
                "consumer_evidence_ref":"receipts/glm53-sovereign-lane/runtime-evidence.glm-sovereign.json" if success else None,
                "private_endpoint_declared":bool(endpoint),
                "model_path_declared":bool(model_path),
                "cost_measurements_declared":{key.removeprefix("--"): value is not None for key,value in measurements.items()},
                "vendor_api_credential_used":False,
                "network_model_download_performed":False,
                "hosted_inference_substitution_performed":False,
            }

    result.update({
        "credential_authority":"TV/TVC",
        "credential_material_exported":False,
        "github_token_runtime_authority":"NONE",
        "heartbeat_grants_execution_authority":False,
        "execution_authorized_by_request":False,
        "publication_authorized":False,
    })
    receipt={"schema":"stegverse.glm53-sovereign-lane-worker-receipt/v1","task_id":TASK_ID,"state":state,"result":result,"authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"}
    write(RECEIPT,receipt)
    blocker=None if state=="COMPLETED" else {
        "dependency_class":"PHYSICAL_RESOURCE_OR_LOCAL_RUNTIME",
        "problem_statement":result["reason"],
        "solution_required":True,
        "may_remain_blocked":True,
        "next_solution_action":"RECHECK_ALREADY_LOCAL_MICRO_NODE_ROOT_AND_PRIVATE_GLM53_ENDPOINT",
        "machine_observable_release_condition":"one resident WorkerCoordinator execution emits consumer-compatible private GLM-5.3-Flash SV-RECON-001 evidence"
    }
    response={
        "schema":"stegverse.worker-response/v0.1",
        "state":state,
        "transition_id":transition,
        "transition_sequence":1,
        "expected_next_transition":None if state=="COMPLETED" else "GLM53_SOVEREIGN_LANE_RECHECK",
        "expected_next_earliest_epoch":None,
        "expected_next_latest_epoch":None,
        "recheck_policy":None if state=="COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref":"receipts/glm53-sovereign-lane/SHWP-GLM53-SOVEREIGN-LANE-001.json",
        "evidence_refs":["handoffs/SHWP-GLM53-SOVEREIGN-LANE-001.json","receipts/glm53-sovereign-lane/SHWP-GLM53-SOVEREIGN-LANE-001.json"] + (["receipts/glm53-sovereign-lane/runtime-evidence.glm-sovereign.json"] if state=="COMPLETED" else []),
        "blocker":blocker,
        "cost_observation":{"task_control_evaluations":1,"compute_units":1,"external_cost_usd":0,"task_class":"glm53_sovereign_lane_evidence"}
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n")
    return 0

if __name__=="__main__": raise SystemExit(main())
