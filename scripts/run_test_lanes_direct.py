#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "workers" / "test_lanes_autolaunch_worker.py"
PROVIDERS = ("openai", "anthropic", "deepseek", "kimi")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical StegVerse nine-lane experiment directly without heartbeat/G18 dependency.")
    parser.add_argument("--tvc-root", type=Path, default=Path(os.environ.get("STEGVERSE_TVC_ROOT", Path.home() / ".stegverse" / "workloads" / "TVC")))
    parser.add_argument("--test-lanes-root", type=Path, default=Path(os.environ.get("STEGVERSE_TEST_LANES_ROOT", Path.home() / ".stegverse" / "workloads" / "workflows")))
    parser.add_argument("--primary-endpoint", default=os.environ.get("STEGVERSE_PRIMARY_ENDPOINT", "http://127.0.0.1:8765"))
    parser.add_argument("--vault-agent-socket", default=os.environ.get("STEGVERSE_VAULT_AGENT_SOCKET", "/run/stegverse/vault-agent.sock"))
    parser.add_argument("--vault-broker-socket", default=os.environ.get("STEGVERSE_VAULT_BROKER_SOCKET", "/run/stegverse/vault-broker.sock"))
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
    }
    run_dir: Path | None = None
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
        health = primary_health(args.primary_endpoint)
        if not Path(args.vault_agent_socket).exists():
            raise RuntimeError("TVC vault-agent socket is not present")
        if not Path(args.vault_broker_socket).exists():
            raise RuntimeError("TVC vault-broker socket is not present")

        run_dir = args.run_root.expanduser().resolve() / receipt["run_id"].replace(":", "_")
        run_dir.mkdir(parents=True, exist_ok=False)
        plan, plan_steps = HELPERS.plan_and_resolve(tvc_root, lanes_root, run_dir, args.vault_agent_socket)
        if not isinstance(plan, Mapping):
            raise RuntimeError("TVC capsule materialization/resolution did not produce a plan")
        assert_full_nine_ready(plan)

        receipt["model_selection"] = models
        receipt["model_selection_ref"] = str(model_path)
        receipt["primary_health"] = {
            "state": health.get("state"),
            "model": health.get("model"),
            "private_endpoint_only": health.get("private_endpoint_only"),
            "third_party_inference_required": health.get("third_party_inference_required"),
        }
        receipt["plan_hash"] = plan.get("plan_hash")
        receipt["manifest_hash"] = plan.get("manifest_hash")
        receipt["lane_count"] = 9
        receipt["candidate_execution_count"] = 5

        success, execution = HELPERS.execute_run(
            plan=plan,
            plan_steps=plan_steps,
            models=models,
            endpoint=args.primary_endpoint,
            tvc_root=tvc_root,
            lanes_root=lanes_root,
            run_dir=run_dir,
            vault_broker_socket=args.vault_broker_socket,
        )
        receipt["execution"] = execution
        comparison = execution.get("comparison") if isinstance(execution, Mapping) else None
        receipt["state"] = "PASS" if success and isinstance(comparison, Mapping) and comparison.get("state") == "PASS" and comparison.get("lane_evidence_count") == 9 else "FAILED"
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:
        receipt["state"] = "BLOCKED"
        receipt["reason"] = str(exc)
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()

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
