#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "STEGVERSE-TEST-LANES-AUTOLAUNCH-001"
MATRIX_PATH = ROOT / "control" / "test-lanes-autolaunch-matrix.v1.json"
RECEIPT_ROOT = ROOT / "receipts" / "test-lanes-autolaunch"
STATUS_RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
ACTIVE_CLAIM = RECEIPT_ROOT / "active-claim.json"
FORBIDDEN_SECRET_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "MOONSHOT_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
)
HOSTED_MARKERS = ("GITHUB_ACTIONS", "RENDER", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
PROVIDERS = ("openai", "anthropic", "deepseek", "kimi")

SPEC = importlib.util.spec_from_file_location("test_lanes_matrix", ROOT / "scripts" / "evaluate_test_lanes_autolaunch_matrix.py")
MATRIX_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MATRIX_MODULE)


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(dict(value), handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def hosted_environment() -> bool:
    return any(truthy(os.environ.get(key)) for key in HOSTED_MARKERS)


def secret_env_detected() -> bool:
    return any(bool(os.environ.get(key)) for key in FORBIDDEN_SECRET_ENV)


def recursive_values(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if raw_key == key:
                found.append(child)
            found.extend(recursive_values(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(recursive_values(child, key))
    return found


def first_int(value: Mapping[str, Any] | None, keys: Iterable[str]) -> int | None:
    if not isinstance(value, Mapping):
        return None
    for key in keys:
        for candidate in recursive_values(value, key):
            if isinstance(candidate, int) and not isinstance(candidate, bool):
                return candidate
    return None


def any_true(value: Mapping[str, Any] | None, key: str) -> bool:
    return any(candidate is True for candidate in recursive_values(value or {}, key))


def any_value(value: Mapping[str, Any] | None, key: str, expected: Any) -> bool:
    return any(candidate == expected for candidate in recursive_values(value or {}, key))


def find_root(env_name: str, candidates: list[Path], required: list[Path]) -> Path | None:
    roots: list[Path] = []
    override = os.environ.get(env_name)
    if override:
        roots.append(Path(override).expanduser())
    roots.extend(candidates)
    seen: set[str] = set()
    for raw in roots:
        try:
            root = raw.resolve()
        except Exception:
            continue
        marker = str(root)
        if marker in seen:
            continue
        seen.add(marker)
        if all((root / item).is_file() for item in required):
            return root
    return None


def run(command: list[str], *, cwd: Path, timeout: int = 180) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(cwd),
            "HOME": os.environ.get("HOME", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        },
    )
    return {
        "returncode": process.returncode,
        "stdout_tail": process.stdout[-2000:],
        "stderr_tail": process.stderr[-2000:],
    }


def run_json_command(command: list[str], *, cwd: Path, output_path: Path, timeout: int = 180) -> tuple[bool, dict[str, Any] | None, dict[str, Any]]:
    result = run(command, cwd=cwd, timeout=timeout)
    value = load_json(output_path) if result["returncode"] == 0 else None
    return result["returncode"] == 0 and isinstance(value, dict), value, result


def http_health(endpoint: str | None) -> dict[str, Any] | None:
    if not isinstance(endpoint, str):
        return None
    parsed = urlparse(endpoint)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        return None
    try:
        with urlopen(endpoint.rstrip("/") + "/health", timeout=2) as response:
            value = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def source_validation(tvc_root: Path | None, lanes_root: Path | None) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    local = run([sys.executable, "tests/test_test_lanes_autolaunch_matrix.py"], cwd=ROOT, timeout=30)
    checks.append({"name": "autolaunch_matrix", **local})
    if lanes_root is None:
        checks.append({"name": "test_lanes", "returncode": 127, "stderr_tail": "TEST_LANES_ROOT_NOT_MATERIALIZED", "stdout_tail": ""})
    else:
        for test in (
            "tests/test_plan_test_lanes.py",
            "tests/test_compare_test_lanes.py",
            "tests/test_run_stegverse_primary_candidate.py",
            "tests/test_build_lane_evidence.py",
        ):
            result = run([sys.executable, test], cwd=lanes_root / "experiments" / "stegverse-test-lanes", timeout=45)
            checks.append({"name": "test_lanes:" + test, **result})
    if tvc_root is None:
        checks.append({"name": "tvc", "returncode": 127, "stderr_tail": "TVC_ROOT_NOT_MATERIALIZED", "stdout_tail": ""})
    else:
        tests = [
            "tests/test_provider_capsule.py",
            "tests/test_tvc_materialize_provider_capsule_bindings.py",
            "tests/test_tvc_resolve_test_lane_capsules.py",
            "tests/test_tvc_issue_test_lane_lease.py",
            "tests/test_tvc_run_test_lane_external_candidate.py",
            "tests/test_tvc_test_lane_capsule_execution_guard.py",
        ]
        result = run([sys.executable, "-m", "pytest", "-q", *tests], cwd=tvc_root, timeout=120)
        checks.append({"name": "tvc_provider_capsule_test_lanes", **result})
    return all(item.get("returncode") == 0 for item in checks), checks


def model_selection() -> tuple[dict[str, str], Path | None]:
    candidates: list[Path] = []
    override = os.environ.get("STEGVERSE_TEST_LANES_MODEL_SELECTION")
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend([
        Path.home() / ".stegverse" / "test-lanes" / "model-selection.json",
        ROOT / "runtime" / "test-lanes" / "model-selection.json",
    ])
    for path in candidates:
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        if data.get("schema") != "stegverse.test-lanes-model-selection/v1" or data.get("test_id") != "SV-COST-NINE-LANE-v1":
            continue
        models = data.get("models")
        if not isinstance(models, dict):
            continue
        selected = {provider: str(models.get(provider) or "").strip() for provider in PROVIDERS}
        if all(selected.values()):
            return selected, path
    return {}, None


def plan_and_resolve(tvc_root: Path, lanes_root: Path, run_dir: Path, vault_agent_socket: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    lane_dir = lanes_root / "experiments" / "stegverse-test-lanes"
    manifest = lane_dir / "manifests" / "sv-cost-nine-lane.v1.json"
    preplan = run_dir / "preplan.json"
    materialized_registry = run_dir / "provider-capsules.materialized.json"
    materialization_receipt = run_dir / "provider-capsules.materialization.json"
    resolutions = run_dir / "capsule-resolutions.json"
    final_plan = run_dir / "plan.json"
    steps: dict[str, Any] = {}

    ok, _, steps["preplan"] = run_json_command(
        [sys.executable, str(lane_dir / "plan_test_lanes.py"), str(manifest), "--output", str(preplan)],
        cwd=lanes_root,
        output_path=preplan,
    )
    if not ok:
        return None, steps
    ok, _, steps["materialize"] = run_json_command(
        [
            sys.executable,
            "scripts/tvc_materialize_provider_capsule_bindings.py",
            "--registry-template", "config/provider_capsules.example.json",
            "--vault-agent-socket", vault_agent_socket,
            "--output-registry", str(materialized_registry),
            "--receipt", str(materialization_receipt),
        ],
        cwd=tvc_root,
        output_path=materialized_registry,
    )
    if not ok:
        return None, steps
    ok, _, steps["resolve"] = run_json_command(
        [
            sys.executable,
            "scripts/tvc_resolve_test_lane_capsules.py",
            str(preplan),
            "--registry", "config/provider_capsules.example.json",
            "--vault-agent-socket", vault_agent_socket,
            "--output", str(resolutions),
        ],
        cwd=tvc_root,
        output_path=resolutions,
    )
    if not ok:
        return None, steps
    ok, plan, steps["replan"] = run_json_command(
        [
            sys.executable,
            str(lane_dir / "plan_test_lanes.py"),
            str(manifest),
            "--capsule-resolutions", str(resolutions),
            "--output", str(final_plan),
        ],
        cwd=lanes_root,
        output_path=final_plan,
    )
    if not ok:
        return plan, steps
    steps["paths"] = {
        "manifest": str(manifest),
        "preplan": str(preplan),
        "materialized_registry": str(materialized_registry),
        "materialization_receipt": str(materialization_receipt),
        "resolutions": str(resolutions),
        "final_plan": str(final_plan),
    }
    return plan, steps


def provider_states(plan: Mapping[str, Any] | None) -> dict[str, str]:
    result = {provider: "UNOBSERVED" for provider in PROVIDERS}
    if not isinstance(plan, Mapping):
        return result
    lanes = plan.get("lanes")
    if not isinstance(lanes, list):
        return result
    for provider in PROVIDERS:
        states = {str(item.get("state")) for item in lanes if isinstance(item, Mapping) and item.get("provider") == provider}
        if len(states) == 1:
            result[provider] = next(iter(states))
        elif states:
            result[provider] = "INCONSISTENT"
    return result


def active_claim_conflict(current_fence: int) -> tuple[bool, dict[str, Any] | None]:
    active = load_json(ACTIVE_CLAIM)
    if not isinstance(active, dict) or active.get("state") != "ACTIVE":
        return False, active
    fence = active.get("fencing_token")
    if isinstance(fence, int) and fence < current_fence:
        superseded = {**active, "state": "SUPERSEDED", "superseded_by_fencing_token": current_fence}
        old_id = str(active.get("test_run_claim_id") or "stale").replace("/", "_")
        atomic_write(RECEIPT_ROOT / f"claim-{old_id}.json", superseded)
        try:
            ACTIVE_CLAIM.unlink()
        except FileNotFoundError:
            pass
        return False, superseded
    return True, active


def snapshot(
    *,
    plan: Mapping[str, Any] | None,
    source_valid: bool,
    models_selected: bool,
    current_fence: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    carrier = load_json(ROOT / "control" / "heartbeat-carrier-runtime-state.json")
    worker = load_json(ROOT / "control" / "worker-runtime-state.json")
    transition = load_json(ROOT / "receipts" / "heartbeat-transition-continuity" / "latest.json")
    sovereign = load_json(ROOT / "receipts" / "ecosystem-chat-sovereign-inference" / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json")
    live_model = load_json(ROOT / "receipts" / "ecosystem-chat-sovereign-inference" / "live_model_process.json")
    route = load_json(ROOT / "receipts" / "ecosystem-chat-sovereign-inference" / "tvc_local_model_route.json")

    carrier_epoch = first_int(carrier, ("carrier_epoch", "heartbeat_epoch", "epoch")) or 0
    worker_epoch = first_int(worker, ("observed_carrier_epoch", "carrier_epoch", "heartbeat_epoch", "epoch")) or 0
    endpoint = None
    if isinstance(sovereign, dict):
        values = recursive_values(sovereign, "live_model_endpoint")
        endpoint = next((item for item in values if isinstance(item, str)), None)
    if endpoint is None and isinstance(live_model, dict) and isinstance(live_model.get("endpoint"), str):
        endpoint = str(live_model["endpoint"])
    health = http_health(endpoint)

    terminal_flags = (
        "real_model_process_observed",
        "private_endpoint_only",
        "ephemeral_e1_e2_execution_observed",
        "measured_usage_persisted",
        "provider_usage_reconstruction_pass",
        "transition_reconstruction_pass",
        "same_execution",
    )
    same_execution = isinstance(sovereign, dict) and all(any_true(sovereign, key) for key in terminal_flags)
    route_admitted = isinstance(route, dict) and (
        any_value(route, "decision", "ROUTE_ADMITTED") or any_value(route, "state", "ROUTE_ADMITTED")
    ) and any_value(route, "credential_requirement", "NONE")
    conflict, prior_claim = active_claim_conflict(current_fence)

    lanes = plan.get("lanes") if isinstance(plan, Mapping) else []
    groups = plan.get("execution_groups") if isinstance(plan, Mapping) else []
    ready_lane_count = sum(
        1 for item in lanes or [] if isinstance(item, Mapping) and item.get("state") in {"READY_LOCAL_PRIMARY", "READY_FOR_TVC_EXECUTION"}
    )
    ready_group_count = sum(
        1 for item in groups or [] if isinstance(item, Mapping) and item.get("state") in {"READY_LOCAL_PRIMARY", "READY_FOR_TVC_EXECUTION"}
    )
    task_exact = False
    if isinstance(plan, Mapping):
        manifest_path = None
        task_path = None
        # final paths are deterministic under the locally materialized Test Lanes tree; caller records exact paths separately.
        lane_requests = [item for item in lanes or [] if isinstance(item, Mapping)]
        if lane_requests:
            task_sha = lane_requests[0].get("task_source_blob_sha")
            task_source = lane_requests[0].get("task_source")
            lanes_root_raw = os.environ.get("STEGVERSE_TEST_LANES_ROOT")
            if lanes_root_raw and isinstance(task_source, str):
                candidate = Path(lanes_root_raw).expanduser().resolve() / task_source
                if candidate.is_file():
                    task_path = candidate
                    task_exact = git_blob_sha(candidate.read_bytes()) == task_sha

    state = {
        "schema": "stegverse.test-lanes-autolaunch-snapshot/v1",
        "matrix_id": EXPECTED_TASK,
        "runtime": {
            "carrier_epoch": carrier_epoch,
            "worker_observed_current_carrier": carrier_epoch >= 30 and worker_epoch >= carrier_epoch,
            "state_reconstruction_pass": any_true(transition, "state_reconstruction_pass") or any_value(transition, "state", "CARRIER_TRANSITION_COMPLETE"),
        },
        "sovereign": {
            "same_execution_activation": same_execution,
            "primary_endpoint_ready": isinstance(health, dict) and health.get("state") == "READY",
            "model_verified": isinstance(health, dict) and health.get("model") == "stegverse-reference-lm-v1" and health.get("private_endpoint_only") is True,
            "credential_requirement": "NONE" if isinstance(sovereign, dict) and any_value(sovereign, "credential_requirement", "NONE") else None,
            "third_party_inference_required": False if isinstance(sovereign, dict) and any_value(sovereign, "third_party_inference_required", False) else None,
            "endpoint": endpoint,
        },
        "tvc": {
            "route_admitted": route_admitted,
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_detected": secret_env_detected(),
        },
        "providers": provider_states(plan),
        "test": {
            "manifest_valid": isinstance(plan, Mapping),
            "task_blob_exact": task_exact,
            "plan_state": plan.get("state") if isinstance(plan, Mapping) else None,
            "external_models_selected": models_selected,
            "primary_provider": plan.get("primary_provider") if isinstance(plan, Mapping) else None,
            "ready_lane_count": ready_lane_count,
            "ready_execution_group_count": ready_group_count,
        },
        "validation": {"source_validation_observed": source_valid},
        "evidence": {"sink_ready": RECEIPT_ROOT.exists() and os.access(RECEIPT_ROOT, os.W_OK)},
        "claims": {"conflicting_active_claim": conflict},
    }
    observed = {
        "carrier_state_present": carrier is not None,
        "worker_state_present": worker is not None,
        "transition_receipt_present": transition is not None,
        "sovereign_receipt_present": sovereign is not None,
        "live_model_state_present": live_model is not None,
        "route_receipt_present": route is not None,
        "prior_claim": prior_claim,
    }
    return state, observed


def acquire_claim(*, parent_claim_id: str, fencing_token: int, epoch: int, plan: Mapping[str, Any], evaluation: Mapping[str, Any], model_selection_path: Path) -> dict[str, Any]:
    claim = {
        "schema": "stegverse.test-lanes-run-claim/v1",
        "state": "ACTIVE",
        "task_id": EXPECTED_TASK,
        "test_id": plan.get("test_id"),
        "test_run_claim_id": f"{EXPECTED_TASK}:HB{epoch}:G{fencing_token}:{str(plan.get('plan_hash'))[-12:]}",
        "parent_worker_claim_id": parent_claim_id,
        "fencing_token": fencing_token,
        "heartbeat_epoch": epoch,
        "plan_hash": plan.get("plan_hash"),
        "manifest_hash": plan.get("manifest_hash"),
        "matrix_evaluation_sha256": evaluation.get("evaluation_sha256"),
        "model_selection_sha256": digest_bytes(model_selection_path.read_bytes()),
        "primary_provider": "stegverse_local",
        "third_party_role": "CONTROL_OR_FALLBACK_ONLY",
        "credential_authority": "TV/TVC",
        "heartbeat_grants_execution_authority": False,
        "non_tv_tvc_secret_or_token_allowed": False,
    }
    if ACTIVE_CLAIM.exists():
        raise RuntimeError("active test-run claim appeared after matrix evaluation")
    atomic_write(ACTIVE_CLAIM, claim)
    return claim


def execute_run(
    *,
    plan: Mapping[str, Any],
    plan_steps: Mapping[str, Any],
    models: Mapping[str, str],
    endpoint: str,
    tvc_root: Path,
    lanes_root: Path,
    run_dir: Path,
    vault_broker_socket: str,
) -> tuple[bool, dict[str, Any]]:
    lane_dir = lanes_root / "experiments" / "stegverse-test-lanes"
    paths = plan_steps.get("paths") if isinstance(plan_steps, Mapping) else None
    if not isinstance(paths, Mapping):
        return False, {"reason": "PLAN_PATHS_MISSING"}
    plan_path = Path(str(paths["final_plan"]))
    resolutions = Path(str(paths["resolutions"]))
    registry = Path(str(paths["materialized_registry"]))
    task_source = str((plan.get("lanes") or [{}])[0].get("task_source") or "")
    task_path = lanes_root / task_source
    if not task_path.is_file():
        return False, {"reason": "TASK_SOURCE_NOT_MATERIALIZED", "task_path": str(task_path)}

    primary_path = run_dir / "candidate-stegverse-primary.json"
    ok, _, primary_step = run_json_command(
        [
            sys.executable,
            str(lane_dir / "run_stegverse_primary_candidate.py"),
            "--plan", str(plan_path),
            "--task-json", str(task_path),
            "--endpoint", endpoint,
            "--out", str(primary_path),
        ],
        cwd=lanes_root,
        output_path=primary_path,
        timeout=60,
    )
    if not ok:
        return False, {"primary": primary_step}

    external_paths: list[Path] = []
    external_steps: dict[str, Any] = {}
    for group in plan.get("execution_groups") or []:
        if not isinstance(group, Mapping) or group.get("provider") == "stegverse_local":
            continue
        provider = str(group.get("provider"))
        if provider not in PROVIDERS or group.get("state") != "READY_FOR_TVC_EXECUTION":
            return False, {"reason": f"EXTERNAL_GROUP_NOT_READY:{provider}:{group.get('state')}"}
        out = run_dir / f"candidate-{provider}.json"
        ok, _, step = run_json_command(
            [
                sys.executable,
                "scripts/tvc_run_test_lane_external_candidate.py",
                "--plan", str(plan_path),
                "--capsule-resolutions", str(resolutions),
                "--local-capsule-registry", str(registry),
                "--group-id", str(group.get("execution_group_id")),
                "--task-json", str(task_path),
                "--model", str(models[provider]),
                "--vault-broker-socket", vault_broker_socket,
                "--out", str(out),
            ],
            cwd=tvc_root,
            output_path=out,
            timeout=180,
        )
        external_steps[provider] = step
        if not ok:
            return False, {"primary": primary_step, "external": external_steps}
        external_paths.append(out)

    if len(external_paths) != 4:
        return False, {"reason": "CANONICAL_RUN_REQUIRES_FOUR_EXTERNAL_CANDIDATES", "external_count": len(external_paths)}

    bundle = run_dir / "lane-evidence.json"
    command = [
        sys.executable,
        str(lane_dir / "build_lane_evidence.py"),
        "--plan", str(plan_path),
        "--task-json", str(task_path),
        "--primary-candidate", str(primary_path),
    ]
    for path in external_paths:
        command.extend(["--external-candidate", str(path)])
    command.extend(["--out", str(bundle)])
    ok, _, evidence_step = run_json_command(command, cwd=lanes_root, output_path=bundle, timeout=45)
    if not ok:
        return False, {"primary": primary_step, "external": external_steps, "evidence": evidence_step}

    comparison = run_dir / "comparison.json"
    ok, comparison_value, comparison_step = run_json_command(
        [sys.executable, str(lane_dir / "compare_test_lanes.py"), str(plan_path), str(bundle), "--output", str(comparison)],
        cwd=lanes_root,
        output_path=comparison,
        timeout=45,
    )
    success = ok and isinstance(comparison_value, dict) and comparison_value.get("state") == "PASS" and comparison_value.get("lane_evidence_count") == 9
    return success, {
        "primary": primary_step,
        "external": external_steps,
        "evidence": evidence_step,
        "comparison": comparison_step,
        "comparison_path": str(comparison),
        "evidence_bundle_path": str(bundle),
        "comparison_state": comparison_value.get("state") if isinstance(comparison_value, dict) else None,
        "lane_evidence_count": comparison_value.get("lane_evidence_count") if isinstance(comparison_value, dict) else None,
    }


def worker_response(state: str, transition: str, *, blocker: Mapping[str, Any] | None = None, evidence_refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "expected_next_transition": None if state == "COMPLETED" else "REEVALUATE_TEST_LANES_AUTOLAUNCH_MATRIX",
        "checkpoint_ref": str(STATUS_RECEIPT.relative_to(ROOT)),
        "evidence_refs": evidence_refs or [str(STATUS_RECEIPT.relative_to(ROOT))],
        "blocker": dict(blocker) if blocker else None,
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    task = invocation.get("task") or {}
    if task.get("task_id") != EXPECTED_TASK:
        return 3
    epoch = invocation.get("heartbeat_epoch")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    parent_claim_id = str(task.get("claim_id") or "")
    if not isinstance(epoch, int) or not isinstance(fence, int) or not parent_claim_id:
        return 4
    if hosted_environment():
        receipt = {"state": "BLOCKED", "reason": "HOSTED_RUNTIME_IS_VALIDATION_ONLY", "heartbeat_epoch": epoch, "fencing_token": fence}
        atomic_write(STATUS_RECEIPT, receipt)
        json.dump(worker_response("BLOCKED", "HOSTED_RUNTIME_REJECTED", blocker={"dependency_class": "PHYSICAL_RESOURCE", "machine_observable_release_condition": "execute on admitted StegVerse-controlled local runtime", "third_party_blocker": False}), sys.stdout, sort_keys=True); sys.stdout.write("\n")
        return 0

    RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
    tvc_root = find_root(
        "STEGVERSE_TVC_ROOT",
        [ROOT.parent / "TVC", Path.home() / ".stegverse" / "workloads" / "TVC"],
        [Path("scripts/tvc_resolve_test_lane_capsules.py"), Path("scripts/tvc_run_test_lane_external_candidate.py")],
    )
    lanes_root = find_root(
        "STEGVERSE_TEST_LANES_ROOT",
        [Path.home() / ".stegverse" / "workloads" / "workflows"],
        [Path("experiments/stegverse-test-lanes/plan_test_lanes.py"), Path("experiments/stegverse-test-lanes/build_lane_evidence.py")],
    )
    source_valid, validation_checks = source_validation(tvc_root, lanes_root)
    models, model_path = model_selection()
    run_dir = RECEIPT_ROOT / f"HB{epoch}-G{fence}"
    run_dir.mkdir(parents=True, exist_ok=True)
    vault_agent_socket = os.environ.get("STEGVERSE_VAULT_AGENT_SOCKET", "/run/stegverse/vault-agent.sock")
    vault_broker_socket = os.environ.get("STEGVERSE_VAULT_BROKER_SOCKET", "/run/stegverse/vault-broker.sock")

    plan = None
    plan_steps: dict[str, Any] = {}
    if tvc_root is not None and lanes_root is not None:
        plan, plan_steps = plan_and_resolve(tvc_root, lanes_root, run_dir, vault_agent_socket)
    state_snapshot, observed = snapshot(
        plan=plan,
        source_valid=source_valid,
        models_selected=bool(model_path and len(models) == 4),
        current_fence=fence,
    )
    # task source exactness can use the discovered lanes root even when it was not explicitly exported in the parent environment.
    if lanes_root is not None and isinstance(plan, Mapping):
        lane_requests = [item for item in plan.get("lanes") or [] if isinstance(item, Mapping)]
        if lane_requests:
            task_source = lane_requests[0].get("task_source")
            task_sha = lane_requests[0].get("task_source_blob_sha")
            if isinstance(task_source, str):
                task_file = lanes_root / task_source
                state_snapshot["test"]["task_blob_exact"] = task_file.is_file() and git_blob_sha(task_file.read_bytes()) == task_sha

    matrix = load_json(MATRIX_PATH)
    if not isinstance(matrix, dict):
        return 5
    evaluation = MATRIX_MODULE.evaluate(matrix, state_snapshot)
    snapshot_path = run_dir / "matrix-snapshot.json"
    evaluation_path = run_dir / "matrix-evaluation.json"
    atomic_write(snapshot_path, state_snapshot)
    atomic_write(evaluation_path, evaluation)

    base_receipt: dict[str, Any] = {
        "schema": "stegverse.test-lanes-autolaunch-worker-receipt/v1",
        "task_id": EXPECTED_TASK,
        "test_id": "SV-COST-NINE-LANE-v1",
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "parent_worker_claim_id": parent_claim_id,
        "matrix_state": evaluation.get("state"),
        "matrix_evaluation_sha256": evaluation.get("evaluation_sha256"),
        "blocking_predicates": evaluation.get("blocking_predicates"),
        "prohibitive_failures": evaluation.get("prohibitive_failures"),
        "source_validation_checks": validation_checks,
        "plan_steps": plan_steps,
        "observed": observed,
        "model_selection_path": str(model_path) if model_path else None,
        "model_selection_sha256": digest_bytes(model_path.read_bytes()) if model_path else None,
        "primary_provider": "stegverse_local",
        "third_party_role": "CONTROL_OR_FALLBACK_ONLY",
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
    }

    if evaluation.get("state") == "FAIL_CLOSED":
        base_receipt.update({"state": "FAILED", "transition_id": "AUTOLAUNCH_MATRIX_FAIL_CLOSED"})
        atomic_write(STATUS_RECEIPT, base_receipt)
        response = worker_response("FAILED", "AUTOLAUNCH_MATRIX_FAIL_CLOSED", blocker={
            "dependency_class": "AUTHORITY_OR_INTEGRITY_VIOLATION",
            "machine_observable_release_condition": "all prohibitive matrix predicates pass",
            "prohibitive_failures": evaluation.get("prohibitive_failures"),
            "third_party_blocker": False,
        })
        json.dump(response, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    if evaluation.get("state") != "ALLOW_EXECUTION_CLAIM":
        base_receipt.update({"state": "BLOCKED", "transition_id": "AUTOLAUNCH_MATRIX_BLOCKED"})
        atomic_write(STATUS_RECEIPT, base_receipt)
        response = worker_response("BLOCKED", "AUTOLAUNCH_MATRIX_BLOCKED", blocker={
            "dependency_class": "CONDITIONAL_MATRIX",
            "machine_observable_release_condition": "all required nine-lane autolaunch predicates pass simultaneously",
            "blocking_predicates": evaluation.get("blocking_predicates"),
            "third_party_blocker": False,
        })
        json.dump(response, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    if not isinstance(plan, Mapping) or not isinstance(model_path, Path) or tvc_root is None or lanes_root is None:
        base_receipt.update({"state": "FAILED", "transition_id": "ALLOW_STATE_INPUTS_MISSING"})
        atomic_write(STATUS_RECEIPT, base_receipt)
        json.dump(worker_response("FAILED", "ALLOW_STATE_INPUTS_MISSING"), sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    claim = acquire_claim(
        parent_claim_id=parent_claim_id,
        fencing_token=fence,
        epoch=epoch,
        plan=plan,
        evaluation=evaluation,
        model_selection_path=model_path,
    )
    endpoint = state_snapshot.get("sovereign", {}).get("endpoint")
    if not isinstance(endpoint, str):
        raise RuntimeError("matrix allowed execution without primary endpoint")
    success, execution = execute_run(
        plan=plan,
        plan_steps=plan_steps,
        models=models,
        endpoint=endpoint,
        tvc_root=tvc_root,
        lanes_root=lanes_root,
        run_dir=run_dir,
        vault_broker_socket=vault_broker_socket,
    )
    claim_terminal = {**claim, "state": "COMPLETED" if success else "FAILED", "execution": execution}
    atomic_write(ACTIVE_CLAIM, claim_terminal)
    atomic_write(RECEIPT_ROOT / f"claim-{claim['test_run_claim_id'].replace(':', '_')}.json", claim_terminal)
    try:
        ACTIVE_CLAIM.unlink()
    except FileNotFoundError:
        pass

    base_receipt.update({
        "state": "COMPLETED" if success else "FAILED",
        "transition_id": "CANONICAL_9_LANE_TEST_COMPLETE" if success else "CANONICAL_9_LANE_TEST_EXECUTION_FAILED",
        "test_run_claim": claim_terminal,
        "execution": execution,
        "all_nine_lanes_executed": success and execution.get("lane_evidence_count") == 9,
        "comparison_pass": success and execution.get("comparison_state") == "PASS",
    })
    atomic_write(STATUS_RECEIPT, base_receipt)
    response = worker_response(
        "COMPLETED" if success else "FAILED",
        base_receipt["transition_id"],
        evidence_refs=[
            str(STATUS_RECEIPT.relative_to(ROOT)),
            str(snapshot_path.relative_to(ROOT)),
            str(evaluation_path.relative_to(ROOT)),
        ],
    )
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
