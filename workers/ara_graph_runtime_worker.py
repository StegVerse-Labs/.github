#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
HANDOFF_PATH = ROOT / "handoffs" / "SHWP-ARA-GRAPH-RUNTIME-086.json"
RECEIPT_PATH = ROOT / "receipts" / "ara-graph-runtime" / "SHWP-ARA-GRAPH-RUNTIME-086.json"
TASK_ID = "SHWP-ARA-GRAPH-RUNTIME-086"
CAPABILITY = "tvc_ara_graph_runtime_execution"
REQUIRED_TVC_ANCESTOR = "e36dc36f697afc27936403db171f23a6cc45edf3"
AUTHORITY_ENV = "STEGTV_ARA_GRAPH_RUNTIME_AUTHORITY"
AUTHORITY_VALUE = "TV/TVC"

REQUIRED_TVC_FILES = (
    "tools/task_dispatcher.py",
    "tvc_ara_graph_runtime_tasks.py",
    "scripts/tvc_ara_graph_operations.py",
    "scripts/tvc_ara_graph_resident_intake.py",
    "scripts/tvc_ara_graph_kv_intr_carrier.py",
    "scripts/observe_ara_graph_provider_permissions.py",
    "scripts/observe_ara_graph_policy_bindings.py",
    "config/ara_graph_operation_admission.json",
    "config/ara_graph_resident_intake.json",
    "config/task_catalog.d/ara-graph-runtime.json",
    "tasks/TVC-ARA-GRAPH-086.json",
    "tasks/TVC-ARA-GRAPH-RUNTIME-EXECUTION-086.json",
)

HOSTED_ENV = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "WALLET_PRIVATE_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC",
    "TVC_EPHEMERAL_GITHUB_TOKEN",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def _hosted_runtime_active() -> list[str]:
    return [name for name in HOSTED_ENV if _truthy(os.environ.get(name))]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def _git_head(root: Path) -> str:
    proc = _git(root, "rev-parse", "HEAD")
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _clean_worktree(root: Path) -> bool:
    proc = _git(root, "status", "--porcelain")
    return proc.returncode == 0 and proc.stdout.strip() == ""


def _contains_required_ancestor(root: Path) -> bool:
    proc = _git(root, "merge-base", "--is-ancestor", REQUIRED_TVC_ANCESTOR, "HEAD")
    return proc.returncode == 0


def locate_tvc() -> tuple[Path | None, list[dict[str, Any]]]:
    candidates: list[Path] = []
    raw = os.environ.get("STEGVERSE_TVC_ROOT", "").strip()
    if raw:
        candidates.append(Path(raw).expanduser())
    candidates.extend([
        Path.home() / ".stegverse" / "repos" / "StegVerse-Labs" / "TVC",
        Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"),
        Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),
        Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),
    ])
    observed: list[dict[str, Any]] = []
    for candidate in candidates:
        if not (candidate / ".git").is_dir():
            continue
        head = _git_head(candidate)
        complete = all((candidate / rel).is_file() for rel in REQUIRED_TVC_FILES)
        clean = _clean_worktree(candidate)
        ancestor = _contains_required_ancestor(candidate)
        row = {
            "path": str(candidate),
            "head": head,
            "required_source_present": complete,
            "clean_worktree": clean,
            "required_ancestor_present": ancestor,
        }
        observed.append(row)
        if head and complete and clean and ancestor:
            row["selected"] = True
            return candidate.resolve(), observed
    return None, observed


def child_env(*, authority: bool) -> dict[str, str]:
    allow = {
        "HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG", "LC_ALL",
        "TMPDIR", "XDG_CONFIG_HOME", "XDG_STATE_HOME",
        "STEGVERSE_TVC_ROOT",
        "STEGVERSE_ARA_MAIL_SENDER",
        "STEGVERSE_ARA_MAIL_RECIPIENT",
        "STEGVERSE_VAULT_AGENT_SOCKET",
    }
    env = {name: os.environ[name] for name in allow if os.environ.get(name)}
    for name in FORBIDDEN_ENV:
        env.pop(name, None)
    if authority:
        env[AUTHORITY_ENV] = AUTHORITY_VALUE
    else:
        env.pop(AUTHORITY_ENV, None)
    return env


