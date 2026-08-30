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
HANDOFF_PATH = ROOT / "handoffs" / "SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json"
RECEIPT_PATH = ROOT / "receipts" / "tvc-repository-broker-validation" / "SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json"
TASK_ID = "SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001"
CAPABILITY = "tvc_repository_broker_validation"
EXPECTED_SOURCE_BUNDLE_SHA256_KEY = "expected_source_bundle_sha256"
FORBIDDEN_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "WALLET_PRIVATE_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC",
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


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def locate_tvc(expected_head: str) -> tuple[Path | None, str]:
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
    observed: list[str] = []
    for candidate in candidates:
        if not (candidate / ".git").is_dir():
            continue
        try:
            head = git(candidate, "rev-parse", "HEAD")
        except Exception:
            continue
        observed.append(f"{candidate}:{head}")
        if head == expected_head and not git(candidate, "status", "--porcelain"):
            return candidate.resolve(), head
    return None, ";".join(observed)


def cleaned_env() -> dict[str, str]:
    env = dict(os.environ)
    for name in FORBIDDEN_ENV:
        env.pop(name, None)
    env.pop("TVC_EPHEMERAL_GITHUB_TOKEN", None)
    return env


def _optional_task_control_identity(invocation: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    lease = task.get("lease") if isinstance(task.get("lease"), dict) else {}
    legacy_timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    fence = lease.get("fencing_token")
    if fence is None:
        fence = legacy_timing.get("fencing_token")
    observed_epoch = invocation.get("heartbeat_epoch")
    return {
        "claim_id": task.get("claim_id") if isinstance(task.get("claim_id"), str) else None,
        "fencing_token": fence if isinstance(fence, int) else None,
        "observed_heartbeat_epoch": observed_epoch if isinstance(observed_epoch, int) else None,
        "heartbeat_reference_only": True,
        "heartbeat_dependency": False,
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
    if "receipts/tvc-repository-broker-validation/**" not in set(execution.get("allowed_paths") or []):
        return 7

    task_control = _optional_task_control_identity(invocation, task)
    canonical = load(HANDOFF_PATH)
    expected_head = str((canonical.get("execution") or {}).get("expected_tvc_head") or "")
    expected_bundle_digest = str((canonical.get("execution") or {}).get(EXPECTED_SOURCE_BUNDLE_SHA256_KEY) or "")
    tvc_root, observed = locate_tvc(expected_head)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if tvc_root is None:
        state = "BLOCKED"
        result: dict[str, Any] = {
            "reason": "EXACT_TVC_SOURCE_NOT_MATERIALIZED",
            "expected_tvc_head": expected_head,
            "observed_candidates": observed,
            "machine_observable_release_condition": "A StegVerse-controlled local TVC repository exists at the exact pinned PR #92 head with a clean worktree",
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
        }
    else:
        command = ["python", "tools/task_dispatcher.py", "tvc.github_repository_operation_broker.verify"]
        proc = subprocess.run(command, cwd=tvc_root, env=cleaned_env(), text=True, capture_output=True, timeout=180, check=False)
        try:
            report = json.loads(proc.stdout)
        except Exception:
            report = None
        nested = report.get("result") if isinstance(report, dict) else None
        bundle_digest = nested.get("source_bundle_sha256") if isinstance(nested, dict) else None
        bundle_count = nested.get("source_bundle_file_count") if isinstance(nested, dict) else None
        passed = (
            proc.returncode == 0 and isinstance(report, dict) and report.get("status") == "ok" and
            isinstance(nested, dict) and nested.get("result") == "PASS" and
            bundle_count == 16 and isinstance(bundle_digest, str) and bundle_digest == expected_bundle_digest and
            nested.get("consumer_credential_used") is False and
            nested.get("tvc_github_credential_used") is False and
            nested.get("non_tv_tvc_secret_or_token_used") is False and
            nested.get("protected_value_disclosure") is False
        )
        state = "COMPLETED" if passed else "FAILED"
        result = {
            "reason": "TVC_BROKER_VALIDATION_PASS" if passed else "TVC_BROKER_VALIDATION_FAILED",
            "expected_tvc_head": expected_head,
            "source_root": str(tvc_root),
            "source_head": git(tvc_root, "rev-parse", "HEAD"),
            "source_bundle_file_count": bundle_count,
            "source_bundle_sha256": bundle_digest,
            "expected_source_bundle_sha256": expected_bundle_digest,
            "integration_binding_rule": "REVALIDATE_IF_BUNDLE_DIGEST_CHANGES",
            "dispatcher_exit_code": proc.returncode,
            "dispatcher_report": report,
            "stderr_tail": (proc.stderr or "")[-4000:],
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
            "merge_authority": False,
        }

    receipt = {
        "schema": "stegverse.tvc-repository-broker-validation-carrier-receipt/v0.2",
        "task_id": TASK_ID,
        "task_control": task_control,
        "generated_at": now,
        "state": state,
        "result": result,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "heartbeat_grants_execution_authority": False,
        "heartbeat_dependency": False,
        "authority_effect": "NONE_VALIDATION_ONLY",
    }
    atomic_write(RECEIPT_PATH, receipt)

    blocker = None
    if state != "COMPLETED":
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": result["reason"],
            "solution_required": True,
            "may_remain_blocked": state == "BLOCKED",
            "next_solution_action": "RECHECK_LOCAL_TVC_SOURCE_THEN_EXECUTE_REPOSITORY_NATIVE_VALIDATION",
            "machine_observable_release_condition": result.get("machine_observable_release_condition", "The exact validation command returns PASS with a 16-file source bundle digest")
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": f"TVC_REPOSITORY_BROKER_VALIDATION_{state}",
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "TVC_REPOSITORY_BROKER_VALIDATION_RECHECK",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "recheck_policy": None if state == "COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref": "receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json",
        "evidence_refs": ["handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json", "receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json"],
        "blocker": blocker,
        "cost_observation": {
            "task_control_evaluations": 1,
            "observed_heartbeat_reference_count": 1 if task_control["observed_heartbeat_epoch"] is not None else 0,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "tvc_repository_broker_validation"
        }
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
