#!/usr/bin/env python3
"""One-shot sovereign resident observer for the SV-DN-1 public-source lane."""
from __future__ import annotations

import importlib.util
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

TASK_ID = "SV-DN1-RESIDENT-OBSERVER-001"
WORKER_ID = "sv-dn1-resident-observer-worker"
ROOT_ENV = "STEGVERSE_SV_DN1_SOURCE_ROOT"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
TARGET_URL = "https://huggingface.co/api/models/Qwen/Qwen3-8B"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)
REQUIRED_SOURCE_FILES = (
    Path("docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md"),
    Path("tasks/SV-DN1-RESIDENT-OBSERVER-001.json"),
    Path("scripts/observe_sv_dn1_hf_public.py"),
    Path("scripts/sv_dn1_hf_interlock.py"),
    Path("scripts/sv_dn1_stegverse_interlock.py"),
    Path("config/sv_dn1_hf_mapping.v1.json"),
    Path("config/sv_dn1_runtime_source_manifest.json"),
)


class SourceUnavailable(RuntimeError):
    """Exact demo-suite source is not yet locally materialized."""


class PublicSourceUnavailable(RuntimeError):
    """The admitted public source is currently unavailable without widening authority."""


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            node = read_json(path)
            if node.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if node.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if node.get("github_token_required") is not False:
                raise RuntimeError("resident observer may not require GitHub token")
            return path, node
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    authority = (invocation.get("handoff") or {}).get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("observer may not write back to repositories")
    if authority.get("sdk_admission_authority") is not False:
        raise RuntimeError("resident observer may not claim SDK admission authority")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant observer execution authority")


def local_source_roots() -> list[Path]:
    roots: list[Path] = []
    explicit = str(os.getenv(ROOT_ENV) or "").strip()
    if explicit:
        roots.append(Path(explicit))
    roots.extend([
        Path.cwd() / "workloads" / "stegverse-demo-suite",
        Path.cwd() / "workloads" / "StegVerse-demo-suite",
        Path.home() / ".stegverse" / "workloads" / "stegverse-demo-suite",
        Path("/var/lib/stegverse/workloads/stegverse-demo-suite"),
        Path.home() / ".stegverse" / "source" / "stegverse-demo-suite",
        Path("/var/lib/stegverse/source/stegverse-demo-suite"),
    ])
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in roots:
        try:
            key = str(candidate.expanduser().resolve())
        except Exception:
            key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def find_source_root() -> Path | None:
    for candidate in local_source_roots():
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        if root.is_dir() and all((root / relative).is_file() for relative in REQUIRED_SOURCE_FILES):
            return root
    return None



def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def validate_pinned_source(root: Path) -> dict[str, Any]:
    manifest_path = root / "config" / "sv_dn1_runtime_source_manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("schema") != "stegverse.sv-dn1.runtime-source-manifest/v1":
        raise RuntimeError("wrong SV-DN-1 runtime source manifest schema")
    if manifest.get("hash_profile") != "git-blob-sha1":
        raise RuntimeError("unsupported SV-DN-1 runtime source hash profile")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise RuntimeError("SV-DN-1 runtime source manifest files missing")
    failures: list[str] = []
    for rel, expected in sorted(files.items()):
        path = root / str(rel)
        if not path.is_file():
            failures.append(f"missing:{rel}")
            continue
        actual = git_blob_sha1(path.read_bytes())
        if actual != expected:
            failures.append(f"drift:{rel}:{expected}:{actual}")
    if failures:
        raise SourceUnavailable("exact pinned SV-DN-1 source validation failed: " + ";".join(failures))
    return manifest

def require_source_root() -> Path:
    root = find_source_root()
    if root is None:
        raise SourceUnavailable(
            "materialized stegverse-demo-suite source root is missing from explicit locator and canonical local paths"
        )
    return root


def require_bound_state_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    if not raw:
        raise RuntimeError("bounded observer state root is not available")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def clean_child_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
    }


