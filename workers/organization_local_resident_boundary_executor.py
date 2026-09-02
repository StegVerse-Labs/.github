#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.intr_carrier_profile import validate_carrier_binding

TASK_ID = "ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001"
PACKET_SCHEMA = "stegverse.organization-local-boundary.packet/v1"
PROFILE_ID = "stegverse.organization-local-intr/v1"
INGRESS_DIR = ROOT / "spool/organization-local-boundary/ingress"
EGRESS_DIR = ROOT / "spool/organization-local-boundary/egress"
RECEIPT_DIR = ROOT / "receipts/organization-local-boundary"
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
FORBIDDEN_KEYS = {
    "password","secret","credential_value","private_key","private_key_material",
    "token","access_token","refresh_token","cookie","mnemonic","seed","raw_biometric",
    "shell","command","argv",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical_json(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as h:
        json.dump(dict(value), h, indent=2, sort_keys=True)
        h.write("\n")
        tmp = Path(h.name)
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def reject_forbidden(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("non_string_key")
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden_field:{key}")
            reject_forbidden(child)
    elif isinstance(value, list):
        for child in value:
            reject_forbidden(child)


def blocker(problem: str, action: str, release: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": action,
        "machine_observable_release_condition": release,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "human_action_required": False,
    }


def response(state: str, transition: str, epoch: int, blocked: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "ORGANIZATION_LOCAL_BOUNDARY_ITEM_CONSUMED",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 100,
        "checkpoint_ref": "docs/ORGANIZATION_LOCAL_RESIDENT_BOUNDARY_EXECUTOR_MIRROR_HANDOFF.md",
        "evidence_refs": [
            "docs/ORGANIZATION_LOCAL_RESIDENT_BOUNDARY_EXECUTOR_MIRROR_HANDOFF.md",
            "workers/organization_local_resident_boundary_executor.py",
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "organization_local_resident_boundary",
        },
    }
    if blocked is not None:
        out["blocker"] = blocked
    return out


def validate_packet(packet: Mapping[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    reject_forbidden(packet)
    expected = {
        "schema": PACKET_SCHEMA,
        "profile_id": PROFILE_ID,
        "direction": "INGRESS",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "carrier_grants_execution_authority": False,
        "canonical_state_change_authorized": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if packet.get(key) != wanted:
            raise ValueError(f"packet_{key}_mismatch")
    packet_id = packet.get("packet_id")
    if not isinstance(packet_id, str) or not SAFE_ID.fullmatch(packet_id):
        raise ValueError("packet_id_invalid")
    payload = packet.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("payload_object_required")
    payload_hash = packet.get("payload_hash")
    if payload_hash != sha256_uri(payload):
        raise ValueError("payload_hash_mismatch")
    transition_basis = packet.get("transition_basis")
    if transition_basis is not None:
        if not isinstance(transition_basis, Mapping):
            raise ValueError("transition_basis_object_required")
        if transition_basis.get("authority_effect") not in {None, "NONE", "NONE_EVIDENCE_ONLY"}:
            raise ValueError("transition_basis_authority_escalation")
    carrier = packet.get("carrier_binding")
    validated_carrier = None
    if carrier is not None:
        validated_carrier = validate_carrier_binding(carrier, packet_id=packet_id, payload_hash=payload_hash)
    return packet_id, payload_hash, validated_carrier


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    claim_id = task.get("claim_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int) or fence < 1:
        return 3
    if not claim_id.endswith(f"-G{fence}"):
        return 4

    pending = sorted(p for p in INGRESS_DIR.glob("*.json") if p.is_file()) if INGRESS_DIR.is_dir() else []
    if not pending:
        b = blocker(
            "No organization-local ingress item is present.",
            "Wait for or materialize one already-governed local Interlock/InTr ingress packet.",
            "spool/organization-local-boundary/ingress contains one valid JSON packet",
        )
        json.dump(response("BLOCKED", "ORGANIZATION_LOCAL_BOUNDARY_INGRESS_REQUIRED", epoch, b), sys.stdout)
        print()
        return 0

    path = pending[0]
    try:
        packet = load_json(path)
        packet_id, payload_hash, carrier = validate_packet(packet)
    except Exception as exc:
        b = blocker(
            f"Organization-local ingress packet failed closed validation: {type(exc).__name__}: {exc}",
            "Repair or replace the local ingress packet under the canonical boundary profile.",
            "next ingress packet validates exact schema/profile/payload/carrier/authority invariants",
        )
        json.dump(response("BLOCKED", "ORGANIZATION_LOCAL_BOUNDARY_PACKET_REPAIR_REQUIRED", epoch, b), sys.stdout)
        print()
        return 0

    ingress_hash = sha256_uri(packet)
    receipt_path = RECEIPT_DIR / f"{packet_id}.json"
    egress_path = EGRESS_DIR / f"{packet_id}.json"

    if receipt_path.is_file() and egress_path.is_file():
        receipt = load_json(receipt_path)
        egress = load_json(egress_path)
        if receipt.get("ingress_packet_sha256") == ingress_hash and receipt.get("egress_packet_sha256") == sha256_uri(egress):
            json.dump(response("COMPLETED", "ORGANIZATION_LOCAL_BOUNDARY_ITEM_CONSUMED", epoch), sys.stdout)
            print()
            return 0
        return 5

    egress_payload = {
        "disposition": "ACCEPTED_LOCAL_BOUNDARY",
        "ingress_packet_id": packet_id,
        "ingress_packet_sha256": ingress_hash,
        "payload_hash": payload_hash,
        "canonical_state_changed": False,
        "external_side_effect_performed": False,
    }
    egress_payload_hash = sha256_uri(egress_payload)
    egress = {
        "schema": PACKET_SCHEMA,
        "profile_id": PROFILE_ID,
        "direction": "EGRESS",
        "packet_id": packet_id,
        "payload": egress_payload,
        "payload_hash": egress_payload_hash,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "carrier_grants_execution_authority": False,
        "canonical_state_change_authorized": False,
        "authority_effect": "NONE_EGRESS_ONLY",
    }
    receipt = {
        "schema": "stegverse.organization-local-boundary.receipt/v1",
        "task_id": TASK_ID,
        "packet_id": packet_id,
        "profile_id": PROFILE_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "ingress_packet_sha256": ingress_hash,
        "payload_hash": payload_hash,
        "carrier_binding_present": carrier is not None,
        "carrier_binding_sha256": carrier.get("binding_sha256") if carrier else None,
        "transition_basis": packet.get("transition_basis"),
        "disposition": "ACCEPTED_LOCAL_BOUNDARY",
        "canonical_state_changed": False,
        "external_side_effect_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE",
    }
    receipt["egress_packet_sha256"] = sha256_uri(egress)
    atomic_json(egress_path, egress)
    atomic_json(receipt_path, receipt)

    if load_json(egress_path) != egress or load_json(receipt_path) != receipt:
        return 6
    json.dump(response("COMPLETED", "ORGANIZATION_LOCAL_BOUNDARY_ITEM_CONSUMED", epoch), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
