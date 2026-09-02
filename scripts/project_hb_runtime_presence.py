#!/usr/bin/env python3
"""Project shared HB runtime presence / resident observability from existing state.

This projection is observation-only. It creates no heartbeat, scheduler, claim,
fence, credential, route, transition, receiving, publication, custody, or
consequence authority.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA="stegverse.hb-runtime-presence-resident-observability/v1"
DEFAULT_OUTPUT=Path("control/hb-runtime-presence-resident-observability.json")

def load(path:Path)->dict[str,Any]|None:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value,dict) else None

def parse_time(value:Any)->float|None:
    if not isinstance(value,str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()
    except Exception:
        return None

def age_seconds(timestamp:float|None, now:float)->float|None:
    if timestamp is None:
        return None
    return max(0.0,now-timestamp)

def node_identity(root:Path)->tuple[dict[str,Any]|None,str|None]:
    candidates=[
        root/"control/sovereign-node.json",
        Path.home()/".stegverse/node.json",
        Path("/etc/stegverse/node.json"),
    ]
    for path in candidates:
        value=load(path)
        if value:
            node_id=value.get("node_id") or value.get("resident_id") or value.get("runtime_id")
            if node_id:
                return value,str(path)
    return None,None

def service_active(service:Mapping[str,Any]|None)->bool:
    if not service or service.get("active") is not True:
        return False
    if service.get("registration_kind")=="stegverse-ephemeral-console":
        return service.get("stegverse_process_supervision") is True
    return (
        service.get("native_process_supervision_only") is True
        and service.get("carrier_active") is True
        and service.get("worker_active") is True
    )

def worker_timestamp(worker:Mapping[str,Any]|None)->float|None:
    if not worker:
        return None
    for key in ("last_cycle_at","observed_at","updated_at","last_seen_at"):
        parsed=parse_time(worker.get(key))
        if parsed is not None:
            return parsed
    return None

def carrier_timestamp(carrier:Mapping[str,Any]|None)->float|None:
    if not carrier:
        return None
    oscillator=carrier.get("oscillator") if isinstance(carrier.get("oscillator"),dict) else {}
    sampled=oscillator.get("sampled_unix_ns")
    if isinstance(sampled,int) and not isinstance(sampled,bool):
        return sampled/1_000_000_000
    return parse_time(carrier.get("last_cycle_at"))

def nested_items(value:Any,prefix:str="")->Iterable[tuple[str,Any]]:
    if isinstance(value,dict):
        for key,item in value.items():
            path=f"{prefix}.{key}" if prefix else str(key)
            yield path,item
            yield from nested_items(item,path)
    elif isinstance(value,list):
        for index,item in enumerate(value):
            path=f"{prefix}[{index}]"
            yield path,item
            yield from nested_items(item,path)

def truth_marker(value:Mapping[str,Any]|None,needle:str)->bool:
    if not value:
        return False
    for path,item in nested_items(value):
        if needle in path.lower() and item in (True,"PASS","RECONSTRUCTED_PASS","COMPLETED","VERIFIED"):
            return True
    return False

def evidence_refs(value:Mapping[str,Any]|None)->list[str]:
    refs:set[str]=set()
    if not value:
        return []
    for path,item in nested_items(value):
        if isinstance(item,str) and (
            path.lower().endswith("receipt_path")
            or path.lower().endswith("receipt_ref")
            or "evidence_ref" in path.lower()
            or path.lower().endswith("proof_path")
        ):
            refs.add(item)
    return sorted(refs)

def matching_request(root:Path,task_id:str|None)->tuple[dict[str,Any]|None,str|None]:
    directory=root/"control/resident-execution-request.d"
    if not directory.is_dir():
        return None,None
    candidates=[]
    for path in sorted(directory.glob("*.json")):
        value=load(path)
        if not value:
            continue
        if task_id and value.get("task_id")!=task_id:
            continue
        candidates.append((path,value))
    if not candidates:
        return None,None
    path,value=candidates[-1]
    return value,str(path)

def matching_consumption(root:Path,task_id:str|None,request_id:str|None)->tuple[dict[str,Any]|None,str|None]:
    directory=root/"receipts/sovereign-host"
    if not directory.is_dir():
        return None,None
    candidates=[]
    for path in sorted(directory.glob("*request-consumption*.json")):
        value=load(path)
        if not value:
            continue
        if task_id and value.get("task_id")!=task_id:
            continue
        if request_id and value.get("request_id") not in (None,request_id):
            continue
        candidates.append((path,value))
    if not candidates:
        return None,None
    path,value=candidates[-1]
    return value,str(path)

def project(runtime_root:Path,*,task_id:str|None=None,max_age_seconds:float=120.0,now:float|None=None)->dict[str,Any]:
    root=runtime_root.expanduser().resolve()
    current=time.time() if now is None else float(now)
    node,node_ref=node_identity(root)
    service_path=root/"receipts/sovereign-host/activation.latest.json"
    carrier_path=root/"control/heartbeat-carrier-runtime-state.json"
    worker_path=root/"control/worker-runtime-state.json"
    control_path=root/"control/worker-control-plane-coordination.json"
    service=load(service_path)
    carrier=load(carrier_path)
    worker=load(worker_path)
    control=load(control_path)
    carrier_age=age_seconds(carrier_timestamp(carrier),current)
    worker_age=age_seconds(worker_timestamp(worker),current)
    carrier_fresh=carrier_age is not None and carrier_age<=max_age_seconds
    worker_fresh=worker_age is not None and worker_age<=max_age_seconds
    supervised=service_active(service)
    request,request_ref=matching_request(root,task_id)
    request_id=str(request.get("request_id")) if request and request.get("request_id") else None
    consumption,consumption_ref=matching_consumption(root,task_id,request_id)
    consumption_state=consumption.get("state") if consumption else None
    consumption_observed=bool(consumption and consumption_state not in (None,"NO_REQUEST"))
    execution_attempted=bool(consumption and consumption.get("runtime_execution_attempted") is True)
    execution_transition=None
    if consumption:
        execution_transition=consumption.get("transition_id")
        if execution_transition is None:
            for path,item in nested_items(consumption):
                if path.lower().endswith("transition_id") and isinstance(item,str):
                    execution_transition=item
                    break
    admitted=None
    if consumption:
        for path,item in nested_items(consumption):
            if ("admission" in path.lower() or path.lower().endswith("authorized_execution")) and item is True:
                admitted=True
                break
    retained=[]
    if consumption_ref:
        retained.append(consumption_ref)
    retained.extend(evidence_refs(consumption))
    projection={
        "schema":SCHEMA,
        "projection_role":"OBSERVATION_ONLY",
        "runtime_root":str(root),
        "resident":{
            "node_id":(node or {}).get("node_id") if node else None,
            "identity_ref":node_ref,
            "supervision_observed":supervised,
            "registration_kind":(service or {}).get("registration_kind"),
            "carrier_process_observed":bool(service and service.get("carrier_active") is True),
            "worker_process_observed":bool(service and service.get("worker_active") is True),
            "alive_current":supervised and carrier_fresh and worker_fresh,
            "last_observed_at":max(
                [x for x in (carrier_timestamp(carrier),worker_timestamp(worker)) if x is not None],
                default=None,
            ),
        },
        "hb_reference":{
            "state_ref":str(carrier_path),
            "observed":carrier is not None,
            "epoch":(carrier or {}).get("epoch"),
            "generation":(carrier or {}).get("generation"),
            "reference_frame":(carrier or {}).get("reference_frame"),
            "sample_age_seconds":carrier_age,
            "fresh":carrier_fresh,
            "freshness_threshold_seconds":max_age_seconds,
            "progression_grants_authority":False,
        },
        "worker_runtime":{
            "state_ref":str(worker_path),
            "control_plane_ref":str(control_path),
            "observed":worker is not None,
            "runtime_tick":(worker or {}).get("runtime_tick"),
            "observation_mode":(worker or {}).get("observation_mode"),
            "sample_age_seconds":worker_age,
            "fresh":worker_fresh,
            "worker_coordinator_observed":control is not None,
        },
        "governed_request":{
            "task_id":task_id or (request or {}).get("task_id"),
            "request_id":request_id,
            "request_ref":request_ref,
            "request_observed":request is not None,
            "admission_observed":admitted,
            "consumption_ref":consumption_ref,
            "consumption_observed":consumption_observed,
            "consumption_state":consumption_state,
            "runtime_execution_attempted":execution_attempted,
            "execution_transition_observed":execution_transition,
        },
        "retained_evidence":{
            "refs":sorted(set(retained)),
            "receipt_retained":bool(retained),
            "replay_observed":truth_marker(consumption,"replay"),
            "reconstruction_observed":truth_marker(consumption,"reconstruction"),
        },
        "distinct_runtime_predicates":{
            "resident_process_alive_supervised":supervised,
            "node_runtime_fresh":carrier_fresh and worker_fresh,
            "governed_request_consumed":consumption_observed,
            "runtime_execution_completed":bool(consumption and consumption_state in ("COMPLETED","ALREADY_CONSUMED")),
            "receipt_retained":bool(retained),
            "replay_reconstruction_proven":truth_marker(consumption,"reconstruction"),
        },
        "authority":{
            "heartbeat_grants_execution_authority":False,
            "heartbeat_grants_admission_authority":False,
            "heartbeat_grants_claim_fence_authority":False,
            "heartbeat_grants_transition_authority":False,
            "projection_grants_authority":False,
            "credential_authority":"TV/TVC",
            "github_token_runtime_authority":"NONE",
        },
    }
    return projection

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--runtime-root",type=Path,required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--max-age-seconds",type=float,default=120.0)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=project(args.runtime_root,task_id=args.task_id,max_age_seconds=args.max_age_seconds)
    output=(args.output or (args.runtime_root/DEFAULT_OUTPUT)).expanduser().resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_name("."+output.name+".tmp")
    tmp.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,output)
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
