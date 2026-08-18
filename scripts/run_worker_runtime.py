#!/usr/bin/env python3
"""Run StegVerse worker lifecycle coordination separately from the heartbeat carrier.

When the separated-v12 carrier has not yet been materialized, this entry point
first consumes a valid portable iPhone recovery receipt when one is present; if
none is available it executes the canonical bounded transition producer. If a
carrier is already materialized but the worker control-plane projection is
absent, it reconstructs that observation without advancing the carrier. After
each WorkerCoordinator cycle it refreshes the seven transition release
predicates without advancing the carrier.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
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
DEFAULT_INTERVAL_MS = 10.0
INITIAL_CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CONTROL_PLANE_REL = Path("control/worker-control-plane-coordination.json")
LEGACY_STATE_REL = Path("control/heartbeat-state.json")
TRANSITION_PRODUCER_REL = Path("scripts/advance_heartbeat_transition.py")
TRANSITION_RECEIPT_REL = Path("receipts/heartbeat-transition-continuity/latest.json")
PORTABLE_RECEIPT_DIR_REL = Path("receipts/heartbeat-transition-continuity")
IPHONE_VERIFIER_REL = Path("scripts/verify_iphone_heartbeat_transition_receipt.py")
TRANSITION_REFRESH_REL = Path("scripts/refresh_heartbeat_transition_receipt.py")
CONTROL_PLANE_PROJECTOR_REL = Path("scripts/project_worker_control_plane_from_carrier.py")
SAFE_BOOTSTRAP_ENV = {
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID", "STEGVERSE_HEARTBEAT_ROOT",
}


def _read_registry(path: Path, *, fragment: bool) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = FRAGMENT_SCHEMA if fragment else SCHEMA
    if value.get("schema") != expected:
        kind = "fragment" if fragment else "registry"
        raise RuntimeError(f"unsupported process worker adapter {kind}: {path}")
    adapters = value.get("adapters")
    if not isinstance(adapters, list):
        raise RuntimeError(f"process worker adapters must be a list: {path}")
    return [entry for entry in adapters if isinstance(entry, dict)]


def adapter_entries(root: Path) -> list[dict[str, Any]]:
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
    for entry in adapter_entries(root):
        if not entry.get("enabled"):
            continue
        adapter_ref = entry.get("adapter_ref")
        if not isinstance(adapter_ref, str) or not adapter_ref:
            raise RuntimeError("enabled process adapter missing adapter_ref")
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
            list(entry["command"]), cwd=cwd, timeout_seconds=float(entry["timeout_seconds"]),
            env_allowlist=tuple(entry.get("env_allowlist", [])), bound_state_root=bound_state_root,
            bound_state_allowed_paths=bound_state_allowed_paths,
        )
    return adapters


def _safe_bootstrap_env(values: dict[str, str] | None = None) -> dict[str, str]:
    source = os.environ if values is None else values
    return {name: source[name] for name in SAFE_BOOTSTRAP_ENV if source.get(name)}


def _latest_portable_receipt(root: Path) -> Path | None:
    directory = root / PORTABLE_RECEIPT_DIR_REL
    if not directory.is_dir():
        return None
    candidates = sorted(directory.glob("iphone-portable-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _materialize_portable_receipt(root: Path, receipt: Path, *, env: dict[str, str] | None = None, runner=subprocess.run) -> dict[str, Any]:
    verifier = root / IPHONE_VERIFIER_REL
    carrier = root / INITIAL_CARRIER_REL
    if not verifier.is_file():
        return {"attempted": False, "state": "PORTABLE_VERIFIER_MISSING"}
    completed = runner(
        [sys.executable, str(verifier), str(receipt), "--root", str(root), "--materialize"],
        check=False, capture_output=True, text=True, timeout=90, env=_safe_bootstrap_env(env),
    )
    if completed.returncode == 0 and carrier.is_file():
        value = json.loads(carrier.read_text(encoding="utf-8"))
        if isinstance(value.get("epoch"), int) and value["epoch"] >= 30:
            return {
                "attempted": True,
                "state": "PORTABLE_RECEIPT_MATERIALIZED",
                "carrier_epoch": value["epoch"],
                "portable_receipt_ref": str(receipt.relative_to(root)),
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
            }
    return {
        "attempted": True,
        "state": "PORTABLE_RECEIPT_MATERIALIZATION_FAILED",
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-1000:],
    }


def bootstrap_initial_carrier(root: Path, *, env: dict[str, str] | None = None, runner=subprocess.run) -> dict[str, Any]:
    root = root.resolve()
    carrier_path = root / INITIAL_CARRIER_REL
    legacy_path = root / LEGACY_STATE_REL
    producer_path = root / TRANSITION_PRODUCER_REL
    receipt_path = root / TRANSITION_RECEIPT_REL
    if carrier_path.is_file():
        carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
        epoch = carrier.get("epoch")
        if not isinstance(epoch, int) or epoch < 30:
            raise RuntimeError("existing separated carrier state is below HB30")
        return {"attempted": False, "state": "CARRIER_ALREADY_PRESENT", "carrier_epoch": epoch,
                "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE"}
    if not legacy_path.is_file() or not producer_path.is_file():
        raise RuntimeError("HB29 bootstrap source is incomplete")
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    if int(legacy.get("epoch", -1)) != 29:
        raise RuntimeError("initial separated-v12 bootstrap requires immutable legacy HB29")
    portable = _latest_portable_receipt(root)
    if portable is not None:
        portable_result = _materialize_portable_receipt(root, portable, env=env, runner=runner)
        if portable_result.get("state") == "PORTABLE_RECEIPT_MATERIALIZED":
            return portable_result
    completed = runner(
        [sys.executable, str(producer_path), "--root", str(root), "--receipt-path", str(receipt_path)],
        check=False, capture_output=True, text=True, timeout=90, env=_safe_bootstrap_env(env),
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else {}
    if completed.returncode != 0 or receipt.get("state") != "CARRIER_TRANSITION_COMPLETE" or not carrier_path.is_file():
        reason = receipt.get("reason") or "INITIAL_CARRIER_TRANSITION_FAILED"
        raise RuntimeError(f"HB29->HB30 bootstrap failed closed: {reason}")
    carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
    epoch = carrier.get("epoch")
    if not isinstance(epoch, int) or epoch < 30:
        raise RuntimeError("HB29->HB30 bootstrap did not persist an HB30+ carrier state")
    return {"attempted": True, "state": "CARRIER_TRANSITION_COMPLETE", "carrier_epoch": epoch,
            "receipt_ref": str(TRANSITION_RECEIPT_REL), "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE", "non_tv_tvc_secret_or_token_forwarded": False}


def project_control_plane_if_missing(root: Path, *, runner=subprocess.run) -> dict[str, Any] | None:
    carrier = root / INITIAL_CARRIER_REL
    control = root / CONTROL_PLANE_REL
    script = root / CONTROL_PLANE_PROJECTOR_REL
    if control.is_file() or not carrier.is_file():
        return None
    if not script.is_file():
        raise RuntimeError("HB30 carrier exists without worker control-plane projection source")
    completed = runner(
        [sys.executable, str(script), "--root", str(root)],
        check=False, capture_output=True, text=True, timeout=30, env=_safe_bootstrap_env(),
    )
    if completed.returncode != 0 or not control.is_file():
        raise RuntimeError("failed to project worker control plane from existing carrier")
    value = json.loads(control.read_text(encoding="utf-8"))
    return {"state": "CONTROL_PLANE_PROJECTED", "carrier_generation": (value.get("observed_reference") or {}).get("carrier_generation")}


def refresh_transition_release(root: Path, *, runner=subprocess.run) -> dict[str, Any] | None:
    script = root / TRANSITION_REFRESH_REL
    receipt = root / TRANSITION_RECEIPT_REL
    if not script.is_file() or not receipt.is_file():
        return None
    completed = runner(
        [sys.executable, str(script), "--root", str(root)],
        check=False, capture_output=True, text=True, timeout=30, env=_safe_bootstrap_env(),
    )
    value = json.loads(receipt.read_text(encoding="utf-8"))
    return {"returncode": completed.returncode, "release_state": value.get("release_state"), "all_release_predicates_pass": value.get("all_release_predicates_pass")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--cycles", type=int, default=1, help="Finite worker-runtime cycles when --continuous is not set.")
    parser.add_argument("--continuous", action="store_true", help="Run worker coordination continuously under native StegVerse process supervision.")
    parser.add_argument("--interval-ms", type=float, default=DEFAULT_INTERVAL_MS, help="Delay between worker-runtime ticks. Timers use HB-sized logical units but this loop does not advance or depend on carrier epochs.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")
    if args.continuous and args.dry_run:
        raise SystemExit("continuous dry-run is prohibited because it cannot retain worker timer state")
    root = Path(args.root).resolve()
    bootstrap_result = None
    if not args.dry_run and not (root / INITIAL_CARRIER_REL).is_file():
        bootstrap_result = bootstrap_initial_carrier(root)
    control_projection = None
    if not args.dry_run:
        control_projection = project_control_plane_if_missing(root)
    runtime = WorkerCoordinator(root, adapters=load_adapters(root))
    running = True
    def stop(_signum, _frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    index = 0
    while running and (args.continuous or index < args.cycles):
        result = runtime.cycle(write=not args.dry_run)
        if bootstrap_result is not None:
            result["initial_carrier_bootstrap"] = bootstrap_result
            bootstrap_result = None
        if control_projection is not None:
            result["worker_control_plane_projection"] = control_projection
            control_projection = None
        if not args.dry_run:
            refresh = refresh_transition_release(root)
            if refresh is not None:
                result["transition_release_refresh"] = refresh
        print(json.dumps(result, sort_keys=True), flush=True)
        index += 1
        if running and (args.continuous or index < args.cycles) and args.interval_ms:
            time.sleep(args.interval_ms / 1000.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
