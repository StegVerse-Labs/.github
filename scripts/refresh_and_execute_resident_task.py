#!/usr/bin/env python3
"""Refresh already-local resident WorkerCoordinator source, then execute one bounded task.

This bridge is intentionally transport-free and scheduler-neutral. It consumes only an
already-local canonical source tree, preserves mutable resident runtime state through
refresh_sovereign_worker_runtime_source.refresh(), strips GitHub/hosted authority
environment variables, and invokes exactly one bounded execution entrypoint.

Supported modes:
- independently admitted task control via run_worker_runtime.py --task-id;
- resume an already-claimed ACTIVE/BLOCKED task in place through the same targeted
  WorkerCoordinator cycle, without minting a new claim/fence;
- the dedicated Ecosystem Chat parent executor, which retains its stronger recovery
  and fence semantics.

For compact canonical continuation, targeted/resume modes may additionally provide
--cosv-task-vector. After source refresh and before execution, the task ID/vector pair
is resolved exactly once against control/task-vector-index.json and the referenced
canonical task-vector record; index/source-vector parity drift fails closed. Pointer
validation grants no execution, claim, fence, credential, transition, or custody authority.

Running this script on a sovereign resident surface may produce real runtime evidence.
Merely merging or validating this source does not.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERIC_RUNNER = Path("scripts/run_worker_runtime.py")
ECOSYSTEM_CHAT_PARENT_RUNNER = Path("scripts/run_independent_ecosystem_chat_parent.py")
CARRIER_REF = Path("control/heartbeat-carrier-runtime-state.json")
REGISTRY_REF = Path("control/worker-registry.json")
COSV_INDEX_REF = Path("control/task-vector-index.json")
RECEIPT_REL = Path("receipts/sovereign-host/resident-targeted-execution.latest.json")
IMMUTABLE_RECEIPT_DIR_REL = Path("receipts/sovereign-host/resident-targeted-execution.by-receipt")

GITHUB_AUTH_ENV = {
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
}
HOSTED_MARKERS = {
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "VERCEL_ENV",
    "CLOUDFLARE_API_TOKEN",
}
NONSECRET_FORWARD = {
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "XDG_STATE_HOME",
    "XDG_CONFIG_HOME",
    "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_VAULT_AGENT_SOCKET",
    "STEGVERSE_ARA_MAIL_RECIPIENT",
    "STEGVERSE_ARA_MAIL_SENDER",
    "STEGVERSE_TV_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_MASTER_RECORDS_ENDPOINT",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
    "STEGVERSE_ORG_LEDGER_ROOT",
    "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
    "MASTER_RECORDS_DB",
    "MASTER_RECORDS_RECEIPT_KEY",
    "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
    "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_HIL_STATE_ROOT",
    "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_STEGOS_ROOT",
    "STEGVERSE_KV_SOURCE_ROOT",
    "STEGVERSE_KV_ROOT",
    "STEGVERSE_SITE_ROOT",
    "STEGVERSE_STEGINDEX_SOURCE_ROOT",
    "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_HEALER_ROOT",
    "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_PORT",
    "STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS",
    "STEGVERSE_RELAY_RUNTIME_BASE",
    "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT",
    "STEGVERSE_GTG_ROOT",
    "STEGVERSE_AE_ROOT",
    "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT",
    "STEGVERSE_SELF_CHAR_MODEL_ID",
    "STEGVERSE_OLLAMA_MODEL",
    "STEGVERSE_SV011_ORG_ROOT",
    "STEGVERSE_SV011_MATERIALIZED_ROOT",
    "STEGVERSE_GLM53_ENDPOINT",
    "STEGVERSE_GLM53_MODEL_PATH",
    "STEGVERSE_GLM53_RUNTIME_IDENTITY",
    "STEGVERSE_GLM53_ENERGY_KWH",
    "STEGVERSE_GLM53_HARDWARE_AMORTIZATION_USD",
    "STEGVERSE_GLM53_ENERGY_COST_USD",
    "STEGVERSE_GLM53_STORAGE_NETWORK_RUNTIME_OVERHEAD_USD",
    "STEGVERSE_WARRANT_JSON",
    "TV_POLICY_BUNDLE_SHA256",
    "TV_WARRANT_ISSUER_PUBKEY_B64",
    "TV_WARRANT_MAX_TTL_SECONDS",
}
Runner = Callable[..., subprocess.CompletedProcess[str]]


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def clean_exec_env(source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {name: values[name] for name in NONSECRET_FORWARD if name in values}
    for name in GITHUB_AUTH_ENV | HOSTED_MARKERS:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def _write_receipt_surfaces(runtime_root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    """Persist latest plus immutable content-addressed resident execution evidence."""
    unsigned = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    body_sha256 = hashlib.sha256(unsigned).hexdigest()
    persisted = dict(receipt)
    persisted["receipt_body_sha256"] = "sha256:" + body_sha256
    encoded = json.dumps(persisted, indent=2, sort_keys=True) + "\n"

    immutable_path = runtime_root / IMMUTABLE_RECEIPT_DIR_REL / f"{body_sha256}.json"
    immutable_path.parent.mkdir(parents=True, exist_ok=True)
    if immutable_path.exists():
        if immutable_path.read_text(encoding="utf-8") != encoded:
            raise RuntimeError("immutable resident execution receipt collision")
    else:
        immutable_path.write_text(encoded, encoding="utf-8")

    latest_path = runtime_root / RECEIPT_REL
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(encoded, encoding="utf-8")
    return persisted


def _parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _load_registry(runtime_root: Path) -> dict[str, Any]:
    path = runtime_root / REGISTRY_REF
    if not path.is_file():
        raise RuntimeError("resident worker registry is not materialized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("resident worker registry is unreadable") from exc
    if not isinstance(value, dict) or not isinstance(value.get("tasks"), list):
        raise RuntimeError("resident worker registry shape is invalid")
    return value


def validate_cosv_task_pointer(runtime_root: Path, task_id: str, vector: str) -> dict[str, Any]:
    """Verify a compact task.v1 pointer against index and canonical vector record."""
    if not isinstance(vector, str) or len(vector) != 14 or not vector.isdigit():
        raise RuntimeError("COSV task vector must be a 14-digit task.v1 vector")
    path = runtime_root / COSV_INDEX_REF
    if not path.is_file():
        raise RuntimeError("canonical COSV task-vector index is not materialized")
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("canonical COSV task-vector index is unreadable") from exc
    if not isinstance(index, dict) or index.get("profile") not in (None, "task.v1"):
        raise RuntimeError("canonical COSV task-vector index profile is invalid")
    rows = index.get("tasks")
    if not isinstance(rows, list):
        raise RuntimeError("canonical COSV task-vector index shape is invalid")
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) != 1:
        raise RuntimeError("canonical COSV task pointer must resolve exactly once")
    row = matches[0]
    if row.get("vector") != vector:
        raise RuntimeError("task_id/COSV vector binding mismatch")
    if row.get("vector_state") not in (None, "EMITTED") or row.get("authority_effect") not in (None, "NONE"):
        raise RuntimeError("canonical COSV task-vector index row is not non-authorizing EMITTED state")
    source_ref = row.get("source_state_vector_ref")
    if not isinstance(source_ref, str) or not source_ref:
        raise RuntimeError("canonical COSV task pointer lacks source state-vector provenance")
    source_path = (runtime_root / source_ref.split("#", 1)[0]).resolve()
    try:
        source_path.relative_to(runtime_root.resolve())
    except ValueError as exc:
        raise RuntimeError("canonical COSV source state-vector escaped resident root") from exc
    if not source_path.is_file():
        raise RuntimeError("canonical COSV source state-vector is not materialized")
    try:
        source_vector = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("canonical COSV source state-vector is unreadable") from exc
    identity = str(source_vector.get("identity") or "") if isinstance(source_vector, dict) else ""
    if not (
        isinstance(source_vector, dict)
        and source_vector.get("profile") == "task.v1"
        and source_vector.get("level") == "task"
        and identity.endswith(f":task:{task_id}")
        and source_vector.get("vector") == vector
    ):
        raise RuntimeError("canonical COSV index/source state-vector parity mismatch")
    return {
        "profile": "task.v1",
        "task_id": task_id,
        "vector": vector,
        "source_state_vector_ref": source_ref,
        "registry_ref": row.get("registry_ref"),
        "validated_against": str(COSV_INDEX_REF),
        "source_vector_verified": True,
        "binding_verified": True,
        "authority_effect": "NONE",
    }


def claimed_task_snapshot(runtime_root: Path, task_id: str) -> dict[str, Any]:
    registry = _load_registry(runtime_root)
    task = next(
        (row for row in registry["tasks"] if isinstance(row, dict) and row.get("task_id") == task_id),
        None,
    )
    if task is None:
        raise RuntimeError("claimed task is not present in resident worker registry")
    timing = task.get("heartbeat_timing") or {}
    state = task.get("state")
    claim_id = task.get("claim_id")
    worker_id = task.get("worker_id")
    worker_instance_id = task.get("worker_instance_id")
    fencing_token = timing.get("fencing_token")
    if state not in {"ACTIVE", "BLOCKED", "RETRY"}:
        raise RuntimeError("claimed-task resume requires ACTIVE/BLOCKED/RETRY state")
    if not isinstance(claim_id, str) or not claim_id:
        raise RuntimeError("claimed-task resume requires existing claim_id")
    if not isinstance(worker_id, str) or not worker_id:
        raise RuntimeError("claimed-task resume requires existing worker_id")
    if not isinstance(worker_instance_id, str) or not worker_instance_id:
        raise RuntimeError("claimed-task resume requires existing worker_instance_id")
    if not isinstance(fencing_token, int):
        raise RuntimeError("claimed-task resume requires existing fencing_token")
    return {
        "task_id": task_id,
        "state": state,
        "claim_id": claim_id,
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "fencing_token": fencing_token,
        "registry_generation": registry.get("generation"),
    }


def execution_command(
    runtime_root: Path,
    *,
    task_id: str | None,
    resume_claimed_task_id: str | None = None,
    ecosystem_chat_parent: bool,
) -> list[str]:
    runtime = runtime_root.expanduser().resolve()
    selected = [value is not None for value in (task_id, resume_claimed_task_id)]
    if ecosystem_chat_parent:
        if any(selected):
            raise ValueError("task modes and ecosystem_chat_parent are mutually exclusive")
        script = runtime / ECOSYSTEM_CHAT_PARENT_RUNNER
        return [sys.executable, str(script), "--root", str(runtime)]
    if sum(selected) != 1:
        raise ValueError("exactly one task_id or resume_claimed_task_id is required")
    selected_task = task_id if task_id is not None else resume_claimed_task_id
    script = runtime / GENERIC_RUNNER
    return [
        sys.executable,
        str(script),
        "--root",
        str(runtime),
        "--task-id",
        str(selected_task),
    ]


def _at_transition_boundary(stage: str, operation: Callable[[], Any]) -> Any:
    """Mark an existing execution stage without changing exception types or authority."""
    try:
        return operation()
    except Exception as exc:
        setattr(exc, "stegverse_transition_boundary", stage)
        raise


def _require_entrypoint(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"refreshed execution entrypoint missing: {path}")


def _refresh_and_execute_inner(
    source_root: Path,
    runtime_root: Path,
    *,
    task_id: str | None = None,
    resume_claimed_task_id: str | None = None,
    ecosystem_chat_parent: bool = False,
    cosv_task_vector: str | None = None,
    runner: Runner = subprocess.run,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if resume_claimed_task_id is not None and (task_id is not None or ecosystem_chat_parent):
        raise ValueError("resume_claimed_task_id is mutually exclusive with other execution modes")
    if ecosystem_chat_parent and cosv_task_vector is not None:
        raise ValueError("cosv_task_vector applies only to explicit task modes")

    if source == runtime:
        refresh_receipt = {
            "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
            "state": "SOURCE_EQUALS_RUNTIME_NO_REFRESH_REQUIRED",
            "source_root": str(source),
            "runtime_root": str(runtime),
            "mutable_runtime_state_preserved": True,
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
            "authority_effect": "NONE_ALREADY_MATERIALIZED_SOURCE",
        }
    else:
        refresh_receipt = _at_transition_boundary("LOCAL_SOURCE_REFRESH", lambda: refresh(source, runtime))
    selected_pointer_task_id = resume_claimed_task_id or task_id
    pointer_receipt = (
        _at_transition_boundary(
            "COSV_POINTER_VALIDATION",
            lambda: validate_cosv_task_pointer(runtime, str(selected_pointer_task_id), cosv_task_vector),
        )
        if cosv_task_vector is not None and selected_pointer_task_id is not None
        else None
    )
    claim_before = (
        _at_transition_boundary("EXISTING_CLAIM_PREFLIGHT", lambda: claimed_task_snapshot(runtime, resume_claimed_task_id))
        if resume_claimed_task_id is not None
        else None
    )

    command = _at_transition_boundary(
        "TARGETED_ENTRYPOINT_RESOLUTION",
        lambda: execution_command(
            runtime,
            task_id=task_id,
            resume_claimed_task_id=resume_claimed_task_id,
            ecosystem_chat_parent=ecosystem_chat_parent,
        ),
    )
    executable = Path(command[1])
    _at_transition_boundary("TARGETED_ENTRYPOINT_VALIDATION", lambda: _require_entrypoint(executable))
    # Independent --task-id execution is admitted directly by WorkerCoordinator and
    # must not be gated by a separated carrier reference. Resume mode preserves an
    # already-existing claim/fence and retains its historical carrier requirement.
    if resume_claimed_task_id is not None and not (runtime / CARRIER_REF).is_file():
        _at_transition_boundary(
            "EXISTING_CLAIM_CARRIER_VALIDATION",
            lambda: (_ for _ in ()).throw(RuntimeError(
                "claimed-task resume requires the preserved separated carrier reference"
            )),
        )

    completed = _at_transition_boundary(
        "TARGETED_WORKER_SUBPROCESS",
        lambda: runner(
            command,
            cwd=runtime,
            capture_output=True,
            text=True,
            check=False,
            env=clean_exec_env(env),
        ),
    )
    result = _parse_last_json(completed.stdout)
    claim_after: dict[str, Any] | None = None
    if resume_claimed_task_id is not None:
        try:
            claim_after = claimed_task_snapshot(runtime, resume_claimed_task_id)
        except RuntimeError:
            claim_after = None

    mode = (
        "DEDICATED_ECOSYSTEM_CHAT_PARENT"
        if ecosystem_chat_parent
        else (
            "RESUME_EXISTING_CLAIM"
            if resume_claimed_task_id is not None
            else "TARGETED_INDEPENDENT_TASK_CONTROL"
        )
    )
    selected_task_id = (
        "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
        if ecosystem_chat_parent
        else (resume_claimed_task_id or task_id)
    )
    receipt = {
        "schema": "stegverse.resident-refresh-targeted-execution/v3",
        "source_root": str(source),
        "runtime_root": str(runtime),
        "mode": mode,
        "task_id": selected_task_id,
        "cosv_task_pointer": pointer_receipt,
        "cosv_pointer_required_by_this_invocation": cosv_task_vector is not None,
        "command": command,
        "refresh_receipt": refresh_receipt,
        "existing_claim_preflight": claim_before,
        "existing_claim_postflight": claim_after,
        "new_claim_requested": False if resume_claimed_task_id is not None else None,
        "existing_fence_preserved_by_mode": True if resume_claimed_task_id is not None else None,
        "execution_returncode": completed.returncode,
        "execution_result": result,
        "execution_result_observed": isinstance(result, dict),
        "runtime_execution_attempted": True,
        "source_refresh_is_runtime_execution": False,
        "network_fetch_performed": False,
        "third_party_scheduler_required": False,
        "systemd_required_for_one_shot": False,
        "second_machine_required": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_value_exposed": False,
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
    }
    return _write_receipt_surfaces(runtime, receipt)



def refresh_and_execute(
    source_root: Path,
    runtime_root: Path,
    *,
    task_id: str | None = None,
    resume_claimed_task_id: str | None = None,
    ecosystem_chat_parent: bool = False,
    cosv_task_vector: str | None = None,
    runner: Runner = subprocess.run,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Retain the first failed bridge stage in existing immutable resident receipts.

    This evidence-only envelope does not admit execution, mint a claim/fence,
    substitute a worker outcome, or promote a task. Only the resident process
    actually running this bridge can create an authentic receipt.
    """
    try:
        return _refresh_and_execute_inner(
            source_root, runtime_root,
            task_id=task_id,
            resume_claimed_task_id=resume_claimed_task_id,
            ecosystem_chat_parent=ecosystem_chat_parent,
            cosv_task_vector=cosv_task_vector,
            runner=runner,
            env=env,
        )
    except Exception as exc:
        boundary = getattr(exc, "stegverse_transition_boundary", "BRIDGE_PRE_RESULT_UNCLASSIFIED")
        selected = resume_claimed_task_id or task_id or (
            "SHWP-ECOSYSTEM-CHAT-INFERENCE-001" if ecosystem_chat_parent else None
        )
        failure = {
            "schema": "stegverse.resident-refresh-targeted-execution/v3",
            "state": "BOUNDARY_FAILED",
            "task_id": selected,
            "cosv_task_vector_requested": cosv_task_vector,
            "mode": (
                "RESUME_EXISTING_CLAIM" if resume_claimed_task_id
                else "DEDICATED_ECOSYSTEM_CHAT_PARENT" if ecosystem_chat_parent
                else "TARGETED_INDEPENDENT_TASK_CONTROL"
            ),
            "failed_transition_boundary": boundary,
            "failure_type": type(exc).__name__,
            "failure_detail_carried": False,
            "claim_id": None,
            "fencing_token": None,
            "claim_or_fence_inferred": False,
            "worker_completion_claimed": False,
            "runtime_execution_attempted": boundary == "TARGETED_WORKER_SUBPROCESS",
            "canonical_state_transition_claimed": False,
            "source_root": str(source_root.expanduser().resolve()),
            "runtime_root": str(runtime_root.expanduser().resolve()),
            "network_source_fetch_performed": False if boundary != "LOCAL_SOURCE_REFRESH" else None,
            "credential_value_exposed": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_FAILURE_EVIDENCE_ONLY",
            "next_replay_boundary": boundary,
        }
        _write_receipt_surfaces(runtime_root.expanduser().resolve(), failure)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh resident WorkerCoordinator source and execute exactly one bounded task."
    )
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runtime-root", type=Path, default=default_runtime_root())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--task-id")
    mode.add_argument("--resume-claimed-task-id")
    mode.add_argument("--ecosystem-chat-parent", action="store_true")
    parser.add_argument("--cosv-task-vector")
    args = parser.parse_args()

    receipt = refresh_and_execute(
        args.source_root,
        args.runtime_root,
        task_id=args.task_id,
        resume_claimed_task_id=args.resume_claimed_task_id,
        ecosystem_chat_parent=args.ecosystem_chat_parent,
        cosv_task_vector=args.cosv_task_vector,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["execution_returncode"] == 0 and receipt["execution_result_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())