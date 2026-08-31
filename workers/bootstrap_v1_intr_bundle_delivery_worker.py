#!/usr/bin/env python3
"""Fenced launcher for the Bootstrap v1 Universal InTr bundle-delivery runtime."""
from __future__ import annotations

import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import time
from typing import Any, Mapping
import urllib.request

TASK_ID = "BOOTSTRAP-V1-INTR-BUNDLE-DELIVERY-001"
WORKER_ID = "bootstrap-v1-intr-bundle-delivery-worker"
CONFIG_ENV = "STEGVERSE_BOOTSTRAP_V1_INTR_ROUTE_CONFIG"
DEFAULT_CONFIG = Path.home() / ".stegverse" / "config" / "bootstrap-v1-intr-bundle-delivery.json"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL",
    "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "OAUTH_TOKEN",
)


class RoutePending(RuntimeError):
    pass


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("unexpected invocation schema")
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID or task.get("worker_id") != WORKER_ID:
        raise RuntimeError("task/worker identity mismatch")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim required")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(fence, int) or fence <= 22:
        raise RuntimeError("fresh fencing token >22 required")
    authority = (invocation.get("handoff") or {}).get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("GitHub token boundary drift")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("non-TV/TVC credential boundary drift")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat authority drift")
    return dict(task)


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if not path.is_file():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("declared") is not True:
            raise RoutePending("sovereign node is not declared")
        if value.get("credential_authority") != "TV/TVC":
            raise RuntimeError("node credential authority drift")
        if value.get("github_token_required") is not False:
            raise RuntimeError("node requires GitHub token")
        return path, value
    raise RoutePending("no declared sovereign StegVerse node marker")


