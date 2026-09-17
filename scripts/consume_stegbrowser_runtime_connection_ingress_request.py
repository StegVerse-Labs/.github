#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/stegbrowser-runtime-connection-ingress-001.json")
TASK_ID = "STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001"
PARENT_TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
MANIFEST_REF = "control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json"
OBS_SCHEMA = "stegverse.intr-runtime-connection-transition-observation/v1"
SOURCE_REFRESH_RT = "RT-SOVEREIGN-SOURCE-REFRESH-001"
PROTOCOL_RT = "RT-INTR-PROTOCOL-ESTABLISH-001"
STEGBROWSER_RT = "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001"
CANONICAL_NODE_SELECTOR = "CANONICAL_REGISTERED_STEGVERSE_NODE_BINDING"
NODE_PATH_ENV = "STEGVERSE_NODE_GENESIS_RECEIPT"
MANIFEST_RUNNER_REL = Path("scripts/run_stegbrowser_manifest_bound_runtime.py")
MANIFEST_INGRESS_REL = Path("workers/stegbrowser_manifest_intr_ingress.py")
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_request(value: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv_task_vector": COSV,
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "entrypoint": "scripts/consume_stegbrowser_runtime_connection_ingress_request.py",
        "manifest_ref": MANIFEST_REF,
        "node_binding_selector": CANONICAL_NODE_SELECTOR,
        "canonical_node_receipt_path_parameter": "node_genesis_receipt",
        "canonical_node_receipt_path_environment": NODE_PATH_ENV,
        "round_trip_1_payload_processing_allowed": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        require(value.get(key) == wanted, f"request_{key}_mismatch")


def load_shared_ingress() -> Any:
    installer = ROOT / "scripts/install_canonical_work_universal_intr_route.py"
    subprocess.run([sys.executable, str(installer)], cwd=str(ROOT), check=True)
    subprocess.run([sys.executable, str(installer), "--check"], cwd=str(ROOT), check=True)
    path = ROOT / "workers/universal_intr_profiled_ingress.py"
    spec = importlib.util.spec_from_file_location("stegbrowser_a1_shared_intr", path)
    require(spec is not None and spec.loader is not None, "shared_intr_import_spec_missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observe_live_profile(module: Any, runtime_root: Path) -> dict[str, Any]:
    server = module.Server(("127.0.0.1", 0), runtime_root, 0)
    host, port = server.server_address
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://{host}:{port}{module.PROFILE_PATH}", timeout=5) as response:
            require(int(response.status) == 200, "intr_profile_http_status_invalid")
            profile = json.loads(response.read().decode("utf-8"))
    finally:
        thread.join(timeout=5)
        server.server_close()
    require(isinstance(profile, dict), "intr_profile_object_required")
    require(profile.get("schema") == "stegverse.universal-intr-profiled-ingress/v1", "intr_profile_schema_mismatch")
    require(profile.get("state") == "ACTIVE_SOVEREIGN_INTR_INGRESS", "intr_profile_not_active")
    require(profile.get("protocol") == "InTr", "intr_protocol_mismatch")
    return profile


def resolve_module() -> Any:
    path = ROOT / "scripts/resolve_stegbrowser_runtime_connection_transition.py"
    spec = importlib.util.spec_from_file_location("stegbrowser_a1_resolver", path)
    require(spec is not None and spec.loader is not None, "resolver_import_spec_missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def refreshable_for_invocation(source_root: Path, runtime_root: Path, profile: dict[str, Any]) -> bool:
    return bool(
        profile.get("event_triggered") is True
        and source_root.resolve() != runtime_root.resolve()
        and (source_root / "source-bundles/reusable-task-registry.d/RT-SOVEREIGN-SOURCE-REFRESH-001.json").is_file()
    )


def exact_manifest_protocol_resolved(source_root: Path, profile: dict[str, Any]) -> bool:
    return bool(
        profile.get("protocol") == "InTr"
        and profile.get("state") == "ACTIVE_SOVEREIGN_INTR_INGRESS"
        and (source_root / MANIFEST_INGRESS_REL).is_file()
    )


def run_source_refresh(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    script = ROOT / "scripts/refresh_sovereign_worker_runtime_source_reusable.py"
    env = dict(os.environ)
    env["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = json.dumps({
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "callable": True,
        "refreshable": True,
        "transition_ref": "receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json",
    }, sort_keys=True)
    completed = subprocess.run([sys.executable, str(script)], cwd=str(ROOT), env=env, text=True, capture_output=True, check=True)
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    require(lines, "source_refresh_receipt_missing")
    return json.loads(lines[-1])


def resolve_registered_node_receipt(request: dict[str, Any]) -> Path:
    require(request.get("node_binding_selector") == CANONICAL_NODE_SELECTOR, "canonical_node_selector_mismatch")
    raw = str(os.environ.get(NODE_PATH_ENV) or "").strip()
    require(raw, "canonical_registered_stegverse_node_receipt_1_not_available")
    path = Path(raw).expanduser().resolve()
    require(path.is_file(), "canonical_registered_stegverse_node_receipt_1_path_missing")
    return path


def run_canonical_node_bound_invocation(source_root: Path, runtime_root: Path, node_receipt: Path) -> dict[str, Any]:
    runner = source_root / MANIFEST_RUNNER_REL
    require(runner.is_file(), "canonical_stegbrowser_manifest_runner_missing")
    stegos_raw = str(os.environ.get("STEGVERSE_STEGOS_SOURCE_ROOT") or "").strip()
    stegos_root = Path(stegos_raw).expanduser().resolve() if stegos_raw else (source_root.parent / "StegOS").resolve()
    require((stegos_root / "stegos/network_manifold.py").is_file(), "canonical_stegos_node_validator_missing")
    params: dict[str, Any] = {
        "source_root": str(source_root),
        "sovereign_source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "stegos_source_root": str(stegos_root),
        "node_genesis_receipt": str(node_receipt),
    }
    runtime_base = str(os.environ.get("STEGVERSE_EPHEMERAL_RUNTIME_BASE") or "").strip()
    if runtime_base:
        params["runtime_base"] = runtime_base
    env = dict(os.environ)
    env["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = json.dumps(params, sort_keys=True, separators=(",", ":"))
    completed = subprocess.run([sys.executable, str(runner)], cwd=str(source_root), env=env, text=True, capture_output=True, check=False, timeout=1800)
    boundary_path = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
    boundary = load(boundary_path) if boundary_path.is_file() else {}
    return {
        "runner_returncode": completed.returncode,
        "runner_stdout_tail": completed.stdout[-2000:],
        "runner_stderr_tail": completed.stderr[-1200:],
        "boundary_ref": str(boundary_path),
        "boundary": boundary,
    }


def main() -> int:
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()

    active_hosted = [name for name in HOSTED if truthy(os.environ.get(name))]
    require(not active_hosted, "hosted_environment_forbidden:" + ",".join(active_hosted))

    source_root = args.source_root.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    request = load(source_root / REQUEST_REL)
    validate_request(request)
    manifest = load(source_root / MANIFEST_REF)
    require(manifest.get("task_id") == PARENT_TASK_ID, "manifest_parent_goal_mismatch")
    require(str(manifest.get("cosv_task_vector")) == COSV, "manifest_cosv_mismatch")

    shared_intr = load_shared_ingress()
    profile = observe_live_profile(shared_intr, runtime_root)
    profiles = profile.get("profiles") or []
    callable_value = bool(
        profile.get("state") == "ACTIVE_SOVEREIGN_INTR_INGRESS"
        and profile.get("protocol") == "InTr"
        and profile.get("event_triggered") is True
        and "CanonicalWork:Coordination" in profiles
    )
    protocol_resolved = bool(callable_value and exact_manifest_protocol_resolved(source_root, profile))
    refreshable_value = bool(callable_value and refreshable_for_invocation(source_root, runtime_root, profile))

    observation = {
        "schema": OBS_SCHEMA,
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv": COSV,
        "manifest_ref": MANIFEST_REF,
        "authority_owner": "Interlock/InTr",
        "authority_effect": "OBSERVATION_ONLY",
        "observation_source": "LIVE_SHARED_UNIVERSAL_INTR_PROFILE_PLUS_ALREADY_LOCAL_EXACT_MANIFEST_ADAPTER",
        "callable": callable_value,
        "refreshable": refreshable_value,
        "applicable_protocol_resolved": protocol_resolved,
        "always_on_runtime_source_assumed": False,
        "second_user_operated_device_required": False,
    }
    observation_path = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json"
    atomic_json(observation_path, observation)

    resolver = resolve_module()
    resolution = resolver.resolve(observation)
    resolution_path = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-connection-resolution.latest.json"
    atomic_json(resolution_path, resolution)
    selected = list(resolution.get("selected_reusable_tasks", []))

    refresh_receipt = None
    if SOURCE_REFRESH_RT in selected:
        refresh_receipt = run_source_refresh(source_root, runtime_root)
    execution_surface_materialized = bool(callable_value and (not refreshable_value or refresh_receipt is not None))

    invocation = None
    node_receipt_ref = None
    node_resolution_error = None
    if callable_value and protocol_resolved and execution_surface_materialized and PROTOCOL_RT not in selected:
        try:
            node_receipt = resolve_registered_node_receipt(request)
        except RuntimeError as exc:
            node_resolution_error = str(exc)
        else:
            node_receipt_ref = str(node_receipt)
            if STEGBROWSER_RT not in selected:
                selected.append(STEGBROWSER_RT)
            invocation = run_canonical_node_bound_invocation(source_root, runtime_root, node_receipt)

    boundary = invocation.get("boundary", {}) if isinstance(invocation, dict) else {}
    projection = boundary.get("runtime_ingress_projection") if isinstance(boundary, dict) else {}
    a4_observed = bool(
        boundary.get("authentic_intr_ingress_observed") is True
        and projection.get("authentic_intr_ingress_observed") is True
        and projection.get("organization_local_intr_ingress_receipt_verified") is True
        and projection.get("node_interlock_lease_runtime_correlation_verified") is True
    )
    claim_id = projection.get("claim_ref") if isinstance(projection, dict) else None
    fence = projection.get("fence_ref") if isinstance(projection, dict) else None
    claim_observed = bool(isinstance(claim_id, str) and isinstance(fence, int) and claim_id.endswith(f"-G{fence}"))
    binding = boundary.get("node_interlock_runtime_binding") if isinstance(boundary, dict) else {}
    a1_observed = bool(
        isinstance(binding, dict)
        and node_receipt_ref
        and binding.get("node_id")
        and binding.get("interlock_id")
        and binding.get("registration_receipt_sha256")
    )
    a2_1_observed = bool(a1_observed and binding.get("lease_id") and binding.get("state_root_binding"))
    a2_2_observed = bool(a1_observed and binding.get("runtime_class") == "EVENT_EPHEMERAL" and binding.get("runtime_id"))

    if a4_observed and claim_observed and a2_1_observed and a2_2_observed:
        state = "A1_A2_A2_1_A2_2_A3_A4_OBSERVED"
    elif a1_observed:
        state = "A1_OBSERVED_CANONICAL_INVOCATION_PENDING_OR_BOUNDARY"
    elif node_resolution_error:
        state = "A1_NOT_OBSERVED_REGISTERED_NODE_RECEIPT_UNAVAILABLE"
    elif callable_value:
        state = "A1_NOT_OBSERVED_CANONICAL_INVOCATION_NOT_RETAINED"
    else:
        state = "A1_NOT_OBSERVED_NOT_CALLABLE"

    result = {
        "schema": "stegverse.stegbrowser-runtime-connection-a1-a4-observation/v2",
        "state": state,
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv": COSV,
        "observation_ref": str(observation_path),
        "resolution_ref": str(resolution_path),
        "node_binding_selector": CANONICAL_NODE_SELECTOR,
        "canonical_node_receipt_path_parameter": "node_genesis_receipt",
        "canonical_node_receipt_path_environment": NODE_PATH_ENV,
        "resolved_node_genesis_receipt_ref": node_receipt_ref,
        "node_resolution_error": node_resolution_error,
        "callable": callable_value,
        "refreshable": refreshable_value,
        "applicable_protocol_resolved": protocol_resolved,
        "selected_reusable_tasks": selected,
        "source_refresh_receipt": refresh_receipt,
        "admitted_execution_surface_materialized": execution_surface_materialized,
        "canonical_node_bound_invocation": invocation,
        "registered_stegverse_node_bound_to_invocation": a1_observed,
        "a2_1_invocation_scoped_lease_observed": a2_1_observed,
        "a2_2_event_ephemeral_runtime_observed": a2_2_observed,
        "workercoordinator_claim_or_fence_observed": claim_observed,
        "claim_id": claim_id,
        "fencing_token": fence,
        "intr_admission_observed": a4_observed,
        "round_trip_1_payload_processing_attempted": False,
        "external_runtime_device_host_discovery_performed": False,
        "next_gc_stage": "ROUND_TRIP_1_DECLARED_OWNED_MIRROR_PATH" if a4_observed else "A1_A4_CANONICAL_INVOCATION_CONTINUATION",
        "authority_effect": "NONE_OBSERVATION_SELECTION_AND_EXISTING_AUTHORITY_COMPOSITION_ONLY",
    }
    out = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json"
    atomic_json(out, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
