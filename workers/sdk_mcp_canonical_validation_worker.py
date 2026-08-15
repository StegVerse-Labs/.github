#!/usr/bin/env python3
"""Machine-owned exact-artifact validation worker for SDK MCP production tests.

The worker creates no credential, route, custody, or execution authority. It may run
only on a declared non-hosted sovereign StegVerse node after the canonical scheduler
has assigned a collision-safe claim. Canonical source roots must already be locally
materialized. No repository checkout or protected credential is performed here.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

TASK_ID = "SDK-MCP-CANONICAL-VALIDATION-009"
WORKER_ID = "sdk-mcp-canonical-validation-worker"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
ROOT_ENV = {
    "sdk": "STEGVERSE_SDK_SOURCE_ROOT",
    "stegcore": "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "core_lite": "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "master_records": "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
}
REQUIRED_FILES = {
    "sdk": "stegverse/mcp_governance.py",
    "stegcore": "src/stegcore/transaction_lifecycle.py",
    "core_lite": "core_lite/transaction_route.py",
    "master_records": "services/manifest_receipt_custody.py",
}
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV_MARKERS = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "API_KEY", "PRIVATE_KEY", "PASSWORD",
    "BEARER", "AUTHORIZATION", "WALLET_KEY", "MNEMONIC", "SEED", "SECRET", "TOKEN",
    "AWS_", "AZURE_", "GOOGLE_APPLICATION_CREDENTIALS",
)
Runner = Callable[..., subprocess.CompletedProcess[str]]

EXACT_RUN_PROGRAM = r'''
import json
from pathlib import Path
from stegverse.mcp_governance import run_mcp_governed_test
from stegverse.sovereign_validation_runtime import replay_sovereign, reconstruct_sovereign

root = Path.home() / ".stegverse" / "sdk-mcp-canonical-validation-009"
root.mkdir(parents=True, exist_ok=True)
db = str(root / "master-records.db")
try:
    Path(db).unlink()
except FileNotFoundError:
    pass

inspect = run_mcp_governed_test(
    source="reference", descriptor_path=None, tool_name="inspect_state", arguments={},
    custody_db=db, host_identity="sdk-mcp-canonical-validation-worker",
)
inspect_g = inspect["governed_result"]
rid = inspect["manifest_receipt_id"]
replay = replay_sovereign(rid, custody_db=db)
reconstruct = reconstruct_sovereign(rid, custody_db=db)
write = run_mcp_governed_test(
    source="reference", descriptor_path=None, tool_name="write_bounded_value", arguments={"value": 42},
    custody_db=db, host_identity="sdk-mcp-canonical-validation-worker",
)
write_g = write["governed_result"]

assert inspect_g["governance_state"] == "ALLOW"
assert inspect_g["master_records_custody_status"] == "RECORDED"
assert inspect_g["chain_verified"] is True
assert inspect_g["transaction_identity_continuous"] is True
assert inspect_g["route_receipt_ids"]
assert inspect_g["execution_result"]["status"] == "MCP_TOOL_RESULT_OBSERVED"
assert inspect_g["execution_result"]["mcp_contract_hash"] == inspect["portable_packet"]["mcp_contract_hash"]
assert inspect_g["execution_result"]["mcp_call_hash"] == inspect["portable_packet"]["proposed_call_hash"]
assert replay["consequence_reexecuted"] is False
assert replay["operation_transition_custody_status"] == "RECORDED"
assert replay["operation_receipt_ids"]
assert reconstruct["consequence_reexecuted"] is False
assert reconstruct["operation_transition_custody_status"] == "RECORDED"
assert reconstruct["operation_receipt_ids"]
assert write_g["governance_state"] == "ALLOW"
assert write_g["master_records_custody_status"] == "RECORDED"
assert write_g["chain_verified"] is True
assert write_g["transaction_identity_continuous"] is True
assert write_g["execution_result"]["status"] == "MCP_TOOL_RESULT_OBSERVED"
assert write_g["execution_result"]["mcp_result"]["structuredContent"]["status"] == "UPDATED"
assert write_g["execution_result"]["mcp_result"]["structuredContent"]["bounded_value"] == 42

print(json.dumps({
    "schema": "stegverse.sdk-mcp-canonical-validation-result/v1",
    "state": "COMPLETE",
    "inspect": {
        "manifest_receipt_id": rid,
        "route_manifest_id": inspect_g["route_manifest_id"],
        "transaction_id": inspect_g["transaction_id"],
        "route_receipt_ids": inspect_g["route_receipt_ids"],
        "contract_hash": inspect["portable_packet"]["mcp_contract_hash"],
        "call_hash": inspect["portable_packet"]["proposed_call_hash"],
        "governance_state": inspect_g["governance_state"],
        "master_records_custody_status": inspect_g["master_records_custody_status"],
        "chain_verified": inspect_g["chain_verified"],
        "transaction_identity_continuous": inspect_g["transaction_identity_continuous"],
    },
    "replay": {
        "consequence_reexecuted": replay["consequence_reexecuted"],
        "operation_transition_custody_status": replay["operation_transition_custody_status"],
        "operation_receipt_ids": replay["operation_receipt_ids"],
    },
    "reconstruction": {
        "consequence_reexecuted": reconstruct["consequence_reexecuted"],
        "operation_transition_custody_status": reconstruct["operation_transition_custody_status"],
        "operation_receipt_ids": reconstruct["operation_receipt_ids"],
    },
    "bounded_write": {
        "manifest_receipt_id": write["manifest_receipt_id"],
        "route_receipt_ids": write_g["route_receipt_ids"],
        "contract_hash": write["portable_packet"]["mcp_contract_hash"],
        "call_hash": write["portable_packet"]["proposed_call_hash"],
        "status": write_g["execution_result"]["mcp_result"]["structuredContent"]["status"],
        "bounded_value": write_g["execution_result"]["mcp_result"]["structuredContent"]["bounded_value"],
    },
}, sort_keys=True))
'''


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def hosted_environment(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in HOSTED_ENV)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def validate_node_declaration(path: Path) -> dict[str, Any]:
    node = read_json(path)
    if node.get("schema") not in {"stegverse.sovereign-node-declaration/v0.1", "stegverse.sovereign-node-declaration/v0.2"}:
        raise RuntimeError("unsupported sovereign-node declaration schema")
    if node.get("declared") is not True:
        raise RuntimeError("sovereign node is not declared")
    if node.get("credential_authority") != "TV/TVC":
        raise RuntimeError("credential authority must be TV/TVC")
    if node.get("github_token_required") is not False:
        raise RuntimeError("sovereign node may not require a GitHub token")
    return node


def find_node_declaration(explicit: Path | None = None) -> tuple[Path, dict[str, Any]]:
    candidates = (explicit,) if explicit is not None else NODE_MARKERS
    for raw in candidates:
        if raw is None:
            continue
        path = raw.expanduser().resolve()
        if path.is_file():
            return path, validate_node_declaration(path)
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")


def resolve_roots(env: Mapping[str, str] | None = None) -> dict[str, Path]:
    values = os.environ if env is None else env
    roots: dict[str, Path] = {}
    for key, env_name in ROOT_ENV.items():
        raw = str(values.get(env_name) or "").strip()
        if not raw:
            raise RuntimeError(f"missing non-secret local source locator {env_name}")
        root = Path(raw).expanduser().resolve()
        required = root / REQUIRED_FILES[key]
        if not required.is_file():
            raise RuntimeError(f"canonical local artifact missing: {required}")
        roots[key] = root
    return roots


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_evidence(roots: Mapping[str, Path]) -> dict[str, Any]:
    return {
        key: {
            "root": str(root),
            "required_file": REQUIRED_FILES[key],
            "required_file_sha256": sha256_file(root / REQUIRED_FILES[key]),
        }
        for key, root in roots.items()
    }


def child_environment(roots: Mapping[str, Path], env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    child = {
        "PATH": values.get("PATH", "/usr/bin:/bin"),
        "HOME": values.get("HOME", str(Path.home())),
        "LANG": values.get("LANG", "C.UTF-8"),
        "LC_ALL": values.get("LC_ALL", "C.UTF-8"),
    }
    pythonpath = [
        str(roots["sdk"]),
        str(roots["stegcore"] / "src"),
        str(roots["core_lite"]),
        str(roots["master_records"]),
    ]
    child["PYTHONPATH"] = os.pathsep.join(pythonpath)
    for key in child:
        upper = key.upper()
        if any(marker in upper for marker in FORBIDDEN_ENV_MARKERS):
            raise RuntimeError(f"forbidden child environment key: {key}")
    return child


def execute(invocation: Mapping[str, Any], *, env: Mapping[str, str] | None = None, node_declaration: Path | None = None, runner: Runner = subprocess.run) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    if hosted_environment(values):
        raise RuntimeError("hosted environments are validation-only and cannot execute exact sovereign MCP validation")
    node_path, node = find_node_declaration(node_declaration)
    validate_invocation(invocation)
    roots = resolve_roots(values)
    child = child_environment(roots, values)

    unit = runner(
        [sys.executable, "-m", "unittest", "tests.test_mcp_production_artifact.MCPProductionArtifactGovernedIntegrationTests", "-v"],
        cwd=roots["sdk"], text=True, capture_output=True, timeout=180, check=False, env=child,
    )
    if unit.returncode != 0:
        raise RuntimeError("canonical governed integration suite failed: " + (unit.stderr or unit.stdout)[-2000:])
    if "skipped" in (unit.stdout + unit.stderr).lower():
        raise RuntimeError("canonical governed integration suite skipped; exact artifacts were not proven")

    run = runner(
        [sys.executable, "-c", EXACT_RUN_PROGRAM], cwd=roots["sdk"], text=True,
        capture_output=True, timeout=180, check=False, env=child,
    )
    if run.returncode != 0:
        raise RuntimeError("exact MCP governed run failed: " + (run.stderr or run.stdout)[-2000:])
    try:
        result = json.loads(run.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("exact MCP governed run did not emit a valid result") from exc
    if result.get("state") != "COMPLETE":
        raise RuntimeError("exact MCP governed result is not COMPLETE")

    receipt = {
        "schema": "stegverse.sdk-mcp-canonical-validation-worker-receipt/v1",
        "task_id": TASK_ID,
        "state": "COMPLETE",
        "transition_id": "SDK_MCP_CANONICAL_VALIDATION_COMPLETE",
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "worker_id": WORKER_ID,
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "source_evidence": source_evidence(roots),
        "result": result,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_used": False,
        "provider_secret_exported": False,
        "signed": False,
        "broadcast": False,
        "authority_effect": "VALIDATION_ONLY_NO_NEW_AUTHORITY",
    }
    target = Path(child["HOME"]) / ".stegverse" / "receipts" / "sdk-mcp-canonical-validation-009.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = str(target)
    return receipt


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        receipt = execute(invocation)
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETE",
            "transition_id": "SDK_MCP_CANONICAL_VALIDATION_COMPLETE",
            "evidence_refs": [receipt["local_receipt_ref"]],
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "non_tv_tvc_secret_or_token_used": False,
        }
        print(json.dumps(response, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "SDK_MCP_CANONICAL_VALIDATION_BLOCKED",
            "error": str(exc),
            "evidence_refs": [],
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "non_tv_tvc_secret_or_token_used": False,
        }, sort_keys=True))
        return 75


if __name__ == "__main__":
    raise SystemExit(main())