def config_path() -> Path:
    raw = str(os.getenv(CONFIG_ENV) or "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_CONFIG.expanduser().resolve()


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        raise RoutePending(f"Bootstrap v1 InTr route config not present: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Bootstrap v1 InTr route config object required")
    required = (
        "stegos_root", "runtime_root", "bundle_state_root", "host", "port",
        "allowed_origin", "boundary_identity_ref",
    )
    for key in required:
        if value.get(key) in (None, ""):
            raise RoutePending(f"route config missing {key}")
    if value.get("credential_authority") != "TV/TVC":
        raise RuntimeError("route credential authority drift")
    if value.get("github_token_runtime_authority") != "NONE":
        raise RuntimeError("route GitHub authority drift")
    if value.get("universal_intr_policy_id") != "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001":
        raise RuntimeError("route Universal InTr policy drift")

    for key in ("stegos_root", "runtime_root", "bundle_state_root"):
        if not Path(str(value[key])).expanduser().is_dir():
            raise RoutePending(f"local source/runtime root unavailable: {key}")
    bundle = Path(str(value["bundle_state_root"])).expanduser().resolve() / "bundle" / "bootstrap-v1-1.0.0-rc.1.bundle.json"
    receipt = Path(str(value["bundle_state_root"])).expanduser().resolve() / "receipts" / "latest.json"
    if not bundle.is_file() or not receipt.is_file():
        raise RoutePending("canonical Bootstrap v1 bundle state not materialized")

    host = str(value["host"])
    if host not in {"127.0.0.1", "::1", "localhost"}:
        for key in ("tls_cert", "tls_key"):
            if not value.get(key):
                raise RoutePending(f"public Bootstrap v1 route requires {key}")
            if not Path(str(value[key])).expanduser().is_file():
                raise RoutePending(f"public Bootstrap v1 route {key} not materialized")
    return value


def service_paths(config: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    root = (
        Path(str(config["runtime_root"])).expanduser().resolve()
        / "receipts" / "sovereign-network" / "bootstrap-v1-intr"
    )
    return root / "receiver.pid", root / "receiver.log", root / "receiver.latest.json"


def pid_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid(path: Path) -> int | None:
    try:
        value = int(path.read_text(encoding="utf-8").strip())
        return value if pid_alive(value) else None
    except Exception:
        return None


def observed_delivery(config: Mapping[str, Any]) -> dict[str, Any] | None:
    root = (
        Path(str(config["runtime_root"])).expanduser().resolve()
        / "receipts" / "sovereign-network" / "bootstrap-v1-intr"
    )
    if not root.is_dir():
        return None
    for path in sorted(root.glob("*.json")):
        if path.name == "receiver.latest.json":
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(value, dict):
            continue
        if (
            value.get("state") == "DELIVERY_FORWARDED"
            and value.get("transition_id") == "BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED"
            and value.get("transport_profile") == "stegverse.universal-intr.adjacent-hop/v1"
            and value.get("universal_intr_policy_id") == "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001"
            and value.get("credential_used") is False
            and value.get("github_token_used") is False
            and value.get("execution_authority") == "NONE"
        ):
            ingress = value.get("request_ingress_receipt") or {}
            egress = value.get("response_egress_receipt") or {}
            if egress.get("prior_receipt_hash") != ingress.get("receipt_hash"):
                raise RuntimeError("Bootstrap v1 delivery receipt chain drift")
            return {"path": str(path), "value": value}
    return None


def readiness(config: Mapping[str, Any]) -> dict[str, Any]:
    host = str(config["host"])
    port = int(config["port"])
    tls = host not in {"127.0.0.1", "::1", "localhost"}
    scheme = "https" if tls else "http"
    context = ssl._create_unverified_context() if tls else None
    with urllib.request.urlopen(
        f"{scheme}://127.0.0.1:{port}/intr/bootstrap-v1/readiness",
        timeout=2,
        context=context,
    ) as response:
        value = json.loads(response.read().decode("utf-8"))
        status = response.status
    if status != 200 or value.get("state") != "READY" or value.get("transport") != "InTr":
        raise RoutePending("Bootstrap v1 receiver readiness not observed")
    if value.get("transport_profile") != "stegverse.universal-intr.adjacent-hop/v1":
        raise RuntimeError("Bootstrap v1 receiver transport profile drift")
    if value.get("universal_intr_policy_id") != "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001":
        raise RuntimeError("Bootstrap v1 receiver Universal InTr policy drift")
    if value.get("credential_required") is not False or value.get("execution_authority") != "NONE":
        raise RuntimeError("Bootstrap v1 receiver readiness authority drift")
    return value


def ensure_receiver(config: Mapping[str, Any], server: Path) -> dict[str, Any]:
    observed = observed_delivery(config)
    if observed is not None:
        return {
            "schema": "stegverse.bootstrap.intr-bundle-delivery-worker-completion/v1",
            "state": "COMPLETE",
            "transition_id": "BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED",
            "delivery_receipt_ref": observed["path"],
            "bundle_identity": observed["value"].get("bundle_identity"),
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "authority_effect": "NONE_BUNDLE_DELIVERY_ONLY",
        }

    pid_file, log_file, ready_file = service_paths(config)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid = read_pid(pid_file)
    if pid is None:
        command = [
            sys.executable,
            str(server),
            "--stegos-root", str(config["stegos_root"]),
            "--runtime-root", str(config["runtime_root"]),
            "--bundle-state-root", str(config["bundle_state_root"]),
            "--host", str(config["host"]),
            "--port", str(config["port"]),
            "--max-requests", "0",
            "--allowed-origin", str(config["allowed_origin"]),
            "--boundary-identity-ref", str(config["boundary_identity_ref"]),
        ]
        if config.get("tls_cert"):
            command += ["--tls-cert", str(config["tls_cert"])]
        if config.get("tls_key"):
            command += ["--tls-key", str(config["tls_key"])]
        log = log_file.open("ab", buffering=0)
        child_env = {
            "PATH": os.getenv("PATH", ""),
            "HOME": os.getenv("HOME", ""),
            "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
            "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE",
        }
        process = subprocess.Popen(
            command,
            cwd=server.parent.parent,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
        pid = process.pid
        pid_file.write_text(str(pid) + "\n", encoding="utf-8")

    observed_readiness = None
    last: Exception | None = None
    for _ in range(40):
        if not pid_alive(pid):
            raise RuntimeError("Bootstrap v1 receiver exited before readiness")
        try:
            observed_readiness = readiness(config)
            break
        except Exception as exc:
            last = exc
            time.sleep(0.1)
    if observed_readiness is None:
        raise RoutePending("Bootstrap v1 receiver readiness unavailable:" + type(last).__name__)

    receipt = {
        "schema": "stegverse.bootstrap.intr-bundle-delivery-readiness-receipt/v1",
        "state": "READY",
        "transition_id": "BOOTSTRAP_V1_INTR_BUNDLE_RECEIVER_READY",
        "pid": pid,
        "host": config["host"],
        "port": config["port"],
        "readiness": observed_readiness,
        "persistent_receiver": True,
        "delivery_observed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "public_tls_terminated_by": config.get("public_tls_terminated_by"),
        "authority_effect": "NONE_READINESS_ONLY",
    }
    ready_file.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(key)) for key in HOSTED_ENV):
        raise RuntimeError("hosted runtime forbidden")
    present = [key for key in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(key))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden:" + ",".join(sorted(present)))
    task = validate_invocation(invocation)
    node_path, _ = find_node()
    config = load_config()
    server = Path(__file__).resolve().parents[1] / "scripts" / "serve_bootstrap_v1_intr_bundle_delivery.py"
    result = ensure_receiver(config, server)
    result["task_id"] = TASK_ID
    result["worker_id"] = WORKER_ID
    result["claim_id"] = task.get("claim_id")
    result["fencing_token"] = (task.get("heartbeat_timing") or {}).get("fencing_token")
    result["node_declaration_ref"] = str(node_path)
    return result


def response(state: str, transition: str, **extra: Any) -> dict[str, Any]:
    value = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "authority_effect": "NONE_BUNDLE_DELIVERY_ONLY",
    }
    value.update(extra)
    return value


