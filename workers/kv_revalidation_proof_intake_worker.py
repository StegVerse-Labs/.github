#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID = "KV-REVALIDATION-PROOF-INTAKE-001"
TARGET_TASK_ID = "KV-CONNECTION-REVALIDATION-WORKER-001"
MANIFEST_SCHEMA = "stegverse.kv.revalidation-proof-intake/v1"
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "HEALER_GH_TOKEN", "COINBASE_API_KEY", "COINBASE_API_SECRET",
    "COINBASE_PRIVATE_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_SECRET_ACCESS_KEY",
)
CREDENTIAL_TERMS = ("password", "passwd", "secret", "token", "api_key", "apikey", "private_key", "cookie", "credential", "skap")
ALLOWED_KEYS = {
    "schema", "task_id", "assembly_id", "cvk_root", "kv_root", "conformance_proof_path",
    "readback_proof_path", "required_after", "provider_operation_authorized",
    "credential_material_present", "authority_effect",
}


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def blocked(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema": "stegverse.kv.revalidation-proof-intake-worker/v1",
        "state": "BLOCKED",
        "transition_id": reason,
        "task_id": TASK_ID,
        "target_task_id": TARGET_TASK_ID,
        "provider_operation_authorized": False,
        "credential_material_present": False,
        "provider_network_access_performed": False,
        "proof_manufactured": False,
        "connection_verified_by_intake": False,
        "authority_effect": "NONE",
        **extra,
    }


def _is_local_path(value: str) -> bool:
    lowered = value.strip().lower()
    return bool(value.strip()) and "://" not in lowered and not lowered.startswith(("http:", "https:", "ftp:", "s3:", "gs:"))


