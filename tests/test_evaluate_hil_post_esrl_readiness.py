import json
from pathlib import Path

from scripts import evaluate_hil_post_esrl_readiness as mod


def write(root: Path, rel: Path, value: dict):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def esrl():
    return {
        "schema": mod.ESRL_SCHEMA,
        "state": "ACCEPTED",
        "task_id": mod.TASK_ID,
        "lease_state": "LEASE_OPEN",
        "esrl_lease_open_observed": True,
    }



def consumption_ready():
    return {
        "schema": "stegverse.hil-resident-execution-request-consumption/v1",
        "state": "COMPLETED",
        "task_id": mod.TASK_ID,
        "terminal_hil_transition_observed": True,
        "terminal_hil_transition": "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED",
        "runtime_execution_attempted": True,
        "runtime_execution_surface": "CURRENT_USER_IPHONE_BROWSER",
        "second_machine_required": False,
        "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25",
        "fencing_token": 25,
    }

def worker():
    return {
        "schema": mod.WORKER_SCHEMA,
        "task_id": mod.TASK_ID,
        "receiver_ready": True,
    }


def restart():
    return {
        "schema": mod.RESTART_SCHEMA,
        "state": "PASS",
        "receiver_restart_reconstruction_observed": True,
        "reconstruction_state": "EXACT_BYTES_HASH_VERIFIED",
    }


def tvc():
    return {
        "schema": mod.TVC_SCHEMA,
        "state": "ADMITTED_TO_TVC_HIL_LIFECYCLE",
        "results": [{"admitted": True}],
    }


def test_without_esrl_stays_at_first_parent_blocker(tmp_path):
    value = mod.evaluate(repo_root=tmp_path)
    assert value["first_unresolved_stage"] == "ESRL_LEASE_OPEN"
    assert value["remaining_parent_blockers"] == list(mod.PARENT_BLOCKERS)


def test_accepted_esrl_advances_only_to_receiver_ready(tmp_path):
    ep = write(tmp_path, Path("esrl.json"), esrl())
    value = mod.evaluate(repo_root=tmp_path, esrl_intake=ep)
    assert value["first_unresolved_stage"] == "HIL_RECEIVER_READY_AND_CUSTODY"
    assert value["remaining_parent_blockers"] == list(mod.PARENT_BLOCKERS[1:])


def test_retained_resident_consumption_satisfies_receiver_ready_but_not_custody(tmp_path):
    ep = write(tmp_path, Path("esrl.json"), esrl())
    write(tmp_path, mod.CONSUMPTION_REL, consumption_ready())
    value = mod.evaluate(repo_root=tmp_path, esrl_intake=ep)
    assert value["first_unresolved_stage"] == "HIL_RECEIVER_CUSTODY"
    assert "receiver READY is retained" in value["reason"]
    assert value["second_user_device_required"] is False


def test_receiver_ready_does_not_imply_restart_proof(tmp_path):
    ep = write(tmp_path, Path("esrl.json"), esrl())
    write(tmp_path, mod.WORKER_REL, worker())
    value = mod.evaluate(repo_root=tmp_path, esrl_intake=ep)
    assert value["first_unresolved_stage"] == "POST_RESTART_EXACT_BYTE_PROOF"
    assert mod.PARENT_BLOCKERS[1] in value["remaining_parent_blockers"]


def test_restart_pass_advances_to_tvc_only(tmp_path):
    ep = write(tmp_path, Path("esrl.json"), esrl())
    write(tmp_path, mod.WORKER_REL, worker())
    write(tmp_path, mod.RESTART_REL, restart())
    value = mod.evaluate(repo_root=tmp_path, esrl_intake=ep)
    assert value["first_unresolved_stage"] == "TVC_HIL_LIFECYCLE_HANDOFF"
    assert value["remaining_parent_blockers"] == [mod.PARENT_BLOCKERS[2]]


def test_all_direct_receipts_clear_parent_runtime_evidence_only(tmp_path):
    ep = write(tmp_path, Path("esrl.json"), esrl())
    write(tmp_path, mod.WORKER_REL, worker())
    write(tmp_path, mod.RESTART_REL, restart())
    write(tmp_path, mod.TVC_REL, tvc())
    value = mod.evaluate(repo_root=tmp_path, esrl_intake=ep)
    assert value["state"] == "PARENT_RUNTIME_EVIDENCE_COMPLETE"
    assert value["remaining_parent_blockers"] == []
    assert value["source_or_ci_can_satisfy_runtime_predicate"] is False
    assert value["authority_effect"] == "NONE_READ_ONLY_CLASSIFICATION"
