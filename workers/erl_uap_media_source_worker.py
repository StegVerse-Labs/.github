#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK = "SHWP-ERL-UAP-MEDIA-001"
RECEIPT = ROOT / "receipts" / "erl-uap-media" / f"{TASK}.json"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def source_roots() -> list[Path]:
    roots: list[Path] = []
    explicit = os.environ.get("STEGVERSE_ERL_SOURCE_ROOT")
    if explicit:
        roots.append(Path(explicit))
    roots.extend([
        ROOT / "workloads" / "Executive_Rhetoric_Ledger",
        Path.home() / ".stegverse" / "workloads" / "Executive_Rhetoric_Ledger",
        Path.home() / ".stegverse" / "source" / "Executive_Rhetoric_Ledger",
        Path("/var/lib/stegverse/workloads/Executive_Rhetoric_Ledger"),
        Path("/var/lib/stegverse/source/Executive_Rhetoric_Ledger"),
    ])
    return roots


def find_source_root() -> Path | None:
    for candidate in source_roots():
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        if (
            (root / "scripts" / "process_uap_source_queue.py").is_file()
            and (root / "config" / "uap-media-source-queue.json").is_file()
            and (root / "docs" / "UAP_MEDIA_RESEARCH_MIRROR_HANDOFF.md").is_file()
        ):
            return root
    return None


def child_env(source_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(source_root),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": os.environ.get("HOME", str(Path.home())),
    }


def blocker(problem: str, action: str, condition: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "workaround_candidates": [
            "Resolve the released Executive_Rhetoric_Ledger source from canonical local StegVerse source/workload locations; do not perform network repository checkout.",
            "Retry the same task after the locally materialized source or public source endpoint becomes available; do not widen credential authority."
        ],
        "next_solution_action": action,
        "machine_observable_release_condition": condition,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "third_party_blocker": False,
        "human_action_required": False,
    }


def response(state: str, transition: str, seq: int, next_transition: str | None, block: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": seq,
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [
            str(RECEIPT.relative_to(ROOT)),
            "StegVerse-Labs/Executive_Rhetoric_Ledger:scripts/process_uap_source_queue.py",
            "StegVerse-Labs/Executive_Rhetoric_Ledger:task-state/UAP-MEDIA-001.json",
        ],
    }
    if block is not None:
        out["blocker"] = block
    return out


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK or not isinstance(epoch, int):
        return 2
    timing = task.get("heartbeat_timing") or {}
    claim = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim, str) or not claim or not isinstance(fence, int):
        return 3
    required = {"runtime_observation", "bounded_process_execution", "public_source_acquisition", "evidence_class_preservation"}
    capabilities = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if not required.issubset(capabilities):
        return 4

    source_root = find_source_root()
    if source_root is None:
        block = blocker(
            "The released Executive_Rhetoric_Ledger UAP source worker is not locally materialized on the sovereign carrier.",
            "Resolve/materialize the released ERL source through canonical local StegVerse source/workload storage.",
            "find_source_root resolves process_uap_source_queue.py, the UAP queue, and the bounded UAP mirror handoff",
        )
        durable = {
            "schema": "stegverse.erl-uap-media-worker-receipt/v0.1",
            "task_id": TASK,
            "heartbeat_epoch": epoch,
            "claim_id": claim,
            "fencing_token": fence,
            "state": "BLOCKED",
            "transition_id": "ERL_UAP_SOURCE_NOT_MATERIALIZED",
            "github_token_required": False,
            "github_token_used": False,
            "non_tv_tvc_secret_or_token_used": False,
            "research_promotion_authority": False,
            "publication_authority": False,
            "blocker": block,
        }
        atomic_write(RECEIPT, durable)
        json.dump(response("BLOCKED", durable["transition_id"], 1, "ERL_UAP_SOURCE_ACQUISITION_COMPLETE", block), sys.stdout)
        print()
        return 0

    workspace = Path.home() / ".stegverse" / "workloads" / "erl-uap-media" / f"epoch-{epoch}-fence-{fence}"
    workspace.mkdir(parents=True, exist_ok=True)
    execution_receipt = workspace / "source-worker-receipt.json"
    command = [
        sys.executable,
        str(source_root / "scripts" / "process_uap_source_queue.py"),
        "--fetch",
        "--output-root",
        str(workspace),
        "--receipt",
        str(execution_receipt),
    ]
    completed = subprocess.run(
        command,
        cwd=source_root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        env=child_env(source_root),
    )
    result = None
    if execution_receipt.is_file():
        try:
            result = json.loads(execution_receipt.read_text(encoding="utf-8"))
        except Exception:
            result = None

    success = completed.returncode == 0 and isinstance(result, dict) and result.get("execution_status") == "PASS" and result.get("github_token_used") is False
    if success:
        durable = {
            "schema": "stegverse.erl-uap-media-worker-receipt/v0.1",
            "task_id": TASK,
            "heartbeat_epoch": epoch,
            "claim_id": claim,
            "fencing_token": fence,
            "state": "COMPLETED",
            "transition_id": "ERL_UAP_SOURCE_ACQUISITION_COMPLETE",
            "workspace": str(workspace),
            "source_result_count": len(result.get("results") or []),
            "source_execution_receipt": str(execution_receipt),
            "github_token_required": False,
            "github_token_used": False,
            "non_tv_tvc_secret_or_token_used": False,
            "research_promotion_authority": False,
            "publication_authority": False,
        }
        atomic_write(RECEIPT, durable)
        json.dump(response("COMPLETED", durable["transition_id"], 2, None), sys.stdout)
        print()
        return 0

    block = blocker(
        "Public source acquisition did not complete for every READY queue item.",
        "Preserve the RETRY receipt and retry only failed public-source items under the same class and credential boundaries.",
        "process_uap_source_queue.py returns PASS with github_token_used=false and class-valid receipts for every selected READY item",
    )
    durable = {
        "schema": "stegverse.erl-uap-media-worker-receipt/v0.1",
        "task_id": TASK,
        "heartbeat_epoch": epoch,
        "claim_id": claim,
        "fencing_token": fence,
        "state": "BLOCKED",
        "transition_id": "ERL_UAP_SOURCE_RETRY_REQUIRED",
        "runner_returncode": completed.returncode,
        "runner_stdout_tail": completed.stdout[-2000:],
        "runner_stderr_tail": completed.stderr[-2000:],
        "source_execution_receipt": str(execution_receipt) if execution_receipt.exists() else None,
        "github_token_required": False,
        "github_token_used": False,
        "non_tv_tvc_secret_or_token_used": False,
        "research_promotion_authority": False,
        "publication_authority": False,
        "blocker": block,
    }
    atomic_write(RECEIPT, durable)
    json.dump(response("BLOCKED", durable["transition_id"], 1, "ERL_UAP_SOURCE_ACQUISITION_COMPLETE", block), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
