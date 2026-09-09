#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "DECISION-ENVELOPE-DE006"
PROFILE_ID = "runtime-node:decision-envelope-de006"
PARENT_TASK_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
PARENT_REQUEST_ID = "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002"
OBSERVABILITY_REL = Path("control/runtime-observability-consumers/ecosystem-chat-sovereign-inference-001.json")
DE006_CONSUMER_REL = Path("control/runtime-observability-consumers/decision-envelope-de006.json")
PARENT_RUNNER_REL = Path("scripts/run_independent_ecosystem_chat_parent.py")
PARENT_ACTIVATION_REL = Path("receipts/ecosystem-chat-sovereign-inference/independent_parent_activation.latest.json")
OUTPUT_REL = Path("receipts/sovereign-host/de006-profiled-parent-reexecution.latest.json")
EXPECTED_BINDING_RECEIPT_SHA256 = "26728181de31c9b3d402c2cb30414a83aedfbfa175cc8fe7a1e2af68f5874fe4"
EXPECTED_JOURNAL_TAIL_SHA256 = "897b9c70e704243939659009ef8d2e9d5ba984d1c4d0edd835afdaf26c5f4b69"
EXPECTED_DEVICE_TASK = "STEGOS-LOCAL-INFERENCE-bde14fe691cc86924cee9a44"
EXPECTED_DEVICE_CLAIM = "STEGOS-STEGOS-LOCAL-INFERENCE-bde14fe691cc86924cee9a44-G11"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required: {path}")
    return value


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require_resident_env() -> None:
    active = [name for name in HOSTED_ENV if truthy(os.environ.get(name))]
    if active:
        raise RuntimeError("hosted environment may not execute DE-006 parent reexecution: " + ",".join(sorted(active)))


def verified_candidate(source: Path, runtime: Path) -> dict[str, Any]:
    path = runtime / OBSERVABILITY_REL
    if not path.is_file():
        path = source / OBSERVABILITY_REL
    data = load_json(path)
    evidence = data.get("pre_admission_evidence") or {}
    if not (
        evidence.get("state") == "PARENT_EVIDENCE_CANDIDATE_VERIFIED"
        and evidence.get("de006_execution_binding_verified") is True
        and evidence.get("task_id") == EXPECTED_DEVICE_TASK
        and evidence.get("claim_id") == EXPECTED_DEVICE_CLAIM
        and evidence.get("fencing_token") == 11
        and evidence.get("reconstruction_state") == "PASS"
        and evidence.get("same_execution") is True
        and evidence.get("replay_relation") == "VALID_APPEND_ONLY_DESCENDANT"
        and evidence.get("journal_tail_sha256") == EXPECTED_JOURNAL_TAIL_SHA256
        and evidence.get("bound_admitted_inference_receipt_sha256") == EXPECTED_BINDING_RECEIPT_SHA256
        and evidence.get("parent_execution_proven") is False
        and evidence.get("parent_fence_promoted") is False
    ):
        raise RuntimeError("exact DE-006 parent evidence candidate is not verified")
    return evidence


def parent_activation_verified(value: dict[str, Any] | None) -> bool:
    return bool(
        isinstance(value, dict)
        and value.get("schema") == "stegverse.ecosystem-chat-independent-parent-activation/v1"
        and value.get("task_id") == PARENT_TASK_ID
        and value.get("state") == "PASS"
        and isinstance(value.get("fencing_token"), int)
        and value.get("fencing_token") > 24
        and value.get("sovereign_runtime_execution_surface_observed") is True
        and value.get("ephemeral_e1_e2_execution_observed") is True
        and value.get("measured_usage_persisted") is True
        and value.get("provider_usage_reconstruction_pass") is True
        and value.get("transition_reconstruction_pass") is True
        and value.get("same_execution") is True
        and value.get("persistent_conversational_runtime_ready") is True
        and value.get("credential_authority") == "TV/TVC"
        and value.get("credential_requirement") == "NONE"
        and value.get("github_token_required") is False
    )


