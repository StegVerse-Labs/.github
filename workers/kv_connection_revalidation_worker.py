#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID = "KV-CONNECTION-REVALIDATION-WORKER-001"
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "HEALER_GH_TOKEN", "COINBASE_API_KEY", "COINBASE_API_SECRET",
    "COINBASE_PRIVATE_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_SECRET_ACCESS_KEY",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def _blocked(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema": "stegverse.kv.connection-revalidation-worker/v1",
        "state": "BLOCKED",
        "transition_id": reason,
        "task_id": TASK_ID,
        "provider_operation_authorized": False,
        "credential_material_present": False,
        "provider_network_access_performed": False,
        "proof_manufactured": False,
        "connection_verified": False,
        "authority_effect": "NONE",
        **extra,
    }


def _load_modules(cvk_root: Path) -> dict[str, Any]:
    required = [
        "runtime/connection_assembly.py",
        "runtime/connection_revalidation.py",
        "runtime/connection_registry_store.py",
    ]
    missing = [rel for rel in required if not (cvk_root / rel).is_file()]
    if missing:
        raise ValueError("CVK_REVALIDATION_RUNTIME_INCOMPLETE:" + ",".join(missing))
    root = str(cvk_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    return {
        "revalidation": importlib.import_module("runtime.connection_revalidation"),
        "store": importlib.import_module("runtime.connection_registry_store"),
    }


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label}_MISSING")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{label}_UNREADABLE") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label}_MUST_BE_OBJECT")
    return value


def execute(env: dict[str, str] | None = None, *, modules: dict[str, Any] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    hosted = [key for key in HOSTED_ENV if truthy(values.get(key))]
    if hosted:
        return _blocked("HOSTED_SURFACE_REJECTED", hosted=sorted(hosted))
    forbidden = [key for key in FORBIDDEN_ENV if values.get(key)]
    if forbidden:
        return _blocked("FORBIDDEN_CREDENTIAL_ENV", forbidden=sorted(forbidden))

    cvk_ref = values.get("STEGVERSE_CVK_ROOT", "").strip()
    kv_ref = values.get("STEGVERSE_KV_ROOT", "").strip()
    assembly_id = values.get("STEGVERSE_KV_CONNECTION_ASSEMBLY_ID", "").strip()
    conformance_ref = values.get("STEGVERSE_KV_CONNECTION_CONFORMANCE_PROOF", "").strip()
    readback_ref = values.get("STEGVERSE_KV_CONNECTION_READBACK_PROOF", "").strip()
    required_after = values.get("STEGVERSE_KV_CONNECTION_REQUIRED_AFTER", "").strip() or None
    if not all((cvk_ref, kv_ref, assembly_id, conformance_ref, readback_ref)):
        return _blocked("REVALIDATION_BINDINGS_REQUIRED")

    cvk = Path(cvk_ref).expanduser().resolve()
    kv = Path(kv_ref).expanduser().resolve()
    if not cvk.is_dir():
        return _blocked("CVK_LOCAL_SOURCE_MISSING")
    if not kv.is_dir():
        return _blocked("PRIVATE_KV_ROOT_MISSING")

    try:
        mods = modules or _load_modules(cvk)
        conformance = _load_json(Path(conformance_ref).expanduser().resolve(), "CONFORMANCE_PROOF")
        readback = _load_json(Path(readback_ref).expanduser().resolve(), "READBACK_PROOF")
        registry = mods["store"].load_registry(kv)
    except Exception as exc:
        return _blocked("REVALIDATION_INPUT_INVALID", detail=str(exc))

    matches = [row for row in registry.get("assemblies", []) if row.get("assembly_id") == assembly_id]
    if len(matches) != 1:
        return _blocked("EXACT_CONNECTION_ASSEMBLY_NOT_FOUND", assembly_id=assembly_id, matches=len(matches))

    current = matches[0]
    try:
        updated, receipt = mods["revalidation"].admit_revalidation(
            current,
            conformance,
            readback,
            required_after=required_after,
        )
    except Exception as exc:
        return _blocked("CONNECTION_REVALIDATION_REJECTED", assembly_id=assembly_id, detail=str(exc))

    if updated.get("compatibility_state") != "VERIFIED":
        return _blocked("CANONICAL_REVALIDATION_DID_NOT_VERIFY", assembly_id=assembly_id)
    if receipt.get("provider_operation_authorized") is not False or receipt.get("credential_material_present") is not False:
        return _blocked("CANONICAL_RECEIPT_AUTHORITY_BOUNDARY_VIOLATION", assembly_id=assembly_id)

    try:
        persisted_registry = mods["store"].upsert_assembly(kv, updated)
        health_path = mods["store"].persist_health_receipt(kv, receipt)
    except Exception as exc:
        return _blocked("VERIFIED_CONNECTION_PERSISTENCE_FAILED", assembly_id=assembly_id, detail=str(exc))

    persisted = [row for row in persisted_registry.get("assemblies", []) if row.get("assembly_id") == assembly_id]
    if len(persisted) != 1 or persisted[0].get("compatibility_state") != "VERIFIED":
        return _blocked("VERIFIED_CONNECTION_READBACK_FAILED", assembly_id=assembly_id)

    return {
        "schema": "stegverse.kv.connection-revalidation-worker/v1",
        "state": "COMPLETED",
        "transition_id": "KV_CONNECTION_REVALIDATION_COMPLETED",
        "task_id": TASK_ID,
        "assembly_id": assembly_id,
        "compatibility_state": "VERIFIED",
        "health_receipt_path": str(health_path),
        "required_after_enforced": required_after is not None,
        "provider_operation_authorized": False,
        "credential_material_present": False,
        "provider_network_access_performed": False,
        "proof_manufactured": False,
        "connection_verified": True,
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
        "checkpoint_ref": "handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json",
        "evidence_refs": ["KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md"],
        "cost_observation": {
            "hb_transition_count": 0,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "kv_connection_revalidation",
        },
        "result": result,
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
