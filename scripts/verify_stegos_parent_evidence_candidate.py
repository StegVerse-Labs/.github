#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCHEMA = "stegverse.ecosystem-chat.stegos-parent-evidence-candidate/v1"
DE006_BINDING = {
    "schema": "stegos.web_execution_binding.v1",
    "goal_id": "DE-006",
    "task_id": "DE-006",
    "source_repository": "Admissible-Existence/GCAT-BCAT",
    "review_tag": "decision-envelope-review-v0.1.0",
    "review_commit": "7e053d007e416ff51e76cb4e9c0ffd73943b3acc",
    "authority_effect": "NONE_BINDING_ONLY",
}


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value



def de006_binding_receipt(bundle_value: dict, proof: dict | None) -> dict | None:
    rows = bundle_value.get("receipts")
    if not isinstance(rows, list) or not isinstance(proof, dict):
        return None
    task_id = proof.get("task_id")
    claim_id = proof.get("claim_id")
    fence = proof.get("fencing_token")
    claim_row = next(
        (
            row for row in reversed(rows)
            if isinstance(row, dict)
            and isinstance(row.get("receipt"), dict)
            and row["receipt"].get("schema") == "stegos.web_task_claim_receipt.v1"
            and row["receipt"].get("task_id") == task_id
            and row["receipt"].get("claim_id") == claim_id
            and row["receipt"].get("fencing_token") == fence
        ),
        None,
    )
    request_sha = (claim_row or {}).get("receipt", {}).get("request_sha256")
    if not isinstance(request_sha, str):
        return None
    admitted = next(
        (
            row.get("receipt") for row in reversed(rows)
            if isinstance(row, dict)
            and isinstance(row.get("receipt"), dict)
            and row["receipt"].get("schema") == "stegos.web_admitted_inference_receipt.v1"
            and row["receipt"].get("request_sha256") == request_sha
            and row["receipt"].get("execution_binding") == DE006_BINDING
        ),
        None,
    )
    return admitted if isinstance(admitted, dict) else None

def verify(stegos_root: Path, bundle: Path, *, runner=subprocess.run) -> dict:
    root = stegos_root.expanduser().resolve()
    bundle = bundle.expanduser().resolve()
    verifier = root / "scripts/verify_device_task_execution_proof.py"
    if not verifier.is_file():
        raise RuntimeError("canonical StegOS device-task verifier missing")
    if not bundle.is_file():
        raise RuntimeError("StegOS evidence bundle missing")

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }
    completed = runner(
        [sys.executable, str(verifier), str(bundle)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=60,
    )
    report = None
    try:
        report = json.loads(completed.stdout)
    except Exception:
        report = None
    bundle_value = load_json(bundle)
    proof = report.get("proof") if isinstance(report, dict) else None
    bound_receipt = de006_binding_receipt(bundle_value, proof)

    accepted = bool(
        completed.returncode == 0
        and isinstance(report, dict)
        and report.get("state") == "PASS"
        and report.get("physical_acceptance") == "ACCEPTED"
        and report.get("independent_replay_verified") is True
        and isinstance(report.get("proof"), dict)
        and report["proof"].get("task_scope") == "DEVICE_LOCAL_INFERENCE_ONLY"
        and report["proof"].get("global_workercoordinator_authority") is False
        and report["proof"].get("same_execution") is True
        and report["proof"].get("reconstruction_state") == "PASS"
        and report["proof"].get("credential_authority") == "TV/TVC"
        and report["proof"].get("external_non_stegverse_machine_required") is False
        and isinstance(bound_receipt, dict)
        and bound_receipt.get("execution_binding") == DE006_BINDING
        and bound_receipt.get("credential_authority") == "TV/TVC"
        and bound_receipt.get("credential_requirement") == "NONE"
        and bound_receipt.get("github_token_required") is False
        and bound_receipt.get("external_non_stegverse_machine_used") is False
    )
    return {
        "schema": SCHEMA,
        "state": "PARENT_EVIDENCE_CANDIDATE_VERIFIED" if accepted else "FAIL_CLOSED",
        "stegos_verifier_returncode": completed.returncode,
        "stegos_verifier_report": report,
        "device_local_execution_proven": bool(
            isinstance(report, dict) and report.get("state") == "PASS"
        ),
        "de006_execution_binding_verified": accepted,
        "de006_execution_binding": DE006_BINDING if accepted else None,
        "bound_admitted_inference_receipt": bound_receipt,
        "parent_execution_proven": False,
        "global_workercoordinator_authority": False,
        "device_local_fence_promoted_to_parent_fence": False,
        "task_id": proof.get("task_id") if isinstance(proof, dict) else None,
        "claim_id": proof.get("claim_id") if isinstance(proof, dict) else None,
        "fencing_token": proof.get("fencing_token") if isinstance(proof, dict) else None,
        "reconstruction_state": proof.get("reconstruction_state") if isinstance(proof, dict) else None,
        "same_execution": proof.get("same_execution") if isinstance(proof, dict) else False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "network_fetch_performed": False,
        "second_user_operated_machine_required": False,
        "authority_effect": "NONE_OBSERVATION_ADMISSION_CANDIDATE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stegos-root", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.stegos_root, args.bundle)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["state"] == "PARENT_EVIDENCE_CANDIDATE_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
