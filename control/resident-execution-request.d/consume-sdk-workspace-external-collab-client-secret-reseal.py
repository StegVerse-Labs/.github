#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("control/resident-execution-request.d/sdk-workspace-external-collab-client-secret-reseal-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/sdk-workspace-external-collab-client-secret-reseal.latest.json")
TASK_ID = "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003"
SELECTOR = "sdk_workspace_external_collab_client_secret_reseal"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
TVC_CANDIDATES = (
    Path.home() / ".stegverse" / "repos" / "StegVerse-Labs" / "TVC",
    Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
    Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
    Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
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
    raw = (json.dumps(dict(value), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    tmp.write_bytes(raw)
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
        "tvc_root_locator_required": True,
        "target_purpose": "google_drive.external_collaboration.client_secret",
        "personal_kv_source_purpose": "google_drive.personal_kv.client_secret",
        "target_existing_policy": "VALIDATE_PRESENCE_DO_NOT_OVERWRITE",
        "execution_requires_root": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise RuntimeError(f"resident reseal request {key} mismatch")
    for key in ("request_id", "tvc_reseal_script", "expected_tvc_reseal_script_git_blob", "source_custody_receipt", "target_custody_receipt", "resident_seal_activation_receipt", "resident_private_key"):
        if not isinstance(value.get(key), str) or not value[key]:
            raise RuntimeError(f"resident reseal request {key} missing")


def _clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = sorted(name for name in HOSTED if _truthy(values.get(name)))
    if hosted:
        raise RuntimeError("hosted environment may not consume resident client-secret reseal request: " + ",".join(hosted))
    allowed = ("PATH", "HOME", "LANG", "LC_ALL")
    env = {name: values[name] for name in allowed if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def _locate_tvc_root(request: Mapping[str, Any], environ: Mapping[str, str]) -> tuple[Path | None, str | None]:
    candidates: list[Path] = []
    explicit = str(environ.get("STEGVERSE_TVC_ROOT") or "").strip()
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(TVC_CANDIDATES)
    expected_blob = str(request["expected_tvc_reseal_script_git_blob"])
    rel = Path(str(request["tvc_reseal_script"]))
    observations: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        root = candidate.resolve()
        if str(root) in seen:
            continue
        seen.add(str(root))
        script = (root / rel).resolve()
        try:
            script.relative_to(root)
        except ValueError:
            observations.append(f"{root}:SCRIPT_ESCAPE")
            continue
        if not script.is_file():
            observations.append(f"{root}:SCRIPT_MISSING")
            continue
        completed = subprocess.run(["git", "-C", str(root), "hash-object", str(script)], capture_output=True, text=True, check=False, timeout=20, env=_clean_env(environ))
        blob = completed.stdout.strip()
        if completed.returncode != 0 or blob != expected_blob:
            observations.append(f"{root}:SCRIPT_BLOB={blob or 'UNRESOLVED'}")
            continue
        return root, f"{root}:SCRIPT_BLOB={blob}"
    return None, ";".join(observations) if observations else None


def consume(runtime_root: Path, *, environ: Mapping[str, str] | None = None, runner=subprocess.run) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request = _load(runtime / REQUEST_REL)
    _validate_request(request)
    request_hash = _stable_hash(request)
    previous_path = runtime / CONSUMPTION_REL
    if previous_path.is_file():
        previous = _load(previous_path)
        if previous.get("request_sha256") == request_hash and previous.get("state") in {"COMPLETED", "TARGET_ALREADY_PRESENT"}:
            return previous

    values = dict(os.environ if environ is None else environ)
    safe_env = _clean_env(values)
    tvc_root, tvc_observation = _locate_tvc_root(request, values)
    source = Path(str(request["source_custody_receipt"]))
    target = Path(str(request["target_custody_receipt"]))
    activation = Path(str(request["resident_seal_activation_receipt"]))
    private_key = Path(str(request["resident_private_key"]))
    base = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "request_id": request["request_id"], "request_sha256": request_hash,
        "task_id": TASK_ID, "selector": SELECTOR, "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE", "heartbeat_grants_execution_authority": False,
        "credential_material_present": False, "second_machine_required": False,
        "provider_contact_performed": False, "authority_effect": "NONE_RESIDENT_RESEAL_EXECUTION_ONLY",
        "tvc_root_observation": tvc_observation,
        "source_custody_receipt_present": source.is_file(), "target_custody_receipt_present_before": target.is_file(),
        "resident_seal_activation_receipt_present": activation.is_file(), "resident_private_key_present": private_key.is_file(),
    }
    if tvc_root is None:
        receipt = {**base, "state": "BLOCKED", "reason": "CANONICAL_TVC_RESEAL_SOURCE_NOT_MATERIALIZED"}
        _atomic_json(previous_path, receipt); return receipt
    if target.is_file():
        receipt = {**base, "state": "TARGET_ALREADY_PRESENT", "reason": "VALIDATE_EXISTING_TARGET_DO_NOT_OVERWRITE", "target_custody_receipt_present_after": True}
        _atomic_json(previous_path, receipt); return receipt
    missing = [label for label, path in (("SOURCE_CUSTODY", source), ("RESIDENT_SEAL_ACTIVATION", activation), ("RESIDENT_PRIVATE_KEY", private_key)) if not path.is_file()]
    if missing:
        receipt = {**base, "state": "BLOCKED", "reason": "REQUIRED_RESIDENT_CUSTODY_MATERIAL_ABSENT:" + ",".join(missing)}
        _atomic_json(previous_path, receipt); return receipt
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        receipt = {**base, "state": "BLOCKED", "reason": "TVC_ROOT_EXECUTION_REQUIRED"}
        _atomic_json(previous_path, receipt); return receipt

    command = [sys.executable, str((tvc_root / str(request["tvc_reseal_script"])).resolve())]
    completed = runner(command, cwd=tvc_root, env=safe_env, capture_output=True, text=True, check=False, timeout=120)
    result = None
    for line in reversed([line.strip() for line in completed.stdout.splitlines() if line.strip()]):
        try: parsed = json.loads(line)
        except Exception: continue
        if isinstance(parsed, dict): result = parsed; break
    ok = (
        completed.returncode == 0 and isinstance(result, dict)
        and result.get("state") == "PURPOSE_SPECIFIC_CIPHERTEXT_CUSTODY_MATERIALIZED"
        and result.get("target_purpose") == request["target_purpose"]
        and result.get("credential_authority") == "TV/TVC"
        and result.get("plaintext_returned") is False and result.get("plaintext_persisted") is False
        and result.get("plaintext_logged") is False and result.get("plaintext_hashed") is False
        and result.get("provider_operation_authority") is False and target.is_file()
    )
    receipt = {
        **base, "state": "COMPLETED" if ok else "FAILED",
        "reason": "PURPOSE_SPECIFIC_CIPHERTEXT_CUSTODY_MATERIALIZED" if ok else "RESEAL_EXECUTION_DID_NOT_PROVE_TARGET_CUSTODY",
        "returncode": completed.returncode, "secret_free_reseal_result": result if ok else None,
        "target_custody_receipt_present_after": target.is_file(),
        "stdout_secret_material_retained": False, "stderr_secret_material_retained": False,
    }
    _atomic_json(previous_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = consume(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"COMPLETED", "TARGET_ALREADY_PRESENT", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