def run_parent(source: Path, runtime: Path) -> dict[str, Any]:
    runner = runtime / PARENT_RUNNER_REL
    if not runner.is_file():
        runner = source / PARENT_RUNNER_REL
    if not runner.is_file():
        return {"state":"DE006_PARENT_RUNNER_NOT_MATERIALIZED"}
    env = {k:v for k,v in os.environ.items() if k not in {"GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}}
    completed = subprocess.run(
        [sys.executable, str(runner), "--root", str(runtime)],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        timeout=7200,
        env=env,
    )
    result = None
    try:
        result = json.loads(completed.stdout)
    except Exception:
        pass
    return {
        "state": result.get("state") if isinstance(result, dict) else "DE006_PARENT_NO_MACHINE_RESULT",
        "returncode": completed.returncode,
        "result": result,
        "stderr_tail": completed.stderr[-1200:] if completed.returncode else None,
    }


def prior_verified(path: Path, activation: dict[str, Any]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        receipt = load_json(path)
    except Exception:
        return None
    return receipt if (
        receipt.get("schema") == "stegverse.de006-profiled-parent-reexecution/v1"
        and receipt.get("state") == "DE006_EXACT_PARENT_REEXECUTION_OBSERVED"
        and receipt.get("task_id") == TASK_ID
        and receipt.get("runtime_node_profile_id") == PROFILE_ID
        and receipt.get("parent_request_id") == PARENT_REQUEST_ID
        and receipt.get("parent_claim_id") == activation.get("claim_id")
        and receipt.get("parent_fencing_token") == activation.get("fencing_token")
        and receipt.get("candidate_receipt_sha256") == EXPECTED_BINDING_RECEIPT_SHA256
        and receipt.get("same_execution") is True
    ) else None


def execute(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    require_resident_env()
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    candidate = verified_candidate(source, runtime)
    activation_path = runtime / PARENT_ACTIVATION_REL
    activation = load_json(activation_path) if activation_path.is_file() else None
    parent_attempt = None
    if not parent_activation_verified(activation):
        parent_attempt = run_parent(source, runtime)
        activation = load_json(activation_path) if activation_path.is_file() else None
    if not parent_activation_verified(activation):
        return {
            "schema":"stegverse.de006-profiled-parent-reexecution/v1",
            "state":"DE006_EXACT_PARENT_REEXECUTION_PENDING",
            "task_id":TASK_ID,
            "runtime_node_profile_id":PROFILE_ID,
            "parent_request_id":PARENT_REQUEST_ID,
            "candidate_task_id":candidate.get("task_id"),
            "candidate_receipt_sha256":EXPECTED_BINDING_RECEIPT_SHA256,
            "parent_attempt":parent_attempt,
            "github_token_required":False,
            "credential_authority":"TV/TVC",
        }

    output = runtime / OUTPUT_REL
    prior = prior_verified(output, activation)
    if prior is not None:
        return {**prior, "reused":True}

    receipt = {
        "schema":"stegverse.de006-profiled-parent-reexecution/v1",
        "state":"DE006_EXACT_PARENT_REEXECUTION_OBSERVED",
        "task_id":TASK_ID,
        "runtime_node_profile_id":PROFILE_ID,
        "source_task":"DE-006",
        "parent_task_id":PARENT_TASK_ID,
        "parent_request_id":PARENT_REQUEST_ID,
        "candidate_task_id":candidate["task_id"],
        "candidate_claim_id":candidate["claim_id"],
        "candidate_fencing_token":candidate["fencing_token"],
        "candidate_receipt_sha256":EXPECTED_BINDING_RECEIPT_SHA256,
        "candidate_journal_tail_sha256":EXPECTED_JOURNAL_TAIL_SHA256,
        "candidate_parent_execution_proven":False,
        "candidate_fence_promoted":False,
        "parent_activation_ref":str(PARENT_ACTIVATION_REL),
        "parent_claim_id":activation.get("claim_id"),
        "parent_fencing_token":activation["fencing_token"],
        "parent_fence_independent_of_candidate":activation["fencing_token"] != candidate["fencing_token"],
        "sovereign_runtime_execution_surface_observed":True,
        "provider_usage_reconstruction_pass":True,
        "transition_reconstruction_pass":True,
        "same_execution":True,
        "persistent_conversational_runtime_ready":True,
        "credential_authority":"TV/TVC",
        "credential_requirement":"NONE",
        "github_token_required":False,
        "activation_effect":False,
        "authority_effect":"NONE_EVIDENCE_ONLY",
        "reused":False,
    }
    if receipt["parent_fencing_token"] <= 24 or not receipt["parent_fence_independent_of_candidate"]:
        raise RuntimeError("DE-006 parent fence is not an independently acquired G25+ fence")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, default=ROOT)
    p.add_argument("--runtime-root", type=Path, default=ROOT)
    args = p.parse_args()
    result = execute(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
