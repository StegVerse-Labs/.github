#!/usr/bin/env python3
from __future__ import annotations

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


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


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
    if profile.get("event_triggered") is not True:
        return False
    if source_root.resolve() == runtime_root.resolve():
        return False
    return (source_root / "source-bundles/reusable-task-registry.d/RT-SOVEREIGN-SOURCE-REFRESH-001.json").is_file()


def exact_manifest_protocol_resolved(source_root: Path, profile: dict[str, Any]) -> bool:
    """Resolve protocol availability without treating source as transport admission.

    The live shared profile proves the resident InTr protocol is callable. The
    already-local manifest ingress worker proves the exact declared StegBrowser
    organization-local InTr adapter exists. Neither fact proves A4 admission.
    """
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


def run_existing_manifest_ingress(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    """Perform A3/A4 through the already-existing exact manifest ingress path.

    stegbrowser_manifest_intr_ingress.py delegates to the canonical organization-
    local boundary executor. That existing task obtains the WorkerCoordinator
    claim/fence and emits the exact accepted local-boundary receipt. This function
    creates no new WorkerCoordinator task, scheduler, credential route, or A5+
    Round Trip 1 execution path.
    """
    worker = runtime_root / MANIFEST_INGRESS_REL
    if not worker.is_file():
        worker = source_root / MANIFEST_INGRESS_REL
    require(worker.is_file(), "existing_manifest_ingress_worker_missing")
    completed = subprocess.run(
        [sys.executable, str(worker), "--source-root", str(source_root), "--runtime-root", str(runtime_root)],
        cwd=str(runtime_root),
        text=True,
        capture_output=True,
        check=False,
        timeout=1200,
        env=os.environ.copy(),
    )
    result = None
    for line in reversed([line.strip() for line in completed.stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            result = value
            break
    if not isinstance(result, dict):
        return {
            "state": "A3_A4_RUNTIME_RESULT_UNAVAILABLE",
            "returncode": completed.returncode,
            "stderr_tail": completed.stderr[-1200:],
        }
    result = dict(result)
    result["returncode"] = completed.returncode
    return result


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
        "profile_schema": profile.get("schema"),
        "profile_state": profile.get("state"),
        "profile_protocol": profile.get("protocol"),
        "canonical_work_profile_present": "CanonicalWork:Coordination" in profiles,
        "exact_manifest_ingress_adapter_present": (source_root / MANIFEST_INGRESS_REL).is_file(),
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

    refresh_receipt = None
    selected = resolution.get("selected_reusable_tasks", [])
    if SOURCE_REFRESH_RT in selected:
        refresh_receipt = run_source_refresh(source_root, runtime_root)

    execution_surface_materialized = bool(callable_value and (not refreshable_value or refresh_receipt is not None))
    a3_a4 = None
    if callable_value and protocol_resolved and execution_surface_materialized and PROTOCOL_RT not in selected:
        a3_a4 = run_existing_manifest_ingress(source_root, runtime_root)

    a4_observed = bool(isinstance(a3_a4, dict) and a3_a4.get("state") == "AUTHENTIC_INTR_INGRESS_OBSERVED")
    claim_id = a3_a4.get("claim_id") if isinstance(a3_a4, dict) else None
    fence = a3_a4.get("fencing_token") if isinstance(a3_a4, dict) else None
    claim_observed = bool(isinstance(claim_id, str) and isinstance(fence, int) and claim_id.endswith(f"-G{fence}"))

    result = {
        "schema": "stegverse.stegbrowser-runtime-connection-a1-a4-observation/v1",
        "state": "A1_A2_A3_A4_OBSERVED" if (a4_observed and claim_observed) else ("A1_A2_OBSERVED_A3_A4_PENDING" if execution_surface_materialized else "A1_OBSERVED_NOT_MATERIALIZED"),
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "cosv": COSV,
        "observation_ref": str(observation_path),
        "resolution_ref": str(resolution_path),
        "callable": callable_value,
        "refreshable": refreshable_value,
        "applicable_protocol_resolved": protocol_resolved,
        "selected_reusable_tasks": selected,
        "source_refresh_receipt": refresh_receipt,
        "admitted_execution_surface_materialized": execution_surface_materialized,
        "a3_a4_result": a3_a4,
        "workercoordinator_claim_or_fence_observed": claim_observed,
        "claim_id": claim_id,
        "fencing_token": fence,
        "intr_admission_observed": a4_observed,
        "round_trip_1_payload_processing_attempted": False,
        "next_gc_stage": "A5_DECLARED_OWNED_MIRROR_PATH" if a4_observed else "A3_A4_EXISTING_BOUNDARY_EXECUTOR_CONTINUATION",
        "authority_effect": "NONE_OBSERVATION_SELECTION_MATERIALIZATION_AND_EXISTING_AUTHORITY_COMPOSITION_ONLY",
    }
    out = runtime_root / "receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json"
    atomic_json(out, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