def parse_dispatcher(proc: subprocess.CompletedProcess[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(proc.stdout)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _optional_task_control_identity(invocation: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    lease = task.get("lease") if isinstance(task.get("lease"), dict) else {}
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    fence = lease.get("fencing_token")
    if fence is None:
        fence = timing.get("fencing_token")
    epoch = invocation.get("heartbeat_epoch")
    return {
        "claim_id": task.get("claim_id") if isinstance(task.get("claim_id"), str) else None,
        "fencing_token": fence if isinstance(fence, int) else None,
        "observed_heartbeat_epoch": epoch if isinstance(epoch, int) else None,
        "heartbeat_reference_only": True,
        "heartbeat_grants_execution_authority": False,
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if task.get("task_id") != TASK_ID:
        return 4

    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 6
    if "receipts/ara-graph-runtime/**" not in set(execution.get("allowed_paths") or []):
        return 7

    task_control = _optional_task_control_identity(invocation, task)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    hosted = _hosted_runtime_active()
    tvc_root: Path | None = None
    observed: list[dict[str, Any]] = []

    if hosted:
        state = "BLOCKED"
        result: dict[str, Any] = {
            "reason": "HOSTED_RUNTIME_PROHIBITED",
            "hosted_markers": hosted,
            "provider_operation_performed": False,
            "credential_authority": "TV/TVC",
            "credential_material_exported": False,
            "provider_access_material_exported": False,
        }
    else:
        tvc_root, observed = locate_tvc()
        if tvc_root is None:
            state = "BLOCKED"
            result = {
                "reason": "CURRENT_LOCAL_TVC_SOURCE_NOT_MATERIALIZED",
                "required_ancestor": REQUIRED_TVC_ANCESTOR,
                "observed_candidates": observed,
                "network_source_fetch_performed": False,
                "source_mutation_performed": False,
                "provider_operation_performed": False,
                "credential_authority": "TV/TVC",
                "credential_material_exported": False,
                "provider_access_material_exported": False,
            }
        else:
            preflight = subprocess.run(
                ["python", "tools/task_dispatcher.py", "tvc.ara_graph.activation_preflight"],
                cwd=tvc_root,
                env=child_env(authority=False),
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
            )
            preflight_report = parse_dispatcher(preflight)
            preflight_result = preflight_report.get("result") if isinstance(preflight_report, dict) else None
            preflight_ready = (
                preflight.returncode == 0
                and isinstance(preflight_report, dict)
                and preflight_report.get("status") == "ok"
                and isinstance(preflight_result, dict)
                and preflight_result.get("state") == "READY_FOR_RESIDENT_INTAKE"
                and isinstance(preflight_result.get("request_hash"), str)
                and len(preflight_result["request_hash"]) == 64
                and preflight_result.get("resident_intake_invoked") is False
                and preflight_result.get("provider_operation_performed") is False
            )
            if not preflight_ready:
                state = "BLOCKED"
                result = {
                    "reason": "ARA_GRAPH_PREFLIGHT_BLOCKED",
                    "tvc_source_root": str(tvc_root),
                    "tvc_source_head": _git_head(tvc_root),
                    "preflight_exit_code": preflight.returncode,
                    "preflight_report": preflight_report,
                    "preflight_stderr_tail": (preflight.stderr or "")[-4000:],
                    "provider_operation_performed": False,
                    "credential_authority": "TV/TVC",
                    "credential_material_exported": False,
                    "provider_access_material_exported": False,
                }
            else:
                execute = subprocess.run(
                    ["python", "tools/task_dispatcher.py", "tvc.ara_graph.execute_once"],
                    cwd=tvc_root,
                    env=child_env(authority=True),
                    text=True,
                    capture_output=True,
                    timeout=240,
                    check=False,
                )
                execute_report = parse_dispatcher(execute)
                execute_result = execute_report.get("result") if isinstance(execute_report, dict) else None
                success = (
                    execute.returncode == 0
                    and isinstance(execute_report, dict)
                    and execute_report.get("status") == "ok"
                    and isinstance(execute_result, dict)
                    and execute_result.get("state") == "PROVIDER_OPERATION_RESULT_RECORDED"
                    and execute_result.get("preflight_ready") is True
                    and execute_result.get("resident_intake_invoked") is True
                    and execute_result.get("provider_operation_result_recorded") is True
                    and execute_result.get("credential_material_exported") is False
                    and execute_result.get("provider_access_material_exported") is False
                    and execute_result.get("runtime_activation_claimed") is False
                    and execute_result.get("ara_release_authority_effect") == "NONE"
                    and execute_result.get("request_hash") == preflight_result.get("request_hash")
                )
                state = "COMPLETED" if success else "BLOCKED"
                result = {
                    "reason": "ARA_GRAPH_PROVIDER_OPERATION_RECORDED" if success else "ARA_GRAPH_EXECUTE_ONCE_BLOCKED",
                    "tvc_source_root": str(tvc_root),
                    "tvc_source_head": _git_head(tvc_root),
                    "required_ancestor": REQUIRED_TVC_ANCESTOR,
                    "preflight_request_hash": preflight_result.get("request_hash"),
                    "operation_class": execute_result.get("operation_class") if isinstance(execute_result, dict) else None,
                    "provider_result_path": execute_result.get("provider_result_path") if isinstance(execute_result, dict) else None,
                    "execute_exit_code": execute.returncode,
                    "execute_report": execute_report,
                    "execute_stderr_tail": (execute.stderr or "")[-4000:],
                    "credential_authority": "TV/TVC",
                    "runtime_authority_declared_by_registered_worker": True,
                    "credential_material_exported": False,
                    "provider_access_material_exported": False,
                    "github_token_runtime_authority": "NONE",
                    "network_source_fetch_performed": False,
                    "source_mutation_performed": False,
                    "ara_release_authority_effect": "NONE",
                }

    receipt = {
        "schema": "stegverse.ara-graph-runtime-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "task_control": task_control,
        "generated_at": now,
        "state": state,
        "result": result,
        "credential_authority": "TV/TVC",
        "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE",
        "authority_effect": "REGISTERED_TV_TVC_RUNTIME_TASK_ONLY",
    }
    atomic_write(RECEIPT_PATH, receipt)

    blocker = None
    if state != "COMPLETED":
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": result["reason"],
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "RECHECK_CURRENT_LOCAL_TVC_THEN_RUN_ARA_GRAPH_PREFLIGHT",
            "machine_observable_release_condition": "A registered sovereign worker cycle records one bounded secret-free ARA Graph provider operation result",
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": f"ARA_GRAPH_RUNTIME_{state}",
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "ARA_GRAPH_RUNTIME_RECHECK",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "recheck_policy": None if state == "COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref": "receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json",
        "evidence_refs": [
            "handoffs/SHWP-ARA-GRAPH-RUNTIME-086.json",
            "receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json",
            "StegVerse-Labs/TVC/tasks/TVC-ARA-GRAPH-RUNTIME-EXECUTION-086.json",
        ],
        "blocker": blocker,
        "cost_observation": {
            "task_control_evaluations": 1,
            "observed_heartbeat_reference_count": 1 if task_control["observed_heartbeat_epoch"] is not None else 0,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "tvc_ara_graph_runtime_execution",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
