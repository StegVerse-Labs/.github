#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
Q=ROOT/"control/current-user-ios-interaction-queue.json"

def fail(msg:str)->None:
    raise SystemExit("FAIL: "+msg)

def main()->int:
    q=json.loads(Q.read_text())
    if q.get("schema")!="stegverse.current-user-ios-interaction-queue/v1": fail("schema")
    if q.get("physical_device_count_required")!=1: fail("device count")
    if q.get("second_user_operated_machine_required") is not False: fail("second-machine dependency")
    for key in (
        "grants_workercoordinator_authority","grants_intr_authority","grants_tvc_authority",
        "grants_custody_authority","grants_execution_authority","grants_credential_authority"
    ):
        if q.get(key) is not False: fail(key+" widened")
    if q.get("github_token_runtime_authority")!="NONE": fail("GitHub runtime authority")
    actions=q.get("candidate_actions") or []
    ids=[a.get("action_id") for a in actions]
    if len(ids)!=len(set(ids)): fail("duplicate action_id")
    admitted=[a for a in actions if a.get("queue_state")=="ADMITTED_FOR_USER_EXECUTION"]
    if len(admitted)>q["admission_rule"]["max_admitted_user_mutations"]: fail("multiple admitted mutations")
    if q.get("active_action_id") is None and admitted: fail("admitted action without active_action_id")
    if q.get("active_action_id") is not None:
        if len(admitted)!=1 or admitted[0].get("action_id")!=q["active_action_id"]: fail("active action mismatch")
    if q.get("state","").startswith("HOLD_"):
        if q.get("state_mutating_actions_permitted") is not False: fail("hold permits mutation")
        if admitted or q.get("active_action_id") is not None: fail("hold has admitted mutation")
    for a in actions:
        if a.get("rerun_terminal_source") is True: fail("terminal rerun admitted")
    resolved=q.get("resolved_non_mutation_intents") or []
    for r in resolved:
        if r.get("human_device_mutation_required") is not False: fail("resolved non-mutation intent requires mutation")
    print("CURRENT_USER_IOS_INTERACTION_QUEUE_PASS")
    print("candidate_count="+str(len(actions)))
    print("admitted_count="+str(len(admitted)))
    print("state="+str(q.get("state")))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
