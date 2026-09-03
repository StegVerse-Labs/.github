#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCHEMA = "stegverse.ecosystem-chat.stegos-parent-evidence-candidate/v1"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


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
    )
    proof = report.get("proof") if isinstance(report, dict) else None
    return {
        "schema": SCHEMA,
        "state": "PARENT_EVIDENCE_CANDIDATE_VERIFIED" if accepted else "FAIL_CLOSED",
        "stegos_verifier_returncode": completed.returncode,
        "stegos_verifier_report": report,
        "device_local_execution_proven": accepted,
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
