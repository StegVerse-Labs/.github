from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from scripts.verify_stegos_parent_evidence_candidate import DE006_BINDING, verify


def make_report() -> dict:
    return {
        "state": "PASS",
        "physical_acceptance": "ACCEPTED",
        "independent_replay_verified": True,
        "proof": {
            "task_scope": "DEVICE_LOCAL_INFERENCE_ONLY",
            "global_workercoordinator_authority": False,
            "same_execution": True,
            "reconstruction_state": "PASS",
            "credential_authority": "TV/TVC",
            "external_non_stegverse_machine_required": False,
            "task_id": "T1",
            "claim_id": "C1",
            "fencing_token": 7,
        },
    }


def make_bundle(binding: dict) -> dict:
    return {
        "schema": "stegos.web_bootstrap_evidence_bundle.v1",
        "receipts": [
            {
                "receipt": {
                    "schema": "stegos.web_task_claim_receipt.v1",
                    "task_id": "T1",
                    "claim_id": "C1",
                    "fencing_token": 7,
                    "request_sha256": "a" * 64,
                }
            },
            {
                "receipt": {
                    "schema": "stegos.web_admitted_inference_receipt.v1",
                    "request_sha256": "a" * 64,
                    "execution_binding": binding,
                    "credential_authority": "TV/TVC",
                    "credential_requirement": "NONE",
                    "github_token_required": False,
                    "external_non_stegverse_machine_used": False,
                }
            },
        ],
    }


def run_case(binding: dict) -> dict:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "stegos"
        bundle = Path(td) / "bundle.json"
        verifier = root / "scripts/verify_device_task_execution_proof.py"
        verifier.parent.mkdir(parents=True)
        verifier.write_text("# placeholder\n", encoding="utf-8")
        bundle.write_text(json.dumps(make_bundle(binding)), encoding="utf-8")
        report = make_report()

        def runner(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 0, stdout=json.dumps(report), stderr="")

        return verify(root, bundle, runner=runner)


def test_candidate_verifier_requires_exact_de006_binding_and_preserves_parent_boundary() -> None:
    result = run_case(dict(DE006_BINDING))
    assert result["state"] == "PARENT_EVIDENCE_CANDIDATE_VERIFIED"
    assert result["device_local_execution_proven"] is True
    assert result["de006_execution_binding_verified"] is True
    assert result["de006_execution_binding"] == DE006_BINDING
    assert result["parent_execution_proven"] is False
    assert result["global_workercoordinator_authority"] is False
    assert result["device_local_fence_promoted_to_parent_fence"] is False
    assert result["second_user_operated_machine_required"] is False
    assert result["authority_effect"] == "NONE_OBSERVATION_ADMISSION_CANDIDATE_ONLY"


def test_wrong_review_commit_fails_closed_even_when_device_task_verifier_passes() -> None:
    binding = dict(DE006_BINDING)
    binding["review_commit"] = "0" * 40
    result = run_case(binding)
    assert result["state"] == "FAIL_CLOSED"
    assert result["device_local_execution_proven"] is True
    assert result["de006_execution_binding_verified"] is False
    assert result["parent_execution_proven"] is False
