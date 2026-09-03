from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from scripts.verify_stegos_parent_evidence_candidate import verify


def test_candidate_verifier_preserves_device_local_parent_boundary() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "stegos"
        bundle = Path(td) / "bundle.json"
        verifier = root / "scripts/verify_device_task_execution_proof.py"
        verifier.parent.mkdir(parents=True)
        verifier.write_text("# placeholder\n", encoding="utf-8")
        bundle.write_text("{}\n", encoding="utf-8")
        report = {
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
        def runner(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 0, stdout=json.dumps(report), stderr="")
        result = verify(root, bundle, runner=runner)
        assert result["state"] == "PARENT_EVIDENCE_CANDIDATE_VERIFIED"
        assert result["device_local_execution_proven"] is True
        assert result["parent_execution_proven"] is False
        assert result["global_workercoordinator_authority"] is False
        assert result["device_local_fence_promoted_to_parent_fence"] is False
        assert result["second_user_operated_machine_required"] is False
        assert result["authority_effect"] == "NONE_OBSERVATION_ADMISSION_CANDIDATE_ONLY"
