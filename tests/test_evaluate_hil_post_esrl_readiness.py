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
