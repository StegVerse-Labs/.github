#!/usr/bin/env python3
"""One-shot activation of the complete resident StegVerse execution stack.

This is a local sovereign orchestration entrypoint. It packages the canonical
.github control plane, passes that bundle to local StegDeploy, and relies on
StegDeploy's post-health hook to materialize and invoke the resident bootstrap.
The bootstrap primes the resident WorkerCoordinator, dispatches resident requests,
and immediately advances independently admitted successors. G18 verification is
retained only as diagnostic/housekeeping evidence and does not gate downstream work.

The entrypoint grants no claim, fence, heartbeat, credential, route, provider,
or execution authority. It refuses hosted execution surfaces.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_sovereign_control_plane_bundle.py"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_RUNTIME_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "STEGVERSE_GITHUB_TOKEN",
)
DEFAULT_RECEIPT = ROOT / "receipts" / "sovereign-host" / "resident-stack-activation.latest.json"


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def clean_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    hosted = sorted(name for name in HOSTED_ENV if truthy(source.get(name)))
    if hosted:
        raise RuntimeError("hosted execution surface rejected: " + ",".join(hosted))
    for name in FORBIDDEN_RUNTIME_ENV:
        source.pop(name, None)
    source["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    source["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    return source


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def activate(
    source_root: Path,
    llm_adapter_root: Path,
    *,
    stegos_root: Path,
    kv_source_root: Path,
    health_url: str,
    receipt_path: Path,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    llm = llm_adapter_root.expanduser().resolve()
    receipt_path = receipt_path.expanduser().resolve()
    packager = source / "scripts" / "package_sovereign_control_plane_bundle.py"
    stegdeploy = llm / "scripts" / "stegdeploy_bootstrap.py"
    if not packager.is_file():
        raise RuntimeError("canonical control-plane packager missing")
    if not stegdeploy.is_file():
        raise RuntimeError("StegDeploy bootstrap missing")

    safe_env = clean_env(env)
    with tempfile.TemporaryDirectory(prefix="stegverse-resident-stack-") as tmp:
        bundle = Path(tmp) / "sovereign-control-plane.zip"
        package = runner(
            [
                sys.executable, str(packager),
                "--source-root", str(source),
                "--output", str(bundle),
                "--stegos-root", str(stegos_root.expanduser().resolve()),
                "--kv-source-root", str(kv_source_root.expanduser().resolve()),
            ],
            cwd=source,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
            env=safe_env,
        )
        package_result = parse_last_json(package.stdout) or {}
        if package.returncode != 0 or not bundle.is_file():
            raise RuntimeError("control-plane bundle packaging failed")

        deploy_env = dict(safe_env)
        deploy_env["STEGVERSE_ORG_CONTROL_BUNDLE"] = str(bundle)
        deploy = runner(
            [
                sys.executable, str(stegdeploy),
                "deploy",
                "--health-url", health_url,
            ],
            cwd=llm,
            check=False,
            capture_output=True,
            text=True,
            timeout=5400,
            env=deploy_env,
        )

        deployment_receipt_path = llm / ".stegdeploy" / "deployment-receipt.json"
        deployment = load_json(deployment_receipt_path) or parse_last_json(deploy.stdout) or {}
        resident = deployment.get("resident_control_plane_bootstrap") if isinstance(deployment, dict) else None
        resident = resident if isinstance(resident, dict) else {}
        resident_result = resident.get("result") if isinstance(resident.get("result"), dict) else {}
        skap = resident_result.get("post_bootstrap_tvc_skap_successor") if isinstance(resident_result, dict) else None
        skap = skap if isinstance(skap, dict) else {}

        prime = resident_result.get("post_install_worker_prime") if isinstance(resident_result, dict) else None
        prime = prime if isinstance(prime, dict) else {}
        dispatch = resident_result.get("post_bootstrap_resident_request_dispatch") if isinstance(resident_result, dict) else None
        dispatch = dispatch if isinstance(dispatch, dict) else {}
        resident_task_capable = prime.get("task_capable_cycle_observed") is True
        resident_dispatch_attempted = dispatch.get("attempted") is True

        state = "COMPLETE" if (
            deploy.returncode == 0
            and resident.get("attempted") is True
            and resident_task_capable
            and resident_dispatch_attempted
        ) else "INCOMPLETE"

        receipt = {
            "schema": "stegverse.resident-stack-activation/v1",
            "state": state,
            "source_root": str(source),
            "llm_adapter_root": str(llm),
            "health_url": health_url,
            "control_bundle_packaged": True,
            "stegos_source_bundled": True,
            "kv_source_bundled": True,
            "control_bundle_sha256": package_result.get("bundle_sha256"),
            "stegdeploy_returncode": deploy.returncode,
            "stegdeploy_receipt_ref": str(deployment_receipt_path),
            "stegdeploy_receipt_observed": bool(deployment),
            "resident_bootstrap": resident,
            "resident_task_capable_cycle_observed": resident_task_capable,
            "resident_request_dispatch_attempted": resident_dispatch_attempted,
            "g18_housekeeping_state": resident.get("state"),
            "g18_required_for_stack_completion": False,
            "tvc_skap_successor_attempted": skap.get("attempted") is True,
            "tvc_skap_successor_state": skap.get("state"),
            "network_source_fetch_performed_by_orchestrator": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "heartbeat_grants_execution_authority": False,
            "orchestrator_grants_authority": False,
            "third_party_primary_runtime": False,
            "authority_effect": "NONE_LOCAL_STACK_ORCHESTRATION_ONLY",
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--llm-adapter-root", type=Path, default=None)
    parser.add_argument("--health-url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--stegos-root", type=Path)
    parser.add_argument("--kv-source-root", type=Path)
    parser.add_argument("--receipt-path", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    llm = args.llm_adapter_root
    if llm is None:
        configured = str(os.environ.get("STEGVERSE_LLM_ADAPTER_ROOT") or "").strip()
        if not configured:
            raise SystemExit("--llm-adapter-root or STEGVERSE_LLM_ADAPTER_ROOT is required")
        llm = Path(configured)
    stegos = args.stegos_root or (Path(os.environ["STEGVERSE_STEGOS_ROOT"]) if os.environ.get("STEGVERSE_STEGOS_ROOT") else None)
    kv_source = args.kv_source_root or (Path(os.environ["STEGVERSE_KV_SOURCE_ROOT"]) if os.environ.get("STEGVERSE_KV_SOURCE_ROOT") else None)
    if stegos is None or kv_source is None:
        raise SystemExit("--stegos-root/STEGVERSE_STEGOS_ROOT and --kv-source-root/STEGVERSE_KV_SOURCE_ROOT are required")
    receipt = activate(
        args.source_root,
        llm,
        stegos_root=stegos,
        kv_source_root=kv_source,
        health_url=args.health_url,
        receipt_path=args.receipt_path,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
