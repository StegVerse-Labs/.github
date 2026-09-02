from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from workers.stegos_sovereign_relay_bridge import find_stegos_root

PROFILE_URL = "https://stegverse.org/intr/profile"
REQUIRED_PROFILE = "SV002:PublicObservation"
PUBLIC_VERIFYING_HISTORY = [
    "ABSENT", "REQUESTED", "ADMITTED", "PROVISIONING", "LOCAL_READY", "PUBLIC_VERIFYING",
]
LEASE_OPEN_HISTORY = PUBLIC_VERIFYING_HISTORY + ["LEASE_OPEN"]
OBSERVATION_SCHEMA = "stegverse.sv002-public-profile-lease-open-observation/v1"
Verifier = Callable[..., Mapping[str, Any]]


class SV002PublicLeaseOpenError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SV002PublicLeaseOpenError(f"json_object_required:{path}")
    return value


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(dict(value), handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    os.replace(temp, path)


def _load_stegos_modules(stegos_root: Path):
    root = stegos_root.expanduser().resolve()
    required = (
        root / "stegos/ephemeral_runtime_lease.py",
        root / "stegos/universal_intr_public_profile.py",
    )
    if not all(path.is_file() for path in required):
        raise SV002PublicLeaseOpenError("stegos_public_lease_source_missing")
    root_text = str(root)
    inserted = False
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
        inserted = True
    try:
        lease_mod = importlib.import_module("stegos.ephemeral_runtime_lease")
        profile_mod = importlib.import_module("stegos.universal_intr_public_profile")
        for module in (lease_mod, profile_mod):
            origin = Path(str(module.__file__)).resolve()
            if root not in origin.parents:
                raise SV002PublicLeaseOpenError("stegos_module_origin_mismatch")
        return lease_mod, profile_mod
    finally:
        if inserted:
            try:
                sys.path.remove(root_text)
            except ValueError:
                pass


def _validate_public_observation(value: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema": "stegverse.universal-intr-public-profile-observation/v1",
        "verified": True,
        "observation_origin": "INDEPENDENT_PUBLIC_HTTPS",
        "observed_profile_url": PROFILE_URL,
        "required_profile": REQUIRED_PROFILE,
        "credential_used": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise SV002PublicLeaseOpenError(f"public_profile_observation_{key}_mismatch")
    schema = value.get("profile_schema")
    if schema not in {
        "stegverse.universal-intr-profiled-ingress/v1",
        "stegverse.hil-intr-materialization-ingress-profile/v1",
    }:
        raise SV002PublicLeaseOpenError("public_profile_schema_invalid")
    profile_hash = value.get("profile_sha256")
    if (
        not isinstance(profile_hash, str)
        or len(profile_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in profile_hash)
    ):
        raise SV002PublicLeaseOpenError("public_profile_sha256_invalid")
    profile = value.get("profile")
    if not isinstance(profile, Mapping):
        raise SV002PublicLeaseOpenError("public_profile_body_missing")
    return dict(value)


def resume_public_lease(
    *,
    control_root: Path,
    execution_runtime: Path,
    snapshot_path: Path,
    expected_snapshot_digest: str,
    env: Mapping[str, str] | None = None,
    verifier: Verifier | None = None,
) -> dict[str, Any]:
    runtime = execution_runtime.expanduser().resolve()
    snapshot_file = snapshot_path.expanduser().resolve()
    try:
        snapshot_file.relative_to(runtime)
    except ValueError as exc:
        raise SV002PublicLeaseOpenError("lease_snapshot_outside_runtime") from exc
    if not snapshot_file.is_file():
        raise SV002PublicLeaseOpenError("lease_snapshot_missing")

    before = load_json(snapshot_file)
    before_digest = digest_uri(before)
    if before_digest != expected_snapshot_digest:
        raise SV002PublicLeaseOpenError("lease_snapshot_digest_drift")

    observation_path = snapshot_file.with_name("canonical-runtime-public-profile.observation.json")

    stegos_root = find_stegos_root(control_root.expanduser().resolve(), env)
    if stegos_root is None:
        raise SV002PublicLeaseOpenError("stegos_public_lease_source_not_materialized")
    lease_mod, profile_mod = _load_stegos_modules(stegos_root)

    if before.get("schema") != lease_mod.LeaseMachine.SNAPSHOT_SCHEMA:
        raise SV002PublicLeaseOpenError("lease_snapshot_schema_invalid")
    if before.get("credential_authority") != "TV/TVC" or before.get("authority_effect") != "NONE":
        raise SV002PublicLeaseOpenError("lease_snapshot_authority_invalid")

    if before.get("state") == "LEASE_OPEN":
        if before.get("history") != LEASE_OPEN_HISTORY:
            raise SV002PublicLeaseOpenError("lease_open_history_drift")
        if not observation_path.is_file():
            raise SV002PublicLeaseOpenError("lease_open_public_observation_missing")
        observation = load_json(observation_path)
        if observation.get("schema") != OBSERVATION_SCHEMA:
            raise SV002PublicLeaseOpenError("lease_open_public_observation_schema_invalid")
        if observation.get("lease_snapshot_sha256_after") != before_digest:
            raise SV002PublicLeaseOpenError("lease_open_public_observation_snapshot_binding_mismatch")
        if observation.get("public_profile_url") != PROFILE_URL:
            raise SV002PublicLeaseOpenError("lease_open_public_observation_url_mismatch")
        if observation.get("required_profile") != REQUIRED_PROFILE:
            raise SV002PublicLeaseOpenError("lease_open_public_observation_profile_mismatch")
        if observation.get("observation_origin") != "INDEPENDENT_PUBLIC_HTTPS":
            raise SV002PublicLeaseOpenError("lease_open_public_observation_origin_mismatch")
        return {
            "state": "LEASE_OPEN",
            "lease_snapshot": before,
            "lease_snapshot_sha256": before_digest,
            "public_profile_observation": observation,
            "public_profile_observation_ref": str(observation_path),
            "idempotent_existing_lease_open": True,
            "runtime_execution_authority_granted_by_observation": False,
            "authority_effect": "NONE_OBSERVATION_ONLY",
        }

    if before.get("state") != "PUBLIC_VERIFYING" or before.get("history") != PUBLIC_VERIFYING_HISTORY:
        raise SV002PublicLeaseOpenError("lease_public_verifying_precondition_invalid")

    machine = lease_mod.LeaseMachine.from_snapshot(before)
    if machine.snapshot().get("request") != before.get("request"):
        raise SV002PublicLeaseOpenError("lease_request_identity_drift")

    selected_verifier: Verifier = profile_mod.verify_public_intr_profile if verifier is None else verifier
    observed = selected_verifier(
        PROFILE_URL,
        required_profile=REQUIRED_PROFILE,
        timeout_seconds=10.0,
    )
    public = _validate_public_observation(observed)

    machine.transition(lease_mod.LeaseState.LEASE_OPEN)
    evolved = machine.snapshot()
    if evolved.get("state") != "LEASE_OPEN" or evolved.get("history") != LEASE_OPEN_HISTORY:
        raise SV002PublicLeaseOpenError("lease_open_transition_invalid")
    if evolved.get("request") != before.get("request"):
        raise SV002PublicLeaseOpenError("lease_request_identity_changed")
    evolved_digest = digest_uri(evolved)

    observation = {
        "schema": OBSERVATION_SCHEMA,
        "state": "VERIFIED_PUBLIC_PROFILE_LEASE_OPEN",
        "lease_snapshot_sha256_before": before_digest,
        "lease_snapshot_sha256_after": evolved_digest,
        "lease_history_before": list(PUBLIC_VERIFYING_HISTORY),
        "lease_history_after": list(LEASE_OPEN_HISTORY),
        "public_profile_url": public["observed_profile_url"],
        "public_profile_schema": public["profile_schema"],
        "public_profile_sha256": public["profile_sha256"],
        "required_profile": public["required_profile"],
        "observation_origin": public["observation_origin"],
        "credential_used": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "receiver_ready_claimed": False,
        "round_trip_claimed": False,
        "master_records_custody_claimed": False,
        "sv002_principal_execution_claimed": False,
        "public_profile_grants_execution_authority": False,
        "public_profile_grants_transition_authority": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    atomic_json(observation_path, observation)
    atomic_json(snapshot_file, evolved)
    if digest_uri(load_json(snapshot_file)) != evolved_digest:
        raise SV002PublicLeaseOpenError("lease_open_snapshot_readback_mismatch")
    if load_json(observation_path) != observation:
        raise SV002PublicLeaseOpenError("public_profile_observation_readback_mismatch")
    return {
        "state": "LEASE_OPEN",
        "lease_snapshot": evolved,
        "lease_snapshot_sha256": evolved_digest,
        "public_profile_observation": observation,
        "public_profile_observation_ref": str(observation_path),
        "idempotent_existing_lease_open": False,
        "runtime_execution_authority_granted_by_observation": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
