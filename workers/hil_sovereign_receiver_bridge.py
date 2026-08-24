#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

CREDENTIAL_AUTHORITY = "TV/TVC"
PRIMARY_SHA256 = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT_SHA256 = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
GITHUB_AUTH_ENV = {
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
}
PROHIBITED_HOST_ENV = {
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
}
REQUIRED_BACKEND_FILES = (
    Path("llm_adapter/combined_gateway.py"),
    Path("llm_adapter/hil_intake_v1_1_api.py"),
    Path("llm_adapter/hil_sovereign_receiver_profile.py"),
    Path("tasks/LLMA-HIL-SOVEREIGN-RECEIVER-021.json"),
    Path("tasks/LLMA-HIL-POST-SUBMIT-RECONSTRUCTION-029.json"),
    Path("tasks/LLMA-HIL-SITE-RECEIPT-COMPAT-030.json"),
    Path("docs/HIL_RUNTIME_MIRROR_HANDOFF.md"),
    Path("docs/HIL_SITE_RECEIPT_COMPAT_MIRROR_HANDOFF.md"),
)
REQUIRED_INTAKE_MARKERS = (
    '@router.get("/submissions/{submission_id}/status")',
    '@router.get("/submissions/{submission_id}/exact-bytes")',
    '"custody_state": "EXACT_BYTES_PERSISTED"',
    '"registry_state": "RECORDED"',
    'EXACT_BYTES_HASH_VERIFIED',
    'hil_submission_registry_hash_mismatch',
    'hil_submission_persistence_verification_failed',
)
REQUIRED_GATEWAY_MARKERS = (
    'hil_intake_status_endpoint_template',
    'hil_intake_exact_bytes_endpoint_template',
    'EXISTING_TV_TVC_REVIEW_AUTH_REQUIRED',
)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = dict(os.environ if env is None else env)
    return any(_truthy(values.get(name)) for name in PROHIBITED_HOST_ENV)


def local_llm_adapter_roots(root: Path, env: dict[str, str] | None = None) -> list[Path]:
    values = dict(os.environ if env is None else env)
    candidates: list[Path] = []
    override = values.get("STEGVERSE_LLM_ADAPTER_ROOT")
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.extend(
        [
            (root / "workloads" / "LLM-adapter").resolve(),
            (Path.home() / ".stegverse" / "workloads" / "LLM-adapter").resolve(),
            Path("/var/lib/stegverse/workloads/LLM-adapter"),
        ]
    )
    return candidates


