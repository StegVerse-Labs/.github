#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001"
TARGET_TASK = "SHWP-DURABLE-RUNTIME-ACTIVATION"
EXPECTED_CLAIM = "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18"
EXPECTED_FENCE = 18
RECEIPT_REL = Path("receipts/sovereign-host/g18-resident-request-resolution.latest.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/g18-resident-execution-request-consumption.latest.json")
BOOTSTRAP_RECEIPT_REL = Path("receipts/sovereign-host/g18-resolution-bootstrap.latest.json")
BOOTSTRAP_PROOF_REL = Path("receipts/sovereign-host/g18-resolution-activation.latest.json")
BOOTSTRAP_NODE_REL = Path("control/sovereign-node.json")
THIRD_PARTY_ENV = ("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
NONSECRET_ENV = {
    "PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT",
}

def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("","0","false","no")

def hosted(env: dict[str,str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV)

def runtime_root(env: dict[str,str] | None = None) -> Path:
    values = os.environ if env is None else env
    if values.get("STEGVERSE_HEARTBEAT_ROOT"):
        return Path(values["STEGVERSE_HEARTBEAT_ROOT"]).expanduser().resolve()
    base = Path(values.get("XDG_STATE_HOME", str(Path.home()/".local"/"state")))
    return (base/"stegverse"/"heartbeat-runtime").resolve()

def source_root(env: dict[str,str] | None = None) -> Path:
    values = os.environ if env is None else env
    if values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT"):
        return Path(values["STEGVERSE_HEARTBEAT_SOURCE_ROOT"]).expanduser().resolve()
    return ROOT

def clean_env(env: dict[str,str] | None = None) -> dict[str,str]:
    values = os.environ if env is None else env
    out = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    out["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    out["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return out

def load_json(path: Path) -> dict[str,Any] | None:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else None
    except Exception:
        return None

def atomic_write(path: Path, value: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h:
        json.dump(value,h,indent=2,sort_keys=True); h.write("\n"); name=h.name
    os.replace(name,path)

def exact_g18_claim(runtime: Path) -> dict[str,Any] | None:
    registry=load_json(runtime/"control"/"worker-registry.json") or {}
    for row in registry.get("tasks") or []:
        if not isinstance(row,dict) or row.get("task_id") != TARGET_TASK:
            continue
        timing=row.get("heartbeat_timing") or {}
        if (
            row.get("claim_id")==EXPECTED_CLAIM
            and timing.get("fencing_token")==EXPECTED_FENCE
            and row.get("state") in {"ACTIVE","BLOCKED","RETRY"}
        ):
            return {
                "task_id":TARGET_TASK,
                "claim_id":EXPECTED_CLAIM,
                "fencing_token":EXPECTED_FENCE,
                "state":row.get("state"),
                "worker_id":row.get("worker_id"),
                "worker_instance_id":row.get("worker_instance_id"),
            }
    return None

def blocker(problem: str, reason: str, level: str) -> dict[str,Any]:
    return {
        "dependency_class":"PHYSICAL_RESOURCE",
        "problem_statement":problem,
        "solution_required":True,
        "may_remain_blocked":False,
        "workaround_candidates":[
            "Use an already-materialized non-hosted sovereign resident runtime and the portable local-source refresh bridge.",
            "If no such resident runtime is present, escalate to component authority to select an existing StegVerse-owned/federated eligible surface; do not require a second machine by default."
        ],
        "next_solution_action":level,
        "observed_reason":reason,
        "physical_additional_machine_required":False,
        "always_on_external_host_required":False,
        "third_party_runtime_required":False,
        "human_action_required":False,
        "heartbeat_activation_blocked":False,
    }

def run_resolution(source: Path, runtime: Path, *, runner=subprocess.run, env: dict[str,str] | None=None) -> dict[str,Any]:
    base={
        "schema":"stegverse.g18-resident-request-resolution/v1",
        "task_id":TASK_ID,
        "target_task_id":TARGET_TASK,
        "target_claim_id":EXPECTED_CLAIM,
        "target_fencing_token":EXPECTED_FENCE,
        "source_root":str(source),
        "runtime_root":str(runtime),
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "heartbeat_grants_execution_authority":False,
        "new_g18_claim_allowed":False,
        "second_machine_required":False,
        "third_party_runtime_required":False,
        "runtime_execution_attempted":False,
        "authority_effect":"GOAL_PRESERVING_RESOLUTION_ONLY_NO_G18_AUTHORITY",
    }
    if hosted(env):
        return {**base,"state":"BLOCKED","transition_id":"HOSTED_SURFACE_REJECTED","blocker":blocker(
            "Hosted validation cannot consume the deployment-local G18 resident execution request.",
            "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE",
            "ESCALATE_TO_COMPONENT_AUTHORITY_FOR_EXISTING_SOVEREIGN_RESIDENT"
        )}
    bootstrap_attempted=False
    bootstrap_returncode=None
    bootstrap_state=None
    registry_path=runtime/"control"/"worker-registry.json"
    if not registry_path.is_file():
        bootstrap_script=source/"scripts"/"bootstrap_sovereign_runtime.py"
        if not bootstrap_script.is_file():
            return {**base,"state":"BLOCKED","transition_id":"LOCAL_BOOTSTRAP_SOURCE_REQUIRED","blocker":{
                **blocker(
                    "No resident WorkerCoordinator registry is present and the already-local canonical source does not contain the v13 sovereign bootstrap.",
                    "LOCAL_BOOTSTRAP_SCRIPT_MISSING",
                    "ESCALATE_TO_REPOSITORY_OWNER_SOURCE_RECONCILIATION"
                ),
                "dependency_class":"INTERNAL_CAPABILITY",
            }}
        bootstrap_attempted=True
        bootstrap_receipt=runtime/BOOTSTRAP_RECEIPT_REL
        bootstrap_proof=runtime/BOOTSTRAP_PROOF_REL
        bootstrap_node=runtime/BOOTSTRAP_NODE_REL
        boot=runner(
            [
                sys.executable,str(bootstrap_script),
                "--source-root",str(source),
                "--runtime-root",str(runtime),
                "--node-marker",str(bootstrap_node),
                "--proof-path",str(bootstrap_proof),
                "--receipt-path",str(bootstrap_receipt),
                "--skip-post-bootstrap-stegfin",
            ],
            cwd=source,capture_output=True,text=True,check=False,env=clean_env(env),timeout=600,
        )
        bootstrap_returncode=boot.returncode
        bootstrap_body=load_json(bootstrap_receipt) or {}
        bootstrap_state=bootstrap_body.get("state")
        if boot.returncode != 0 or bootstrap_state != "COMPLETE" or not registry_path.is_file():
            return {
                **base,
                "state":"BLOCKED",
                "transition_id":"SOVEREIGN_RESIDENT_BOOTSTRAP_REPAIR_REQUIRED",
                "bootstrap_attempted":True,
                "bootstrap_returncode":boot.returncode,
                "bootstrap_state":bootstrap_state,
                "bootstrap_receipt_ref":BOOTSTRAP_RECEIPT_REL.as_posix(),
                "blocker":{
                    **blocker(
                        "The canonical v13 local bootstrap did not produce a verified resident WorkerCoordinator runtime.",
                        bootstrap_body.get("reason") or "SOVEREIGN_RESIDENT_BOOTSTRAP_INCOMPLETE",
                        "ESCALATE_TO_COMPONENT_AUTHORITY_FOR_SOVEREIGN_BOOTSTRAP_REPAIR"
                    ),
                    "dependency_class":"INTERNAL_CAPABILITY",
                },
            }
    claim=exact_g18_claim(runtime)
    if claim is None:
        return {**base,"state":"BLOCKED","transition_id":"EXACT_G18_CLAIM_NOT_RESIDENT","blocker":{
            **blocker(
                "The resident runtime does not carry the exact existing G18 fence18 claim required by the one-shot request.",
                "EXACT_EXISTING_G18_CLAIM_NOT_PRESENT",
                "ESCALATE_TO_COMPONENT_AUTHORITY_FOR_G18_CLAIM_RECONCILIATION"
            ),
            "dependency_class":"AUTHORITY",
        }}
    refresh_script=source/"scripts"/"refresh_sovereign_worker_runtime_source.py"
    if not refresh_script.is_file():
        return {**base,"state":"BLOCKED","transition_id":"LOCAL_REFRESH_SOURCE_REQUIRED","existing_claim":claim,"blocker":{
            **blocker(
                "The already-local canonical source does not contain the merged portable refresh bridge.",
                "LOCAL_REFRESH_SCRIPT_MISSING",
                "ESCALATE_TO_REPOSITORY_OWNER_SOURCE_RECONCILIATION"
            ),
            "dependency_class":"INTERNAL_CAPABILITY",
        }}
    refresh=runner(
        [sys.executable,str(refresh_script),"--source-root",str(source),"--runtime-root",str(runtime)],
        cwd=source,capture_output=True,text=True,check=False,env=clean_env(env),timeout=120,
    )
    consumer=runtime/"scripts"/"consume_g18_resident_execution_request.py"
    if refresh.returncode != 0 or not consumer.is_file():
        return {**base,"state":"BLOCKED","transition_id":"RESIDENT_SOURCE_REFRESH_REPAIR_REQUIRED","existing_claim":claim,
            "refresh_returncode":refresh.returncode,"blocker":{
                **blocker(
                    "Portable local-source refresh did not produce the G18 request consumer on the resident runtime.",
                    "RESIDENT_SOURCE_REFRESH_INCOMPLETE",
                    "ESCALATE_TO_REPOSITORY_OWNER_SOURCE_RECONCILIATION"
                ),
                "dependency_class":"INTERNAL_CAPABILITY",
            }}
    consume=runner(
        [sys.executable,str(consumer),"--source-root",str(source),"--runtime-root",str(runtime)],
        cwd=runtime,capture_output=True,text=True,check=False,env=clean_env(env),timeout=900,
    )
    receipt=load_json(runtime/CONSUMPTION_REL) or {}
    success=(
        receipt.get("state") in {"ATTEMPT_RECORDED","ALREADY_CONSUMED"}
        and (
            receipt.get("state")=="ALREADY_CONSUMED"
            or (
                receipt.get("exact_existing_claim_observed") is True
                and receipt.get("bridge_mode_valid") is True
            )
        )
    )
    return {
        **base,
        "state":"COMPLETED" if success else "BLOCKED",
        "transition_id":"G18_RESIDENT_REQUEST_CONSUMPTION_VERIFIED" if success else "G18_RESIDENT_REQUEST_CONSUMPTION_REPAIR_REQUIRED",
        "existing_claim":claim,
        "bootstrap_attempted":bootstrap_attempted,
        "bootstrap_returncode":bootstrap_returncode,
        "bootstrap_state":bootstrap_state,
        "refresh_returncode":refresh.returncode,
        "consumer_returncode":consume.returncode,
        "runtime_execution_attempted":receipt.get("runtime_execution_attempted") is True,
        "consumption_state":receipt.get("state"),
        "consumption_receipt_ref":CONSUMPTION_REL.as_posix(),
        "request_id":receipt.get("request_id"),
        "request_sha256":receipt.get("request_sha256"),
        "blocker":None if success else {
            **blocker(
                "The one-shot request consumer did not verify an attempt through the exact existing G18 claim/fence.",
                receipt.get("state") or "CONSUMPTION_RECEIPT_NOT_VERIFIED",
                "ESCALATE_TO_COMPONENT_AUTHORITY_FOR_G18_RESIDENT_CONSUMPTION"
            ),
            "dependency_class":"AUTHORITY" if receipt.get("state")=="FAIL_CLOSED" else "INTERNAL_CAPABILITY",
        },
    }

def main() -> int:
    invocation=json.load(sys.stdin)
    task=invocation.get("task") or {}
    handoff=invocation.get("handoff") or {}
    epoch=invocation.get("heartbeat_epoch")
    timing=task.get("heartbeat_timing") or {}
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or not isinstance(epoch,int):
        return 2
    if not isinstance(task.get("claim_id"),str) or not isinstance(timing.get("fencing_token"),int):
        return 3
    required={"runtime_observation","bounded_process_execution","durable_state_reconstruction","g18_resident_request_consumption_resolution"}
    if not required.issubset(set((handoff.get("execution") or {}).get("required_capabilities") or [])):
        return 4
    result=run_resolution(source_root(),runtime_root())
    result["resolution_claim_id"]=task.get("claim_id")
    result["resolution_fencing_token"]=timing.get("fencing_token")
    result["heartbeat_epoch_at_invocation"]=epoch
    receipt_path=ROOT/RECEIPT_REL
    atomic_write(receipt_path,result)
    state=result["state"]
    response={
        "schema":"stegverse.worker-response/v0.1",
        "state":state,
        "transition_id":result["transition_id"],
        "transition_sequence":1,
        "expected_next_transition":None if state=="COMPLETED" else "DERIVE_AND_REGISTER_RESOLUTION_TASK",
        "expected_next_earliest_epoch":None if state=="COMPLETED" else epoch+1,
        "expected_next_latest_epoch":None if state=="COMPLETED" else epoch+1,
        "checkpoint_ref":RECEIPT_REL.as_posix(),
        "evidence_refs":[
            RECEIPT_REL.as_posix(),
            "control/resident-execution-request.d/g18-sovereign-runtime-resume.json",
            "scripts/refresh_sovereign_worker_runtime_source.py",
            "scripts/consume_g18_resident_execution_request.py",
            "scripts/refresh_and_execute_resident_task.py",
        ],
        "cost_observation":{"hb_transition_count":0,"compute_units":2,"external_cost_usd":0,"task_class":"g18_resident_request_consumption_resolution"},
    }
    if result.get("blocker"):
        response["blocker"]=result["blocker"]
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
