from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

MIR_ONE_WAY_SCHEMA = "stegverse.mir-mirror-one-way-transition-evidence/v1"
MIR_CONFIRMATION_SCHEMA = "stegverse.mir-state-transition-confirmation/v1"


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _binding() -> tuple[Path, Path] | dict[str, Any]:
    raw_roots = os.getenv("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    runtime_raw = os.getenv("STEGVERSE_HEARTBEAT_ROOT", "").strip()
    if not raw_roots or not runtime_raw:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_RUNTIME_BINDING_MISSING","authority_effect":"NONE"}
    roots = json.loads(raw_roots)
    if not isinstance(roots, dict):
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_REPOSITORY_MAP_INVALID","authority_effect":"NONE"}
    root_raw = roots.get("master-records/orchestration")
    if not isinstance(root_raw, str) or not root_raw:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_ORCHESTRATION_ROOT_MISSING","authority_effect":"NONE"}
    mr_root = Path(root_raw).expanduser().resolve()
    ingest = mr_root / "scripts/ingest_reusable_task_lifecycle.py"
    reconstruct = mr_root / "scripts/reconstruct_reusable_task_lifecycle.py"
    if not ingest.is_file() or not reconstruct.is_file():
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_REUSABLE_LIFECYCLE_SOURCE_MISSING","authority_effect":"NONE"}
    runtime_root = Path(runtime_raw).expanduser().resolve()
    custody_root = runtime_root / "master-records" / "reusable-task-lifecycle"
    return mr_root, custody_root


def _roundtrip_one(request_path: Path, *, binding: tuple[Path, Path] | None = None) -> dict[str, Any]:
    resolved = binding if binding is not None else _binding()
    if isinstance(resolved, dict):
        return resolved
    mr_root, custody_root = resolved
    ingest = mr_root / "scripts/ingest_reusable_task_lifecycle.py"
    reconstruct = mr_root / "scripts/reconstruct_reusable_task_lifecycle.py"
    reconstructed = request_path.with_name(request_path.stem + ".reconstructed.json")
    env = {key: os.environ[key] for key in ("PATH","PYTHONPATH","LANG","LC_ALL") if key in os.environ}
    first = subprocess.run([sys.executable, str(ingest), "--request", str(request_path), "--custody-root", str(custody_root)], cwd=mr_root, env=env, text=True, capture_output=True, check=False, timeout=60)
    if first.returncode != 0:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_INGEST_FAILED","returncode":first.returncode,"stderr_tail":first.stderr[-1200:],"authority_effect":"NONE"}
    try:
        ingest_result = json.loads(first.stdout.strip().splitlines()[-1])
        custody_ref = Path(str(ingest_result["custody_ref"]))
    except Exception:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_INGEST_RESULT_INVALID","authority_effect":"NONE"}
    second = subprocess.run([sys.executable, str(reconstruct), "--record", str(custody_ref), "--custody-root", str(custody_root), "--output", str(reconstructed)], cwd=mr_root, env=env, text=True, capture_output=True, check=False, timeout=60)
    if second.returncode != 0 or not reconstructed.is_file():
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_RECONSTRUCTION_FAILED","returncode":second.returncode,"stderr_tail":second.stderr[-1200:],"authority_effect":"NONE"}
    if reconstructed.read_bytes() != request_path.read_bytes():
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_RECONSTRUCTION_BYTES_MISMATCH","authority_effect":"NONE"}
    record = json.loads(custody_ref.read_text(encoding="utf-8"))
    return {"state":"RETURNED","custody_ref":str(custody_ref),"reconstructed_ref":str(reconstructed),"record":record,"authority_effect":"NONE"}


def _mir_transition_packets(value: dict[str, Any]) -> list[dict[str, Any]]:
    common = {
        "schema": MIR_CONFIRMATION_SCHEMA,
        "goal_task_id": value.get("goal_task_id"),
        "root_goal_task_id": value.get("root_goal_task_id"),
        "cosv_task_vector": value.get("cosv_task_vector"),
        "claim_id": value.get("claim_id"),
        "fencing_token": value.get("fencing_token"),
        "destination_profile": value.get("destination_profile"),
        "destination": value.get("destination"),
        "provenance": value.get("provenance"),
        "authority_effect": "NONE_CONFIRMATION_EVIDENCE_ONLY",
        "master_records_may_grant_transition_authority": False,
    }
    rows = [
        (1, "CURRENT_GOAL_COSV_BOUND", {
            "goal_task_id": value.get("goal_task_id"),
            "cosv_task_vector": value.get("cosv_task_vector"),
            "claim_id": value.get("claim_id"),
            "fencing_token": value.get("fencing_token"),
        }),
        (2, "CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED", value.get("request_ingress_receipt")),
        (3, "RTC-STEGVERSE-EGRESS-007", value.get("response_egress_receipt")),
        (4, "RTC-INTERLOCK-INTR-TRANSPORT-008", {
            "request_ingress_receipt": value.get("request_ingress_receipt"),
            "response_egress_receipt": value.get("response_egress_receipt"),
            "receipt_chain_linked": value.get("receipt_chain_linked"),
        }),
        (5, "RTC-FARSIDE-FINAL-009", value.get("mir_external_ingress_receipt")),
        (6, "MIR_DESTINATION_EVIDENCE_RETAINED", value.get("return_queue_receipt")),
        (7, "EXACT_GOVERNED_RETURN_PACKET_RETAINED", {
            "response_packet_sha256": value.get("response_packet_sha256"),
        }),
    ]
    packets: list[dict[str, Any]] = []
    for sequence, transition_id, evidence in rows:
        observed = evidence is not None
        if isinstance(evidence, dict) and transition_id == "RTC-INTERLOCK-INTR-TRANSPORT-008":
            observed = evidence.get("receipt_chain_linked") is True and isinstance(evidence.get("request_ingress_receipt"), dict) and isinstance(evidence.get("response_egress_receipt"), dict)
        elif isinstance(evidence, dict) and transition_id == "CURRENT_GOAL_COSV_BOUND":
            observed = all(evidence.get(key) not in (None, "") for key in ("goal_task_id", "cosv_task_vector", "claim_id", "fencing_token"))
        elif isinstance(evidence, dict) and transition_id == "EXACT_GOVERNED_RETURN_PACKET_RETAINED":
            observed = isinstance(evidence.get("response_packet_sha256"), str) and evidence.get("response_packet_sha256", "").startswith("sha256:")
        packets.append({
            **common,
            "state": "TRANSITION_CONFIRMATION_READY" if observed else "TRANSITION_NOT_OBSERVED",
            "transition_sequence": sequence,
            "transition_id": transition_id,
            "transition_observed": observed,
            "transition_evidence": evidence,
        })
    return packets


def _execute_mir_transition_confirmations(request_path: Path, value: dict[str, Any], *, binding: tuple[Path, Path]) -> dict[str, Any]:
    packet_dir = request_path.parent / "transition-confirmations"
    confirmations: list[dict[str, Any]] = []
    first_non_return: str | None = None
    for packet in _mir_transition_packets(value):
        transition_id = str(packet["transition_id"])
        sequence = int(packet["transition_sequence"])
        packet_path = packet_dir / f"{sequence:02d}-{transition_id}.json"
        _atomic_json(packet_path, packet)
        if packet.get("transition_observed") is not True:
            result = {"state":"NOT_ATTEMPTED","reason":"TRANSITION_NOT_OBSERVED","authority_effect":"NONE"}
        else:
            result = _roundtrip_one(packet_path, binding=binding)
        returned = result.get("state") == "RETURNED"
        if not returned and first_non_return is None:
            first_non_return = transition_id
        confirmations.append({
            "transition_sequence": sequence,
            "transition_id": transition_id,
            "packet_ref": str(packet_path),
            "transition_observed": packet.get("transition_observed") is True,
            "master_records_state": result.get("state"),
            "master_records_reason": result.get("reason"),
            "returned": returned,
            "custody_ref": result.get("custody_ref"),
            "reconstructed_ref": result.get("reconstructed_ref"),
        })
    return {
        "schema": "stegverse.mir-state-transition-master-records-diagnostic/v1",
        "state": "ALL_OBSERVED_TRANSITIONS_RETURNED" if first_non_return is None else "FIRST_NON_RETURN_IDENTIFIED",
        "first_non_return_transition_id": first_non_return,
        "transition_confirmations": confirmations,
        "authority_effect": "NONE_DIAGNOSTIC_ONLY",
    }


def execute(request_path: Path) -> dict[str, Any]:
    binding = _binding()
    if isinstance(binding, dict):
        return binding
    try:
        value = json.loads(request_path.read_text(encoding="utf-8"))
    except Exception:
        value = None
    diagnostic = None
    if isinstance(value, dict) and value.get("schema") == MIR_ONE_WAY_SCHEMA:
        diagnostic = _execute_mir_transition_confirmations(request_path, value, binding=binding)
        if diagnostic.get("first_non_return_transition_id") is not None:
            return {
                "state":"BOUNDARY",
                "reason":"MIR_STATE_TRANSITION_CONFIRMATION_NOT_RETURNED",
                "first_non_return_transition_id":diagnostic.get("first_non_return_transition_id"),
                "transition_diagnostic":diagnostic,
                "authority_effect":"NONE",
            }
    final = _roundtrip_one(request_path, binding=binding)
    if diagnostic is not None:
        final = {**final, "transition_diagnostic": diagnostic}
    return final
