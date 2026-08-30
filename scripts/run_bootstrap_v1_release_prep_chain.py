#!/usr/bin/env python3
"""Execute Bootstrap v1 release-preparation tasks on one sovereign resident opportunity."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = Path("scripts/run_worker_runtime.py")
REGISTRY_REL = Path("control/worker-registry.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CHAIN_RECEIPT_REL = Path("receipts/sovereign-host/bootstrap-v1-release-prep-chain.latest.json")

UPSTREAM_TASK = "SV-DN1-PRODUCTION-SOURCE-PREP-001"
TASKS = (
    "BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001",
    "BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001",
    "BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001",
    "BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001",
)

HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN",
    "HUGGING_FACE_HUB_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET", "OAUTH_TOKEN",
)
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_SOURCE_PACKAGE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT",
)

Runner = Callable[..., subprocess.CompletedProcess[str]]


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def hosted_environment(values: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if values is None else values
    return sorted(name for name in HOSTED_ENV if truthy(env.get(name)))


def clean_exec_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    hosted = hosted_environment(source)
    if hosted:
        raise RuntimeError(
            "hosted execution cannot produce sovereign Bootstrap v1 release-prep evidence: "
            + ",".join(hosted)
        )
    env = {name: source[name] for name in NONSECRET_ENV if source.get(name)}
    for name in FORBIDDEN_CREDENTIAL_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def default_runtime_root(values: Mapping[str, str] | None = None) -> Path:
    env = os.environ if values is None else values
    override = str(env.get("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    base = Path(str(env.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").expanduser().resolve()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _task(registry: Mapping[str, Any], task_id: str) -> dict[str, Any] | None:
    matches = [
        row for row in registry.get("tasks", [])
        if isinstance(row, dict) and row.get("task_id") == task_id
    ]
    if len(matches) > 1:
        raise RuntimeError(f"duplicate task identity in runtime registry: {task_id}")
    return dict(matches[0]) if matches else None


def _state_root(values: Mapping[str, str], env_name: str, default: Path) -> Path:
    raw = str(values.get(env_name) or "").strip()
    return Path(raw).expanduser().resolve() if raw else default.expanduser().resolve()


def source_prep_receipt_path(values: Mapping[str, str]) -> Path:
    root = _state_root(
        values,
        "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
        Path.home() / ".stegverse" / "state" / "sv-dn1-production-source-prep",
    )
    return root / "receipts" / "latest.json"


def validate_source_prep_prerequisite(values: Mapping[str, str]) -> dict[str, Any]:
    path = source_prep_receipt_path(values)
    if not path.is_file():
        raise RuntimeError(f"Bootstrap release prep prerequisite receipt missing: {path}")
    receipt = _load(path)
    expected = {
        "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
        "state": "COMPLETE",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "source_identity_scheme": "sha256-content-manifest",
        "migration_anchors_verified": True,
        "network_source_fetch_performed": False,
        "github_platform_required": False,
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "sdk_admitted": False,
    }
    failures = [
        f"{field}={receipt.get(field)!r}, expected {wanted!r}"
        for field, wanted in expected.items()
        if receipt.get(field) != wanted
    ]
    components = {
        "stegverse.sdk",
        "stegverse.stegcore",
        "stegverse.core-lite",
        "stegverse.master-records",
    }
    ids = receipt.get("source_identities")
    roots = receipt.get("source_roots")
    if not isinstance(ids, dict) or set(ids) != components:
        failures.append("source_identities must contain exactly four canonical components")
    elif not all(
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(ch in "0123456789abcdef" for ch in value[7:])
        for value in ids.values()
    ):
        failures.append("source identities must all be sha256:<64 lowercase hex>")
    if not isinstance(roots, dict) or set(roots) != components:
        failures.append("source_roots must contain exactly four canonical components")
    elif not all(isinstance(value, str) and value for value in roots.values()):
        failures.append("source roots must be non-empty local locators")
    if failures:
        raise RuntimeError("Bootstrap release prep prerequisite failed validation: " + "; ".join(failures))
    return {"receipt_path": str(path), "receipt": receipt}


def _receipt_specs(values: Mapping[str, str]) -> dict[str, tuple[Path, dict[str, Any]]]:
    home = Path.home()
    source_freeze = _state_root(
        values,
        "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT",
        home / ".stegverse" / "state" / "bootstrap-v1-source-identity-freeze",
    )
    package_prod = home / ".stegverse" / "state" / "bootstrap-v1-source-package-production"
    rc = _state_root(
        values,
        "STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT",
        home / ".stegverse" / "state" / "bootstrap-v1-release-candidate-freeze",
    )
    bundle = home / ".stegverse" / "state" / "bootstrap-v1-distributable-bundle"
    return {
        "BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001": (
            source_freeze / "receipts" / "latest.json",
            {
                "schema": "stegverse.bootstrap.source-identity-freeze-receipt/v1",
                "state": "COMPLETE",
                "transition_id": "BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN",
                "component_count": 4,
                "source_identity_scheme": "sha256-content-manifest",
                "github_platform_required": False,
                "network_access_performed": False,
                "credential_used": False,
                "github_token_used": False,
                "repository_writeback_performed": False,
                "execution_authority": "NONE",
            },
        ),
        "BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001": (
            package_prod / "receipts" / "latest.json",
            {
                "schema": "stegverse.bootstrap.source-package-production-receipt/v1",
                "state": "COMPLETE",
                "transition_id": "BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED",
                "source_identity_scheme": "sha256-content-manifest",
                "package_schema": "stegverse.source-package/v1",
                "package_version": "1.0.0",
                "component_count": 4,
                "github_platform_required": False,
                "specific_external_platform_required": False,
                "network_access_performed": False,
                "credential_used": False,
                "github_token_used": False,
                "repository_writeback_performed": False,
                "package_execution_performed": False,
                "sdk_admitted": False,
                "release_activated": False,
                "publication_performed": False,
                "execution_authority": "NONE",
            },
        ),
        "BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001": (
            rc / "receipts" / "latest.json",
            {
                "schema": "stegverse.bootstrap.release-candidate-freeze-receipt/v1",
                "state": "COMPLETE",
                "transition_id": "BOOTSTRAP_V1_RELEASE_CANDIDATE_FROZEN",
                "candidate_version": "1.0.0-rc.1",
                "github_platform_required": False,
                "network_access_performed": False,
                "credential_used": False,
                "repository_writeback_performed": False,
                "release_activated": False,
                "publication_performed": False,
                "execution_authority": "NONE",
            },
        ),
        "BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001": (
            bundle / "receipts" / "latest.json",
            {
                "schema": "stegverse.bootstrap.distributable-bundle-build-receipt/v1",
                "state": "COMPLETE",
                "transition_id": "BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT",
                "bundle_version": "1.0.0-rc.1",
                "component_count": 4,
                "github_platform_required": False,
                "network_access_performed": False,
                "credential_used": False,
                "repository_writeback_performed": False,
                "release_activated": False,
                "publication_performed": False,
                "execution_authority": "NONE",
            },
        ),
    }


def validate_durable_receipt(task_id: str, values: Mapping[str, str]) -> dict[str, Any]:
    path, expected = _receipt_specs(values)[task_id]
    if not path.is_file():
        raise RuntimeError(f"{task_id}: durable receipt missing: {path}")
    receipt = _load(path)
    failures = [
        f"{field}={receipt.get(field)!r}, expected {wanted!r}"
        for field, wanted in expected.items()
        if receipt.get(field) != wanted
    ]
    if task_id == "BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001":
        rows = receipt.get("packages")
        if not isinstance(rows, list) or len(rows) != 4:
            failures.append("packages must contain four rows")
        elif {row.get("component_id") for row in rows if isinstance(row, dict)} != {
            "stegverse.sdk", "stegverse.stegcore", "stegverse.core-lite", "stegverse.master-records"
        }:
            failures.append("package component set mismatch")
    if failures:
        raise RuntimeError(f"{task_id}: durable receipt failed validation: " + "; ".join(failures))
    return {"task_id": task_id, "receipt_path": str(path), "receipt": receipt}


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    temp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def execute_chain(
    source_root: Path,
    runtime_root: Path,
    *,
    runner: Runner = subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    if hosted_environment(values):
        raise RuntimeError("hosted execution cannot produce sovereign Bootstrap v1 release-prep evidence")

    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    refresh_receipt = refresh(source, runtime)

    carrier = runtime / CARRIER_REL
    if not carrier.is_file():
        return {
            "schema": "stegverse.bootstrap.release-prep-chain/v1",
            "state": "HANDOFF_READY",
            "transition_id": "BOOTSTRAP_V1_SOVEREIGN_CARRIER_REFERENCE_PENDING",
            "completed_tasks": [],
            "next_task": TASKS[0],
            "runtime_root": str(runtime),
            "refresh_receipt": refresh_receipt,
            "github_token_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE_ORCHESTRATION_ONLY",
        }

    runner_path = runtime / RUNNER_REL
    registry_path = runtime / REGISTRY_REL
    if not runner_path.is_file():
        raise RuntimeError(f"targeted WorkerCoordinator runner missing after refresh: {runner_path}")
    if not registry_path.is_file():
        raise RuntimeError(f"mutable worker registry missing from resident runtime: {registry_path}")

    registry = _load(registry_path)
    upstream = _task(registry, UPSTREAM_TASK)
    if upstream is None or upstream.get("state") != "COMPLETED":
        return {
            "schema": "stegverse.bootstrap.release-prep-chain/v1",
            "state": "HANDOFF_READY",
            "transition_id": "BOOTSTRAP_V1_PRODUCTION_SOURCE_PREP_PENDING",
            "completed_tasks": [],
            "next_task": TASKS[0],
            "upstream_task_state": None if upstream is None else upstream.get("state"),
            "runtime_root": str(runtime),
            "refresh_receipt": refresh_receipt,
            "github_token_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE_ORCHESTRATION_ONLY",
        }

    try:
        prerequisite = validate_source_prep_prerequisite(values)
    except Exception as exc:
        return {
            "schema": "stegverse.bootstrap.release-prep-chain/v1",
            "state": "HANDOFF_READY",
            "transition_id": "BOOTSTRAP_V1_PRODUCTION_SOURCE_PREP_RECEIPT_PENDING",
            "completed_tasks": [],
            "next_task": TASKS[0],
            "error": str(exc),
            "runtime_root": str(runtime),
            "refresh_receipt": refresh_receipt,
            "github_token_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE_ORCHESTRATION_ONLY",
        }

    child_env = clean_exec_env(values)
    completed_tasks: list[str] = []
    task_results: list[dict[str, Any]] = []

    for task_id in TASKS:
        registry = _load(registry_path)
        row = _task(registry, task_id)

        if row is not None and row.get("state") == "COMPLETED":
            validated = validate_durable_receipt(task_id, values)
            completed_tasks.append(task_id)
            task_results.append({
                "task_id": task_id,
                "execution_attempted": False,
                "registry_state": "COMPLETED",
                "durable_receipt": validated,
            })
            continue

        if row is not None and row.get("state") in {"ACTIVE", "BLOCKED"}:
            return {
                "schema": "stegverse.bootstrap.release-prep-chain/v1",
                "state": "HANDOFF_READY",
                "transition_id": "BOOTSTRAP_V1_EXISTING_TASK_LIFECYCLE_MUST_RESOLVE",
                "completed_tasks": completed_tasks,
                "next_task": task_id,
                "task_state": row.get("state"),
                "claim_id": row.get("claim_id"),
                "worker_id": row.get("worker_id"),
                "runtime_root": str(runtime),
                "refresh_receipt": refresh_receipt,
                "task_results": task_results,
                "github_token_required": False,
                "second_machine_required": False,
                "authority_effect": "NONE_ORCHESTRATION_ONLY",
            }

        command = [
            sys.executable,
            str(runner_path),
            "--root",
            str(runtime),
            "--task-id",
            task_id,
        ]
        completed = runner(
            command,
            cwd=runtime,
            capture_output=True,
            text=True,
            check=False,
            env=child_env,
            timeout=900,
        )

        registry = _load(registry_path)
        row = _task(registry, task_id)
        state = None if row is None else row.get("state")
        result = {
            "task_id": task_id,
            "execution_attempted": True,
            "command": command,
            "returncode": completed.returncode,
            "registry_state": state,
            "stderr_tail": (completed.stderr or "")[-2000:],
        }

        if completed.returncode != 0 or state != "COMPLETED":
            task_results.append(result)
            return {
                "schema": "stegverse.bootstrap.release-prep-chain/v1",
                "state": "HANDOFF_READY",
                "transition_id": "BOOTSTRAP_V1_RELEASE_PREP_STEP_NOT_TERMINAL",
                "completed_tasks": completed_tasks,
                "next_task": task_id,
                "task_state": state,
                "runtime_root": str(runtime),
                "refresh_receipt": refresh_receipt,
                "task_results": task_results,
                "github_token_required": False,
                "second_machine_required": False,
                "authority_effect": "NONE_ORCHESTRATION_ONLY",
            }

        try:
            validated = validate_durable_receipt(task_id, values)
        except Exception as exc:
            result["durable_receipt_error"] = str(exc)
            task_results.append(result)
            return {
                "schema": "stegverse.bootstrap.release-prep-chain/v1",
                "state": "BLOCKED",
                "transition_id": "BOOTSTRAP_V1_RELEASE_PREP_DURABLE_RECEIPT_MISMATCH",
                "completed_tasks": completed_tasks,
                "next_task": task_id,
                "runtime_root": str(runtime),
                "refresh_receipt": refresh_receipt,
                "task_results": task_results,
                "github_token_required": False,
                "second_machine_required": False,
                "authority_effect": "NONE_ORCHESTRATION_ONLY",
            }

        result["durable_receipt"] = validated
        task_results.append(result)
        completed_tasks.append(task_id)

    receipt = {
        "schema": "stegverse.bootstrap.release-prep-chain/v1",
        "state": "COMPLETE",
        "transition_id": "BOOTSTRAP_V1_SOVEREIGN_RELEASE_PREP_COMPLETE",
        "completed_tasks": completed_tasks,
        "next_task": None,
        "runtime_root": str(runtime),
        "source_root": str(source),
        "refresh_receipt": refresh_receipt,
        "source_prep_prerequisite": prerequisite,
        "task_results": task_results,
        "github_platform_required": False,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "repository_writeback_performed": False,
        "package_execution_performed": False,
        "sdk_admitted": False,
        "release_activated": False,
        "publication_performed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_ORCHESTRATION_ONLY",
    }
    _atomic_json(runtime / CHAIN_RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute the Bootstrap v1 sovereign release-preparation chain."
    )
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runtime-root", type=Path, default=default_runtime_root())
    args = parser.parse_args()
    try:
        result = execute_chain(args.source_root, args.runtime_root)
    except Exception as exc:
        result = {
            "schema": "stegverse.bootstrap.release-prep-chain/v1",
            "state": "BLOCKED",
            "transition_id": "BOOTSTRAP_V1_SOVEREIGN_RELEASE_PREP_BLOCKED",
            "error": str(exc),
            "github_token_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE_ORCHESTRATION_ONLY",
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"COMPLETE", "HANDOFF_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
