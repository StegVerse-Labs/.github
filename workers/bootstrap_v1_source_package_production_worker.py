#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
from typing import Any, Mapping

TASK_ID = "BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001"
WORKER_ID = "bootstrap-v1-source-package-production-worker"
SOURCE_PREP_ENV = "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT"
PACKAGE_ENV = "STEGVERSE_SOURCE_PACKAGE_ROOT"
BOUND_ENV = "STEGVERSE_BOUND_STATE_ROOT"

DEFAULT_SOURCE_PREP = Path.home() / ".stegverse" / "state" / "sv-dn1-production-source-prep"
DEFAULT_PACKAGES = Path.home() / ".stegverse" / "packages" / "source" / "v1"
DEFAULT_BOUND = Path.home() / ".stegverse" / "state" / "bootstrap-v1-source-package-production"

PACKAGE_SCHEMA = "stegverse.source-package/v1"
PACKAGE_VERSION = "1.0.0"
COMPONENTS = (
    "stegverse.sdk",
    "stegverse.stegcore",
    "stegverse.core-lite",
    "stegverse.master-records",
)
ROOT_ENV = {
    "stegverse.sdk": "STEGVERSE_SDK_SOURCE_ROOT",
    "stegverse.stegcore": "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "stegverse.core-lite": "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "stegverse.master-records": "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
}
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AZURE_CLIENT_SECRET", "OAUTH_TOKEN",
)

class UpstreamPending(RuntimeError):
    pass

class PackageConflict(RuntimeError):
    pass

def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def bytes_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def slug(component: str) -> str:
    return component.lower().replace("/", "--").replace("_", "-").replace(".", "-")

