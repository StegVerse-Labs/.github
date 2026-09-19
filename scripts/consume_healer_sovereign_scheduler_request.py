#!/usr/bin/env python3
"""Consume the standing Healer sovereign scheduler resident request."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/healer-sovereign-scheduler-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json")
CHECKPOINT_REL = Path("receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json")
ROOT_OBSERVATION_REL = Path("receipts/sovereign-host/stegbrowser-resident-custody-root-observation.latest.json")
RETENTION_POINTER_FIELDS = ("packet_ref", "packet_relative_path", "packet_sha256", "retained_under_root", "retained_under_root_source", "packet_state")
TARGET_TASK = "SHWP-HEALER-SOVEREIGN-SCHEDULER-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
REUSABLE_REFRESH_ENTRYPOINT = Path("scripts/refresh_sovereign_worker_runtime_source_reusable.py")
NEUTRAL_SCHEDULER_REQUIRED = (
    Path("scripts/run_reusable_task_scheduler.py"),
    Path("data/reusable-task-scheduler-contract.json"),
)
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_HEALER_ROOT", "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_TVC_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_env(source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {key: values[key] for key in NONSECRET_ENV if values.get(key)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        "standing_request": True,
        "recurrence": "EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise RuntimeError(f"Healer resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        raise RuntimeError("request_id missing")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def resolve_source_root(source_root: Path, runtime_root: Path, values: dict[str, str]) -> tuple[Path | None, str]:
    """Keep canonical source distinct from mutable resident runtime.

    Prefer an explicit dispatcher source, then the installed worker's canonical
    source binding, then the already-standard local repository-root map. The map
    is discovery metadata only; it grants no execution or transition authority.
    """
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if source != runtime:
        return (source, "DISPATCHER_DISTINCT_SOURCE") if source.is_dir() else (None, "DISPATCHER_SOURCE_MISSING")

    raw = str(values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    if raw:
        candidate = Path(raw).expanduser().resolve()
        if candidate == runtime:
            return None, "SOURCE_ROOT_EQUALS_RUNTIME"
        if not candidate.is_dir():
            return None, "SOURCE_ROOT_NOT_MATERIALIZED"
        required = candidate / TARGET_ENTRYPOINT
        if not required.is_file():
            return None, "SOURCE_ROOT_INCOMPLETE"
        return candidate, "STEGVERSE_HEARTBEAT_SOURCE_ROOT"

    roots_raw = str(values.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if roots_raw:
        try:
            roots = json.loads(roots_raw)
        except Exception:
            return None, "REPO_ROOTS_JSON_INVALID"
        if not isinstance(roots, dict):
            return None, "REPO_ROOTS_JSON_INVALID"
        mapped = roots.get("StegVerse-Labs/.github")
        if isinstance(mapped, str) and mapped.strip():
            candidate = Path(mapped).expanduser().resolve()
            if candidate == runtime:
                return None, "REPO_ROOT_EQUALS_RUNTIME"
            if not candidate.is_dir():
                return None, "REPO_ROOT_NOT_MATERIALIZED"
            required = candidate / TARGET_ENTRYPOINT
            if not required.is_file():
                return None, "REPO_ROOT_INCOMPLETE"
            return candidate, "STEGVERSE_REPO_ROOTS_JSON"

    return None, "DISTINCT_SOURCE_ROOT_NOT_PROVIDED"


def synchronize_standing_request(source: Path, runtime: Path) -> dict[str, Any]:
    """Exact-sync the non-authorizing standing request from already-local source.

    This is source transport only. The request cannot mint a claim, fence, credential,
    transition, publication state, or user-verification authority.
    """
    canonical = source / REQUEST_REL
    if not canonical.is_file():
        raise RuntimeError(f"canonical Healer standing request missing: {canonical}")
    canonical_doc = load_json(canonical)
    validate_request(canonical_doc)
    canonical_bytes = canonical.read_bytes()
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

    resident = runtime / REQUEST_REL
    previous_hash = file_sha256(resident) if resident.is_file() else None
    copied = previous_hash != canonical_hash
    if copied:
        resident.parent.mkdir(parents=True, exist_ok=True)
        tmp = resident.with_name("." + resident.name + ".tmp")
        tmp.write_bytes(canonical_bytes)
        os.replace(tmp, resident)
    if not resident.is_file() or resident.read_bytes() != canonical_bytes:
        raise RuntimeError("Healer standing request exact-byte materialization failed")
    validate_request(load_json(resident))
    return {
        "state": "EXACT_CANONICAL_REQUEST_MATERIALIZED" if copied else "EXACT_CANONICAL_REQUEST_ALREADY_PRESENT",
        "request_ref": REQUEST_REL.as_posix(),
        "sha256": canonical_hash,
        "copied": copied,
        "request_granted_authority": False,
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
    }


def ensure_neutral_scheduler_materialized(
    source: Path,
    runtime: Path,
    *,
    runner=subprocess.run,
    values: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Break the stale-runtime bootstrap loop before Healer delegates scheduling.

    The canonical resident worker refreshes this consumer before dispatch. If the
    resident runtime does not yet contain the neutral scheduler artifacts, invoke
    the already-registered reusable source-refresh adapter directly from the
    already-local canonical source. This grants no execution or transition authority.
    """
    missing_before = [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED if not (runtime / rel).is_file()]
    if not missing_before:
        return {
            "state": "NEUTRAL_SCHEDULER_ALREADY_MATERIALIZED",
            "attempted": False,
            "required_paths": [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED],
            "missing_before": [],
            "network_source_fetch_performed": False,
            "credential_read_or_acquired": False,
            "authority_effect": "NONE_SOURCE_MATERIALIZATION_ONLY",
        }

    adapter = source / REUSABLE_REFRESH_ENTRYPOINT
    if not adapter.is_file():
        raise RuntimeError(f"canonical reusable source-refresh adapter missing: {adapter}")
    env = clean_env(values)
    env["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = json.dumps(
        {"source_root": str(source), "runtime_root": str(runtime)},
        sort_keys=True,
        separators=(",", ":"),
    )
    completed = runner(
        [sys.executable, str(adapter)],
        cwd=source,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=300,
    )
    refresh_receipt = parse_last_json(completed.stdout)
    missing_after = [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED if not (runtime / rel).is_file()]
    if completed.returncode != 0 or missing_after:
        raise RuntimeError("neutral reusable scheduler bootstrap materialization failed")
    if not isinstance(refresh_receipt, dict) or refresh_receipt.get("schema") != "stegverse.sovereign-worker-runtime-source-refresh/v1":
        raise RuntimeError("neutral scheduler bootstrap did not emit canonical source-refresh receipt")
    if refresh_receipt.get("network_fetch_performed") is not False or refresh_receipt.get("credential_read_or_acquired") is not False:
        raise RuntimeError("neutral scheduler bootstrap violated local-only source-refresh boundary")
    return {
        "state": "NEUTRAL_SCHEDULER_MATERIALIZED_FROM_LOCAL_CANONICAL_SOURCE",
        "attempted": True,
        "adapter_ref": REUSABLE_REFRESH_ENTRYPOINT.as_posix(),
        "required_paths": [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED],
        "missing_before": missing_before,
        "missing_after": missing_after,
        "returncode": completed.returncode,
        "refresh_receipt": refresh_receipt,
        "network_source_fetch_performed": False,
        "credential_read_or_acquired": False,
        "authority_effect": "NONE_SOURCE_MATERIALIZATION_ONLY",
    }



