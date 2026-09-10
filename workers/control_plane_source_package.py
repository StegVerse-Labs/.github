#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any, Mapping

PACKAGE_SCHEMA = "stegverse.source-package/v1"
PACKAGE_VERSION = "1.0.0"
COMPONENT_ID = "stegverse.control-plane"
PACKAGE_SLUG = "stegverse-control-plane"
AUTHORITY_EFFECT = "NONE_SOURCE_TRANSPORT_ONLY"

ALLOWED_PREFIXES = (
    "heartbeat_runtime/",
    "workers/",
    "handoffs/",
    "authorizations/",
    "schemas/",
    "cost-basis/",
    "management/",
    "state_language/",
    "source-bundles/",
    "review-packages/",
    "scripts/",
    "control/worker-registry.d/",
    "control/process-worker-adapters.d/",
    "control/task-vectors/",
    "control/task-vector-index.d/",
    "control/resident-execution-request.d/",
    "control/manifold-lineage.d/",
    "control/runtime-observability-consumers/",
    "data/canonical-task-records/",
)
ALLOWED_EXACT = {
    "control/process-worker-adapters.json",
    "control/worker-capability-profiles.json",
    "control/blocker-resolution-policy.json",
    "control/stegindex-preflight-policy.json",
    "control/task-vector-index.json",
    "control/resident-execution-request.json",
    "control/astra-class-adversarial-resilience-contract.json",
    "control/quantum-resilience-contract.json",
    "control/quantum-crypto-census.json",
    "data/reusable-task-registry.json",
    "data/reusable-task-ephemeral-construct-contract.json",
}
FORBIDDEN_PREFIXES = (
    ".git/", "receipts/", "checkpoints/", "events/", "heartbeats/",
)
FORBIDDEN_EXACT = {
    "control/heartbeat-state.json",
    "control/heartbeat-carrier-runtime-state.json",
    "control/worker-runtime-state.json",
    "control/worker-registry.json",
    "control/worker-control-plane-coordination.json",
    "control/worker-status.json",
}

class ControlPlaneSourcePackageError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _safe_rel(value: Any) -> str:
    rel = str(value or "")
    pure = PurePosixPath(rel)
    if not pure.parts or pure.is_absolute() or ".." in pure.parts:
        raise ControlPlaneSourcePackageError("unsafe package path")
    normalized = pure.as_posix()
    if normalized in FORBIDDEN_EXACT or any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        raise ControlPlaneSourcePackageError(f"mutable/forbidden source path: {normalized}")
    if normalized not in ALLOWED_EXACT and not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        raise ControlPlaneSourcePackageError(f"source path outside control-plane allowlist: {normalized}")
    return normalized


def validate_package(package: Mapping[str, Any]) -> dict[str, Any]:
    if package.get("schema") != PACKAGE_SCHEMA or package.get("package_version") != PACKAGE_VERSION:
        raise ControlPlaneSourcePackageError("package schema/version mismatch")
    if package.get("component_id") != COMPONENT_ID:
        raise ControlPlaneSourcePackageError("package component mismatch")
    if package.get("credential_material_included") is not False:
        raise ControlPlaneSourcePackageError("credential material forbidden")
    if package.get("authority_effect") != AUTHORITY_EFFECT:
        raise ControlPlaneSourcePackageError("package authority effect mismatch")
    manifest = package.get("manifest")
    files = package.get("files")
    if not isinstance(manifest, Mapping) or not isinstance(files, list):
        raise ControlPlaneSourcePackageError("package manifest/files missing")
    manifest_rows = manifest.get("files")
    if not isinstance(manifest_rows, list) or manifest.get("file_count") != len(files) or len(manifest_rows) != len(files):
        raise ControlPlaneSourcePackageError("package file count mismatch")
    rows: list[dict[str, Any]] = []
    decoded: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for index, file_row in enumerate(files):
        manifest_row = manifest_rows[index]
        if not isinstance(file_row, Mapping) or not isinstance(manifest_row, Mapping):
            raise ControlPlaneSourcePackageError("package row malformed")
        rel = _safe_rel(file_row.get("path"))
        if rel in seen:
            raise ControlPlaneSourcePackageError("duplicate package path")
        seen.add(rel)
        expected = {"path": rel, "sha256": file_row.get("sha256"), "size": file_row.get("size")}
        if any(manifest_row.get(key) != value for key, value in expected.items()):
            raise ControlPlaneSourcePackageError("package manifest/file mismatch")
        try:
            raw = base64.b64decode(str(file_row.get("content_base64") or ""), validate=True)
        except Exception as exc:
            raise ControlPlaneSourcePackageError("invalid package base64") from exc
        if len(raw) != file_row.get("size") or sha256_bytes(raw) != file_row.get("sha256"):
            raise ControlPlaneSourcePackageError(f"package file integrity mismatch: {rel}")
        rows.append(expected)
        decoded.append((rel, raw))
    manifest_digest = digest(rows)
    if manifest.get("source_bundle_sha256") != manifest_digest:
        raise ControlPlaneSourcePackageError("package source bundle digest mismatch")
    identity = "sha256:" + manifest_digest
    if package.get("source_identity") != identity:
        raise ControlPlaneSourcePackageError("package source identity mismatch")
    return {"source_identity": identity, "manifest": {"file_count": len(rows), "source_bundle_sha256": manifest_digest, "files": rows}, "decoded": decoded}


def package_store_path(package_root: Path) -> Path:
    return package_root.expanduser().resolve() / PACKAGE_SLUG / "package.json"


def write_once_package(package_root: Path, package: Mapping[str, Any]) -> Path:
    validate_package(package)
    path = package_store_path(package_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(dict(package), indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise ControlPlaneSourcePackageError("control-plane source package write-once collision")
        return path
    fd, temp = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    if path.read_text(encoding="utf-8") != rendered:
        raise ControlPlaneSourcePackageError("control-plane source package persistence verification failed")
    return path


def materialize_into_source(source_root: Path, package: Mapping[str, Any]) -> dict[str, Any]:
    verified = validate_package(package)
    root = source_root.expanduser().resolve()
    if not root.is_dir():
        raise ControlPlaneSourcePackageError("canonical source root missing")
    staged_root = Path(tempfile.mkdtemp(prefix=".stegverse-control-plane-package-", dir=root.parent))
    applied: list[dict[str, Any]] = []
    try:
        for rel, raw in verified["decoded"]:
            staged = staged_root / rel
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(raw)
            if sha256_bytes(staged.read_bytes()) != sha256_bytes(raw):
                raise ControlPlaneSourcePackageError(f"staged verification failed: {rel}")
        for rel, raw in verified["decoded"]:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temp = tempfile.mkstemp(prefix="." + target.name + ".", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                os.replace(temp, target)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            actual = sha256_bytes(target.read_bytes())
            if actual != sha256_bytes(raw):
                raise ControlPlaneSourcePackageError(f"source write/read verification failed: {rel}")
            applied.append({"path": rel, "sha256": actual, "size": len(raw)})
    finally:
        import shutil
        shutil.rmtree(staged_root, ignore_errors=True)
    return {
        "schema": "stegverse.control-plane-source-package-materialization/v1",
        "state": "MATERIALIZED_VERIFIED",
        "component_id": COMPONENT_ID,
        "source_identity": verified["source_identity"],
        "file_count": len(applied),
        "files": applied,
        "network_source_fetch_performed": False,
        "credential_read_or_acquired": False,
        "repository_metadata_mutated": False,
        "mutable_runtime_state_mutated": False,
        "authority_effect": "NONE_LOCAL_SOURCE_MATERIALIZATION_ONLY",
    }
