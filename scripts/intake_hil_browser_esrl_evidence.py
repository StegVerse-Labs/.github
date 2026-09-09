#!/usr/bin/env python3
"""Validate exact current-iPhone HIL browser ESRL LEASE_OPEN evidence.

Source/CI/merge do not satisfy the runtime predicate. This intake only accepts an
exact exported component artifact whose subject bindings agree with the already
canonical G25 request-consumption receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
REQUEST_ID = "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002"
REQUEST_SHA256 = "6bf940fb920f672111ba1040fd0bf9bf7016d6bf032bbcfd164a1a2347ee7038"
SOURCE_PROTOCOL = "HIL_BROWSER_EVIDENCE_V16"
ESRL_PROTOCOL = "HIL_BROWSER_ESRL_V1"
ARTIFACT_SCHEMA = "stegverse.hil-browser-esrl-lease-open/v1"
RECEIPT_SCHEMA = "stegverse.hil-browser-esrl-evidence-intake/v1"
CANONICAL_RECEIPT_REL = Path("receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json")
EXPECTED_STATES = ["REQUESTED", "ADMITTED", "PROVISIONING", "LOCAL_READY", "LEASE_OPEN"]


class IntakeError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise IntakeError(reason)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"json_object_required:{path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_sha256_uri(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        return False
    return all(ch in "0123456789abcdef" for ch in value[7:])


def validate_artifact(artifact: Mapping[str, Any], canonical: Mapping[str, Any]) -> dict[str, Any]:
    execution = canonical.get("execution_result")
    require(isinstance(execution, Mapping), "canonical_execution_result_required")
    require(canonical.get("schema") == "stegverse.hil-resident-execution-request-consumption/v1", "canonical_receipt_schema_invalid")
    require(canonical.get("state") == "COMPLETED", "canonical_request_consumption_not_completed")
    require(canonical.get("task_id") == TASK_ID, "canonical_task_mismatch")
    require(canonical.get("request_id") == REQUEST_ID and canonical.get("request_sha256") == REQUEST_SHA256, "canonical_request_binding_mismatch")
    require(canonical.get("terminal_hil_transition_observed") is True, "canonical_terminal_transition_not_observed")

    require(artifact.get("schema") == ARTIFACT_SCHEMA, "artifact_schema_invalid")
    require(artifact.get("state") == "LEASE_OPEN" and artifact.get("lease_state") == "LEASE_OPEN", "esrl_lease_open_not_observed")
    require(artifact.get("hil_esrl_protocol") == ESRL_PROTOCOL, "esrl_protocol_invalid")
    require(artifact.get("source_browser_protocol") == SOURCE_PROTOCOL, "source_browser_protocol_invalid")
    require(artifact.get("task_id") == TASK_ID, "artifact_task_mismatch")
    require(artifact.get("resident_request_id") == REQUEST_ID and artifact.get("resident_request_sha256") == REQUEST_SHA256, "artifact_request_binding_mismatch")
    require(artifact.get("browser_context_id") == canonical.get("browser_context_id") == execution.get("browser_context_id"), "browser_context_mismatch")
    require(artifact.get("node_id") == execution.get("node_id"), "node_identity_mismatch")
    require(artifact.get("claim_id") == canonical.get("claim_id") == execution.get("claim_id"), "claim_mismatch")
    require(artifact.get("fencing_token") == canonical.get("fencing_token") == execution.get("fencing_token"), "fencing_token_mismatch")
    require(artifact.get("source_execution_entry_sha256") == execution.get("execution_entry_sha256"), "source_execution_entry_mismatch")
    require(artifact.get("journal_replay_state") == "PASS" == execution.get("journal_replay_state"), "journal_replay_not_pass")
    require(is_sha256_uri(artifact.get("canonical_checkout_receipt_sha256")), "checkout_receipt_sha256_invalid")
    require(is_sha256_uri(artifact.get("binding_sha256")), "binding_sha256_invalid")
    lease_id = artifact.get("lease_id")
    require(isinstance(lease_id, str) and lease_id == "HIL-BROWSER-ESRL-" + artifact["binding_sha256"][7:31], "deterministic_lease_id_mismatch")
    require(artifact.get("state_machine") == EXPECTED_STATES, "esrl_state_machine_invalid")
    require(artifact.get("runtime_class") == "EVENT_EPHEMERAL" and artifact.get("lease_profile") == "INTAKE", "runtime_profile_invalid")
    require(artifact.get("runtime_materialized") is True, "runtime_materialization_not_observed")
    require(artifact.get("local_identity_verified") is True and artifact.get("local_ready_source_observed") is True, "local_identity_or_ready_not_verified")
    require(artifact.get("execution_surface") == "CURRENT_USER_IPHONE", "execution_surface_invalid")
    require(artifact.get("same_device_execution_required") is True and artifact.get("requires_other_machine") is False, "same_device_boundary_invalid")
    require(artifact.get("public_https_rendezvous_observed") is False and artifact.get("public_observation_is_downstream_optional") is True, "public_rendezvous_boundary_invalid")
    require(artifact.get("credential_authority") == "TV/TVC", "credential_authority_invalid")
    require(artifact.get("github_token_runtime_authority") == "NONE", "github_runtime_authority_forbidden")
    require(artifact.get("heartbeat_granted_authority") is False, "heartbeat_authority_forbidden")
    require(artifact.get("second_claim_minted") is False and artifact.get("request_consumption_claimed") is False, "claim_or_consumption_promotion_forbidden")
    for key in ("custody_observed", "post_restart_exact_byte_proof_observed", "tvc_lifecycle_receipt_observed", "broader_hil_lifecycle_complete"):
        require(artifact.get(key) is False, f"unexpected_downstream_claim:{key}")
    require(artifact.get("authority_effect") == "NONE_RUNTIME_OBSERVATION_ONLY", "authority_effect_invalid")

    return {
        "schema": RECEIPT_SCHEMA,
        "state": "ACCEPTED",
        "task_id": TASK_ID,
        "request_id": REQUEST_ID,
        "browser_context_id": artifact["browser_context_id"],
        "node_id": artifact["node_id"],
        "claim_id": artifact["claim_id"],
        "fencing_token": artifact["fencing_token"],
        "lease_id": artifact["lease_id"],
        "lease_state": "LEASE_OPEN",
        "runtime_execution_surface": "CURRENT_USER_IPHONE_BROWSER",
        "esrl_lease_open_observed": True,
        "post_restart_exact_byte_proof_observed": False,
        "tvc_lifecycle_receipt_observed": False,
        "broader_hil_lifecycle_complete": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_EVIDENCE_INTAKE_ONLY",
    }


def intake(*, repo_root: Path, artifact_path: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    artifact_file = artifact_path.resolve()
    canonical_path = root / CANONICAL_RECEIPT_REL
    artifact_bytes = artifact_file.read_bytes()
    artifact = json.loads(artifact_bytes.decode("utf-8"))
    require(isinstance(artifact, dict), "artifact_object_required")
    canonical = load_object(canonical_path)
    receipt = validate_artifact(artifact, canonical)
    receipt["source_artifact_sha256"] = "sha256:" + sha256_bytes(artifact_bytes)
    receipt["canonical_request_consumption_ref"] = str(CANONICAL_RECEIPT_REL)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        receipt = intake(repo_root=args.repo_root, artifact_path=args.artifact)
    except Exception as exc:
        print(json.dumps({"schema": RECEIPT_SCHEMA, "state": "FAIL_CLOSED", "reason": f"{type(exc).__name__}:{exc}", "authority_effect": "NONE"}, sort_keys=True))
        return 1
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