def bind_projected_retention_pointer(runtime: Path) -> dict[str, Any]:
    """Read and verify the already-projected Healer checkpoint retention pointer."""
    checkpoint_path = runtime / CHECKPOINT_REL
    if not checkpoint_path.is_file():
        return {"state":"CHECKPOINT_NOT_PRESENT","pointer":None,"checkpoint_ref":CHECKPOINT_REL.as_posix(),"authority_effect":"NONE_EVIDENCE_CARRIAGE_ONLY"}
    checkpoint = load_json(checkpoint_path)
    child = checkpoint.get("child_receipt")
    if not isinstance(child, dict):
        raise RuntimeError("projected Healer checkpoint child_receipt missing")
    raw = child.get("resident_custody_root_observation_retention")
    if not isinstance(raw, dict):
        raise RuntimeError("projected Healer checkpoint retention pointer missing")
    pointer = {field: raw.get(field) for field in RETENTION_POINTER_FIELDS}
    missing = [field for field, value in pointer.items() if value in (None, "")]
    if missing:
        raise RuntimeError("projected Healer checkpoint retention pointer incomplete:" + ",".join(missing))
    if pointer["packet_relative_path"] != ROOT_OBSERVATION_REL.as_posix():
        raise RuntimeError("projected Healer checkpoint retained packet path mismatch")
    packet_path = runtime / ROOT_OBSERVATION_REL
    if not packet_path.is_file():
        raise RuntimeError("projected Healer checkpoint retained packet missing")
    packet_sha256 = file_sha256(packet_path)
    if pointer["packet_sha256"] != packet_sha256:
        raise RuntimeError("projected Healer checkpoint retained packet sha256 mismatch")
    packet = load_json(packet_path)
    if packet.get("state") != pointer["packet_state"]:
        raise RuntimeError("projected Healer checkpoint retained packet state mismatch")
    if Path(str(pointer["retained_under_root"])).expanduser().resolve() != runtime:
        raise RuntimeError("projected Healer checkpoint retained root mismatch")
    return {"state":"VALIDATED_PROJECTED_RETENTION_POINTER_BOUND","pointer":pointer,"checkpoint_ref":CHECKPOINT_REL.as_posix(),"checkpoint_sha256":file_sha256(checkpoint_path),"packet_sha256":packet_sha256,"authority_effect":"NONE_EVIDENCE_CARRIAGE_ONLY"}



