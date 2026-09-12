#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
RECORDS = ROOT / "data" / "canonical-task-records"

EXPECTED = {
    "user_verification_authority": "KV/SKAP Vault",
    "user_verification_authority_exclusive": True,
    "stegos_device_role": "INTERCHANGEABLE_TRANSPORT_NODE",
    "device_user_verifier_authority": "NONE",
    "node_user_verifier_authority": "NONE",
    "transport_user_verifier_authority": "NONE",
    "local_key_user_verifier_authority": "NONE",
    "secure_enclave_user_verifier_authority": "NONE",
}

FORBIDDEN_TRUE_KEYS = {
    "device_is_user_verifier",
    "node_is_user_verifier",
    "transport_is_user_verifier",
    "channel_identity_is_user_verifier",
    "secure_enclave_is_user_verifier",
    "local_key_possession_is_user_verification",
}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def walk(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{path}.{k}" if path else k
            yield p, k, v
            yield from walk(v, p)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")


def validate_record(path: Path) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    for location, key, value in walk(record):
        if key in FORBIDDEN_TRUE_KEYS and value is True:
            fail(f"{path.name}: {location}=true contradicts global verifier invariant")
        if key in {"user_verification_authority", "user_verifier_authority", "user_verification_source"}:
            if value != "KV/SKAP Vault":
                fail(f"{path.name}: {location} must be KV/SKAP Vault")
        if key in {"device_user_verifier_authority", "node_user_verifier_authority", "transport_user_verifier_authority"}:
            if value != "NONE":
                fail(f"{path.name}: {location} must be NONE")


def main() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy.get("schema") != "stegverse.task-registry-global-invariants/v1":
        fail("global invariant schema mismatch")
    if policy.get("applies_to") != "ALL_CANONICAL_TASKS_EXISTING_AND_NEW":
        fail("global invariant scope mismatch")
    invariants = policy.get("invariants") or {}
    for key, expected in EXPECTED.items():
        if invariants.get(key) != expected:
            fail(f"global invariant {key} mismatch")
    if policy.get("authority_effect") != "NONE_REGISTRY_INVARIANT_ONLY":
        fail("global invariant authority effect mismatch")
    for path in sorted(RECORDS.glob("*.json")):
        validate_record(path)
    print("TASK_REGISTRY_GLOBAL_VERIFIER_NODE_INVARIANTS_PASS")

if __name__ == "__main__":
    main()
