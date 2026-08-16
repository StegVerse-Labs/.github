#!/usr/bin/env python3
"""Run StegVerse worker lifecycle coordination separately from the heartbeat carrier."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from heartbeat_runtime.worker_runtime import WorkerCoordinator, ProcessWorkerAdapter

SCHEMA = "stegverse.process-worker-adapters/v0.1"
FRAGMENT_SCHEMA = "stegverse.process-worker-adapter-fragment/v0.1"
PROCESS_TYPE = "process_json_v0.1"
BOUND_STATE_TYPE = "process_json_bound_state_v0.1"


def _read_registry(path: Path, *, fragment: bool) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = FRAGMENT_SCHEMA if fragment else SCHEMA
    if value.get("schema") != expected:
        raise RuntimeError(f"unsupported process worker adapter registry: {path}")
    adapters = value.get("adapters")
    if not isinstance(adapters, list):
        raise RuntimeError(f"process worker adapters must be a list: {path}")
    return [entry for entry in adapters if isinstance(entry, dict)]


def load_adapters(root: Path) -> dict[str, ProcessWorkerAdapter]:
    entries: list[dict[str, Any]] = []
    registry_path = root / "control" / "process-worker-adapters.json"
    if registry_path.exists():
        entries.extend(_read_registry(registry_path, fragment=False))
    fragment_root = root / "control" / "process-worker-adapters.d"
    if fragment_root.is_dir():
        for path in sorted(fragment_root.glob("*.json")):
            entries.extend(_read_registry(path, fragment=True))

    adapters: dict[str, ProcessWorkerAdapter] = {}
    for entry in entries:
        if not entry.get("enabled"):
            continue
        adapter_ref = entry["adapter_ref"]
        adapter_type = entry.get("type", PROCESS_TYPE)
        if adapter_type not in {PROCESS_TYPE, BOUND_STATE_TYPE}:
            raise RuntimeError(f"unsupported process adapter type: {adapter_type}")
        cwd = Path(entry["cwd"])
        if not cwd.is_absolute():
            cwd = root / cwd
        bound_state_root = None
        bound_state_allowed_paths: tuple[str, ...] = ()
        if adapter_type == BOUND_STATE_TYPE:
            bound_state_root = Path(entry["bound_state_root"]).expanduser()
            bound_state_allowed_paths = tuple(entry.get("bound_state_allowed_paths", []))
        adapters[adapter_ref] = ProcessWorkerAdapter(
            list(entry["command"]),
            cwd=cwd,
            timeout_seconds=float(entry["timeout_seconds"]),
            env_allowlist=tuple(entry.get("env_allowlist", [])),
            bound_state_root=bound_state_root,
            bound_state_allowed_paths=bound_state_allowed_paths,
        )
    return adapters


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1:
        raise SystemExit("cycles must be >= 1")

    root = Path(args.root).resolve()
    runtime = WorkerCoordinator(root, adapters=load_adapters(root))
    for _ in range(args.cycles):
        result = runtime.cycle(write=not args.dry_run)
        print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