def load(path: Path, pending: bool = False) -> dict[str, Any]:
    if not path.is_file():
        if pending:
            raise UpstreamPending(f"required upstream object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value

def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(dict(value), handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def source_prep_root() -> Path:
    return Path(os.environ.get(SOURCE_PREP_ENV, str(DEFAULT_SOURCE_PREP))).expanduser().resolve()

def package_root() -> Path:
    return Path(os.environ.get(PACKAGE_ENV, str(DEFAULT_PACKAGES))).expanduser().resolve()

def bound_root() -> Path:
    return Path(os.environ.get(BOUND_ENV, str(DEFAULT_BOUND))).expanduser().resolve()

def package_path(store: Path, component: str) -> Path:
    return store / slug(component) / "package.json"

def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] == ".git":
            continue
        pure = PurePosixPath(rel.as_posix())
        if not pure.parts or pure.is_absolute() or ".." in pure.parts:
            raise RuntimeError(f"unsafe source path: {rel}")
        yield pure.as_posix(), path

def manifest_and_files(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for rel, path in iter_files(root):
        raw = path.read_bytes()
        sha = bytes_digest(raw)
        row = {"path": rel, "sha256": sha, "size": len(raw)}
        rows.append(row)
        files.append({**row, "content_base64": base64.b64encode(raw).decode("ascii")})
    if not rows:
        raise RuntimeError(f"source root contains no packageable files: {root}")
    bundle = digest(rows)
    return {"file_count": len(rows), "source_bundle_sha256": bundle, "files": rows}, files

def validate_upstream(receipt: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    expected = {
        "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
        "state": "COMPLETE",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "source_identity_scheme": "sha256-content-manifest",
        "migration_anchors_verified": True,
        "network_source_fetch_performed": False,
        "github_platform_required": False,
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "sdk_admitted": False,
    }
    for key, wanted in expected.items():
        if receipt.get(key) != wanted:
            raise UpstreamPending(f"source-prep receipt {key} mismatch")
    identities = receipt.get("source_identities")
    roots = receipt.get("source_roots")
    env_map = receipt.get("source_root_env")
    if not isinstance(identities, dict) or set(identities) != set(COMPONENTS):
        raise RuntimeError("source identity component set mismatch")
    if not isinstance(roots, dict) or set(roots) != set(COMPONENTS):
        raise RuntimeError("source root component set mismatch")
    if not isinstance(env_map, dict) or set(env_map) != set(ROOT_ENV.values()):
        raise RuntimeError("source root env component set mismatch")
    out_ids: dict[str, str] = {}
    out_roots: dict[str, str] = {}
    for component in COMPONENTS:
        ident = identities[component]
        root = roots[component]
        env_name = ROOT_ENV[component]
        if not isinstance(ident, str) or len(ident) != 71 or not ident.startswith("sha256:"):
            raise RuntimeError(f"{component}: source identity invalid")
        try:
            int(ident[7:], 16)
        except ValueError as exc:
            raise RuntimeError(f"{component}: source identity hex invalid") from exc
        if not isinstance(root, str) or not root:
            raise RuntimeError(f"{component}: source root missing")
        if env_map.get(env_name) != root:
            raise RuntimeError(f"{component}: source root disagrees with {env_name}")
        resolved = Path(root).expanduser().resolve()
        if not resolved.is_dir():
            raise UpstreamPending(f"{component}: local source root not present: {resolved}")
        out_ids[component] = ident
        out_roots[component] = str(resolved)
    return out_ids, out_roots

def build_package(component: str, root: Path, expected_identity: str) -> dict[str, Any]:
    manifest, files = manifest_and_files(root)
    identity = "sha256:" + manifest["source_bundle_sha256"]
    if identity != expected_identity:
        raise RuntimeError(f"{component}: source bytes no longer match source-prep identity")
    return {
        "schema": PACKAGE_SCHEMA,
        "package_version": PACKAGE_VERSION,
        "component_id": component,
        "source_identity": identity,
        "credential_material_included": False,
        "manifest": manifest,
        "files": files,
        "provenance": {
            "source_identity_scheme": "sha256-content-manifest",
            "upstream_kind": "stegverse.sv-dn1.production-source-prep-receipt/v2",
            "external_platform_required": False,
        },
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
    }

def validate_package(package: Mapping[str, Any], component: str, expected_identity: str) -> None:
    if package.get("schema") != PACKAGE_SCHEMA or package.get("package_version") != PACKAGE_VERSION:
        raise RuntimeError(f"{component}: package contract mismatch")
    if package.get("component_id") != component or package.get("source_identity") != expected_identity:
        raise RuntimeError(f"{component}: package identity mismatch")
    if package.get("credential_material_included") is not False or package.get("authority_effect") != "NONE_SOURCE_TRANSPORT_ONLY":
        raise RuntimeError(f"{component}: package authority boundary mismatch")
    manifest = package.get("manifest")
    files = package.get("files")
    if not isinstance(manifest, dict) or not isinstance(files, list) or not isinstance(manifest.get("files"), list):
        raise RuntimeError(f"{component}: package manifest missing")
    if manifest.get("file_count") != len(files) or len(manifest["files"]) != len(files):
        raise RuntimeError(f"{component}: package file count mismatch")
    rows = []
    for index, file_row in enumerate(files):
        manifest_row = manifest["files"][index]
        if not isinstance(file_row, dict) or not isinstance(manifest_row, dict):
            raise RuntimeError(f"{component}: package row invalid")
        if any(file_row.get(k) != manifest_row.get(k) for k in ("path", "sha256", "size")):
            raise RuntimeError(f"{component}: package manifest/file mismatch")
        pure = PurePosixPath(str(file_row.get("path")))
        if not pure.parts or pure.is_absolute() or ".." in pure.parts:
            raise RuntimeError(f"{component}: unsafe package path")
        try:
            raw = base64.b64decode(file_row.get("content_base64", ""), validate=True)
        except Exception as exc:
            raise RuntimeError(f"{component}: invalid package base64") from exc
        if len(raw) != file_row.get("size") or bytes_digest(raw) != file_row.get("sha256"):
            raise RuntimeError(f"{component}: package file integrity mismatch")
        rows.append({"path": file_row["path"], "sha256": file_row["sha256"], "size": file_row["size"]})
    manifest_digest = digest(rows)
    if manifest_digest != manifest.get("source_bundle_sha256") or "sha256:" + manifest_digest != expected_identity:
        raise RuntimeError(f"{component}: package manifest identity mismatch")

def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED):
        raise RuntimeError("hosted environment cannot produce sovereign Bootstrap v1 source packages")
    present = [name for name in FORBIDDEN if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden: " + ",".join(sorted(present)))
    task = invocation.get("task") or {}
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("worker invocation schema mismatch")
    if task.get("task_id") != TASK_ID or task.get("worker_id") != WORKER_ID or not task.get("claim_id"):
        raise RuntimeError("task/worker/claim identity mismatch")

    upstream_path = source_prep_root() / "receipts" / "latest.json"
    upstream = load(upstream_path, pending=True)
    identities, roots = validate_upstream(upstream)
    store = package_root()
    packages: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []

    for component in COMPONENTS:
        package = build_package(component, Path(roots[component]), identities[component])
        validate_package(package, component, identities[component])
        path = package_path(store, component)
        if path.is_file():
            existing = load(path)
            if existing != package:
                raise PackageConflict(f"BOOTSTRAP_V1_SOURCE_PACKAGE_CONFLICT:{component}")
        else:
            atomic_json(path, package)
        packages[component] = package
        rows.append({
            "component_id": component,
            "source_identity": identities[component],
            "package_path": str(path),
            "package_sha256": digest(package),
            "file_count": package["manifest"]["file_count"],
            "source_bundle_sha256": package["manifest"]["source_bundle_sha256"],
        })

    receipt = {
        "schema": "stegverse.bootstrap.source-package-production-receipt/v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "state": "COMPLETE",
        "transition_id": "BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED",
        "claim_id": task.get("claim_id"),
        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
        "upstream_source_prep_receipt_sha256": digest(upstream),
        "source_identity_scheme": "sha256-content-manifest",
        "package_schema": PACKAGE_SCHEMA,
        "package_version": PACKAGE_VERSION,
        "component_count": 4,
        "packages": rows,
        "github_platform_required": False,
        "specific_external_platform_required": False,
        "network_access_performed": False,
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "package_execution_performed": False,
        "sdk_admitted": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_SOURCE_PACKAGE_PRODUCTION_ONLY",
    }
    atomic_json(bound_root() / "receipts" / "latest.json", receipt)
    return receipt

def main() -> int:
    try:
        invocation = json.loads(sys.stdin.readline())
        receipt = execute(invocation)
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETED",
            "transition_id": "BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED",
            "transition_sequence": 1,
            "expected_next_transition": "BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT",
            "checkpoint_ref": "receipts/latest.json",
            "evidence_refs": ["receipts/latest.json"],
            "component_count": receipt["component_count"],
            "github_platform_required": False,
            "authority_effect": "NONE_SOURCE_PACKAGE_PRODUCTION_ONLY",
        }, sort_keys=True))
        return 0
    except UpstreamPending as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "BOOTSTRAP_V1_SOURCE_PREP_FOR_PACKAGING_PENDING",
            "transition_sequence": 1,
            "expected_next_transition": "BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED",
            "error": str(exc),
            "github_platform_required": False,
            "blocker": {
                "dependency_class": "SOURCE_PREP_RECEIPT_OR_LOCAL_ROOT",
                "problem_statement": str(exc),
                "solution_required": True,
                "may_remain_blocked": False,
                "next_solution_action": "Wait for the authentic platform-neutral source-prep v2 receipt and its exact already-local source roots.",
                "machine_observable_release_condition": "source-prep v2 receipt is COMPLETE and all four exact local source roots are present",
                "physical_additional_machine_required": False,
                "third_party_runtime_required": False,
                "github_platform_required": False,
                "human_action_required": False,
            },
        }, sort_keys=True))
        return 0
    except PackageConflict as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "BOOTSTRAP_V1_SOURCE_PACKAGE_CONFLICT",
            "error": str(exc),
            "github_platform_required": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "BOOTSTRAP_V1_SOURCE_PACKAGE_PRODUCTION_BLOCKED",
            "error": str(exc),
            "github_platform_required": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }, sort_keys=True))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