def _backend_contract_current(candidate: Path) -> bool:
    if not all((candidate / relative).is_file() for relative in REQUIRED_BACKEND_FILES):
        return False
    try:
        intake = (candidate / "llm_adapter/hil_intake_v1_1_api.py").read_text(encoding="utf-8")
        gateway = (candidate / "llm_adapter/combined_gateway.py").read_text(encoding="utf-8")
        receipt_task = json.loads(
            (candidate / "tasks/LLMA-HIL-SITE-RECEIPT-COMPAT-030.json").read_text(encoding="utf-8")
        )
        reconstruction_task = json.loads(
            (candidate / "tasks/LLMA-HIL-POST-SUBMIT-RECONSTRUCTION-029.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    contract = receipt_task.get("required_receipt_contract") or {}
    return (
        all(marker in intake for marker in REQUIRED_INTAKE_MARKERS)
        and all(marker in gateway for marker in REQUIRED_GATEWAY_MARKERS)
        and receipt_task.get("state") == "COMPLETE_MERGED_VALIDATED_RELEASED"
        and contract.get("custody_state") == "EXACT_BYTES_PERSISTED"
        and contract.get("registry_state") == "RECORDED"
        and reconstruction_task.get("state") == "COMPLETE_MERGED_VALIDATED_RELEASED"
    )


def find_hil_receiver_root(root: Path, env: dict[str, str] | None = None) -> Path | None:
    for candidate in local_llm_adapter_roots(root, env):
        if _backend_contract_current(candidate):
            return candidate.resolve()
    return None


def credential_free_receiver_env(
    adapter_root: Path,
    state_root: Path,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    if hosted_environment(values):
        raise RuntimeError("third_party_host_is_not_hil_sovereign_receiver_surface")
    state_root = state_root.expanduser().resolve()
    if str(state_root) in {"/tmp", "/var/tmp"} or str(state_root).startswith("/tmp/") or str(state_root).startswith("/var/tmp/"):
        raise RuntimeError("hil_sovereign_state_root_must_not_be_temporary")
    child = {k: v for k, v in values.items() if k not in GITHUB_AUTH_ENV}
    for key in GITHUB_AUTH_ENV:
        child.pop(key, None)
    child["PYTHONPATH"] = str(adapter_root.resolve())
    child["STEGVERSE_RUNTIME_PROFILE"] = "sovereign-carrier"
    child["STEGVERSE_SOVEREIGN_STATE_DURABLE"] = "true"
    child["STEGVERSE_SOVEREIGN_STATE_DIR"] = str(state_root)
    child["STEGVERSE_ALLOWED_ORIGINS"] = "https://stegverse.org,https://www.stegverse.org"
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = CREDENTIAL_AUTHORITY
    return child


def receiver_command(port: int = 8765) -> list[str]:
    if not 1 <= int(port) <= 65535:
        raise ValueError("invalid_receiver_port")
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "llm_adapter.combined_gateway:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(int(port)),
    ]


def launch_receiver(
    adapter_root: Path,
    state_root: Path,
    *,
    port: int = 8765,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    child_env = credential_free_receiver_env(adapter_root, state_root, env)
    return subprocess.Popen(
        receiver_command(port),
        cwd=adapter_root,
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _get_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"hil_receiver_probe_failed:{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("hil_receiver_probe_invalid_shape")
    return payload


def verify_receiver(base_url: str) -> dict[str, Any]:
    base = base_url.rstrip("/")
    profile = _get_json(f"{base}/api/hil/sovereign-receiver-profile")
    readiness = _get_json(f"{base}/api/hil/readiness")
    profile_ok = (
        profile.get("state") == "ACTIVE_SOVEREIGN_RECEIVER"
        and profile.get("credential_authority") == CREDENTIAL_AUTHORITY
        and profile.get("participant_machine_required") is False
        and profile.get("developer_machine_required") is False
        and profile.get("github_hosted_runtime_required") is False
        and profile.get("third_party_runtime_required") is False
        and profile.get("authority_granted") is False
    )
    readiness_ok = (
        readiness.get("state") == "READY"
        and readiness.get("primary_sha256") == PRIMARY_SHA256
        and readiness.get("prompt_sha256") == PROMPT_SHA256
        and readiness.get("execution_authority") is False
        and readiness.get("publication_authority") is False
        and readiness.get("master_record_append_authority") is False
    )
    return {
        "schema": "stegverse.hil.sovereign-receiver-carrier-observation/v1",
        "state": "READY" if profile_ok and readiness_ok else "FAIL_CLOSED",
        "profile_verified": profile_ok,
        "readiness_verified": readiness_ok,
        "profile": profile,
        "readiness": readiness,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": "NONE",
        "participant_machine_required": False,
        "developer_machine_required": False,
        "third_party_runtime_required": False,
        "public_https_rendezvous_proven": False,
        "browser_submission_proven": False,
        "post_restart_exact_byte_proven": False,
        "tvc_lifecycle_handoff_proven": False,
        "authority_effect": "NONE",
    }


__all__ = [
    "CREDENTIAL_AUTHORITY",
    "PRIMARY_SHA256",
    "PROMPT_SHA256",
    "REQUIRED_BACKEND_FILES",
    "REQUIRED_GATEWAY_MARKERS",
    "REQUIRED_INTAKE_MARKERS",
    "credential_free_receiver_env",
    "find_hil_receiver_root",
    "hosted_environment",
    "launch_receiver",
    "local_llm_adapter_roots",
    "receiver_command",
    "verify_receiver",
]
