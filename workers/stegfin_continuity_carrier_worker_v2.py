#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

TASK_ID = "STEGFIN-CONTINUITY-CARRIER-007"
ROOT = Path.cwd().resolve()
OLD_WORKER = ROOT / "workers" / "stegfin_continuity_carrier_worker.py"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("receipt_sha256", None)
    return "sha256:" + hashlib.sha256(canonical(material)).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def release_owned_claim(worker_instance: str, transition_id: str, *, home: Path | None = None) -> bool:
    base = home or Path.home()
    state_file = base / ".stegverse" / "continuity" / "claims" / f"{TASK_ID}.json"
    if not state_file.is_file():
        return False
    try:
        claim = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(claim, dict):
        return False
    if claim.get("task_id") != TASK_ID or claim.get("state") != "ACTIVE":
        return False
    if str(claim.get("carrier_id") or "") != worker_instance:
        return False
    claim["state"] = "RELEASED"
    claim["released_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    claim["release_reason"] = transition_id or "TERMINAL_WORKER_OUTCOME"
    claim["receipt_sha256"] = digest(claim)
    atomic_write(state_file, claim)
    return True


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    worker_instance = str(task.get("worker_instance_id") or task.get("claim_id") or "stegfin-continuity-worker")
    completed = subprocess.run(
        [sys.executable, str(OLD_WORKER)],
        cwd=ROOT,
        input=json.dumps(invocation, sort_keys=True) + "\n",
        text=True,
        capture_output=True,
        timeout=480,
        check=False,
    )
    stdout = completed.stdout or ""
    terminal = None
    try:
        terminal = json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else None
    except Exception:
        terminal = None
    if isinstance(terminal, dict) and terminal.get("state") in {"BLOCKED", "COMPLETE", "FAILED", "REVIEW_REQUIRED"}:
        release_owned_claim(worker_instance, str(terminal.get("transition_id") or terminal.get("state")))
    if stdout:
        sys.stdout.write(stdout)
        if not stdout.endswith("\n"):
            sys.stdout.write("\n")
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
