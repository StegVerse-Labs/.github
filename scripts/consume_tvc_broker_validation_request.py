#!/usr/bin/env python3
"""Consume the bounded resident request for TVC broker governed validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/tvc-repository-broker-validation-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/tvc-broker-validation-request-consumption.latest.json")
VALIDATION_RECEIPT_REL = Path("receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json")
HANDOFF_REL = Path("handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json")
REGISTRY_REL = Path("control/worker-registry.json")
TARGET_TASK = "SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
MIN_FENCE = 22
_HANDOFF_EXECUTION = json.loads((ROOT / HANDOFF_REL).read_text(encoding="utf-8"))["execution"]
EXPECTED_HEAD = _HANDOFF_EXECUTION["expected_tvc_head"]
EXPECTED_BUNDLE_SHA256 = _HANDOFF_EXECUTION["expected_source_bundle_sha256"]

HOSTED = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","OAUTH_TOKEN",
)
NONSECRET = (
    "PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME",
    "STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_TVC_ROOT","STEGVERSE_TVC_CONTROL_ROOT",
)
PRIVATE_SOURCE_CANDIDATE = Path("/var/lib/stegverse/private-source-read/materialized/tvc-pr92-broker-validation-b5288f99")
TVC_PRIVATE_SOURCE_BOOTSTRAP = Path("scripts/bootstrap_tvc_pr92_validation_source.py")
TVC_ADMISSION_MODULE = "scripts.evaluate_github_repository_operation_broker_admission"
TVC_ADMISSION_SCRIPT = Path("scripts/evaluate_github_repository_operation_broker_admission.py")
TVC_REPOSITORY_AUTHORITY_REQUEST_REL = Path("tvc-handoff/sv-dn1-repository-authority-request.json")
TVC_REPOSITORY_AUTHORITY_REQUEST_SCHEMA = "stegverse.tvc.sv-dn1-repository-authority-request/v1"
TVC_REPOSITORY_AUTHORITY_TARGET_TASK = "tvc.sv_dn1.repository_authority.continue"


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema":"stegverse.resident-execution-request/v1",
        "state":"REQUESTED",
        "task_id":TARGET_TASK,
        "mode":TARGET_MODE,
        "entrypoint":TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive":MIN_FENCE,
        "credential_authority":"TV/TVC",
        "github_token_required":False,
        "github_token_runtime_authority":"NONE",
        "heartbeat_grants_execution_authority":False,
        "second_machine_required":False,
        "network_source_fetch_allowed":False,
        "request_granted_authority":False,
        "tvc_root_locator_required":True,
        "credential_material_allowed":False,
        "authority_effect":"NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"TVC broker validation resident request {key} mismatch")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume TVC broker validation request: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def exact_local_tvc_root(values: Mapping[str, str]) -> tuple[Path | None, str | None]:
    candidates: list[Path] = []
    raw = str(values.get("STEGVERSE_TVC_ROOT") or "").strip()
    if raw:
        candidates.append(Path(raw).expanduser())
    candidates.append(PRIVATE_SOURCE_CANDIDATE)
    observed: list[str] = []
    for candidate in candidates:
        root = candidate.resolve()
        if not (root / ".git").is_dir():
            observed.append(f"{root}:MISSING")
            continue
        completed = subprocess.run(
            ["git","-C",str(root),"rev-parse","HEAD"],
            check=False,capture_output=True,text=True,timeout=20,
            env={k:v for k,v in values.items() if k in {"PATH","HOME","LANG","LC_ALL"}},
        )
        head = completed.stdout.strip()
        if completed.returncode != 0 or head != EXPECTED_HEAD:
            observed.append(f"{root}:{head or 'UNRESOLVED'}")
            continue
        dirty = subprocess.run(
            ["git","-C",str(root),"status","--porcelain"],
            check=False,capture_output=True,text=True,timeout=20,
            env={k:v for k,v in values.items() if k in {"PATH","HOME","LANG","LC_ALL"}},
        )
        if dirty.returncode != 0 or dirty.stdout.strip():
            observed.append(f"{root}:{head}:DIRTY")
            continue
        return root, f"{root}:{head}"
    return None, ";".join(observed) if observed else None


def local_tvc_control_root(values: Mapping[str, str]) -> tuple[Path | None, str | None]:
    candidates: list[Path] = []
    for name in ("STEGVERSE_TVC_CONTROL_ROOT", "STEGVERSE_TVC_ROOT"):
        raw = str(values.get(name) or "").strip()
        if raw:
            candidates.append(Path(raw).expanduser())
    candidates.extend([
        Path.home() / ".stegverse" / "repos" / "StegVerse-Labs" / "TVC",
        Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
        Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
        Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
    ])
    seen: set[str] = set()
    observed: list[str] = []
    for candidate in candidates:
        root = candidate.resolve()
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        if not (root / TVC_PROGRESSION_SCRIPT).is_file():
            observed.append(f"{root}:PROGRESSION_NOT_PRESENT")
            continue
        if not (root / "tools" / "task_dispatcher.py").is_file():
            observed.append(f"{root}:DISPATCHER_NOT_PRESENT")
            continue
        return root, f"{root}:PROGRESSION_READY"
    return None, ";".join(observed) if observed else None


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def run_tvc_private_source_progression(
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str],
) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    helper = runtime / TVC_PRIVATE_SOURCE_BOOTSTRAP
    if not helper.is_file():
        return {
            "command": None,
            "returncode": None,
            "result": None,
            "result_observed": False,
            "request_staged_or_owned": False,
            "reason": "PRIVATE_SOURCE_BOOTSTRAP_HELPER_NOT_MATERIALIZED",
            "credential_value_exposed": False,
            "consumer_credential_used": False,
            "consumer_network_source_fetch_performed": False,
            "systemd_service_start_requested_by_consumer": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }
    command = [
        sys.executable,
        str(helper),
        "--runtime-root",
        str(runtime),
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=dict(env),
        timeout=60,
    )
    result = parse_last_json(completed.stdout)
    staged = bool(
        isinstance(result, dict)
        and result.get("state") in {"READY", "HANDOFF_READY"}
        and result.get("systemd_service_start_requested") is False
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "result": result,
        "result_observed": isinstance(result, dict),
        "request_staged_or_owned": staged,
        "credential_value_exposed": False,
        "consumer_credential_used": False,
        "consumer_network_source_fetch_performed": False,
        "tvc_private_source_service_may_perform_provider_read": True,
        "systemd_service_start_requested_by_consumer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def run_tvc_admission_compatibility(
    control_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str],
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        TVC_ADMISSION_MODULE,
        "--control-root",
        str(control_root),
    ]
    completed = runner(
        command,
        cwd=control_root,
        capture_output=True,
        text=True,
        check=False,
        env=dict(env),
        timeout=900,
    )
    result = parse_last_json(completed.stdout)
    eligible = bool(
        completed.returncode == 0
        and isinstance(result, dict)
        and result.get("state") == "TVC_PR92_BROKER_ADMISSION_ELIGIBLE"
        and result.get("validated_exact_sha") == EXPECTED_HEAD
        and result.get("source_bundle_file_count") == 16
        and result.get("source_bundle_sha256") == EXPECTED_BUNDLE_SHA256
        and result.get("credential_used") is False
        and result.get("network_access_performed") is False
        and result.get("repository_writeback_performed") is False
        and result.get("merge_performed") is False
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "result": result,
        "result_observed": isinstance(result, dict),
        "admission_eligible": eligible,
        "consumer_credential_used": False,
        "consumer_network_access_performed": False,
        "repository_writeback_performed": False,
        "merge_performed": False,
        "authority_effect": "EXISTING_TVC_ADMISSION_COMPATIBILITY_AUTHORITY_ONLY",
    }



def run_tvc_repository_authority_handoff(
    runtime_root: Path,
    *,
    request_id: str,
) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    downstream_request_id = f"{request_id}-repository-authority"
    request_path = runtime / TVC_REPOSITORY_AUTHORITY_REQUEST_REL
    request = {
        "schema": TVC_REPOSITORY_AUTHORITY_REQUEST_SCHEMA,
        "request_id": downstream_request_id,
        "state": "REQUESTED",
        "task": TVC_REPOSITORY_AUTHORITY_TARGET_TASK,
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "request_grants_authority": False,
        "heartbeat_grants_authority": False,
        "repository_write_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    if request_path.is_file():
        existing = load_json(request_path)
        if existing != request:
            raise RuntimeError("TVC repository-authority runtime request conflicts with existing staged request")
    else:
        atomic_json(request_path, request)
    return {
        "command": None,
        "returncode": 0,
        "result": {
            "state": "REQUEST_STAGED_FOR_TVC_SYSTEMD_PATH",
            "request_id": downstream_request_id,
            "request_path": str(request_path),
            "request_sha256": stable_hash(request),
            "credential_value_exposed": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        },
        "result_observed": True,
        "request_staged_or_owned": True,
        "downstream_request_id": downstream_request_id,
        "request_path": str(request_path),
        "request_sha256": stable_hash(request),
        "credential_value_exposed": False,
        "consumer_credential_used": False,
        "repository_write_authority": False,
        "github_token_runtime_authority": "NONE",
        "systemd_service_start_requested_by_consumer": False,
        "systemd_path_activation_expected": True,
        "authority_effect": "NONE_HANDOFF_ONLY",
    }

def terminal_validation(runtime: Path) -> bool:
    receipt_path = runtime / VALIDATION_RECEIPT_REL
    if not receipt_path.is_file():
        return False
    try:
        receipt = load_json(receipt_path)
    except Exception:
        return False
    result = receipt.get("result") or {}
    return (
        receipt.get("state") == "COMPLETED"
        and result.get("reason") == "TVC_BROKER_VALIDATION_PASS"
        and result.get("expected_tvc_head") == EXPECTED_HEAD
        and result.get("source_head") == EXPECTED_HEAD
        and result.get("source_bundle_file_count") == 16
        and result.get("source_bundle_sha256") == EXPECTED_BUNDLE_SHA256
        and receipt.get("credential_authority") == "TV/TVC"
        and receipt.get("authority_effect") == "NONE_VALIDATION_ONLY"
    )


def previously_consumed(runtime: Path, request: Mapping[str, Any], request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    compatibility_required = request.get("admission_compatibility_requested") is True
    compatibility_satisfied = (
        not compatibility_required
        or receipt.get("admission_compatibility_observed") is True
    )
    repository_authority_required = request.get("repository_authority_continuation_requested") is True
    repository_authority_satisfied = (
        not repository_authority_required
        or receipt.get("repository_authority_handoff_observed") is True
    )
    return (
        receipt.get("request_id") == request.get("request_id")
        and receipt.get("request_sha256") == request_hash
        and receipt.get("terminal_validation_observed") is True
        and compatibility_satisfied
        and repository_authority_satisfied
        and terminal_validation(runtime)
    )


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.tvc-broker-validation-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if previously_consumed(runtime, request, request_hash):
        return {
            "schema":"stegverse.tvc-broker-validation-request-consumption/v1",
            "state":"ALREADY_CONSUMED",
            "request_id":request["request_id"],
            "request_sha256":request_hash,
            "runtime_execution_attempted":False,
            "terminal_validation_observed":True,
            "authority_effect":"NONE",
        }

    values = dict(os.environ if env is None else env)
    cleaned = clean_env(values)
    tvc_root, observed = exact_local_tvc_root(cleaned)
    progression: dict[str, Any] | None = None
    admission: dict[str, Any] | None = None
    repository_authority_handoff: dict[str, Any] | None = None
    control_root: Path | None = None
    control_observed: str | None = None
    if tvc_root is None:
        progression = run_tvc_private_source_progression(
            runtime,
            runner=runner,
            env=cleaned,
        )
        tvc_root, observed = exact_local_tvc_root(cleaned)
        control_root, control_observed = local_tvc_control_root(cleaned)

    if tvc_root is None:
        progression_result = progression.get("result") if isinstance(progression, dict) else None
        progression_state = progression_result.get("state") if isinstance(progression_result, dict) else None
        hard_failure = bool(
            isinstance(progression, dict)
            and progression.get("returncode") not in {0, 2, None}
            and progression_state not in {"READY", "HANDOFF_READY"}
        )
        receipt = {
            "schema":"stegverse.tvc-broker-validation-request-consumption/v1",
            "state":"BLOCKED" if hard_failure else "HANDOFF_READY",
            "request_id":request["request_id"],
            "request_sha256":request_hash,
            "runtime_execution_attempted":False,
            "private_source_progression_attempted":progression is not None,
            "private_source_progression":progression,
            "terminal_validation_observed":False,
            "expected_tvc_head":EXPECTED_HEAD,
            "observed_tvc_root":observed,
            "observed_tvc_control_root":control_observed,
            "machine_observable_release_condition":"The non-secret runtime private-source request is consumed by the installed TVC systemd path/timer, producing the exact clean PR #92 checkout and authentic execution receipt; the next resident cycle then runs the existing validation worker",
            "credential_authority":"TV/TVC",
            "github_token_required":False,
            "second_machine_required":False,
            "network_source_fetch_performed_by_consumer":False,
            "request_granted_authority":False,
            "repository_writeback_authority":False,
            "merge_authority":False,
            "authority_effect":"NONE_REQUEST_ONLY",
        }
        atomic_json(runtime / CONSUMPTION_REL, receipt)
        return receipt

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"TVC broker validation resident entrypoint missing: {entrypoint}")
    command = [
        sys.executable,str(entrypoint),
        "--source-root",str(source),
        "--runtime-root",str(runtime),
        "--task-id",TARGET_TASK,
    ]
    completed = runner(
        command,cwd=runtime,capture_output=True,text=True,check=False,
        env=cleaned,timeout=600,
    )
    terminal = terminal_validation(runtime)
    compatibility_required = request.get("admission_compatibility_requested") is True
    compatibility_observed = False
    if terminal and compatibility_required:
        if control_root is None:
            control_root, control_observed = local_tvc_control_root(cleaned)
        if control_root is not None and (control_root / TVC_ADMISSION_SCRIPT).is_file():
            admission = run_tvc_admission_compatibility(
                control_root,
                runner=runner,
                env=cleaned,
            )
            compatibility_observed = admission.get("admission_eligible") is True
    repository_authority_required = request.get("repository_authority_continuation_requested") is True
    repository_authority_handoff_observed = False
    if terminal and compatibility_observed and repository_authority_required:
        repository_authority_handoff = run_tvc_repository_authority_handoff(
            runtime,
            request_id=str(request["request_id"]),
        )
        repository_authority_handoff_observed = repository_authority_handoff.get("request_staged_or_owned") is True
    validation_and_compatibility = terminal and (not compatibility_required or compatibility_observed)
    downstream_handoff_satisfied = (not repository_authority_required or repository_authority_handoff_observed)
    state = "COMPLETED" if validation_and_compatibility and downstream_handoff_satisfied else "HANDOFF_READY"
    receipt = {
        "schema":"stegverse.tvc-broker-validation-request-consumption/v1",
        "state":state,
        "request_id":request["request_id"],
        "request_sha256":request_hash,
        "task_id":TARGET_TASK,
        "command":command,
        "execution_returncode":completed.returncode,
        "runtime_execution_attempted":True,
        "private_source_progression_attempted":progression is not None,
        "private_source_progression":progression,
        "terminal_validation_observed":terminal,
        "admission_compatibility_requested":compatibility_required,
        "admission_compatibility_observed":compatibility_observed,
        "admission_compatibility":admission,
        "repository_authority_continuation_requested":repository_authority_required,
        "repository_authority_handoff_observed":repository_authority_handoff_observed,
        "repository_authority_handoff":repository_authority_handoff,
        "observed_tvc_control_root":control_observed,
        "expected_tvc_head":EXPECTED_HEAD,
        "observed_tvc_root":str(tvc_root),
        "credential_authority":"TV/TVC",
        "github_token_required":False,
        "github_token_runtime_authority":"NONE",
        "second_machine_required":False,
        "network_source_fetch_performed_by_consumer":False,
        "request_granted_authority":False,
        "repository_writeback_authority":False,
        "merge_authority":False,
        "authority_effect":"NONE_REQUEST_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-root",type=Path,default=ROOT)
    parser.add_argument("--runtime-root",type=Path,required=True)
    args=parser.parse_args()
    receipt=consume(args.source_root,args.runtime_root)
    print(json.dumps(receipt,sort_keys=True))
    return 0 if receipt["state"] in {"NO_REQUEST","ALREADY_CONSUMED","HANDOFF_READY","BLOCKED","COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
