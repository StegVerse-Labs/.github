#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

from refresh_and_dispatch_resident_requests import (
    REPO_ROOT,
    default_runtime_root,
    refresh_and_dispatch,
)

RECEIPT_REL=Path("receipts/sovereign-host/stegverse001-activation-progression.latest.json")
STAGE1="one_shot_resident_stack_activation"
STAGE2="stegverse001_bounded_autonomy"

Bridge=Callable[...,dict[str,Any]]

def atomic_json(path:Path,value:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name("."+path.name+".tmp")
    tmp.write_text(json.dumps(dict(value),indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def selected_result(receipt:Mapping[str,Any],consumer:str)->dict[str,Any]:
    if receipt.get("target_consumer")!=consumer:
        raise RuntimeError("progression bridge target mismatch")
    dispatch=receipt.get("dispatch_receipt")
    if not isinstance(dispatch,dict):
        raise RuntimeError("progression dispatch receipt absent")
    if dispatch.get("selection_scope")!="EXACT_SELECTOR":
        raise RuntimeError("progression dispatch was not exact-selector")
    if dispatch.get("selected_consumers")!=[consumer] or dispatch.get("consumer_count")!=1:
        raise RuntimeError("progression selected consumer mismatch")
    outcomes=dispatch.get("outcomes")
    if not isinstance(outcomes,list) or len(outcomes)!=1 or not isinstance(outcomes[0],dict):
        raise RuntimeError("progression exact outcome missing")
    outcome=outcomes[0]
    if outcome.get("consumer")!=consumer:
        raise RuntimeError("progression outcome consumer mismatch")
    result=outcome.get("result")
    if not isinstance(result,dict):
        raise RuntimeError("progression consumer machine result missing")
    return result

def stage1_next(state:str)->str:
    return {
      "SOURCE_ROOTS_PENDING":"MATERIALIZE_REQUIRED_LOCAL_SOURCE_ROOTS_AND_REEXECUTE_STAGE1",
      "ACTIVATION_IN_PROGRESS":"ALLOW_CURRENT_OUTER_ACTIVATION_TO_COMPLETE_THEN_REEXECUTE_BOUNDED_PROGRESSION",
      "ATTEMPT_RECORDED":"REPAIR_ONE_SHOT_ACTIVATION_RESULT_AND_REEXECUTE_STAGE1",
      "BLOCKED":"REPAIR_ONE_SHOT_ACTIVATION_BLOCKER_AND_REEXECUTE_STAGE1",
    }.get(state,"REPAIR_OR_EXECUTE_ONE_SHOT_STACK_ACTIVATION_AND_REEXECUTE_STAGE1")

def stage2_next(result:Mapping[str,Any])->str:
    state=str(result.get("state") or "UNKNOWN")
    if state=="LEASE_PENDING":
        return "EXECUTE_TVC_LEASE_ISSUANCE_PATH_AND_REEXECUTE_STAGE2"
    if state in {"ATTEMPT_RECORDED","BLOCKED"}:
        return "REPAIR_SV001_BOUNDED_AUTONOMY_TRANSITION_AND_REEXECUTE_STAGE2"
    return "EXECUTE_OR_REPAIR_SV001_BOUNDED_AUTONOMY_TRANSITION_AND_REEXECUTE_STAGE2"

def run(
    source_root:Path,
    runtime_root:Path,
    *,
    bridge:Bridge=refresh_and_dispatch,
    env:Mapping[str,str]|None=None,
)->dict[str,Any]:
    source=source_root.expanduser().resolve()
    runtime=runtime_root.expanduser().resolve()

    first=bridge(source,runtime,target_consumer=STAGE1,env=env)
    first_result=selected_result(first,STAGE1)
    first_state=str(first_result.get("state") or "UNKNOWN")
    first_complete=(
      first_state in {"COMPLETED","ALREADY_CONSUMED"}
      and first_result.get("activation_complete") is True
    )
    if not first_complete:
        out={
          "schema":"stegverse.stegverse001.activation-progression/v1",
          "state":"STACK_ACTIVATION_INCOMPLETE",
          "stage1_consumer":STAGE1,
          "stage1_bridge_receipt":first,
          "stage1_result":first_result,
          "stage1_complete":False,
          "stage2_consumer":STAGE2,
          "stage2_executed":False,
          "next_required_machine_transition":stage1_next(first_state),
          "looping_or_polling_performed":False,
          "network_source_fetch_performed":False,
          "request_grants_authority":False,
          "credential_authority":"TV/TVC",
          "github_token_runtime_authority":"NONE",
          "authority_effect":"NONE_BOUNDED_PROGRESSION_ONLY",
        }
        atomic_json(runtime/RECEIPT_REL,out)
        return out

    second=bridge(source,runtime,target_consumer=STAGE2,env=env)
    second_result=selected_result(second,STAGE2)
    second_state=str(second_result.get("state") or "UNKNOWN")
    terminal=(
      second_state in {"COMPLETED","ALREADY_CONSUMED"}
      and second_result.get("terminal_execution_observed") is True
    )
    out={
      "schema":"stegverse.stegverse001.activation-progression/v1",
      "state":"SV001_AUTONOMY_EXECUTION_COMPLETED" if terminal else "SV001_AUTONOMY_EXECUTION_INCOMPLETE",
      "stage1_consumer":STAGE1,
      "stage1_bridge_receipt":first,
      "stage1_result":first_result,
      "stage1_complete":True,
      "stage2_consumer":STAGE2,
      "stage2_bridge_receipt":second,
      "stage2_result":second_result,
      "stage2_executed":True,
      "stage2_terminal_execution_observed":terminal,
      "next_required_machine_transition":(
        "CONTINUE_MASTER_RECORDS_AND_SV002_SUCCESSORS" if terminal else stage2_next(second_result)
      ),
      "looping_or_polling_performed":False,
      "network_source_fetch_performed":False,
      "request_grants_authority":False,
      "credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE",
      "authority_effect":"NONE_BOUNDED_PROGRESSION_ONLY",
    }
    atomic_json(runtime/RECEIPT_REL,out)
    return out

def main()->int:
    p=argparse.ArgumentParser(description="Execute the bounded current-stack activation -> SV001 autonomy progression once.")
    p.add_argument("--source-root",type=Path,default=REPO_ROOT)
    p.add_argument("--runtime-root",type=Path,default=default_runtime_root())
    a=p.parse_args()
    receipt=run(a.source_root,a.runtime_root)
    print(json.dumps(receipt,sort_keys=True))
    return 0 if receipt["state"]=="SV001_AUTONOMY_EXECUTION_COMPLETED" else 1

if __name__=="__main__":
    raise SystemExit(main())
