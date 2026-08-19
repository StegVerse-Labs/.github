#!/usr/bin/env python3
"""One-shot sovereign live-shadow batch worker for StegVerse-Healer failure intelligence."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

TASK_ID = "HEALER-FAILURE-MAILBOX-LIVE-SHADOW-001"
WORKER_ID = "healer-failure-mailbox-shadow-worker"
ROOT_ENV = "STEGVERSE_HEALER_SOURCE_ROOT"
BATCH_ENV = "STEGVERSE_HEALER_SHADOW_BATCH_PATH"
MANIFEST_ENV = "STEGVERSE_HEALER_SHADOW_MANIFEST_PATH"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "HEALER_GH_TOKEN", "HEALER_PAT",
    "GMAIL_TOKEN", "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)


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
    if authority.get("mailbox_credential_available_to_worker") is not False:
        raise RuntimeError("shadow worker may not receive mailbox credentials")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")


def require_locator(name: str) -> Path:
    raw = str(os.getenv(name) or "").strip()
    if not raw:
        raise RuntimeError(f"missing non-secret local locator {name}")
    return Path(raw).expanduser().resolve()


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign Healer shadow batches")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for shadow worker: " + ",".join(sorted(present)))

    node_path, node = find_node()
    validate_invocation(invocation)
    root = require_locator(ROOT_ENV)
    batch = require_locator(BATCH_ENV)
    manifest_path = require_locator(MANIFEST_ENV)
    if not batch.is_file():
        raise RuntimeError("materialized shadow batch is missing")
    if not manifest_path.is_file():
        raise RuntimeError("materialized shadow manifest is missing")

    manifest = read_json(manifest_path)
    required_manifest = ("batch_id", "source_count", "window_start", "window_end", "source_ref")
    missing = [key for key in required_manifest if key not in manifest]
    if missing:
        raise RuntimeError("shadow manifest missing fields: " + ",".join(missing))
    if manifest.get("mailbox_mutated") is not False:
        raise RuntimeError("shadow manifest must attest mailbox_mutated=false")
    if manifest.get("credential_authority") != "TV/TVC":
        raise RuntimeError("shadow manifest credential authority must be TV/TVC")

    shadow = root / "failure_mailbox" / "shadow.py"
    for required in (
        shadow,
        root / "failure_mailbox" / "backfill.py",
        root / "failure_mailbox" / "coverage_monitor.py",
        root / "failure_mailbox" / "incident_engine.py",
    ):
        if not required.is_file():
            raise RuntimeError(f"required Healer shadow source missing: {required}")

    state_root = Path.home() / ".stegverse" / "state" / "healer-failure-mailbox"
    receipt_root = Path.home() / ".stegverse" / "receipts"
    state_root.mkdir(parents=True, exist_ok=True)
    receipt_root.mkdir(parents=True, exist_ok=True)
    ledger = state_root / "ledger.json"
    state = state_root / "shadow-state.json"
    report_path = state_root / f"shadow-{manifest['batch_id']}.report.json"

    child = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONPATH": str(root),
    }
    cmd = [
        sys.executable,
        str(shadow.relative_to(root)),
        "--input", str(batch),
        "--ledger", str(ledger),
        "--state", str(state),
        "--report", str(report_path),
        "--batch-id", str(manifest["batch_id"]),
        "--source-count", str(int(manifest["source_count"])),
        "--window-start", str(manifest["window_start"]),
        "--window-end", str(manifest["window_end"]),
        "--source-ref", str(manifest["source_ref"]),
    ]
    proc = subprocess.run(cmd, cwd=root, env=child, text=True, capture_output=True, timeout=180, check=False)
    if not report_path.is_file():
        raise RuntimeError("shadow processor did not persist a batch report: " + (proc.stderr or proc.stdout)[-3000:])
    report = read_json(report_path)
    if report.get("result") not in {"PASS", "DUPLICATE_BATCH_NOOP"}:
        coverage_state = ((report.get("coverage") or {}).get("state"))
        raise RuntimeError(f"shadow batch requires coverage action: {coverage_state or report.get('result')}")
    if report.get("mailbox_mutated") is not False:
        raise RuntimeError("shadow report violated mailbox mutation boundary")
    if report.get("authority_effect") is not False or report.get("heartbeat_effect") is not False:
        raise RuntimeError("shadow report violated authority/heartbeat boundary")

    receipt = {
        "schema": "stegverse.healer.failure-mailbox-shadow-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "state": "COMPLETE",
        "transition_id": "HEALER_FAILURE_MAILBOX_SHADOW_BATCH_COMPLETE",
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "worker_id": WORKER_ID,
        "batch_id": manifest["batch_id"],
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "source_root": str(root),
        "batch_ref": str(batch),
        "manifest_ref": str(manifest_path),
        "shadow_report_ref": str(report_path),
        "shadow_result": report.get("result"),
        "coverage_state": ((report.get("coverage") or {}).get("state")),
        "credential_authority": "TV/TVC",
        "mailbox_credential_available_to_worker": False,
        "non_tv_tvc_secret_or_token_used": False,
        "mailbox_mutated": False,
        "authority_effect": "OBSERVATION_ONLY_NO_NEW_AUTHORITY",
        "heartbeat_effect": False,
    }
    target = receipt_root / f"healer-failure-mailbox-shadow-{manifest['batch_id']}.json"
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
            "transition_id": "HEALER_FAILURE_MAILBOX_SHADOW_BATCH_COMPLETE",
            "evidence_refs": [receipt["local_receipt_ref"]],
            "credential_authority": "TV/TVC",
            "mailbox_credential_available_to_worker": False,
            "non_tv_tvc_secret_or_token_used": False,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "HEALER_FAILURE_MAILBOX_SHADOW_BATCH_BLOCKED",
            "error": str(exc),
            "evidence_refs": [],
            "credential_authority": "TV/TVC",
            "mailbox_credential_available_to_worker": False,
            "non_tv_tvc_secret_or_token_used": False,
        }, sort_keys=True))
        return 75


if __name__ == "__main__":
    raise SystemExit(main())
