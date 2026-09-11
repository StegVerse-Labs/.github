#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("control/resident-execution-request.d/sdk-workspace-external-collab-consent-listener-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/sdk-workspace-external-collab-consent-listener.latest.json")
TASK_ID = "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003"
SELECTOR = "sdk_workspace_external_collab_consent_listener"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
TVC_CANDIDATES = (
    Path.home() / ".stegverse" / "repos" / "StegVerse-Labs" / "TVC",
    Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
    Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
    Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
)
NONSECRET_REQUIRED = (
    "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID",
    "STEGVERSE_OWNER_BINDING_DIGEST",
    "STEGVERSE_STEGFIN_SOURCE_ROOT",
)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("JSON object required")
    return value


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _validate_request(value: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "selector": SELECTOR,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "credential_material_allowed": False,
        "request_granted_authority": False,
        "execution_requires_root": True,
        "tvc_root_locator_required": True,
        "expected_client_secret_purpose": "google_drive.external_collaboration.client_secret",
        "public_https_binding_allowed": False,
        "google_owner_consent_allowed": False,
        "provider_contact_allowed": False,
        "gateway_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise RuntimeError(f"resident consent listener request {key} mismatch")
    if value.get("required_nonsecret_environment") != list(NONSECRET_REQUIRED):
        raise RuntimeError("required non-secret environment mismatch")
    for key in ("request_id", "tvc_installer", "expected_tvc_installer_git_blob", "loopback_health_url"):
        if not isinstance(value.get(key), str) or not value[key]:
            raise RuntimeError(f"resident consent listener request {key} missing")


def _clean_env(source: Mapping[str, str]) -> dict[str, str]:
    hosted = sorted(name for name in HOSTED if _truthy(source.get(name)))
    if hosted:
        raise RuntimeError("hosted environment may not consume resident consent-listener request: " + ",".join(hosted))
    keep = ("PATH", "HOME", "LANG", "LC_ALL") + NONSECRET_REQUIRED + ("STEGVERSE_TVC_ROOT",)
    env = {name: source[name] for name in keep if source.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def _locate_tvc_root(request: Mapping[str, Any], environ: Mapping[str, str]) -> tuple[Path | None, str | None]:
    candidates: list[Path] = []
    explicit = str(environ.get("STEGVERSE_TVC_ROOT") or "").strip()
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(TVC_CANDIDATES)
    expected_blob = str(request["expected_tvc_installer_git_blob"])
    rel = Path(str(request["tvc_installer"]))
    observations: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        root = candidate.resolve()
        if str(root) in seen:
            continue
        seen.add(str(root))
        installer = (root / rel).resolve()
        try:
            installer.relative_to(root)
        except ValueError:
            observations.append(f"{root}:INSTALLER_ESCAPE")
            continue
        if not installer.is_file():
            observations.append(f"{root}:INSTALLER_MISSING")
            continue
        completed = subprocess.run(["git", "-C", str(root), "hash-object", str(installer)], capture_output=True, text=True, check=False, timeout=20, env=_clean_env(environ))
        blob = completed.stdout.strip()
        if completed.returncode != 0 or blob != expected_blob:
            observations.append(f"{root}:INSTALLER_BLOB={blob or 'UNRESOLVED'}")
            continue
        return root, f"{root}:INSTALLER_BLOB={blob}"
    return None, ";".join(observations) if observations else None


def _health(url: str, *, opener=urllib.request.urlopen) -> dict[str, Any] | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "StegVerse-TVC-Resident-Consent-Health/1"})
        with opener(request, timeout=5) as response:
            if getattr(response, "status", 200) != 200:
                return None
            value = json.loads(response.read(65536).decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return value if isinstance(value, dict) else None


def _health_valid(value: Mapping[str, Any] | None, request: Mapping[str, Any]) -> bool:
    return bool(
        value
        and value.get("state") == "HEALTHY"
        and value.get("client_secret_purpose") == request["expected_client_secret_purpose"]
        and value.get("credential_material_present") is False
        and value.get("provider_contact_performed") is False
        and value.get("runtime_activation_claimed") is False
    )


def consume(runtime_root: Path, *, environ: Mapping[str, str] | None = None, runner=subprocess.run, opener=urllib.request.urlopen) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request = _load(runtime / REQUEST_REL)
    _validate_request(request)
    request_hash = _stable_hash(request)
    previous_path = runtime / CONSUMPTION_REL
    if previous_path.is_file():
        previous = _load(previous_path)
        if previous.get("request_sha256") == request_hash and previous.get("state") in {"COMPLETED", "SERVICE_ALREADY_HEALTHY"}:
            return previous

    values = dict(os.environ if environ is None else environ)
    safe_env = _clean_env(values)
    health_url = str(request["loopback_health_url"])
    before = _health(health_url, opener=opener)
    base = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "selector": SELECTOR,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "credential_material_present": False,
        "second_machine_required": False,
        "provider_contact_performed": False,
        "public_https_binding_performed": False,
        "google_owner_consent_performed": False,
        "gateway_authority": False,
        "listener_bind": "127.0.0.1:8786",
        "client_secret_purpose": request["expected_client_secret_purpose"],
        "authority_effect": "NONE_RESIDENT_LISTENER_INSTALL_ONLY",
    }
    if _health_valid(before, request):
        receipt = {**base, "state": "SERVICE_ALREADY_HEALTHY", "loopback_health_verified": True, "installer_invoked": False}
        _atomic_json(previous_path, receipt)
        return receipt

    missing = [name for name in NONSECRET_REQUIRED if not str(values.get(name) or "").strip()]
    if missing:
        receipt = {**base, "state": "BLOCKED", "reason": "REQUIRED_NONSECRET_CONFIGURATION_ABSENT:" + ",".join(missing), "loopback_health_verified": False, "installer_invoked": False}
        _atomic_json(previous_path, receipt)
        return receipt
    owner = str(values["STEGVERSE_OWNER_BINDING_DIGEST"]).strip()
    if not owner.startswith("sha256:") or len(owner) != 71:
        receipt = {**base, "state": "BLOCKED", "reason": "OWNER_BINDING_DIGEST_INVALID", "loopback_health_verified": False, "installer_invoked": False}
        _atomic_json(previous_path, receipt)
        return receipt
    stegfin = Path(str(values["STEGVERSE_STEGFIN_SOURCE_ROOT"])).expanduser().resolve()
    if not stegfin.is_dir():
        receipt = {**base, "state": "BLOCKED", "reason": "STEGFIN_SOURCE_ROOT_UNAVAILABLE", "loopback_health_verified": False, "installer_invoked": False}
        _atomic_json(previous_path, receipt)
        return receipt
    tvc_root, observation = _locate_tvc_root(request, values)
    if tvc_root is None:
        receipt = {**base, "state": "BLOCKED", "reason": "CANONICAL_TVC_CONSENT_INSTALLER_NOT_MATERIALIZED", "tvc_root_observation": observation, "loopback_health_verified": False, "installer_invoked": False}
        _atomic_json(previous_path, receipt)
        return receipt
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        receipt = {**base, "state": "BLOCKED", "reason": "TVC_ROOT_EXECUTION_REQUIRED", "tvc_root_observation": observation, "loopback_health_verified": False, "installer_invoked": False}
        _atomic_json(previous_path, receipt)
        return receipt

    command = [
        sys.executable,
        str((tvc_root / str(request["tvc_installer"])).resolve()),
        "--repo-root", str(tvc_root),
        "--stegfin-source-root", str(stegfin),
        "--google-client-id", str(values["STEGVERSE_GOOGLE_DRIVE_CLIENT_ID"]).strip(),
        "--owner-binding-digest", owner,
    ]
    completed = runner(command, cwd=tvc_root, env=safe_env, capture_output=True, text=True, check=False, timeout=120)
    after = _health(health_url, opener=opener)
    ok = completed.returncode == 0 and _health_valid(after, request)
    receipt = {
        **base,
        "state": "COMPLETED" if ok else "BLOCKED",
        "reason": None if ok else "INSTALL_OR_LOOPBACK_HEALTH_VALIDATION_FAILED",
        "tvc_root_observation": observation,
        "installer_invoked": True,
        "installer_returncode": completed.returncode,
        "loopback_health_verified": bool(_health_valid(after, request)),
        "credential_material_logged": False,
        "runtime_activation_claimed": False,
    }
    _atomic_json(previous_path, receipt)
    return receipt


def main() -> int:
    result = consume(ROOT)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"COMPLETED", "SERVICE_ALREADY_HEALTHY", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
