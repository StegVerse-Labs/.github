#!/usr/bin/env python3
"""Validate existing StegOSMobile retained-node discovery evidence for GADI.

This projector is observation-only. It never creates runtime presence, supervision,
WorkerCoordinator claim/fence, InTr admission, credentials, leases, or execution
authority, and it must never emit CURRENT_RUNTIME_SUBJECT_BOUND.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
SOURCE_TASK_ID = "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
SOURCE_COSV = "40000100100000"
SOURCE_SCHEMA = "stegos.stegbrowser.current-iphone-rendezvous-observation/v1"
DISCOVERY_SCHEMA = "stegverse.resident-rendezvous.discovery/v1"
OUTPUT_SCHEMA = "stegverse.gadi-retained-node-discovery-observation/v1"
NODE_RE = re.compile(r"^SV-NODE-[0-9a-f]{24}$")
SHA_URI_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class GADIRetainedNodeDiscoveryError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GADIRetainedNodeDiscoveryError(message)


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha_uri(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def load_latest_jsonl(path: Path) -> dict[str, Any]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise GADIRetainedNodeDiscoveryError("retained-node discovery receipt log empty")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise GADIRetainedNodeDiscoveryError("retained-node discovery receipt must be object")
    return value


def project(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _require(receipt.get("schema") == SOURCE_SCHEMA, "source discovery receipt schema mismatch")
    _require(receipt.get("state") == "LOCAL_DISCOVERY_OBSERVED", "source discovery state mismatch")
    _require(receipt.get("task_id") == SOURCE_TASK_ID, "source discovery task mismatch")
    _require(receipt.get("cosv") == SOURCE_COSV, "source discovery COSV mismatch")
    _require(receipt.get("execution_surface") == "CURRENT_USER_IPHONE", "source execution surface mismatch")
    node_ref = receipt.get("node_ref")
    _require(isinstance(node_ref, str) and NODE_RE.fullmatch(node_ref) is not None, "canonical retained node ref required")
    _require(receipt.get("node_origin") == "STEGBROWSER_RESIDENT", "retained node origin mismatch")
    _require(receipt.get("heartbeat_grants_authority") is False, "heartbeat authority boundary invalid")
    _require(receipt.get("endpoint") == "http://127.0.0.1:8000", "retained-node loopback endpoint mismatch")
    _require(receipt.get("credential_authority") == "TV/TVC", "credential authority mismatch")
    _require(receipt.get("github_token_runtime_authority") == "NONE", "GitHub runtime authority mismatch")
    _require(receipt.get("authority_effect") == "NONE_COMPONENT_EVIDENCE_ONLY", "source authority effect mismatch")
    _require(receipt.get("intr_admission_observed") is False, "discovery receipt may not assert InTr admission")
    _require(receipt.get("workercoordinator_claim_observed") is False, "discovery receipt may not assert WorkerCoordinator claim")
    _require(receipt.get("canonical_request_consumption_observed") is False, "discovery receipt may not assert request consumption")

    discovery = receipt.get("discovery")
    _require(isinstance(discovery, Mapping), "embedded discovery response required")
    _require(discovery.get("schema") == DISCOVERY_SCHEMA, "embedded discovery schema mismatch")
    _require(discovery.get("state") == "AVAILABLE", "embedded discovery state mismatch")
    _require(discovery.get("target_node_ref") == node_ref, "embedded discovery node mismatch")
    _require(discovery.get("gateway_execution_authority") == "NONE", "gateway execution authority mismatch")
    _require(discovery.get("credential_authority") == "TV/TVC", "embedded credential authority mismatch")
    _require(discovery.get("discovery_grants_authority") is False, "discovery authority escalation")
    _require(discovery.get("authority_effect") == "NONE_DISCOVERY_ONLY", "embedded discovery authority effect mismatch")

    receipt_sha = receipt.get("receipt_sha256")
    envelope_sha = receipt.get("envelope_sha256")
    _require(isinstance(receipt_sha, str) and SHA_URI_RE.fullmatch(receipt_sha) is not None, "receipt digest missing")
    _require(isinstance(envelope_sha, str) and SHA_URI_RE.fullmatch(envelope_sha) is not None, "envelope digest missing")

    body = dict(receipt)
    for key in ("receipt_sha256", "retained_node_state_generation", "retained_node_state_commitment", "retained_node_transition_sequence", "retained_node_transition_commitment", "retained_node_lineage_bound", "envelope_sha256"):
        body.pop(key, None)
    _require(_sha_uri(body) == receipt_sha, "receipt body digest mismatch")

    envelope = dict(receipt)
    envelope.pop("envelope_sha256", None)
    _require(_sha_uri(envelope) == envelope_sha, "receipt envelope digest mismatch")

    generation = receipt.get("retained_node_state_generation")
    sequence = receipt.get("retained_node_transition_sequence")
    state_commitment = receipt.get("retained_node_state_commitment")
    transition_commitment = receipt.get("retained_node_transition_commitment")
    _require(isinstance(generation, int) and generation >= 1, "retained-node generation invalid")
    _require(isinstance(sequence, int) and sequence >= 1, "retained-node transition sequence invalid")
    _require(isinstance(state_commitment, str) and HEX64_RE.fullmatch(state_commitment) is not None, "retained-node state commitment invalid")
    _require(isinstance(transition_commitment, str) and HEX64_RE.fullmatch(transition_commitment) is not None, "retained-node transition commitment invalid")
    _require(receipt.get("retained_node_lineage_bound") is True, "retained-node lineage binding missing")

    core = {
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "node_ref": node_ref,
        "source_task_id": SOURCE_TASK_ID,
        "source_cosv": SOURCE_COSV,
        "source_receipt_sha256": receipt_sha,
        "source_envelope_sha256": envelope_sha,
        "retained_node_state_generation": generation,
        "retained_node_state_commitment": state_commitment,
        "retained_node_transition_sequence": sequence,
        "retained_node_transition_commitment": transition_commitment,
        "source_device_hb_reference": receipt.get("source_device_hb_reference"),
        "current_observed_hb_reference": receipt.get("current_observed_hb_reference"),
    }
    observation_ref = "runtime://gadi/retained-node-discovery/" + hashlib.sha256(_canonical_bytes(core)).hexdigest()
    return {
        "schema": OUTPUT_SCHEMA,
        **core,
        "state": "CURRENT_RETAINED_NODE_DISCOVERY_OBSERVED",
        "observation_ref": observation_ref,
        "runtime_presence_observed": False,
        "runtime_supervision_observed": False,
        "runtime_subject_bound": False,
        "intr_admission_observed": False,
        "workercoordinator_claim_observed": False,
        "canonical_request_consumption_observed": False,
        "claim_or_fence_granted": False,
        "runtime_lease_granted": False,
        "execution_authority_granted": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project(load_latest_jsonl(args.receipt_log.expanduser().resolve()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
