#!/usr/bin/env python3
"""Credential-free exact source materializer for the SV-DN-1 resident lane."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping
from urllib.parse import quote
from urllib.request import Request, urlopen

TASK_ID = "SV-DN1-SOURCE-MATERIALIZATION-001"
WORKER_ID = "sv-dn1-source-materialization-worker"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
SOURCE_ROOT_ENV = "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT"
DEFAULT_SOURCE_ROOT = Path.home() / ".stegverse" / "source" / "stegverse-demo-suite"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)
RAW_HOST = "raw.githubusercontent.com"
REPOSITORY = "StegVerse-org/stegverse-demo-suite"
MANIFEST_REF = "main"
MANIFEST_PATH = "config/sv_dn1_runtime_source_manifest.json"
EXPECTED_MANIFEST_BLOB = "47760f63898fff0f5ba6dfab97eee5acd7290c9b"
SUPPORT_FILES = {
    "docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md": "ba9acf76fd6eb488e5f3b9f9be01bb17e3a02d48",
    "tasks/SV-DN1-RESIDENT-OBSERVER-001.json": "0dbe655a86bea3d2a0f77aa2ada57a62882f00db",
}


class SourcePinDrift(RuntimeError):
    """Canonical source pin differs from the admitted materialization task."""


class PublicSourceUnavailable(RuntimeError):
    """Credential-free public source transport is temporarily unavailable."""


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def read_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"{label}: invalid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label}: expected JSON object")
    return value


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def raw_url(ref: str, path: str) -> str:
    safe_path = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"https://{RAW_HOST}/{REPOSITORY}/{quote(ref, safe='')}/{safe_path}"


def fetch_bytes(ref: str, path: str, *, timeout: int = 30) -> bytes:
    url = raw_url(ref, path)
    request = Request(
        url,
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": "StegVerse-SV-DN1-Source-Materializer/1",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            if not final_url.startswith(f"https://{RAW_HOST}/"):
                raise RuntimeError(f"public source redirect left admitted host: {final_url}")
            status = getattr(response, "status", 200)
            if status != 200:
                raise PublicSourceUnavailable(f"public source returned HTTP {status}: {url}")
            data = response.read(5 * 1024 * 1024 + 1)
    except SourcePinDrift:
        raise
    except PublicSourceUnavailable:
        raise
    except Exception as exc:
        raise PublicSourceUnavailable(f"public source fetch failed for {path}: {type(exc).__name__}: {exc}") from exc
    if len(data) > 5 * 1024 * 1024:
        raise RuntimeError(f"public source object exceeds 5 MiB limit: {path}")
    return data


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise RuntimeError("sovereign node marker must be an object")
            if value.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if value.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if value.get("github_token_required") is not False:
                raise RuntimeError("source materialization may not require GitHub token")
            return path, value
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("unexpected invocation schema")
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    timing = task.get("heartbeat_timing") or {}
    if not isinstance(timing.get("fencing_token"), int):
        raise RuntimeError("fresh fencing token is required")

    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("source materializer may not write repositories")
    if authority.get("observation_authority") is not False:
        raise RuntimeError("source materializer may not own observation")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant source-materialization authority")

    contract = handoff.get("input_contract") or {}
    if contract.get("source_repository") != REPOSITORY:
        raise RuntimeError("source repository drift")
    if contract.get("manifest_ref") != MANIFEST_REF:
        raise RuntimeError("manifest ref drift")
    if contract.get("manifest_path") != MANIFEST_PATH:
        raise RuntimeError("manifest path drift")
    if contract.get("manifest_git_blob_sha1") != EXPECTED_MANIFEST_BLOB:
        raise RuntimeError("manifest pin drift in handoff")
    if contract.get("support_files") != SUPPORT_FILES:
        raise RuntimeError("support file pin drift in handoff")
    return dict(task)


def require_bound_state_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    if not raw:
        raise RuntimeError("bounded materialization state root is not available")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def source_root() -> Path:
    raw = str(os.getenv(SOURCE_ROOT_ENV) or "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_SOURCE_ROOT.expanduser().resolve()


def validate_manifest(data: bytes) -> dict[str, Any]:
    actual = git_blob_sha1(data)
    if actual != EXPECTED_MANIFEST_BLOB:
        raise SourcePinDrift(
            f"runtime source manifest blob changed: expected {EXPECTED_MANIFEST_BLOB}, observed {actual}"
        )
    manifest = read_json_bytes(data, "runtime source manifest")
    if manifest.get("schema") != "stegverse.sv-dn1.runtime-source-manifest/v1":
        raise RuntimeError("wrong runtime source manifest schema")
    if manifest.get("profile_id") != "SV-DN-1":
        raise RuntimeError("wrong runtime source manifest profile")
    if manifest.get("source_repository") != REPOSITORY:
        raise RuntimeError("runtime source manifest repository drift")
    if manifest.get("hash_profile") != "git-blob-sha1":
        raise RuntimeError("unsupported runtime source hash profile")
    basis = manifest.get("source_basis_commit")
    if not isinstance(basis, str) or len(basis) != 40:
        raise RuntimeError("runtime source manifest basis commit missing")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise RuntimeError("runtime source manifest files missing")
    for rel, digest in files.items():
        if not isinstance(rel, str) or rel.startswith("/") or ".." in Path(rel).parts:
            raise RuntimeError(f"unsafe runtime source path: {rel}")
        if not isinstance(digest, str) or len(digest) != 40:
            raise RuntimeError(f"invalid runtime source blob identity: {rel}")
    return manifest


def acquire_objects(manifest_data: bytes, manifest: Mapping[str, Any]) -> dict[str, bytes]:
    objects: dict[str, bytes] = {MANIFEST_PATH: manifest_data}
    basis = str(manifest["source_basis_commit"])
    for rel, expected in sorted((manifest.get("files") or {}).items()):
        data = fetch_bytes(basis, str(rel))
        actual = git_blob_sha1(data)
        if actual != expected:
            raise SourcePinDrift(f"source blob mismatch for {rel}: expected {expected}, observed {actual}")
        objects[str(rel)] = data
    for rel, expected in SUPPORT_FILES.items():
        data = fetch_bytes("main", rel)
        actual = git_blob_sha1(data)
        if actual != expected:
            raise SourcePinDrift(f"support blob mismatch for {rel}: expected {expected}, observed {actual}")
        objects[rel] = data
    return objects


def write_tree(root: Path, objects: Mapping[str, bytes]) -> None:
    parent = root.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = Path(tempfile.mkdtemp(prefix=".sv-dn1-source-", dir=parent))
    backup: Path | None = None
    try:
        for rel, data in objects.items():
            assert stage is not None
            path = stage / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if root.exists() or root.is_symlink():
            backup = parent / f".{root.name}.previous"
            if backup.exists() or backup.is_symlink():
                if backup.is_dir() and not backup.is_symlink():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
            os.replace(root, backup)
        assert stage is not None
        os.replace(stage, root)
        stage = None
        if backup is not None:
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            elif backup.exists() or backup.is_symlink():
                backup.unlink()
    except Exception:
        if backup is not None and backup.exists() and not root.exists():
            os.replace(backup, root)
        raise
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def validate_materialized(root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    verified: list[str] = []
    manifest_path = root / MANIFEST_PATH
    if not manifest_path.is_file():
        failures.append(f"missing:{MANIFEST_PATH}")
    else:
        actual = git_blob_sha1(manifest_path.read_bytes())
        if actual != EXPECTED_MANIFEST_BLOB:
            failures.append(f"drift:{MANIFEST_PATH}:{actual}")
        else:
            verified.append(MANIFEST_PATH)
    for rel, expected in sorted((manifest.get("files") or {}).items()):
        path = root / rel
        if not path.is_file():
            failures.append(f"missing:{rel}")
            continue
        actual = git_blob_sha1(path.read_bytes())
        if actual != expected:
            failures.append(f"drift:{rel}:{actual}")
        else:
            verified.append(rel)
    for rel, expected in SUPPORT_FILES.items():
        path = root / rel
        if not path.is_file():
            failures.append(f"missing:{rel}")
            continue
        actual = git_blob_sha1(path.read_bytes())
        if actual != expected:
            failures.append(f"drift:{rel}:{actual}")
        else:
            verified.append(rel)
    return {
        "schema": "stegverse.sv-dn1.source-materialization-validation/v1",
        "state": "PASS" if not failures else "FAIL",
        "source_root": str(root),
        "source_basis_commit": manifest.get("source_basis_commit"),
        "manifest_blob_sha1": EXPECTED_MANIFEST_BLOB,
        "verified_files": sorted(verified),
        "failures": failures,
        "authority_effect": "NONE",
    }


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign SV-DN-1 source materialization")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for source materialization: " + ",".join(sorted(present)))

    node_path, _ = find_node()
    task = validate_invocation(invocation)
    bound = require_bound_state_root()
    root = source_root()

    manifest_data = fetch_bytes(MANIFEST_REF, MANIFEST_PATH)
    manifest = validate_manifest(manifest_data)
    objects = acquire_objects(manifest_data, manifest)
    write_tree(root, objects)
    validation = validate_materialized(root, manifest)
    if validation["state"] != "PASS":
        raise RuntimeError("post-write exact source validation failed: " + ";".join(validation["failures"]))

    materialization_dir = bound / "materialization"
    atomic_json(materialization_dir / "source-manifest.json", manifest)
    atomic_json(materialization_dir / "validation.json", validation)

    receipt = {
        "schema": "stegverse.sv-dn1.source-materialization-receipt/v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "state": "COMPLETE",
        "transition_id": "SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE",
        "claim_id": task.get("claim_id"),
        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
        "node_declaration_ref": str(node_path),
        "source_repository": REPOSITORY,
        "source_root": str(root),
        "source_basis_commit": manifest.get("source_basis_commit"),
        "manifest_blob_sha1": EXPECTED_MANIFEST_BLOB,
        "manifest_blob_verified": True,
        "production_source_blobs_verified": True,
        "support_file_blobs_verified": True,
        "post_write_validation": "PASS",
        "verified_file_count": len(validation["verified_files"]),
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "github_token_used": False,
        "remote_checkout_performed": False,
        "git_client_used": False,
        "repository_writeback_performed": False,
        "observation_performed": False,
        "sdk_admitted": False,
        "governance_decision_performed": False,
        "authority_effect": "SOURCE_MATERIALIZATION_ONLY_NO_NEW_AUTHORITY",
    }
    atomic_json(bound / "receipts" / "latest.json", receipt)
    return receipt


def completed_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
        "checkpoint_ref": "receipts/latest.json",
        "evidence_refs": [
            "materialization/source-manifest.json",
            "materialization/validation.json",
            "receipts/latest.json",
        ],
        "materialized_source_root": receipt.get("source_root"),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def wait_response(exc: Exception, transition: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "dependency_class": "PUBLIC_SOURCE_OR_PIN_STATE",
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Reconcile the exact canonical source pin or retry the same credential-free public source acquisition when available.",
            "machine_observable_release_condition": "canonical manifest/support pins match and all public source blobs verify",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "human_action_required": False,
        },
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "SV_DN1_SOURCE_MATERIALIZATION_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        receipt = execute(invocation)
        print(json.dumps(completed_response(receipt), sort_keys=True))
        return 0
    except SourcePinDrift as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_SOURCE_PIN_RECONCILIATION_REQUIRED"), sort_keys=True))
        return 0
    except PublicSourceUnavailable as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_PUBLIC_SOURCE_MATERIALIZATION_RETRY"), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