def main() -> int:
    try:
        invocation = json.loads(sys.stdin.readline())
        result = execute(invocation)
        if result.get("state") == "COMPLETE":
            print(json.dumps(response(
                "COMPLETED",
                "BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED",
                evidence_refs=[result.get("delivery_receipt_ref")],
                result=result,
            ), sort_keys=True))
            return 0
        config = load_config()
        ready_ref = (
            Path(str(config["runtime_root"])).expanduser().resolve()
            / "receipts" / "sovereign-network" / "bootstrap-v1-intr" / "receiver.latest.json"
        )
        print(json.dumps(response(
            "ACTIVE",
            "BOOTSTRAP_V1_INTR_BUNDLE_RECEIVER_READY",
            evidence_refs=[str(ready_ref)],
            result=result,
        ), sort_keys=True))
        return 0
    except RoutePending as exc:
        print(json.dumps(response(
            "HANDOFF_READY",
            "BOOTSTRAP_V1_INTR_BUNDLE_ROUTE_PENDING",
            blocker={
                "dependency_class": "SOVEREIGN_BOOTSTRAP_BUNDLE_ROUTE",
                "problem_statement": str(exc),
                "solution_required": True,
                "may_remain_blocked": False,
                "machine_observable_release_condition": "declared node + local StegOS root + canonical built bundle + admitted Bootstrap v1 route configuration/TLS identity exist",
                "physical_additional_machine_required": False,
                "third_party_runtime_required": False,
                "github_token_required": False,
                "non_tv_tvc_secret_or_token_required": False,
                "human_action_required": False,
            },
        ), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(response(
            "BLOCKED",
            "BOOTSTRAP_V1_INTR_BUNDLE_RUNTIME_BLOCKED",
            error=str(exc),
        ), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
