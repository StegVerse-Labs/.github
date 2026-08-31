#!/usr/bin/env python3
"""Run StegVerse worker lifecycle coordination separately from the heartbeat carrier.

When the separated-v12 carrier has not yet been materialized, this entry point
uses the canonical StegVerse-native HB29 -> HB30 producer as the primary path
under the exact retained G18 authority. Verified portable iPhone recovery
receipts remain a fallback path, including explicitly identified third-party
hosted fallback, never a primary provider. Initial-carrier production is
serialized with the worker-runtime lock so concurrent starts cannot race the
cutover. If a carrier is already materialized but the worker control-plane
projection is absent, that observation is reconstructed without advancing the
carrier. After each WorkerCoordinator cycle the transition release predicates
are refreshed without advancing the carrier.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from heartbeat_runtime.worker_runtime import WorkerCoordinator, ProcessWorkerAdapter
from heartbeat_runtime.independent_oscillator import current_reference
from heartbeat_runtime.machine_continuation import DEFAULT_CONTINUATION_QUANTA, build_continuation_trigger
from dispatch_resident_execution_requests import dispatch as dispatch_resident_requests

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
RENDEZVOUS_CONSUMER_REL = Path("scripts/consume_resident_rendezvous.py")
RENDEZVOUS_RECEIPT_REL = Path("receipts/sovereign-host/resident-rendezvous-consumption.latest.json")
RENDEZVOUS_POLL_INTERVAL_SECONDS = 30.0
CONTROL_PLANE_PROJECTOR_REL = Path("scripts/project_worker_control_plane_from_carrier.py")
MACHINE_CONTINUATION_STATE_REL = Path("control/hb-machine-continuation-state.json")
MACHINE_CONTINUATION_RECEIPT_REL = Path("receipts/sovereign-host/hb-machine-continuation.latest.json")
G18_TASK_ID = "SHWP-DURABLE-RUNTIME-ACTIVATION"
G18_WORKER_ID = "sovereign-runtime-activation-worker"
G18_CLAIM_ID = "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18"
G18_FENCE = 18
G18_POLICY = "shwp-single-hb-v0.4-sovereign-solution-execution"
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
SAFE_BOOTSTRAP_ENV = {
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_RESIDENT_RENDEZVOUS_URL", "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF",
    *HOSTED_ENV,
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


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def _safe_bootstrap_env(values: dict[str, str] | None = None) -> dict[str, str]:
    source = os.environ if values is None else values
    return {name: source[name] for name in SAFE_BOOTSTRAP_ENV if source.get(name)}


def _fallback_origin(values: dict[str, str] | None = None) -> str | None:
    source = os.environ if values is None else values
    active = [name for name in HOSTED_ENV if _truthy(source.get(name))]
    return active[0] if active else None


def _exact_g18_task(runtime: WorkerCoordinator) -> dict[str, Any]:
    registry = runtime._load(runtime.registry_path)
    matches = [task for task in registry.get("tasks", []) if task.get("task_id") == G18_TASK_ID]
    if len(matches) != 1:
        raise RuntimeError("initial carrier bootstrap requires exactly one canonical G18 task")
    task = matches[0]
    timing = task.get("heartbeat_timing") or {}
    checks = {
        "state": task.get("state") in {"ACTIVE", "BLOCKED"},
        "executor_binding": task.get("executor_binding") == "BOUND",
        "worker_id": task.get("worker_id") == G18_WORKER_ID,
        "claim_id": task.get("claim_id") == G18_CLAIM_ID,
        "fencing_token": timing.get("fencing_token") == G18_FENCE,
        "policy": task.get("authorized_policy_version") == G18_POLICY,
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    if failed:
        raise RuntimeError(f"initial carrier bootstrap G18 invariant mismatch: {','.join(failed)}")
    handoff = runtime._handoff(task)
    if not runtime._execution_authorized(handoff):
        raise RuntimeError("initial carrier bootstrap requires execution-authorized G18 handoff")
    return task


def _existing_carrier_result(carrier_path: Path) -> dict[str, Any]:
    carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
    epoch = carrier.get("epoch")
    if not isinstance(epoch, int) or epoch < 30:
        raise RuntimeError("existing separated carrier state is below HB30")
    return {
        "attempted": False,
        "state": "CARRIER_ALREADY_PRESENT",
        "carrier_epoch": epoch,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }


def _portable_receipts(root: Path) -> list[Path]:
    directory = root / PORTABLE_RECEIPT_DIR_REL
    if not directory.is_dir():
        return []
    ranked: list[tuple[datetime, Path]] = []
    for path in directory.glob("iphone-portable-*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            stamp = str(value.get("executed_at") or "")
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except Exception:
            continue
        ranked.append((parsed, path))
    ranked.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    return [path for _, path in ranked]


def _materialize_portable_receipt(
    root: Path,
    receipt: Path,
    *,
    env: dict[str, str] | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    verifier = root / IPHONE_VERIFIER_REL
    carrier = root / INITIAL_CARRIER_REL
    if not verifier.is_file():
        return {"attempted": False, "state": "PORTABLE_VERIFIER_MISSING"}
    source_env = os.environ if env is None else env
    fallback = _fallback_origin(source_env)
    command = [sys.executable, str(verifier), str(receipt), "--root", str(root), "--materialize"]
    if fallback:
        command.extend(["--allow-third-party-fallback", fallback])
    completed = runner(
        command, check=False, capture_output=True, text=True, timeout=90, env=_safe_bootstrap_env(source_env),
    )
    if completed.returncode == 0 and carrier.is_file():
        value = json.loads(carrier.read_text(encoding="utf-8"))
        if value.get("epoch") == 30:
            return {
                "attempted": True,
                "state": "PORTABLE_RECEIPT_MATERIALIZED",
                "carrier_epoch": 30,
                "portable_receipt_ref": str(receipt.relative_to(root)),
                "execution_provider": fallback or "STEGVERSE_NATIVE",
                "provider_role": "FALLBACK_ONLY",
                "third_party_required_dependency": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
            }
    return {
        "attempted": True,
        "state": "PORTABLE_RECEIPT_MATERIALIZATION_FAILED",
        "portable_receipt_ref": str(receipt.relative_to(root)),
        "execution_provider": fallback or "STEGVERSE_NATIVE",
        "provider_role": "FALLBACK_ONLY",
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-1000:],
    }


def _try_portable_fallback(root: Path, *, env: dict[str, str] | None, runner) -> dict[str, Any] | None:
    rejected: list[dict[str, Any]] = []
    for portable in _portable_receipts(root):
        result = _materialize_portable_receipt(root, portable, env=env, runner=runner)
        if result.get("state") == "PORTABLE_RECEIPT_MATERIALIZED":
            result["rejected_newer_or_invalid_receipts"] = rejected
            return result
        rejected.append({
            "portable_receipt_ref": result.get("portable_receipt_ref"),
            "returncode": result.get("returncode"),
            "state": result.get("state"),
        })
    return None


def bootstrap_initial_carrier(
    root: Path,
    runtime: WorkerCoordinator,
    *,
    env: dict[str, str] | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    """Materialize exactly the first separated carrier under existing G18 authority."""
    root = root.resolve()
    carrier_path = root / INITIAL_CARRIER_REL
    legacy_path = root / LEGACY_STATE_REL
    producer_path = root / TRANSITION_PRODUCER_REL
    receipt_path = root / TRANSITION_RECEIPT_REL
    source_env = os.environ if env is None else env

    runtime._acquire()
    try:
        if carrier_path.is_file():
            return _existing_carrier_result(carrier_path)
        if not legacy_path.is_file() or not producer_path.is_file():
            raise RuntimeError("HB29 bootstrap source is incomplete")
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        if (
            legacy.get("schema") != "stegverse.org-heartbeat-state/v1"
            or int(legacy.get("epoch", -1)) != 29
            or int(legacy.get("generation", -1)) != 29
        ):
            raise RuntimeError("initial separated-v12 bootstrap requires immutable legacy HB29/generation29")

        task = _exact_g18_task(runtime)
        fallback_origin = _fallback_origin(source_env)

        if not fallback_origin:
            completed = runner(
                [sys.executable, str(producer_path), "--root", str(root), "--receipt-path", str(receipt_path)],
                check=False, capture_output=True, text=True, timeout=90, env=_safe_bootstrap_env(source_env),
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else {}
            if (
                completed.returncode == 0
                and receipt.get("state") == "CARRIER_TRANSITION_COMPLETE"
                and receipt.get("carrier_epoch_before") == 29
                and receipt.get("carrier_epoch_after") == 30
                and carrier_path.is_file()
            ):
                carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
                if carrier.get("epoch") == 30 and isinstance(carrier.get("generation"), int) and carrier["generation"] >= 30:
                    return {
                        "attempted": True,
                        "state": "CARRIER_TRANSITION_COMPLETE",
                        "carrier_epoch": 30,
                        "carrier_generation": carrier["generation"],
                        "receipt_ref": str(TRANSITION_RECEIPT_REL),
                        "execution_provider": "STEGVERSE_NATIVE",
                        "provider_role": "PRIMARY",
                        "task_id": task.get("task_id"),
                        "worker_id": task.get("worker_id"),
                        "claim_id": task.get("claim_id"),
                        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
                        "existing_g18_authority_reused": True,
                        "new_claim_or_fence_created": False,
                        "serialized_under_worker_runtime_lock": True,
                        "credential_authority": "TV/TVC",
                        "credential_requirement": "NONE",
                        "github_token_runtime_authority": "NONE",
                        "non_tv_tvc_secret_or_token_forwarded": False,
                        "third_party_runtime_required": False,
                        "authority_effect": "EXISTING_G18_AUTHORITY_ONLY",
                    }

        fallback = _try_portable_fallback(root, env=source_env, runner=runner)
        if fallback is not None:
            fallback.update({
                "task_id": task.get("task_id"),
                "claim_id": task.get("claim_id"),
                "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
                "existing_g18_authority_reused": True,
                "new_claim_or_fence_created": False,
                "serialized_under_worker_runtime_lock": True,
                "authority_effect": "EXISTING_G18_AUTHORITY_ONLY",
            })
            return fallback

        if fallback_origin:
            raise RuntimeError("third-party hosted execution is FALLBACK_ONLY and no verified portable receipt could materialize HB30")
        reason = "INITIAL_CARRIER_TRANSITION_FAILED"
        if receipt_path.is_file():
            try:
                reason = json.loads(receipt_path.read_text(encoding="utf-8")).get("reason") or reason
            except Exception:
                pass
        raise RuntimeError(f"HB29->HB30 bootstrap failed closed: {reason}")
    finally:
        runtime._release_lock()


def project_control_plane_if_missing(root: Path, *, runner=subprocess.run) -> dict[str, Any] | None:
    carrier = root / INITIAL_CARRIER_REL
    control = root / CONTROL_PLANE_REL
    script = root / CONTROL_PLANE_PROJECTOR_REL
    if control.is_file() or not carrier.is_file():
        return None
    if not script.is_file():
        raise RuntimeError("HB30 carrier exists without worker control-plane projection source")
    completed = runner(
        [sys.executable, str(script), "--root", str(root)], check=False, capture_output=True, text=True,
        timeout=30, env=_safe_bootstrap_env(),
    )
    if completed.returncode != 0 or not control.is_file():
        raise RuntimeError("failed to project worker control plane from existing carrier")
    value = json.loads(control.read_text(encoding="utf-8"))
    carrier_value = json.loads(carrier.read_text(encoding="utf-8"))
    observed = value.get("observed_reference") or {}
    if observed.get("carrier_generation") != carrier_value.get("generation") or observed.get("reference_frame") != carrier_value.get("reference_frame"):
        raise RuntimeError("worker control-plane projection does not match current carrier")
    return {"state": "CONTROL_PLANE_PROJECTED", "carrier_generation": observed.get("carrier_generation"), "reference_frame": observed.get("reference_frame")}


def poll_resident_rendezvous(
    root: Path,
    *,
    runner=subprocess.run,
    env: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Poll the non-authorizing Service Gateway request carrier once.

    The rendezvous consumer may materialize one already-admitted local resident
    request and invoke the existing exact consumer. The Gateway request itself
    grants no claim, fence, credential, or execution authority.
    """
    values = dict(os.environ if env is None else env)
    base_url = str(values.get("STEGVERSE_RESIDENT_RENDEZVOUS_URL") or "").strip()
    node_ref = str(values.get("STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF") or "").strip()
    if not base_url or not node_ref:
        return None
    script = root / RENDEZVOUS_CONSUMER_REL
    if not script.is_file():
        return {
            "state": "CONSUMER_NOT_MATERIALIZED",
            "runtime_execution_attempted": False,
            "gateway_execution_authority": "NONE",
            "authority_effect": "NONE",
        }
    completed = runner(
        [
            sys.executable,
            str(script),
            "--runtime-root", str(root),
            "--source-root", str(root),
            "--base-url", base_url,
            "--node-ref", node_ref,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=1800,
        env=_safe_bootstrap_env(values),
    )
    receipt_path = root / RENDEZVOUS_RECEIPT_REL
    receipt = None
    if receipt_path.is_file():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception:
            receipt = None
    return {
        "state": (
            receipt.get("state")
            if isinstance(receipt, dict)
            else ("POLL_COMPLETE" if completed.returncode == 0 else "POLL_FAILED")
        ),
        "returncode": completed.returncode,
        "receipt": receipt,
        "gateway_execution_authority": "NONE",
        "worker_coordinator_remains_execution_admission_authority": True,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_REQUEST_CARRIER_ONLY",
    }


def maybe_dispatch_machine_continuation(
    root: Path,
    *,
    env: dict[str, str] | None = None,
    period_quanta: int = DEFAULT_CONTINUATION_QUANTA,
) -> dict[str, Any]:
    """Dispatch already-registered resident requests once per HB-derived window.

    The trigger is synchronization metadata only. Each request consumer and the
    WorkerCoordinator retain their own admission/claim/fence/credential authority.
    """
    state_path = root / MACHINE_CONTINUATION_STATE_REL
    prior: dict[str, Any] = {}
    if state_path.is_file():
        try:
            value = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                prior = value
        except Exception:
            prior = {}
    last_window = prior.get("last_consumed_window_id")
    if not isinstance(last_window, int):
        last_window = None

    reference = current_reference(now_ns=time.time_ns())
    trigger = build_continuation_trigger(
        int(reference["epoch"]),
        last_consumed_window_id=last_window,
        period_quanta=period_quanta,
    )
    receipt: dict[str, Any] = {
        "schema": "stegverse.hb-machine-continuation-receipt/v1",
        "trigger": trigger,
        "dispatch_attempted": False,
        "dispatch_result": None,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "continuation_trigger_grants_execution_authority": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    if trigger["continuation_due"]:
        result = dispatch_resident_requests(root, root, env=env)
        receipt["dispatch_attempted"] = True
        receipt["dispatch_result"] = result
        window_id = int(trigger["window"]["window_id"])
        state = {
            "schema": "stegverse.hb-machine-continuation-state/v1",
            "last_consumed_window_id": window_id,
            "last_reference_epoch": int(reference["epoch"]),
            "last_reference_heartbeat_id": reference["heartbeat_id"],
            "last_dispatch_state": result.get("state"),
            "heartbeat_progression_effect": "NONE",
            "authority_effect": "NONE_TRIGGER_ONLY",
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt_path = root / MACHINE_CONTINUATION_RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def refresh_transition_release(root: Path, *, runner=subprocess.run) -> dict[str, Any] | None:
    script = root / TRANSITION_REFRESH_REL
    receipt = root / TRANSITION_RECEIPT_REL
    if not script.is_file() or not receipt.is_file():
        return None
    completed = runner(
        [sys.executable, str(script), "--root", str(root)], check=False, capture_output=True, text=True,
        timeout=30, env=_safe_bootstrap_env(),
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
    parser.add_argument("--task-id", help="Execute exactly one independently admitted task without ticking unrelated workers or consuming carrier assignment packets.")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")
    if args.continuous and args.dry_run:
        raise SystemExit("continuous dry-run is prohibited because it cannot retain worker timer state")
    if args.task_id and (args.continuous or args.cycles != 1):
        raise SystemExit("--task-id requires exactly one non-continuous worker-runtime cycle")
    root = Path(args.root).resolve()
    runtime = WorkerCoordinator(root, adapters=load_adapters(root))
    bootstrap_result = None
    if args.task_id and not (root / INITIAL_CARRIER_REL).is_file():
        raise SystemExit("targeted independent execution requires an existing separated carrier reference; it may not bootstrap G18")
    if not args.task_id and not args.dry_run and not (root / INITIAL_CARRIER_REL).is_file():
        bootstrap_result = bootstrap_initial_carrier(root, runtime)
    control_projection = None
    if not args.task_id and not args.dry_run:
        control_projection = project_control_plane_if_missing(root)
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    index = 0
    next_rendezvous_poll = 0.0
    while running and (args.continuous or index < args.cycles):
        rendezvous_result = None
        if not args.task_id and not args.dry_run and time.monotonic() >= next_rendezvous_poll:
            rendezvous_result = poll_resident_rendezvous(root)
            next_rendezvous_poll = time.monotonic() + RENDEZVOUS_POLL_INTERVAL_SECONDS
        result = runtime.cycle(write=not args.dry_run, target_task_id=args.task_id)
        if not args.task_id and not args.dry_run:
            result["hb_machine_continuation"] = maybe_dispatch_machine_continuation(root, env=os.environ)
        if rendezvous_result is not None:
            result["resident_rendezvous"] = rendezvous_result
        if bootstrap_result is not None:
            result["initial_carrier_bootstrap"] = bootstrap_result
            bootstrap_result = None
        if control_projection is not None:
            result["worker_control_plane_projection"] = control_projection
            control_projection = None
        if not args.task_id and not args.dry_run:
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
