#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

EXPECTED_HEAD = "b5288f9910ada26c6ab2e9bca3f7701afaae2cef"
MATERIALIZATION_ID = "tvc-pr92-broker-validation-b5288f99"
DEST = Path("/var/lib/stegverse/private-source-read/materialized") / MATERIALIZATION_ID
EXECUTION_RECEIPT = Path("/var/lib/stegverse/private-source-read/latest-execution-receipt.json")
REQUEST_REL = Path("tvc-handoff/private-source-request.json")


def _git_head(root: Path) -> str | None:
    if not (root / ".git").is_dir():
        return None
    p = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "GIT_TERMINAL_PROMPT": "0"},
    )
    value = p.stdout.strip().lower()
    return value if p.returncode == 0 else None


def _stable_hash(value: Mapping[str, Any]) -> str:
    raw = json.dumps(dict(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _request() -> dict[str, Any]:
    return {
        "caller_repository": "StegVerse-Labs/.github",
        "source_repository": "StegVerse-Labs/TVC",
        "consumer_task": "SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001",
        "reference_mode": "IMMUTABLE_COMMIT",
        "exact_sha": EXPECTED_HEAD,
        "materialization_id": MATERIALIZATION_ID,
        "ttl_seconds": 600,
    }


def stage(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    request = _request()
    request_path.parent.mkdir(parents=True, exist_ok=True)

    if request_path.is_file():
        existing = _load(request_path)
        if existing != request:
            return {
                "schema": "stegverse.tvc-validation-source-bootstrap/v2",
                "state": "BLOCKED",
                "reason": "EXISTING_PRIVATE_SOURCE_REQUEST_CONFLICT",
                "request_path": str(request_path),
                "credential_material_observed": False,
                "systemd_service_start_requested": False,
                "authority_effect": "NONE_FAIL_CLOSED",
            }
    else:
        temp = request_path.with_name("." + request_path.name + ".tmp")
        temp.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(temp, 0o600)
        os.replace(temp, request_path)

    return {
        "schema": "stegverse.tvc-validation-source-bootstrap/v2",
        "state": "HANDOFF_READY",
        "reason": "PRIVATE_SOURCE_REQUEST_STAGED_FOR_TVC_SYSTEMD_PATH",
        "request_path": str(request_path),
        "request_sha256": _stable_hash(request),
        "expected_head": EXPECTED_HEAD,
        "source_root": None,
        "credential_authority": "TV/TVC",
        "credential_material_observed": False,
        "consumer_provider_read_performed": False,
        "systemd_service_start_requested": False,
        "systemd_path_activation_expected": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def bootstrap(runtime_root: Path | None = None) -> dict[str, Any]:
    existing = _git_head(DEST)
    if existing == EXPECTED_HEAD:
        receipt = _load(EXECUTION_RECEIPT)
        verified = bool(
            isinstance(receipt, dict)
            and receipt.get("state") == "COMPLETE"
            and receipt.get("credential_authority") == "TV/TVC"
            and receipt.get("authorized_exact_sha") == EXPECTED_HEAD
            and receipt.get("observed_exact_sha") == EXPECTED_HEAD
            and receipt.get("credential_value_exposed") is False
            and receipt.get("credential_persisted") is False
        )
        return {
            "schema": "stegverse.tvc-validation-source-bootstrap/v2",
            "state": "READY" if verified else "HANDOFF_READY",
            "reason": None if verified else "EXACT_SOURCE_PRESENT_EXECUTION_RECEIPT_NOT_VERIFIED",
            "source_root": str(DEST),
            "source_head": existing,
            "source_reused": True,
            "execution_receipt_observed": isinstance(receipt, dict),
            "credential_authority": "TV/TVC",
            "credential_material_observed": False,
            "systemd_service_start_requested": False,
            "authority_effect": "NONE_SOURCE_BOOTSTRAP_ONLY",
        }
    if existing:
        return {
            "schema": "stegverse.tvc-validation-source-bootstrap/v2",
            "state": "BLOCKED",
            "reason": "EXISTING_MATERIALIZATION_IDENTITY_MISMATCH",
            "observed_head": existing,
            "expected_head": EXPECTED_HEAD,
            "credential_material_observed": False,
            "systemd_service_start_requested": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }

    if runtime_root is None:
        raw = str(os.environ.get("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
        if not raw:
            return {
                "schema": "stegverse.tvc-validation-source-bootstrap/v2",
                "state": "HANDOFF_READY",
                "reason": "SOVEREIGN_RUNTIME_ROOT_NOT_OBSERVED",
                "credential_material_observed": False,
                "systemd_service_start_requested": False,
                "authority_effect": "NONE",
            }
        runtime_root = Path(raw)
    return stage(runtime_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage the non-secret TVC PR #92 private-source request for the resident systemd path watcher.")
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    result = bootstrap(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"READY", "HANDOFF_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
