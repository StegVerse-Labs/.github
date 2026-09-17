#!/usr/bin/env python3
"""Reuse the existing TVC primary-runtime binding through bounded service delivery.

This wrapper stays inside the generic reusable-task scripts/*.py surface while TVC
remains the owner of runtime binding, activation, provider-operation, and credential
semantics. It never enters the forever-serving activation task synchronously.
Instead it validates the existing binder, restarts the already-approved TVC service
through the released activation-delivery installer, then observes the existing
runtime boundary.

When the invocation is RT-TVC-PRIMARY-RUNTIME-BINDING-001, the wrapper emits the
standard reusable-task runner result only after the exact binding predicates are
proved by successful preflight + same-service activation delivery + READY observer.
For observation-only invocations it preserves the existing non-terminal behavior.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

PRIMARY_BINDING_ID = "RT-TVC-PRIMARY-RUNTIME-BINDING-001"
READY_STATE = "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND"


def emit(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")


def run(command: list[str], *, cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    emit(completed)
    return completed


def last_json_object(stdout: str) -> dict[str, Any] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for index in range(len(lines)):
        candidate = "\n".join(lines[index:])
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def write_standard_result(*, evidence: dict[str, Any]) -> None:
    result_raw = os.getenv("STEGVERSE_REUSABLE_TASK_RESULT_PATH", "").strip()
    manifest_raw = os.getenv("STEGVERSE_REUSABLE_TASK_MANIFEST", "").strip()
    invocation_id = os.getenv("STEGVERSE_REUSABLE_TASK_INVOCATION_ID", "").strip()
    reusable_task_id = os.getenv("STEGVERSE_REUSABLE_TASK_ID", "").strip()
    predicates_raw = os.getenv("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]").strip() or "[]"
    if not result_raw or not manifest_raw or not invocation_id or reusable_task_id != PRIMARY_BINDING_ID:
        return
    manifest = load_json(Path(manifest_raw))
    predicates = json.loads(predicates_raw)
    if not isinstance(manifest, dict) or not isinstance(predicates, list) or not all(isinstance(x, str) for x in predicates):
        raise RuntimeError("reusable task result binding metadata invalid")
    manifest_hash = str(manifest.get("manifest_hash") or "")
    if not manifest_hash:
        raise RuntimeError("reusable task manifest hash missing")
    payload = {
        "schema": "stegverse.reusable-task-runner-result/v1",
        "invocation_id": invocation_id,
        "reusable_task_id": reusable_task_id,
        "manifest_hash": manifest_hash,
        "completion_predicates_satisfied": predicates,
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "evidence": evidence,
        "authority_effect": "NONE",
    }
    path = Path(result_raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    raw = os.getenv("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    if not raw:
        print(json.dumps({"state":"BOUNDARY_RECORDED","reason":"TVC_LOCAL_SOURCE_ROOT_MAP_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    roots = json.loads(raw)
    if not isinstance(roots, dict):
        raise SystemExit("STEGVERSE_REPO_ROOTS_JSON must be an object")
    tvc_raw = roots.get("StegVerse-Labs/TVC")
    if not isinstance(tvc_raw, str) or not tvc_raw:
        print(json.dumps({"state":"BOUNDARY_RECORDED","reason":"TVC_LOCAL_SOURCE_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    tvc_root = Path(tvc_raw).expanduser().resolve()
    dispatcher = tvc_root / "tools" / "task_dispatcher.py"
    observer = tvc_root / "scripts" / "observe_tvc_runtime_boundary.py"
    installer = tvc_root / "scripts" / "install_tvc_primary_runtime_service.py"
    if not dispatcher.is_file() or not observer.is_file() or not installer.is_file():
        print(json.dumps({"state":"BOUNDARY_RECORDED","reason":"TVC_DECLARED_RUNNER_DEPENDENCY_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3

    preflight = run([sys.executable, str(dispatcher), "tvc.primary_runtime_binder.preflight"], cwd=tvc_root)
    if preflight.returncode != 0:
        return preflight.returncode
    preflight_report = last_json_object(preflight.stdout)
    if not isinstance(preflight_report, dict) or preflight_report.get("status") != "ok":
        return 3
    preflight_result = preflight_report.get("result")
    if not isinstance(preflight_result, dict) or preflight_result.get("state") != "READY_FOR_TV_TVC_PRIMARY_RUNTIME_SERVE":
        return 3
    if preflight_result.get("credential_authority") != "TV/TVC" or preflight_result.get("github_token_required") is not False:
        return 3

    # Bounded delivery of the existing service. Do not invoke the forever-serving
    # tvc.primary_runtime_binder.activate command synchronously here.
    delivery = run([sys.executable, str(installer), "--repo-root", str(tvc_root), "--activate"], cwd=tvc_root)
    if delivery.returncode != 0:
        return delivery.returncode

    params_raw = os.getenv("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "{}").strip() or "{}"
    params = json.loads(params_raw)
    observation_path = tvc_root / "artifacts" / "tvc-runtime-boundary-observation.json"
    command = [sys.executable, str(observer), "--output", str(observation_path)]
    provider_route = params.get("provider_operation_route") if isinstance(params, dict) else None
    if isinstance(provider_route, str) and provider_route:
        command.extend(["--provider-route", provider_route])
    observed = run(command, cwd=tvc_root)
    if observed.returncode != 0:
        return observed.returncode
    observation = load_json(observation_path)
    if not isinstance(observation, dict) or observation.get("state") != READY_STATE:
        return 3
    if observation.get("credential_authority") != "TV/TVC" or observation.get("github_token_required") is not False:
        return 3
    if observation.get("provider_secret_used") is not False or observation.get("provider_secret_exported") is not False:
        return 3

    if os.getenv("STEGVERSE_REUSABLE_TASK_ID", "").strip() == PRIMARY_BINDING_ID:
        write_standard_result(evidence={
            "preflight_state": preflight_result.get("state"),
            "preflight_task_id": preflight_result.get("task_id"),
            "runtime_id": preflight_result.get("runtime_id"),
            "local_binding_proof": preflight_result.get("local_binding_proof"),
            "service_delivery_runner": "StegVerse-Labs/TVC:scripts/install_tvc_primary_runtime_service.py --activate",
            "service_delivery_returncode": delivery.returncode,
            "same_service_restarted": True,
            "duplicate_runtime_or_host_created": False,
            "runtime_observation_state": observation.get("state"),
            "runtime_observation_ref": str(observation_path),
            "credential_authority": "TV/TVC",
            "github_runtime_authority": "NONE",
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
