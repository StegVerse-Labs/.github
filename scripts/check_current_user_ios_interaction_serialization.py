#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
q=json.loads((ROOT/"control/current-user-ios-interaction-queue.json").read_text())
assert q["schema"]=="stegverse.current-user-ios-interaction-queue/v1"
assert q["physical_device_count_required"]==1
assert q["second_user_operated_machine_required"] is False
assert q["github_token_runtime_authority"]=="NONE"
assert q["grants_workercoordinator_authority"] is False
assert q["grants_intr_authority"] is False
assert q["grants_tvc_authority"] is False
assert q["grants_custody_authority"] is False
assert q["grants_execution_authority"] is False
assert q["grants_credential_authority"] is False
if q["state"].startswith("HOLD_"):
    assert q["state_mutating_actions_permitted"] is False
    assert q["active_action_id"] is None
assert q["admission_rule"]["max_admitted_user_mutations"]==1
print("CURRENT_USER_IOS_INTERACTION_SERIALIZATION_PASS")
