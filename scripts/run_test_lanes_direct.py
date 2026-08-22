#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import socket
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "workers" / "test_lanes_autolaunch_worker.py"
PROVIDERS = ("openai", "anthropic", "deepseek", "kimi")
PROVIDER_SECRET_FILES = {
    "openai": "provider_openai",
    "anthropic": "provider_anthropic",
    "deepseek": "provider_deepseek",
    "kimi": "provider_kimi",
}
FORBIDDEN_SECRET_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "MOONSHOT_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
)
HOSTED_MARKERS = ("GITHUB_ACTIONS", "RENDER", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")

SPEC = importlib.util.spec_from_file_location("stegverse_test_lanes_execution_helpers", HELPER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load Test Lanes execution helpers")
HELPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def preflight_environment() -> None:
    if any(truthy(os.environ.get(name)) for name in HOSTED_MARKERS):
        raise RuntimeError("direct canonical Test Lanes execution must run on a StegVerse-controlled runtime, not a hosted CI/deploy runtime")
    leaked = [name for name in FORBIDDEN_SECRET_ENV if os.environ.get(name)]
    if leaked:
        raise RuntimeError("provider/GitHub secrets may not be supplied through the direct-run environment: " + ",".join(leaked))


def require_root(path: Path, required: tuple[str, ...], label: str) -> Path:
    root = path.expanduser().resolve()
    missing = [item for item in required if not (root / item).is_file()]
    if missing:
        raise RuntimeError(f"{label} root missing required files: {missing}")
    return root


def validate_model_selection(path: Path) -> dict[str, str]:
    value = load_json(path)
    if value.get("schema") != "stegverse.test-lanes-model-selection/v1":
        raise RuntimeError("model-selection schema mismatch")
    if value.get("test_id") != "SV-COST-NINE-LANE-v1":
        raise RuntimeError("model-selection test_id mismatch")
    models = value.get("models")
    if not isinstance(models, Mapping):
        raise RuntimeError("model-selection models object required")
    selected = {provider: str(models.get(provider) or "").strip() for provider in PROVIDERS}
    if not all(selected.values()):
        raise RuntimeError("all four external model IDs must be selected for canonical 9/9 execution")
    return selected


def primary_health(endpoint: str) -> dict[str, Any]:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("StegVerse PRIMARY endpoint must be loopback-local http(s)")
    with urlopen(endpoint.rstrip("/") + "/health", timeout=3) as response:
        health = json.loads(response.read().decode("utf-8"))
    if not isinstance(health, dict):
        raise RuntimeError("StegVerse PRIMARY health response must be an object")
    required = {
        "state": "READY",
        "model": "stegverse-reference-lm-v1",
        "private_endpoint_only": True,
        "third_party_inference_required": False,
        "authority_effect": "NONE",
    }
    failed = {key: {"expected": expected, "observed": health.get(key)} for key, expected in required.items() if health.get(key) != expected}
    if failed:
        raise RuntimeError("StegVerse PRIMARY health predicates failed: " + json.dumps(failed, sort_keys=True))
    return health


def wait_for_primary(endpoint: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return primary_health(endpoint)
        except Exception as exc:
            last_error = exc
            time.sleep(0.1)
    raise RuntimeError(f"StegVerse PRIMARY did not become READY: {last_error}")


def start_test_primary(micro_node_root: Path, endpoint: str) -> subprocess.Popen[str]:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or not isinstance(parsed.port, int):
        raise RuntimeError("auto-launch primary requires explicit loopback http endpoint with port")
    root = require_root(micro_node_root, ("tools/run_sovereign_model.py",), "micro-node")
    process = subprocess.Popen(
        [sys.executable, "tools/run_sovereign_model.py", "--host", str(parsed.hostname), "--port", str(parsed.port)],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(root),
            "HOME": os.environ.get("HOME", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        },
    )
    try:
        wait_for_primary(endpoint, timeout_seconds=10.0)
    except Exception:
        stop_process(process)
        raise
    return process


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def unix_health(socket_path: Path) -> bool:
    request = json.dumps({"operation": "health"}, separators=(",", ":")).encode("utf-8") + b"\n"
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1.0)
            client.connect(str(socket_path))
            client.sendall(request)
            raw = client.recv(65536).split(b"\n", 1)[0]
        value = json.loads(raw.decode("utf-8"))
        return isinstance(value, Mapping) and value.get("decision") == "READY"
    except Exception:
        return False


def wait_unix_health(socket_path: Path, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if unix_health(socket_path):
            return
        time.sleep(0.1)
    raise RuntimeError(f"TVC service did not become READY: {socket_path}")


def provider_secret_paths(governance_root: Path) -> dict[str, Path]:
    secret_dir = governance_root / "runtime-secrets"
    result = {provider: secret_dir / name for provider, name in PROVIDER_SECRET_FILES.items()}
    missing = [provider for provider, path in result.items() if not path.is_file()]
    if missing:
        raise RuntimeError("TVC_PROVIDER_CREDENTIAL_REGISTRATION_REQUIRED:" + ",".join(missing))
    for provider, path in result.items():
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"TVC_PROVIDER_SECRET_NOT_REGULAR:{provider}")
        if metadata.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise RuntimeError(f"TVC_PROVIDER_SECRET_PERMISSIONS_TOO_BROAD:{provider}")
        if metadata.st_size <= 0:
            raise RuntimeError(f"TVC_PROVIDER_SECRET_EMPTY:{provider}")
    return result


def start_tvc_vault_services(governance_root: Path, run_dir: Path) -> tuple[subprocess.Popen[str], subprocess.Popen[str], Path, Path]:
    root = require_root(governance_root, (
        "stegwallet/container_vault_agent.py",
        "scripts/run_vault_broker.py",
    ), "stegfin-governance")
    secrets_by_provider = provider_secret_paths(root)
    service_dir = run_dir / "tvc-runtime"
    service_dir.mkdir(parents=True, exist_ok=True)
    agent_socket = service_dir / "vault-agent.sock"
    broker_socket = service_dir / "vault-broker.sock"
    agent_command = [sys.executable, "-m", "stegwallet.container_vault_agent", "--socket", str(agent_socket)]
    for provider in PROVIDERS:
        agent_command.extend(["--provider-secret-file", f"{provider}={secrets_by_provider[provider]}"])
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(root),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    agent = subprocess.Popen(
        agent_command,
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    broker: subprocess.Popen[str] | None = None
    try:
        wait_unix_health(agent_socket)
        broker = subprocess.Popen(
            [sys.executable, "scripts/run_vault_broker.py", "--broker-socket", str(broker_socket), "--vault-agent-socket", str(agent_socket)],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        wait_unix_health(broker_socket)
        return agent, broker, agent_socket, broker_socket
    except Exception:
        stop_process(broker)
        stop_process(agent)
        for path in (broker_socket, agent_socket):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise


def assert_full_nine_ready(plan: Mapping[str, Any]) -> None:
    if plan.get("state") != "READY" or plan.get("primary_provider") != "stegverse_local":
        raise RuntimeError("canonical Test Lanes plan is not READY with StegVerse local PRIMARY")
    lanes = plan.get("lanes")
    groups = plan.get("execution_groups")
    if not isinstance(lanes, list) or len(lanes) != 9:
        raise RuntimeError("canonical run requires exactly nine logical lanes")
    if not isinstance(groups, list) or len(groups) != 5:
        raise RuntimeError("canonical run requires exactly five candidate execution groups")
    allowed = {"READY_LOCAL_PRIMARY", "READY_FOR_TVC_EXECUTION"}
    bad = [(item.get("lane_id"), item.get("state")) for item in lanes if not isinstance(item, Mapping) or item.get("state") not in allowed]
    if bad:
        raise RuntimeError("canonical 9/9 plan contains non-ready lanes: " + json.dumps(bad, sort_keys=True))
    providers = {str(item.get("provider")) for item in lanes if isinstance(item, Mapping)}
    if providers != {"stegverse_local", *PROVIDERS}:
        raise RuntimeError("canonical 9/9 provider set mismatch")


def execution_passed(success: bool, execution: Mapping[str, Any] | None) -> bool:
    return bool(
        success
        and isinstance(execution, Mapping)
        and execution.get("comparison_state") == "PASS"
        and execution.get("lane_evidence_count") == 9
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical StegVerse nine-lane experiment directly without heartbeat/G18 dependency.")
    parser.add_argument("--tvc-root", type=Path, default=Path(os.environ.get("STEGVERSE_TVC_ROOT", Path.home() / ".stegverse" / "workloads" / "TVC")))
    parser.add_argument("--test-lanes-root", type=Path, default=Path(os.environ.get("STEGVERSE_TEST_LANES_ROOT", Path.home() / ".stegverse" / "workloads" / "workflows")))
    parser.add_argument("--micro-node-root", type=Path, default=Path(os.environ.get("STEGVERSE_MICRO_NODE_ROOT", Path.home() / ".stegverse" / "workloads" / "micro-node-runtime")))
    parser.add_argument("--stegfin-governance-root", type=Path, default=Path(os.environ.get("STEGVERSE_STEGFIN_GOVERNANCE_ROOT", Path.home() / ".stegverse" / "workloads" / "stegfin-governance")))
    parser.add_argument("--primary-endpoint", default=os.environ.get("STEGVERSE_PRIMARY_ENDPOINT", "http://127.0.0.1:11435"))
    parser.add_argument("--launch-primary-if-needed", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--vault-agent-socket", default=os.environ.get("STEGVERSE_VAULT_AGENT_SOCKET", "/run/stegverse/vault-agent.sock"))
    parser.add_argument("--vault-broker-socket", default=os.environ.get("STEGVERSE_VAULT_BROKER_SOCKET", "/run/stegverse/vault-broker.sock"))
    parser.add_argument("--launch-vault-services-if-needed", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--model-selection", type=Path)
    parser.add_argument("--run-root", type=Path, default=Path.home() / ".stegverse" / "test-lanes" / "runs")
    args = parser.parse_args()

    receipt: dict[str, Any] = {
        "schema": "stegverse.test-lanes-direct-run-receipt/v1",
        "run_id": "SV-COST-NINE-LANE-v1:" + secrets.token_hex(8),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "heartbeat_required": False,
        "g18_required": False,
        "worker_coordinator_required": False,
        "primary_provider": "stegverse_local",
        "credential_authority": "TV/TVC",
        "third_party_role": "CONTROL_OR_FALLBACK_ONLY",
        "credential_material_present": False,
        "candidate_execution_count_expected": 5,
        "lane_evidence_count_expected": 9,
    }
    run_dir: Path | None = None
    primary_process: subprocess.Popen[str] | None = None
    vault_agent_process: subprocess.Popen[str] | None = None
    vault_broker_process: subprocess.Popen[str] | None = None
    service_sockets: tuple[Path, Path] | None = None
    try:
        preflight_environment()
        tvc_root = require_root(args.tvc_root, (
            "scripts/tvc_materialize_provider_capsule_bindings.py",
            "scripts/tvc_resolve_test_lane_capsules.py",
            "scripts/tvc_run_test_lane_external_candidate.py",
            "config/test_lanes_model_selection.sv-cost-nine-lane.v1.json",
        ), "TVC")
        lanes_root = require_root(args.test_lanes_root, (
            "experiments/stegverse-test-lanes/plan_test_lanes.py",
            "experiments/stegverse-test-lanes/run_stegverse_primary_candidate.py",
            "experiments/stegverse-test-lanes/build_lane_evidence.py",
            "experiments/stegverse-test-lanes/compare_test_lanes.py",
            "experiments/stegverse-test-lanes/manifests/sv-cost-nine-lane.v1.json",
            "experiments/sv-cost-program/nine-lane-results/task.json",
        ), "Test Lanes")
        model_path = (args.model_selection or (tvc_root / "config" / "test_lanes_model_selection.sv-cost-nine-lane.v1.json")).resolve()
        models = validate_model_selection(model_path)

        run_dir = args.run_root.expanduser().resolve() / receipt["run_id"].replace(":", "_")
        run_dir.mkdir(parents=True, exist_ok=False)

        try:
            health = primary_health(args.primary_endpoint)
            primary_mode = "PREEXISTING_LOOPBACK_RUNTIME"
        except Exception:
            if not args.launch_primary_if_needed:
                raise
            primary_process = start_test_primary(args.micro_node_root, args.primary_endpoint)
            health = primary_health(args.primary_endpoint)
            primary_mode = "BOUNDED_CANONICAL_TEST_PROCESS"

        configured_agent_socket = Path(args.vault_agent_socket)
        configured_broker_socket = Path(args.vault_broker_socket)
        if unix_health(configured_agent_socket) and unix_health(configured_broker_socket):
            vault_agent_socket = configured_agent_socket
            vault_broker_socket = configured_broker_socket
            vault_mode = "PREEXISTING_TVC_SERVICES"
        else:
            if not args.launch_vault_services_if_needed:
                raise RuntimeError("TVC_VAULT_SERVICES_NOT_READY")
            vault_agent_process, vault_broker_process, vault_agent_socket, vault_broker_socket = start_tvc_vault_services(args.stegfin_governance_root, run_dir)
            service_sockets = (vault_agent_socket, vault_broker_socket)
            vault_mode = "BOUNDED_EXISTING_TVC_SERVICES"

        plan, plan_steps = HELPERS.plan_and_resolve(tvc_root, lanes_root, run_dir, str(vault_agent_socket))
        if not isinstance(plan, Mapping):
            raise RuntimeError("TVC capsule materialization/resolution did not produce a plan")
        assert_full_nine_ready(plan)

        receipt["model_selection"] = models
        receipt["model_selection_ref"] = str(model_path)
        receipt["primary_runtime_mode"] = primary_mode
        receipt["primary_runtime_was_started_by_direct_runner"] = primary_process is not None
        receipt["vault_runtime_mode"] = vault_mode
        receipt["vault_services_were_started_by_direct_runner"] = vault_agent_process is not None or vault_broker_process is not None
        receipt["primary_health"] = {
            "state": health.get("state"),
            "model": health.get("model"),
            "private_endpoint_only": health.get("private_endpoint_only"),
            "third_party_inference_required": health.get("third_party_inference_required"),
        }
        receipt["plan_hash"] = plan.get("plan_hash")
        receipt["manifest_hash"] = plan.get("manifest_hash")
        receipt["lane_count_planned"] = 9
        receipt["candidate_execution_count_planned"] = 5

        success, execution = HELPERS.execute_run(
            plan=plan,
            plan_steps=plan_steps,
            models=models,
            endpoint=args.primary_endpoint,
            tvc_root=tvc_root,
            lanes_root=lanes_root,
            run_dir=run_dir,
            vault_broker_socket=str(vault_broker_socket),
        )
        receipt["execution"] = execution
        passed = execution_passed(success, execution if isinstance(execution, Mapping) else None)
        receipt["comparison_state"] = execution.get("comparison_state") if isinstance(execution, Mapping) else None
        receipt["lane_evidence_count"] = execution.get("lane_evidence_count") if isinstance(execution, Mapping) else None
        receipt["candidate_execution_count"] = 5 if passed else None
        receipt["state"] = "PASS" if passed else "FAILED"
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:
        receipt["state"] = "BLOCKED"
        receipt["reason"] = str(exc)
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    finally:
        if vault_broker_process is not None:
            stop_process(vault_broker_process)
        if vault_agent_process is not None:
            stop_process(vault_agent_process)
        if service_sockets is not None:
            for path in service_sockets:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            receipt["bounded_vault_services_stopped"] = True
        if primary_process is not None:
            stop_process(primary_process)
            receipt["primary_test_process_stopped"] = True

    if run_dir is None:
        args.run_root.expanduser().resolve().mkdir(parents=True, exist_ok=True)
        run_dir = args.run_root.expanduser().resolve() / receipt["run_id"].replace(":", "_")
        run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / "direct-run-receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": receipt["state"], "run_id": receipt["run_id"], "receipt": str(out), "heartbeat_required": False}, sort_keys=True))
    return 0 if receipt["state"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