def load_destination_validator(source_root: Path):
    path = source_root / "scripts" / "sv_dn1_stegverse_interlock.py"
    spec = importlib.util.spec_from_file_location("sv_dn1_destination_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign SV-DN-1 observation")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for SV-DN-1 observer: " + ",".join(sorted(present)))

    node_path, node = find_node()
    validate_invocation(invocation)
    source_root = require_source_root()
    source_manifest = validate_pinned_source(source_root)
    bound_state = require_bound_state_root()
    observed = bound_state / "observed"
    observed.mkdir(parents=True, exist_ok=True)

    capture_path = observed / "source-capture.json"
    native_path = observed / "native.json"
    exchange_path = observed / "exchange.json"
    child = clean_child_env()

    capture_proc = subprocess.run(
        [
            sys.executable,
            "scripts/observe_sv_dn1_hf_public.py",
            "--url", TARGET_URL,
            "--observed-at", str((invocation.get("context") or {}).get("observed_at") or ""),
            "--output", str(capture_path),
        ],
        cwd=source_root,
        env=child,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    if capture_proc.returncode != 0:
        tail = (capture_proc.stdout + capture_proc.stderr)[-3000:]
        raise PublicSourceUnavailable("public Hugging Face source capture failed: " + tail)
    capture = read_json(capture_path)
    raw_hash = capture.get("raw_sha256")
    if not isinstance(raw_hash, str) or not raw_hash.startswith("sha256:"):
        raise RuntimeError("source capture did not preserve raw-byte sha256")
    claims = capture.get("claims") or {}
    if claims.get("credential_used") is not False:
        raise RuntimeError("source capture used or claimed a credential")
    if claims.get("hugging_face_endorsement_claimed") is not False:
        raise RuntimeError("source capture inferred Hugging Face endorsement")

    parsed = capture.get("parsed_json")
    if not isinstance(parsed, dict):
        raise RuntimeError("source capture did not preserve parsed JSON object")
    native_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    exchange_proc = subprocess.run(
        [
            sys.executable,
            "scripts/sv_dn1_hf_interlock.py",
            "--input", str(native_path),
            "--native-ref", capture["final_url"],
            "--observed-at", capture["observed_at"],
            "--output", str(exchange_path),
        ],
        cwd=source_root,
        env=child,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if exchange_proc.returncode != 0:
        raise RuntimeError("HF-facing semantic Interlock failed: " + (exchange_proc.stdout + exchange_proc.stderr)[-3000:])
    exchange = read_json(exchange_path)

    validator = load_destination_validator(source_root)
    blockers = validator.validate_exchange(exchange)
    if blockers:
        raise RuntimeError("destination structural validation blocked exchange: " + ",".join(blockers))

    receipt = {
        "schema": "stegverse.sv-dn1.resident-source-observer-receipt/v0.1",
        "task_id": TASK_ID,
        "state": "COMPLETE",
        "transition_id": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "worker_id": WORKER_ID,
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "source_root": str(source_root),
        "source_basis_commit": source_manifest.get("source_basis_commit"),
        "source_hash_profile": source_manifest.get("hash_profile"),
        "source_file_count_verified": len(source_manifest.get("files") or {}),
        "source_discovery_mode": "explicit" if str(os.getenv(ROOT_ENV) or "").strip() else "canonical_local_path",
        "target_url": TARGET_URL,
        "source_capture_ref": "observed/source-capture.json",
        "raw_response_sha256": raw_hash,
        "raw_response_sha256_present": True,
        "semantic_exchange_ref": "observed/exchange.json",
        "semantic_exchange_id": exchange.get("exchange_id"),
        "semantic_exchange_valid": True,
        "destination_structural_validation": "PASS",
        "live_double_interlock_traversal_claimed": False,
        "sdk_admitted": False,
        "dashboard_live_published": False,
        "hugging_face_endorsement_claimed": False,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "heartbeat_effect": False,
        "authority_effect": "OBSERVATION_ONLY_NO_NEW_AUTHORITY",
    }
    target = bound_state / "receipts" / "latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = "receipts/latest.json"
    return receipt


def completed_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
        "transition_sequence": 2,
        "expected_next_transition": "SV_DN1_INTR_SDK_LIVE_ADMISSION",
        "evidence_refs": [
            str(receipt["source_capture_ref"]),
            str(receipt["semantic_exchange_ref"]),
            str(receipt["local_receipt_ref"]),
        ],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def source_wait_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": "SV_DN1_LOCAL_SOURCE_MATERIALIZATION_PENDING",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
        "error": str(exc),
        "evidence_refs": ["StegVerse-org/stegverse-demo-suite:docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md"],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def public_source_wait_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": "SV_DN1_PUBLIC_SOURCE_TEMPORARILY_UNAVAILABLE",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
        "error": str(exc),
        "evidence_refs": [TARGET_URL],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "SV_DN1_RESIDENT_SOURCE_OBSERVATION_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
        "error": str(exc),
        "evidence_refs": [],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "trigger_type": "OBSERVATION_EXECUTION_DEFECT",
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": str(exc),
            "solution_required": True,
            "workaround_candidates": [
                "sandbox-test a bounded repair without widening public-host or credential scope",
                "revalidate canonical demo-suite observer and semantic-adapter contracts"
            ],
            "next_solution_action": "Submit a bounded sovereign-runtime sandbox resolution; do not substitute hosted GitHub execution.",
            "resolvable_by_current_worker": False,
            "escalation_target": "SOVEREIGN_RUNTIME_SANDBOX_RESOLUTION",
            "required_capabilities": ["repository_resolution", "sandbox_validation"],
            "completion_evidence": ["bounded repair tests PASS", "resident observer adapter contract PASS"],
            "same_level_retry_authorized": False,
        },
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
    except SourceUnavailable as exc:
        print(json.dumps(source_wait_response(exc), sort_keys=True))
        return 0
    except PublicSourceUnavailable as exc:
        print(json.dumps(public_source_wait_response(exc), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