def _credential_like_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            current = f"{prefix}.{key}" if prefix else str(key)
            if any(term in normalized for term in CREDENTIAL_TERMS):
                found.append(current)
            found.extend(_credential_like_keys(child, current))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_credential_like_keys(child, f"{prefix}[{index}]"))
    return found


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("INTAKE_MANIFEST_MISSING")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("INTAKE_MANIFEST_UNREADABLE") from exc
    if not isinstance(value, dict):
        raise ValueError("INTAKE_MANIFEST_MUST_BE_OBJECT")
    unexpected = sorted(set(value) - ALLOWED_KEYS)
    if unexpected:
        raise ValueError("INTAKE_MANIFEST_UNEXPECTED_FIELDS:" + ",".join(unexpected))
    credential_keys = _credential_like_keys(value)
    if credential_keys:
        raise ValueError("INTAKE_MANIFEST_CREDENTIAL_FIELDS:" + ",".join(sorted(credential_keys)))
    required = {
        "schema", "task_id", "assembly_id", "cvk_root", "kv_root", "conformance_proof_path",
        "readback_proof_path", "provider_operation_authorized", "credential_material_present", "authority_effect",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ValueError("INTAKE_MANIFEST_REQUIRED_FIELDS:" + ",".join(missing))
    if value.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("INTAKE_MANIFEST_SCHEMA_MISMATCH")
    if value.get("task_id") != TARGET_TASK_ID:
        raise ValueError("INTAKE_TARGET_TASK_MISMATCH")
    if value.get("provider_operation_authorized") is not False:
        raise ValueError("PROVIDER_OPERATION_AUTHORITY_PROHIBITED")
    if value.get("credential_material_present") is not False:
        raise ValueError("CREDENTIAL_MATERIAL_PROHIBITED")
    if value.get("authority_effect") != "NONE":
        raise ValueError("AUTHORITY_EFFECT_PROHIBITED")
    return value


def _load_target_worker(repo_root: Path):
    worker_path = (repo_root / "workers" / "kv_connection_revalidation_worker.py").resolve()
    if not worker_path.is_file():
        raise ValueError("TARGET_REVALIDATION_WORKER_MISSING")
    spec = importlib.util.spec_from_file_location("kv_connection_revalidation_worker", worker_path)
    if not spec or not spec.loader:
        raise ValueError("TARGET_REVALIDATION_WORKER_UNLOADABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "TASK_ID", None) != TARGET_TASK_ID or not callable(getattr(module, "execute", None)):
        raise ValueError("TARGET_REVALIDATION_WORKER_IDENTITY_MISMATCH")
    return module


def _receipt_path(values: dict[str, str]) -> Path:
    state_home = values.get("XDG_STATE_HOME", "").strip()
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return (base / "stegverse" / "kv-revalidation-intake" / "dispatch.latest.json").resolve()


def _persist_dispatch_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def execute(env: dict[str, str] | None = None, *, target_module: Any | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    hosted = [key for key in HOSTED_ENV if truthy(values.get(key))]
    if hosted:
        return blocked("HOSTED_SURFACE_REJECTED", hosted=sorted(hosted))
    forbidden = [key for key in FORBIDDEN_ENV if values.get(key)]
    if forbidden:
        return blocked("FORBIDDEN_CREDENTIAL_ENV", forbidden=sorted(forbidden))

    manifest_ref = values.get("STEGVERSE_KV_REVALIDATION_INTAKE", "").strip()
    if not manifest_ref:
        return blocked("INTAKE_MANIFEST_BINDING_REQUIRED")
    if not _is_local_path(manifest_ref):
        return blocked("INTAKE_MANIFEST_NETWORK_LOCATION_REJECTED")

    repo_root = Path(__file__).resolve().parents[1]
    try:
        manifest = _load_manifest(Path(manifest_ref).expanduser().resolve())
        path_fields = ("cvk_root", "kv_root", "conformance_proof_path", "readback_proof_path")
        for field in path_fields:
            if not _is_local_path(str(manifest[field])):
                raise ValueError(f"{field.upper()}_NETWORK_LOCATION_REJECTED")
        cvk = Path(str(manifest["cvk_root"])).expanduser().resolve()
        kv = Path(str(manifest["kv_root"])).expanduser().resolve()
        conformance = Path(str(manifest["conformance_proof_path"])).expanduser().resolve()
        readback = Path(str(manifest["readback_proof_path"])).expanduser().resolve()
        if not cvk.is_dir():
            raise ValueError("CVK_LOCAL_SOURCE_MISSING")
        if not kv.is_dir():
            raise ValueError("PRIVATE_KV_ROOT_MISSING")
        if not conformance.is_file():
            raise ValueError("CONFORMANCE_PROOF_MISSING")
        if not readback.is_file():
            raise ValueError("READBACK_PROOF_MISSING")
        target = target_module or _load_target_worker(repo_root)
    except Exception as exc:
        return blocked("INTAKE_VALIDATION_FAILED", detail=str(exc))

    child_env = {
        "STEGVERSE_CVK_ROOT": str(cvk),
        "STEGVERSE_KV_ROOT": str(kv),
        "STEGVERSE_KV_CONNECTION_ASSEMBLY_ID": str(manifest["assembly_id"]),
        "STEGVERSE_KV_CONNECTION_CONFORMANCE_PROOF": str(conformance),
        "STEGVERSE_KV_CONNECTION_READBACK_PROOF": str(readback),
    }
    required_after = manifest.get("required_after")
    if isinstance(required_after, str) and required_after.strip():
        child_env["STEGVERSE_KV_CONNECTION_REQUIRED_AFTER"] = required_after.strip()

    downstream = target.execute(child_env)
    receipt = {
        "schema": "stegverse.kv.revalidation-proof-intake-dispatch-receipt/v1",
        "task_id": TASK_ID,
        "target_task_id": TARGET_TASK_ID,
        "assembly_id": str(manifest["assembly_id"]),
        "intake_admitted": True,
        "target_invoked": True,
        "target_state": downstream.get("state"),
        "target_transition_id": downstream.get("transition_id"),
        "provider_operation_authorized": False,
        "credential_material_present": False,
        "provider_network_access_performed": False,
        "proof_manufactured": False,
        "connection_verified_by_intake": False,
        "authority_effect": "NONE",
    }
    try:
        receipt_path = _receipt_path(values)
        _persist_dispatch_receipt(receipt_path, receipt)
    except Exception as exc:
        return blocked("INTAKE_DISPATCH_RECEIPT_PERSISTENCE_FAILED", detail=str(exc))

    return {
        "schema": "stegverse.kv.revalidation-proof-intake-worker/v1",
        "state": "COMPLETED" if downstream.get("state") == "COMPLETED" else "HANDOFF_READY",
        "transition_id": "KV_REVALIDATION_PROOF_INTAKE_DISPATCHED",
        "task_id": TASK_ID,
        "target_task_id": TARGET_TASK_ID,
        "assembly_id": str(manifest["assembly_id"]),
        "dispatch_receipt_path": str(receipt_path),
        "downstream": downstream,
        "provider_operation_authorized": False,
        "credential_material_present": False,
        "provider_network_access_performed": False,
        "proof_manufactured": False,
        "connection_verified_by_intake": False,
        "authority_effect": "NONE",
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID:
        return 2
    result = execute()
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": result["state"],
        "transition_id": result["transition_id"],
        "transition_sequence": 1,
        "expected_next_transition": None if result["state"] == "COMPLETED" else "RETRY_AFTER_RUNTIME_PREDICATE_CHANGE",
        "checkpoint_ref": "handoffs/KV-REVALIDATION-PROOF-INTAKE-001.json",
        "evidence_refs": ["KV_REVALIDATION_PROOF_INTAKE_MIRROR_HANDOFF.md"],
        "cost_observation": {"hb_transition_count": 0, "compute_units": 1, "external_cost_usd": 0, "task_class": "kv_revalidation_proof_intake"},
        "result": result,
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