def completed_healer_cycle_observed(result: dict[str, Any] | None) -> bool:
    """Recognize the real WorkerCoordinator cycle-envelope completion shape."""
    if not isinstance(result, dict):
        return False
    cycle = result.get("execution_result")
    if isinstance(cycle, dict):
        if cycle.get("transition_id") == "HEALER_SOVEREIGN_SCHEDULER_COMPLETED":
            return True
        events = cycle.get("events")
        if isinstance(events, list):
            matches = [
                event for event in events
                if isinstance(event, dict)
                and event.get("event_type") == "worker_response"
                and event.get("task_id") == TARGET_TASK
                and event.get("transition_id") == "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"
                and event.get("response_state") == "HANDOFF_READY"
            ]
            if len(matches) > 1:
                raise RuntimeError("multiple Healer completion events observed in one targeted cycle")
            if len(matches) == 1:
                return True
    return result.get("transition_id") == "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: dict[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    runtime = runtime_root.expanduser().resolve()
    source, source_resolution = resolve_source_root(source_root, runtime_root, values)

    if source is None:
        request_path = runtime / REQUEST_REL
        if not request_path.is_file():
            return {
                "schema": "stegverse.healer-resident-request-consumption/v1",
                "state": "NO_REQUEST",
                "runtime_execution_attempted": False,
                "standing_request": True,
                "source_resolution": source_resolution,
                "retry_allowed": True,
                "authority_effect": "NONE",
            }
        request = load_json(request_path)
        validate_request(request)
        request_hash = stable_hash(request)
        receipt = {
            "schema": "stegverse.healer-resident-request-consumption/v1",
            "state": "ATTEMPT_RECORDED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "task_id": TARGET_TASK,
            "mode": TARGET_MODE,
            "standing_request": True,
            "recurrence": request["recurrence"],
            "source_resolution": source_resolution,
            "runtime_execution_attempted": False,
            "scheduler_cycle_completion_observed": False,
            "terminal_scheduler_completion_observed": False,
            "retry_allowed": True,
            "request_consumed": False,
            "request_granted_authority": False,
            "heartbeat_grants_execution_authority": False,
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "second_machine_required": False,
            "network_source_fetch_performed": False,
            "blocker": "DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED",
            "authority_effect": "NONE_REQUEST_ONLY",
        }
        path = runtime / CONSUMPTION_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    request_materialization = synchronize_standing_request(source, runtime)
    scheduler_materialization = ensure_neutral_scheduler_materialized(source, runtime, runner=runner, values=values)
    request_path = runtime / REQUEST_REL
    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)

    # Execute the canonical source refresh bridge directly. Requiring a stale
    # runtime to already contain the current refresh bridge would recreate the
    # same source-refresh circularity this standing request exists to break.
    entrypoint = source / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"canonical Healer resident execution entrypoint missing: {entrypoint}")

    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(values), timeout=1200)
    result = parse_last_json(completed.stdout)
    execution_result = result.get("execution_result") if isinstance(result, dict) else None
    cycle_completed = completed_healer_cycle_observed(result)
    retention_binding = (
        bind_projected_retention_pointer(runtime)
        if cycle_completed
        else {"state":"CURRENT_CYCLE_NOT_COMPLETED","pointer":None,"checkpoint_ref":CHECKPOINT_REL.as_posix(),"authority_effect":"NONE_EVIDENCE_CARRIAGE_ONLY"}
    )
    if isinstance(result, dict):
        result = dict(result)
        result["resident_custody_root_observation_retention"] = retention_binding.get("pointer")
        result["resident_custody_root_observation_retention_binding"] = {key: value for key, value in retention_binding.items() if key != "pointer"}

    receipt = {
        "schema": "stegverse.healer-resident-request-consumption/v1",
        "state": "CYCLE_COMPLETED" if cycle_completed else "ATTEMPT_RECORDED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "request_materialization": request_materialization,
        "neutral_scheduler_materialization": scheduler_materialization,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "standing_request": True,
        "recurrence": request["recurrence"],
        "source_root": str(source),
        "runtime_root": str(runtime),
        "source_resolution": source_resolution,
        "source_runtime_separated": source != runtime,
        "canonical_refresh_entrypoint": str(entrypoint),
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "scheduler_cycle_completion_observed": cycle_completed,
        "terminal_scheduler_completion_observed": False,
        "retry_allowed": True,
        "request_consumed": False,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    path = runtime / CONSUMPTION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
