#!/usr/bin/env python3
"""Consume the verified IBC ACK request on the canonical sovereign resident substrate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/ibc-verified-intr-ack-request-consumption.latest.json")
TRANSPORT_REL = Path("receipts/sovereign-host/ibc-verified-intr-ack-transport.latest.json")
TARGET_TASK = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
TARGET_MODE = "IBC_VERIFIED_INTR_ACK_RESIDENT"
TARGET_ENTRYPOINT = "scripts/materialize_verified_ibc_intr_ack.py"
TARGET_OBSERVATION_CLASS = "SOVEREIGN_RESIDENT_EXECUTED_CANONICAL_INTR_TRANSPORT_RECEIPT"
EXPECTED_EVIDENCE = (
    "evidence/ibc/cosmoshub-osmosis/ack-sequence-999999.capture.json",
    "evidence/ibc/cosmoshub-osmosis/ack-sequence-999999.ics23-verification.json",
    "evidence/ibc/cosmoshub-osmosis/ack-sequence-999999.signature-verification-record.json",
    "evidence/ibc/cosmoshub-osmosis/ack-sequence-999999.verified-classic-evidence.json",
)
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_STEGOS_ROOT", "STEGVERSE_TV_ROOT", "STEGVERSE_TVC_ROOT",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {key: values[key] for key in NONSECRET_ENV if values.get(key)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "requires_sovereign_node_marker": True,
        "requires_local_stegos_source": True,
        "observation_class": TARGET_OBSERVATION_CLASS,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if request.get(key) != expected_value:
            raise RuntimeError(f"IBC resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"]:
        raise RuntimeError("IBC resident request request_id missing")


def validate_stegos_root(root: Path) -> dict[str, str]:
    entrypoint = root / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError("local StegOS IBC resident materializer missing")
    hashes: dict[str, str] = {TARGET_ENTRYPOINT: file_hash(entrypoint)}
    for rel in EXPECTED_EVIDENCE:
        path = root / rel
        if not path.is_file():
            raise RuntimeError(f"local StegOS IBC evidence missing: {rel}")
        hashes[rel] = file_hash(path)
    verification = load_json(root / EXPECTED_EVIDENCE[1])
    evidence = load_json(root / EXPECTED_EVIDENCE[3])
    if verification.get("result") != "accepted" or verification.get("proof_verified") is not True:
        raise RuntimeError("local StegOS retained ICS23 verification is not accepted")
    if evidence.get("classic_evidence_grants_transition_admission") is not False:
        raise RuntimeError("local StegOS verified evidence widened transition admission")
    if evidence.get("classic_evidence_grants_execution_authority") is not False:
        raise RuntimeError("local StegOS verified evidence widened execution authority")
    if evidence.get("classic_evidence_mints_custody_result") is not False:
        raise RuntimeError("local StegOS verified evidence widened custody")
    return hashes


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.ibc-intr-resident-consumption/v1",
            "state": "NO_REQUEST",
            "resident_runtime_execution_observed": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)

    sovereign_node = str(values.get("STEGVERSE_SOVEREIGN_NODE") or "").strip()
    if not sovereign_node:
        receipt = {
            "schema": "stegverse.ibc-intr-resident-consumption/v1",
            "state": "SOVEREIGN_NODE_MARKER_REQUIRED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "task_id": TARGET_TASK,
            "runtime_execution_attempted": False,
            "resident_runtime_execution_observed": False,
            "original_ibc_packet_relay_observed": False,
            "transition_admission_observed": False,
            "application_execution_observed": False,
            "claim_or_fence_minted": False,
            "custody_result_minted": False,
            "credential_minted": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
        path = runtime / CONSUMPTION_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    stegos_value = str(values.get("STEGVERSE_STEGOS_ROOT") or "").strip()
    if not stegos_value:
        raise RuntimeError("STEGVERSE_STEGOS_ROOT required for IBC resident consumption")
    stegos_root = Path(stegos_value).expanduser().resolve()
    evidence_hashes = validate_stegos_root(stegos_root)

    output = runtime / TRANSPORT_REL
    command = [
        sys.executable,
        str(stegos_root / TARGET_ENTRYPOINT),
        "--observation-class",
        TARGET_OBSERVATION_CLASS,
        "--output",
        str(output),
    ]
    completed = runner(
        command,
        cwd=stegos_root,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(values),
        timeout=1200,
    )
    result = parse_last_json(completed.stdout)
    artifact = load_json(output) if output.is_file() else None
    accepted = bool(
        completed.returncode == 0
        and isinstance(result, dict)
        and isinstance(artifact, dict)
        and result.get("observation_class") == TARGET_OBSERVATION_CLASS
        and result.get("resident_runtime_execution_observed") is True
        and artifact.get("observation_class") == TARGET_OBSERVATION_CLASS
        and artifact.get("resident_runtime_execution_observed") is True
        and artifact.get("original_ibc_packet_relay_observed") is False
        and artifact.get("transition_admission_observed") is False
        and artifact.get("application_execution_observed") is False
        and artifact.get("claim_or_fence_minted") is False
        and artifact.get("custody_result_minted") is False
        and artifact.get("credential_minted") is False
        and artifact.get("authority_effect") == "NONE_RESIDENT_TRANSPORT_ONLY"
    )

    receipt = {
        "schema": "stegverse.ibc-intr-resident-consumption/v1",
        "state": "RESIDENT_INTR_ACK_CONSUMED" if accepted else "RESIDENT_INTR_ACK_NOT_OBSERVED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "sovereign_node_ref": sovereign_node,
        "stegos_source_root": str(stegos_root),
        "stegos_source_hashes": evidence_hashes,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result": result,
        "transport_artifact_ref": str(TRANSPORT_REL),
        "transport_artifact_sha256": file_hash(output) if output.is_file() else None,
        "runtime_execution_attempted": True,
        "resident_runtime_execution_observed": accepted,
        "original_ibc_packet_relay_observed": False,
        "transition_admission_observed": False,
        "application_execution_observed": False,
        "claim_or_fence_minted": False,
        "custody_result_minted": False,
        "credential_minted": False,
        "workercoordinator_claim_fence_observed": False,
        "network_source_fetch_performed": False,
        "second_machine_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "broader_task_complete": False,
        "retry_allowed": not accepted,
        "authority_effect": "NONE_RESIDENT_CONSUMPTION_ONLY",
    }
    path = runtime / CONSUMPTION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] in {"NO_REQUEST", "SOVEREIGN_NODE_MARKER_REQUIRED", "RESIDENT_INTR_ACK_CONSUMED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
