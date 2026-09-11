import json
from pathlib import Path

from scripts.stage_hil_esrl_exact_byte_acceptance import stage

ROOT = Path(__file__).resolve().parents[1]


def _artifact():
    return {
        "schema": "stegverse.hil-browser-esrl-lease-open/v1",
        "state": "LEASE_OPEN",
        "lease_state": "LEASE_OPEN",
        "lease_id": "HIL-BROWSER-ESRL-7bafde4a280e847758da157e",
        "hil_esrl_protocol": "HIL_BROWSER_ESRL_V1",
        "source_browser_protocol": "HIL_BROWSER_EVIDENCE_V16",
        "task_id": "SHWP-HIL-SOVEREIGN-RECEIVER-001",
        "resident_request_id": "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002",
        "resident_request_sha256": "6bf940fb920f672111ba1040fd0bf9bf7016d6bf032bbcfd164a1a2347ee7038",
        "node_id": "stegnode-web-f24e3bfb7f5343cb37323187a88e51f3",
        "browser_context_id": "ctx_d151139d2db1eeecb6512f5844058246",
        "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25",
        "fencing_token": 25,
        "canonical_checkout_receipt_sha256": "sha256:d40bd74a37850f8c0d4020fe3ba033b9dff04577e20b31bbfbfbfbe9d6ae70ef2e",
        "source_execution_entry_sha256": "8ddd8c6fc08038ce4111b349f47a5f44bd48a7bfbc551fae1bfb59a1a384da69",
        "binding_sha256": "sha256:7bafde4a280e847758da157ee03c2ac8310b745931d90a333639d7728d0c98e8",
        "state_machine": ["REQUESTED", "ADMITTED", "PROVISIONING", "LOCAL_READY", "LEASE_OPEN"],
        "runtime_class": "EVENT_EPHEMERAL",
        "lease_profile": "INTAKE",
        "runtime_materialized": True,
        "local_identity_verified": True,
        "local_ready_source_observed": True,
        "journal_replay_state": "PASS",
        "public_https_rendezvous_observed": False,
        "public_observation_is_downstream_optional": True,
        "same_device_execution_required": True,
        "execution_surface": "CURRENT_USER_IPHONE",
        "requires_other_machine": False,
        "second_claim_minted": False,
        "request_consumption_claimed": False,
        "custody_observed": False,
        "post_restart_exact_byte_proof_observed": False,
        "tvc_lifecycle_receipt_observed": False,
        "broader_hil_lifecycle_complete": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_granted_authority": False,
        "authority_effect": "NONE_RUNTIME_OBSERVATION_ONLY",
        "observed_at": "2026-09-11T02:02:11.968Z",
    }


def test_stages_exact_bytes_and_builds_two_blocker_proposal(tmp_path):
    artifact_path = tmp_path / "physical.json"
    raw = json.dumps(_artifact(), indent=2, sort_keys=False).encode("utf-8") + b"\n"
    artifact_path.write_bytes(raw)
    out = tmp_path / "staged"
    result = stage(repo_root=ROOT, artifact_path=artifact_path, output_dir=out)
    assert result["state"] == "READY_FOR_EXACT_BYTE_CANONICAL_INTAKE"
    assert result["intake_state"] == "ACCEPTED"
    assert result["previous_vector"] == "50000000103000"
    assert result["proposed_vector"] == "50000000102000"
    assert result["remaining_blockers"] == [
        "POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED",
        "TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN",
    ]
    assert result["next_runtime_stage"] == "HIL_RECEIVER_READY_AND_CUSTODY"
    assert result["canonical_mutation_performed"] is False
    assert result["runtime_mutation_performed"] is False
    staged = out / result["staged_exact_artifact"]
    assert staged.read_bytes() == raw


def test_rejects_non_lease_open_artifact(tmp_path):
    artifact = _artifact()
    artifact["state"] = "LOCAL_READY"
    artifact_path = tmp_path / "bad.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    try:
        stage(repo_root=ROOT, artifact_path=artifact_path, output_dir=tmp_path / "out")
    except Exception as exc:
        assert "esrl_lease_open_not_observed" in str(exc)
    else:
        raise AssertionError("invalid artifact was accepted")
