from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001"
RECEIPT = ROOT / "receipts/stegos-sovereign-relay" / f"{TASK_ID}.json"
BINDING_SCHEMA = "stegos.sovereign_relay_egress_binding.v1"
AUTH_SCHEMA = "stegverse.tvc.sovereign-relay-egress-authorization/v1"
MAX_DISCOVERY_FILE_BYTES = 2 * 1024 * 1024
MAX_PAYLOAD_FILE_BYTES = 512 * 1024


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"json_object_required:{path}")
    return value


def _stegos_root() -> Path:
    raw = os.environ.get("STEGVERSE_STEGOS_ROOT")
    candidates = [Path(raw).expanduser().resolve()] if raw else []
    candidates += [ROOT.parent / "StegOS", Path.home() / "StegOS"]
    for candidate in candidates:
        if (candidate / "stegos/sovereign_relay_round_trip.py").is_file():
            return candidate
    raise RuntimeError("current_stegos_round_trip_source_not_found")


def _runtime_root() -> Path:
    raw = os.environ.get("STEGVERSE_RELAY_RUNTIME_BASE")
    return Path(raw).expanduser().resolve() if raw else (Path.home() / ".stegverse/runtime/ephemeral-relays").resolve()


def _roots(runtime_root: Path, stegos_root: Path) -> list[Path]:
    roots = [runtime_root, ROOT, stegos_root]
    for name in ("STEGVERSE_TVC_ROOT", "STEGVERSE_ORG_CONTROL_ROOT", "STEGVERSE_HIL_STATE_ROOT"):
        raw = os.environ.get(name)
        if raw:
            roots.append(Path(raw).expanduser().resolve())
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen and root.exists():
            seen.add(key); unique.append(root)
    return unique


def _files(roots: Iterable[Path], *, suffix: str | None = None) -> Iterable[Path]:
    seen: set[str] = set()
    for root in roots:
        if root.is_file():
            candidates = [root]
        else:
            try:
                candidates = root.rglob("*" if suffix is None else f"*{suffix}")
            except OSError:
                continue
        for path in candidates:
            try:
                if not path.is_file() or (suffix and path.suffix != suffix):
                    continue
                key = str(path.resolve())
            except OSError:
                continue
            if key not in seen:
                seen.add(key); yield path


def _explicit(name: str) -> Path | None:
    raw = os.environ.get(name)
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"runtime_artifact_missing:{name}:{path}")
    return path


def _json_candidates(roots: list[Path], schema: str) -> list[tuple[Path, dict]]:
    found: list[tuple[Path, dict]] = []
    for path in _files(roots, suffix=".json"):
        try:
            if path.stat().st_size > MAX_DISCOVERY_FILE_BYTES:
                continue
            value = _load(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, RuntimeError):
            continue
        if value.get("schema") == schema:
            found.append((path, value))
    found.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return found


def _payload_by_hash(roots: list[Path], expected_sha: str, expected_size: int) -> Path:
    for path in _files(roots):
        try:
            size = path.stat().st_size
            if size != expected_size or size > MAX_PAYLOAD_FILE_BYTES:
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha:
                return path
        except OSError:
            continue
    raise RuntimeError("real_relay_payload_not_found_by_exact_hash")


def _discover(runtime_root: Path, stegos_root: Path) -> tuple[Path, Path, Path]:
    roots = _roots(runtime_root, stegos_root)
    explicit_binding = _explicit("STEGVERSE_RELAY_EGRESS_BINDING")
    explicit_auth = _explicit("STEGVERSE_RELAY_EGRESS_AUTHORIZATION")
    explicit_payload = _explicit("STEGVERSE_RELAY_EGRESS_PAYLOAD")

    bindings = [(explicit_binding, _load(explicit_binding))] if explicit_binding else _json_candidates(roots, BINDING_SCHEMA)
    auths = [(explicit_auth, _load(explicit_auth))] if explicit_auth else _json_candidates(roots, AUTH_SCHEMA)
    if not bindings:
        raise RuntimeError("real_relay_egress_binding_not_found")
    if not auths:
        raise RuntimeError("real_relay_egress_authorization_not_found")

    for auth_path, auth in auths:
        if auth.get("decision") != "ALLOW_RELAY_EGRESS" or auth.get("credential_authority") != "TV/TVC":
            continue
        for binding_path, binding in bindings:
            if binding.get("binding_id") != auth.get("binding_id"):
                continue
            if binding.get("route_id") != auth.get("route_id") or binding.get("transport_id") != auth.get("transport_id"):
                continue
            if binding.get("next_hop_transport_endpoint") != auth.get("next_hop_transport_endpoint"):
                continue
            payload_sha = str(auth.get("payload_sha256") or "")
            payload_size = auth.get("payload_size")
            if len(payload_sha) != 64 or not isinstance(payload_size, int):
                continue
            payload_path = explicit_payload or _payload_by_hash(roots, payload_sha, payload_size)
            payload = payload_path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != payload_sha or len(payload) != payload_size:
                raise RuntimeError("explicit_relay_payload_binding_mismatch")
            return binding_path, auth_path, payload_path
    raise RuntimeError("mutually_consistent_real_relay_artifact_set_not_found")


def main() -> int:
    stegos_root = _stegos_root()
    runtime_root = _runtime_root()
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))
    from stegos.sovereign_relay_round_trip import execute_sovereign_relay_round_trip

    binding_path, authorization_path, payload_path = _discover(runtime_root, stegos_root)
    result = execute_sovereign_relay_round_trip(
        authorization=_load(authorization_path),
        binding=_load(binding_path),
        payload=payload_path.read_bytes(),
        runtime_root=runtime_root,
    )
    if result.get("state") != "RETURN_PATH_VERIFIED":
        raise RuntimeError("return_path_terminal_state_not_observed")
    if result.get("far_side_evidence_present") is not True or result.get("durable_return_queue_verified") is not True or result.get("interlock_ingestion_verified") is not True:
        raise RuntimeError("return_path_completion_predicate_failed")
    if result.get("canonical_transition_committed") is not False:
        raise RuntimeError("return_path_canonical_authority_violation")

    receipt = {
        "schema": "stegverse.worker-task-terminal-receipt/v1",
        "task_id": TASK_ID,
        "state": "COMPLETED",
        "transition_id": "SOVEREIGN_RELAY_RETURN_PATH_VERIFIED",
        "artifact_resolution": "EXACT_SCHEMA_LINEAGE_AND_PAYLOAD_HASH_DISCOVERY",
        "stegos_root": str(stegos_root),
        "runtime_root": str(runtime_root),
        "binding_ref": str(binding_path),
        "authorization_ref": str(authorization_path),
        "payload_ref": str(payload_path),
        "round_trip_result": result,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "canonical_transition_committed": False,
        "authority_effect": "NONE_RUNTIME_EVIDENCE_ONLY",
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text(encoding="utf-8") != serialized:
        raise RuntimeError("terminal_receipt_write_once_collision")
    RECEIPT.write_text(serialized, encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
