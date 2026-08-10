#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path.cwd().resolve()
UNDERLYING = ROOT / "workers" / "ecosystem_chat_sovereign_route_worker.py"
RECEIPT_ROOT = ROOT / "receipts" / "ecosystem-chat-sovereign-inference"
NORMALIZE_FILES = (
    RECEIPT_ROOT / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json",
    RECEIPT_ROOT / "llm_adapter_sovereign_execution.json",
)
LEGACY = "StegVerse-Labs/TV+TVC"
CURRENT = "TC/TVC"


def sovereign_child_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if value == LEGACY:
        return CURRENT
    return value


def normalize_file(path: Path) -> None:
    if not path.is_file():
        return
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    normalized = normalize(value)
    if normalized != value:
        path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    invocation = sys.stdin.read()
    completed = subprocess.run(
        [sys.executable, str(UNDERLYING)],
        input=invocation,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env=sovereign_child_env(),
    )
    for path in NORMALIZE_FILES:
        normalize_file(path)
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode
    try:
        response = json.loads(completed.stdout)
    except Exception:
        sys.stderr.write(completed.stderr)
        return 7
    response = normalize(response)
    response["credential_authority_model"] = CURRENT
    response["github_token_required"] = False
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
