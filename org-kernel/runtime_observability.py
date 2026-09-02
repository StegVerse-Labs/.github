#!/usr/bin/env python3
"""Shared HB Runtime Presence / Resident Observability projection.

This module observes existing canonical runtime/evidence state. It never creates
execution, admission, routing, transition, credential, claim/fence, custody,
publication, receiving, or consequence authority.
"""
from __future__ import annotations
import hashlib, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location("stegverse_org_kernel",_HERE/"kernel.py")
K=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(K)

SCHEMA="stegverse.hb-runtime-resident-observability/v1"
DEFAULT_MAX_OBSERVER_AGE_SECONDS=30
CANONICAL_EVIDENCE={
    "resident_request_dispatch":"receipts/sovereign-host/resident-request-dispatch.latest.json",
    "resident_request_consumption":"receipts/sovereign-host/resident-execution-request-consumption.latest.json",
    "resident_targeted_execution":"receipts/sovereign-host/resident-targeted-execution.latest.json",
}

def _load(path:Path)->dict[str,Any]|None:
    if not path.is_file():
        return None
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"_invalid_json":True}
    return value if isinstance(value,dict) else {"_invalid_shape":True}

def _sha_file(path:Path)->str|None:
    if not path.is_file():
        return None
    return "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()

def _parse_time(value:Any)->datetime|None:
    if not isinstance(value,str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def _age_seconds(observed:Any, now:datetime)->float|None:
    dt=_parse_time(observed)
    if dt is None:
        return None
    return max(0.0,(now-dt).total_seconds())

def _evidence_summary(root:Path, rel:str)->dict[str,Any]:
    path=root/rel
    value=_load(path)
    out={"path":rel,"present":path.is_file(),"sha256":_sha_file(path)}
    if value is None:
        return out
    out["valid_json"]=not value.get("_invalid_json",False) and not value.get("_invalid_shape",False)
    if out["valid_json"]:
        for key in ("schema","schema_version","state","status","request_id","task_id","node_id",
                    "runtime_instance_id","worker_instance_id","receipt_hash","response_receipt_hash",
                    "observed_at","completed_at","consumed_at","executed_at"):
            if key in value:
                out[key]=value[key]
    return out

def snapshot(root:Path, *, now_ns:int|None=None, max_observer_age_seconds:int=DEFAULT_MAX_OBSERVER_AGE_SECONDS,
             evidence_bindings:dict[str,str]|None=None)->dict[str,Any]:
    root=Path(root).resolve()
    hb=K.hb_reference(now_ns)
    now=datetime.fromtimestamp(hb["sampled_unix_ns"]/1_000_000_000,tz=timezone.utc)

    activation=_load(root/"resident-runtime/activation-manifest.json") or {}
    carrier=_load(root/"control/heartbeat-carrier-runtime-state.json")
    worker=_load(root/"control/worker-runtime-state.json")
    coordination=_load(root/"control/worker-control-plane-coordination.json")

    carrier_age=_age_seconds((carrier or {}).get("last_cycle_at"),now)
    worker_age=_age_seconds((worker or {}).get("last_cycle_at"),now)

    bindings=dict(CANONICAL_EVIDENCE)
    if evidence_bindings:
        bindings.update(evidence_bindings)
    evidence={name:_evidence_summary(root,rel) for name,rel in sorted(bindings.items())}

    # Presence/currentness is intentionally fail-closed. Repository source state,
    # activation manifests, HB progression, or stale observer snapshots never
    # become a resident-process liveness claim.
    resident_presence_receipt=evidence.get("resident_presence")
    resident_observed=bool(
        resident_presence_receipt
        and resident_presence_receipt.get("present")
        and resident_presence_receipt.get("valid_json")
        and (resident_presence_receipt.get("runtime_instance_id") or resident_presence_receipt.get("node_id"))
        and resident_presence_receipt.get("observed_at")
    )
    resident_age=_age_seconds((resident_presence_receipt or {}).get("observed_at"),now) if resident_observed else None
    resident_current=bool(resident_observed and resident_age is not None and resident_age<=max_observer_age_seconds)

    result={
        "schema":SCHEMA,
        "organization":activation.get("organization"),
        "canonical_repository":activation.get("canonical_repository"),
        "hb_reference":hb,
        "authority":{
            "hb_grants_authority":False,
            "runtime_signal_grants_authority":False,
            "credential_authority":"TV/TVC",
            "github_actions_runtime_authority":"NONE",
        },
        "resident":{
            "activation_source_state":activation.get("state"),
            "source_installed":bool(activation),
            "process_observed":resident_observed,
            "current":resident_current,
            "observation_age_seconds":resident_age,
            "max_observer_age_seconds":max_observer_age_seconds,
            "identity":({
                "runtime_instance_id":resident_presence_receipt.get("runtime_instance_id"),
                "node_id":resident_presence_receipt.get("node_id"),
            } if resident_observed else None),
        },
        "persisted_observers":{
            "carrier":{
                "present":carrier is not None,
                "epoch":(carrier or {}).get("epoch"),
                "generation":(carrier or {}).get("generation"),
                "last_cycle_at":(carrier or {}).get("last_cycle_at"),
                "age_seconds":carrier_age,
                "current_within_threshold":bool(carrier_age is not None and carrier_age<=max_observer_age_seconds),
                "observation_only":True,
            },
            "worker":{
                "present":worker is not None,
                "runtime_tick":(worker or {}).get("runtime_tick"),
                "observation_mode":(worker or {}).get("observation_mode"),
                "last_cycle_at":(worker or {}).get("last_cycle_at"),
                "age_seconds":worker_age,
                "current_within_threshold":bool(worker_age is not None and worker_age<=max_observer_age_seconds),
                "observation_only":True,
            },
        },
        "worker_coordination":{
            "state":((coordination or {}).get("worker_coordination") or {}).get("state"),
            "active_lease_count":len(((coordination or {}).get("worker_coordination") or {}).get("active_leases") or []),
            "lease_presence_grants_authority":False,
        },
        "evidence":evidence,
        "runtime_truth":{
            "resident_process_current":resident_current,
            "governed_request_consumption_proven":False,
            "receiver_ready_proven":False,
            "execution_or_state_transition_proven":False,
            "reconstruction_proven":False,
            "note":"These predicates remain false until a lane-specific verifier admits direct machine-produced receipts. Evidence-file presence alone is not promoted."
        },
    }
    body=dict(result)
    result["projection_sha256"]="sha256:"+hashlib.sha256(K.canon(body)).hexdigest()
    return result

def bind_lane(snapshot_value:dict[str,Any], *, lane_id:str, predicates:dict[str,str])->dict[str,Any]:
    if snapshot_value.get("schema")!=SCHEMA:
        raise ValueError("observability_snapshot_schema_invalid")
    missing=[]
    bound={}
    evidence=snapshot_value.get("evidence") or {}
    for predicate,evidence_name in predicates.items():
        row=evidence.get(evidence_name)
        bound[predicate]={"evidence_name":evidence_name,"evidence":row}
        if not row or not row.get("present"):
            missing.append(predicate)
    return {
        "schema":"stegverse.hb-runtime-resident-observability.lane-binding/v1",
        "lane_id":lane_id,
        "hb_reference":snapshot_value["hb_reference"],
        "resident":snapshot_value["resident"],
        "predicates":bound,
        "missing_evidence_predicates":missing,
        "authority_effect":"NONE_OBSERVATION_ONLY",
    }
