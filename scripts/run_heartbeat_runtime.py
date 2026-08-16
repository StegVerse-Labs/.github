#!/usr/bin/env python3
"""Run the provider-agnostic StegVerse single-heartbeat runtime."""
from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from heartbeat_runtime import ProcessWorkerAdapter
from heartbeat_runtime.engine_v11 import HeartbeatRuntime as HeartbeatRuntimeV11
from heartbeat_runtime.engine_v12 import HeartbeatRuntime as HeartbeatRuntimeV12

SCHEMA = "stegverse.process-worker-adapters/v0.1"
FRAGMENT_SCHEMA = "stegverse.process-worker-adapter-fragment/v0.1"
PROCESS_TYPE = "process_json_v0.1"
BOUND_STATE_TYPE = "process_json_bound_state_v0.1"
LEGACY_HEARTBEAT_SCHEMA = "stegverse.org-heartbeat-state/v1"
SEPARATED_HEARTBEAT_SCHEMA = "stegverse.heartbeat-carrier-runtime-state/v1"
CUTOVER_EPOCH = 29


def _read_registry(path: Path, *, fragment: bool) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = FRAGMENT_SCHEMA if fragment else SCHEMA
    if value.get("schema") != expected:
        raise RuntimeError(f"unsupported process worker adapter {'fragment' if fragment else 'registry'}: {path}")
    adapters = value.get("adapters")
    if not isinstance(adapters, list):
        raise RuntimeError(f"process worker adapters must be a list: {path}")
    return [entry for entry in adapters if isinstance(entry, dict)]


def _adapter_entries(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    registry_path = root / "control" / "process-worker-adapters.json"
    if registry_path.exists():
        entries.extend(_read_registry(registry_path, fragment=False))
    fragment_root = root / "control" / "process-worker-adapters.d"
    if fragment_root.is_dir():
        for path in sorted(fragment_root.glob("*.json")):
            entries.extend(_read_registry(path, fragment=True))
    return entries


def load_adapters(root: Path) -> dict[str, ProcessWorkerAdapter]:
    adapters: dict[str, ProcessWorkerAdapter] = {}
    for entry in _adapter_entries(root):
        if not entry.get("enabled"):
            continue
        adapter_ref = entry["adapter_ref"]
        if adapter_ref in adapters:
            raise RuntimeError(f"duplicate enabled adapter_ref: {adapter_ref}")
        adapter_type = entry.get("type", PROCESS_TYPE)
        if adapter_type not in {PROCESS_TYPE, BOUND_STATE_TYPE}:
            raise RuntimeError(f"unsupported process adapter type: {adapter_type}")
        cwd = Path(entry["cwd"])
        if not cwd.is_absolute():
            cwd = root / cwd

        bound_state_root = None
        bound_state_allowed_paths: tuple[str, ...] = ()
        if adapter_type == BOUND_STATE_TYPE:
            state_value = entry.get("bound_state_root")
            patterns = entry.get("bound_state_allowed_paths")
            if not isinstance(state_value, str) or not state_value:
                raise RuntimeError(f"bound-state adapter missing bound_state_root: {adapter_ref}")
            if not isinstance(patterns, list) or not patterns or any(not isinstance(item, str) or not item for item in patterns):
                raise RuntimeError(f"bound-state adapter missing bound_state_allowed_paths: {adapter_ref}")
            bound_state_root = Path(state_value).expanduser()
            if not bound_state_root.is_absolute():
                raise RuntimeError(f"bound_state_root must resolve to an absolute host path: {adapter_ref}")
            bound_state_allowed_paths = tuple(patterns)

        adapters[adapter_ref] = ProcessWorkerAdapter(
            list(entry["command"]),
            cwd=cwd,
            timeout_seconds=float(entry["timeout_seconds"]),
            env_allowlist=tuple(entry.get("env_allowlist", [])),
            bound_state_root=bound_state_root,
            bound_state_allowed_paths=bound_state_allowed_paths,
        )
    return adapters


def select_runtime(root: Path):
    """Select v12 only at the canonical HB29 cutover or after v12 materialization.

    Arbitrary repository/test fixtures remain on v11. This keeps the compatibility
    API stable while making the production runner the explicit cutover authority
    surface once it observes canonical legacy HB29.
    """
    separated = root / "control" / "heartbeat-carrier-runtime-state.json"
    if separated.is_file():
        state = json.loads(separated.read_text(encoding="utf-8"))
        if state.get("schema") != SEPARATED_HEARTBEAT_SCHEMA:
            raise RuntimeError("separated heartbeat carrier state has unsupported schema")
        return HeartbeatRuntimeV12

    legacy = root / "control" / "heartbeat-state.json"
    if not legacy.is_file():
        return HeartbeatRuntimeV11
    state = json.loads(legacy.read_text(encoding="utf-8"))
    if state.get("schema") == LEGACY_HEARTBEAT_SCHEMA and int(state.get("epoch", -1)) == CUTOVER_EPOCH:
        return HeartbeatRuntimeV12
    return HeartbeatRuntimeV11


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--cycles", type=int, default=1, help="Finite cycle count when --continuous is not set.")
    parser.add_argument("--continuous", action="store_true", help="Run the internal heartbeat loop until terminated by the host/process manager.")
    parser.add_argument("--interval-ms", type=float, default=10.0, help="Internal delay between heartbeat cycles; not a third-party scheduler cadence.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")
    if args.continuous and args.dry_run:
        raise SystemExit("continuous dry-run is prohibited because non-persistent state cannot prove advancing heartbeat epochs")

    root = Path(args.root).resolve()
    runtime_class = select_runtime(root)
    runtime = runtime_class(root, adapters=load_adapters(root))
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    index = 0
    while running and (args.continuous or index < args.cycles):
        result = runtime.cycle(write=not args.dry_run)
        result["selected_runtime"] = f"{runtime_class.__module__}.{runtime_class.__name__}"
        print(json.dumps(result, sort_keys=True), flush=True)
        index += 1
        if running and (args.continuous or index < args.cycles) and args.interval_ms:
            time.sleep(args.interval_ms / 1000.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
