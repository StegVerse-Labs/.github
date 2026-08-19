#!/usr/bin/env python3
"""One-shot sovereign benchmark worker for StegVerse-Healer failure intelligence."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

TASK_ID = "HEALER-FAILURE-MAILBOX-SOVEREIGN-BENCHMARK-001"
WORKER_ID = "healer-failure-mailbox-benchmark-worker"
ROOT_ENV = "STEGVERSE_HEALER_SOURCE_ROOT"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            node = read_json(path)
            if node.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if node.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if node.get("github_token_required") is not False:
                raise RuntimeError("sovereign node may not require GitHub token")
            return path, node
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign Healer benchmark")
    node_path, node = find_node()
    validate_invocation(invocation)
    raw_root = str(os.getenv(ROOT_ENV) or "").strip()
    if not raw_root:
        raise RuntimeError(f"missing non-secret local source locator {ROOT_ENV}")
    root = Path(raw_root).expanduser().resolve()
    benchmark = root / "failure_mailbox" / "benchmark.py"
    engine = root / "failure_mailbox" / "incident_engine.py"
    episode = root / "failure_mailbox" / "episode_analysis.py"
    parser = root / "failure_mailbox" / "github_notification_parser.py"
    for required in (benchmark, engine, episode, parser):
        if not required.is_file():
            raise RuntimeError(f"required Healer benchmark source missing: {required}")

    child = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONPATH": str(root),
    }
    proc = subprocess.run(
        [sys.executable, str(benchmark.relative_to(root))],
        cwd=root,
        env=child,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("Healer failure mailbox benchmark failed: " + (proc.stderr or proc.stdout)[-3000:])
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("benchmark did not emit valid JSON") from exc
    if report.get("result") != "PASS":
        raise RuntimeError("benchmark result is not PASS")
    gate = report.get("packaging_gate") or {}
    if gate.get("deterministic_core_pass") is not True:
        raise RuntimeError("deterministic core benchmark gate did not pass")
    if gate.get("package_release_allowed") is not False:
        raise RuntimeError("benchmark unexpectedly granted package release")

    receipt = {
        "schema": "stegverse.healer.failure-mailbox-benchmark-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "state": "COMPLETE",
        "transition_id": "HEALER_FAILURE_MAILBOX_BENCHMARK_COMPLETE",
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "worker_id": WORKER_ID,
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "source_root": str(root),
        "benchmark_report": report,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_used": False,
        "authority_effect": "VALIDATION_ONLY_NO_NEW_AUTHORITY",
        "heartbeat_effect": False,
    }
    target = Path(child["HOME"]) / ".stegverse" / "receipts" / "healer-failure-mailbox-benchmark-001.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = str(target)
    return receipt


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        receipt = execute(invocation)
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETE",
            "transition_id": "HEALER_FAILURE_MAILBOX_BENCHMARK_COMPLETE",
            "evidence_refs": [receipt["local_receipt_ref"]],
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "non_tv_tvc_secret_or_token_used": False,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "HEALER_FAILURE_MAILBOX_BENCHMARK_BLOCKED",
            "error": str(exc),
            "evidence_refs": [],
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "non_tv_tvc_secret_or_token_used": False,
        }, sort_keys=True))
        return 75


if __name__ == "__main__":
    raise SystemExit(main())
