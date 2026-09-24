#!/usr/bin/env python3
"""Build one content-addressed control-plane source package as a reusable task.

This runner is source packaging only. It does not perform relay transport, issue a
TVC grant/authorization, admit an InTr transition, mint a WorkerCoordinator claim
or fence, or mutate the resident runtime control plane. The package is retained in
an outbox so the existing governed relay path can consume the exact bytes later.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_control_plane_source_package as builder

REUSABLE_TASK_ID = "RT-CONTROL-PLANE-SOURCE-PACKAGE-001"
RESULT_SCHEMA = "stegverse.reusable-task-runner-result/v1"
OUTBOX_REL = Path("outbox/control-plane-source-package")
REQUIRED_FUNCTIONAL_MEMORY_PATHS = (
    "heartbeat_runtime/worker_runtime.py",
    "heartbeat_runtime/admitted_worker_runtime.py",
    "heartbeat_runtime/worker_assignment_functional_memory.py",
    "workers/canonical_state_transition_custody.py",
    ".stegverse/transition-ledger/org-contract.json",
    "resident-runtime/aggregate_repo_transition.py",
    "control/worker-registry.d/stegfin-live-entry-003.json",
)
RELAY_AUTH_ENV = "STEGVERSE_RELAY_EGRESS_AUTHORIZATION"
RELAY_BINDING_ENV = "STEGVERSE_RELAY_EGRESS_BINDING"
STEGOS_ROOT_ENV = "STEGVERSE_STEGOS_ROOT"
RELAY_RECEIPT_REL = Path("receipts/sovereign-host/control-plane-source-package-relay.latest.json")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object_required:{path}")
    return value


def atomic_write_once(path: Path, rendered: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError("control_plane_package_write_once_collision")
        return
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    if path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError("control_plane_package_readback_mismatch")


def _relay_existing_authorized_package(*, package: dict[str, Any], package_path: Path, runtime_root: Path) -> dict[str, Any]:
    """Continue through the already-existing StegOS relay only when all governed inputs already exist."""
    manifest = package.get("manifest")
    rows = manifest.get("files") if isinstance(manifest, dict) else None
    by_path = {row.get("path"): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    missing = [rel for rel in REQUIRED_FUNCTIONAL_MEMORY_PATHS if rel not in by_path]
    if missing:
        raise RuntimeError("functional_memory_package_delta_missing:" + ",".join(missing))

    authorization_raw = str(os.environ.get(RELAY_AUTH_ENV) or "").strip()
    binding_raw = str(os.environ.get(RELAY_BINDING_ENV) or "").strip()
    stegos_raw = str(os.environ.get(STEGOS_ROOT_ENV) or "").strip()
    if not authorization_raw or not binding_raw or not stegos_raw:
        return {
            "state": "EXISTING_RELAY_INPUTS_NOT_CONFIGURED",
            "attempted": False,
            "authorization_present": bool(authorization_raw),
            "binding_present": bool(binding_raw),
            "stegos_root_present": bool(stegos_raw),
            "required_manifest_files": [
                {"path": rel, "sha256": by_path[rel].get("sha256"), "size": by_path[rel].get("size")}
                for rel in REQUIRED_FUNCTIONAL_MEMORY_PATHS
            ],
            "authority_effect": "NONE_EXISTING_RELAY_NOT_INVOKED",
        }

    authorization = Path(authorization_raw).expanduser().resolve()
    binding = Path(binding_raw).expanduser().resolve()
    stegos_root = Path(stegos_raw).expanduser().resolve()
    relay_script = stegos_root / "scripts/execute_control_plane_source_package_relay.py"
    if not authorization.is_file():
        raise RuntimeError("existing_relay_authorization_missing")
    if not binding.is_file():
        raise RuntimeError("existing_relay_binding_missing")
    if not relay_script.is_file():
        raise RuntimeError("existing_stegos_control_plane_relay_cli_missing")

    completed = subprocess.run(
        [
            sys.executable,
            str(relay_script),
            "--authorization", str(authorization),
            "--binding", str(binding),
            "--package", str(package_path),
            "--runtime-root", str(runtime_root),
        ],
        cwd=stegos_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    relay_result = None
    for line in reversed([line.strip() for line in completed.stdout.splitlines() if line.strip()]):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            relay_result = candidate
            break
    if completed.returncode != 0 or not isinstance(relay_result, dict):
        raise RuntimeError("existing_control_plane_relay_invocation_failed")

    result = relay_result.get("result")
    ingress = result.get("source_package_ingress_receipt") if isinstance(result, dict) else None
    materialization = ingress.get("source_materialization") if isinstance(ingress, dict) else None
    files = materialization.get("files") if isinstance(materialization, dict) else None
    materialized = {row.get("path"): row for row in files if isinstance(row, dict)} if isinstance(files, list) else {}
    for rel in REQUIRED_FUNCTIONAL_MEMORY_PATHS:
        packaged = by_path[rel]
        actual = materialized.get(rel)
        if not isinstance(actual, dict) or actual.get("sha256") != packaged.get("sha256") or actual.get("size") != packaged.get("size"):
            raise RuntimeError(f"source_materialization_digest_mismatch:{rel}")
    if (
        relay_result.get("state") != "SOURCE_MATERIALIZED_VERIFIED"
        or relay_result.get("source_package_ingress_verified") is not True
        or not isinstance(ingress, dict)
        or ingress.get("source_identity") != package.get("source_identity")
    ):
        raise RuntimeError("source_materialization_not_verified")

    receipt = {
        "schema": "stegverse.control-plane-source-package-existing-relay-continuation/v1",
        "state": "SOURCE_MATERIALIZED_VERIFIED",
        "source_identity": package.get("source_identity"),
        "authorization_ref": str(authorization),
        "binding_ref": str(binding),
        "relay_script_ref": str(relay_script),
        "required_manifest_files": [
            {"path": rel, "sha256": by_path[rel].get("sha256"), "size": by_path[rel].get("size")}
            for rel in REQUIRED_FUNCTIONAL_MEMORY_PATHS
        ],
        "far_side_materialization_verified": True,
        "relay_result": relay_result,
        "new_authorization_issued": False,
        "new_binding_created": False,
        "new_transport_created": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_EXISTING_RELAY_CONTINUATION_ONLY",
    }
    receipt_path = runtime_root / RELAY_RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = receipt_path.with_name("." + receipt_path.name + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, receipt_path)
    return receipt


def run() -> dict[str, Any]:
    manifest_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_MANIFEST"]).expanduser().resolve()
    result_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_RESULT_PATH"]).expanduser().resolve()
    manifest = load_json(manifest_path)
    if manifest.get("reusable_task_id") != REUSABLE_TASK_ID:
        raise RuntimeError("reusable_task_identity_mismatch")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict):
        raise RuntimeError("parameters_required")

    source_root = Path(str(parameters.get("source_root") or ROOT)).expanduser().resolve()
    runtime_raw = str(parameters.get("runtime_root") or os.environ.get("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    if not runtime_raw:
        raise RuntimeError("runtime_root_required")
    runtime_root = Path(runtime_raw).expanduser().resolve()
    if not source_root.is_dir():
        raise RuntimeError("canonical_source_root_missing")
    runtime_root.mkdir(parents=True, exist_ok=True)

    package = builder.build(source_root, builder.DEFAULT_PATHS)
    source_identity = str(package["source_identity"])
    digest = source_identity.removeprefix("sha256:")
    if len(digest) != 64:
        raise RuntimeError("source_identity_invalid")
    rendered = json.dumps(package, indent=2, sort_keys=True) + "\n"
    output = runtime_root / OUTBOX_REL / f"{digest}.json"
    atomic_write_once(output, rendered)
    relay_continuation = _relay_existing_authorized_package(
        package=package,
        package_path=output,
        runtime_root=runtime_root,
    )

    completion_predicates = json.loads(os.environ.get("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]"))
    result = {
        "schema": RESULT_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": REUSABLE_TASK_ID,
        "manifest_hash": manifest["manifest_hash"],
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "completion_predicates_satisfied": completion_predicates,
        "package": {
            "component_id": package["component_id"],
            "source_identity": source_identity,
            "file_count": package["manifest"]["file_count"],
            "package_ref": str(output),
            "package_size": len(rendered.encode("utf-8")),
            "credential_material_included": False,
            "network_source_fetch_performed": False,
            "relay_transport_executed": False,
            "tvc_authorization_issued": False,
            "existing_relay_continuation": relay_continuation,
        },
        "authority_effect": "NONE_SOURCE_PACKAGE_BUILD_ONLY",
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = result_path.with_name("." + result_path.name + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, result_path)
    return result


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
