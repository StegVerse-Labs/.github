#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping

REQUEST_REL = Path("control/resident-execution-request.d/cross-framework-current-basis-v04-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/cross-framework-current-basis-v04-consumption.latest.json")
STATE_REL = Path("state/cross-framework-current-basis-v04")
EXPECTED_SHA256 = "07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f"
EXPECTED_BLOB = "59d818a15fc7be732c97dae7d2174d8cfe9a7bab"
TASK_ID = "CROSS-FRAMEWORK-CURRENT-BASIS-V04-EXECUTION-001"
MODE = "CROSS_FRAMEWORK_CURRENT_BASIS_V04"
EXPECTED_SOURCE_BLOBS = {
    "STEGVERSE_SDK_SOURCE_ROOT": {
        "scripts/run_cross_framework_current_basis_v04.py": "93a423a76d1662329f0511dd531646c5b21ff55b",
        "inspection/examples/cross-framework-current-basis-request.draft.json": "59d818a15fc7be732c97dae7d2174d8cfe9a7bab",
        "stegverse/sovereign_validation_runtime.py": "6bc0944633b6299c19f065f44dd5999434445dd7",
        "stegverse/current_basis.py": "5971a050d94fc237cad65d23ba5ac873ee6900b4",
    },
    "STEGVERSE_STEGCORE_SOURCE_ROOT": {
        "src/stegcore/current_basis.py": "c56179d1ba92a3f487dd62eddd41b812028c48c3",
        "src/stegcore/transaction_lifecycle.py": "81935669846fedd2867272810b090226b05780ab",
    },
    "STEGVERSE_CORE_LITE_SOURCE_ROOT": {
        "core_lite/transaction_route.py": "734923a86bfcd4d41d07e0fb8797de50f0fb9408",
    },
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": {
        "services/manifest_receipt_custody.py": "26a4c1e082ee91128648b2b9bd13cc32ce915f82",
    },
}

HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_AUTH_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "HF_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
)
REQUIRED_ROOT_ENV = (
    "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
)
SOURCE_MATERIALIZATION_ROOT_ENV = "STEGVERSE_SOURCE_MATERIALIZATION_ROOT"
DEFAULT_SOURCE_MATERIALIZATION_ROOT = Path("/var/lib/stegverse/source")
DEFAULT_COMPONENT_ROOTS = {
    "STEGVERSE_SDK_SOURCE_ROOT": Path("components/sdk"),
    "STEGVERSE_STEGCORE_SOURCE_ROOT": Path("components/stegcore"),
    "STEGVERSE_CORE_LITE_SOURCE_ROOT": Path("components/core-lite"),
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": Path("components/master-records"),
}
SOURCE_PACKAGE_ROOT_ENV = "STEGVERSE_SOURCE_PACKAGE_ROOT"
DEFAULT_SOURCE_PACKAGE_ROOT = Path.home() / ".stegverse" / "packages" / "source" / "v1"
COMPONENT_IDS = {
    "STEGVERSE_SDK_SOURCE_ROOT": "stegverse.sdk",
    "STEGVERSE_STEGCORE_SOURCE_ROOT": "stegverse.stegcore",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT": "stegverse.core-lite",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "stegverse.master-records",
}
PACKAGE_SLUGS = {key: value.replace(".", "-") for key, value in COMPONENT_IDS.items()}
PACKAGE_SCHEMA = "stegverse.source-package/v1"
PACKAGE_VERSION = "1.0.0"


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def verify_exact_source_identity(roots: Mapping[str, Path]) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    observed: dict[str, dict[str, str]] = {}
    mismatches: list[dict[str, str]] = []
    for root_key, files in EXPECTED_SOURCE_BLOBS.items():
        root = roots[root_key]
        observed[root_key] = {}
        for rel, expected in files.items():
            path = root / rel
            if not path.is_file():
                mismatches.append({
                    "root": root_key,
                    "path": rel,
                    "expected_git_blob_sha1": expected,
                    "observed_git_blob_sha1": "MISSING",
                })
                continue
            actual = git_blob_sha1(path.read_bytes())
            observed[root_key][rel] = actual
            if actual != expected:
                mismatches.append({
                    "root": root_key,
                    "path": rel,
                    "expected_git_blob_sha1": expected,
                    "observed_git_blob_sha1": actual,
                })
    return observed, mismatches


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": "scripts/run_cross_framework_current_basis_v04.py",
        "test_id": "cross-framework-current-basis-001",
        "manifest_sha256": EXPECTED_SHA256,
        "manifest_git_blob_sha1": EXPECTED_BLOB,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "counterpart_result_allowed_before_completion": False,
        "external_consequence_allowed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if request.get(key) != expected_value:
            raise RuntimeError(f"current-basis resident request {key} mismatch")
    if not str(request.get("request_id") or "").strip():
        raise RuntimeError("current-basis resident request id missing")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not execute current-basis resident request")
    for name in FORBIDDEN_AUTH_ENV:
        if truthy(values.get(name)):
            raise RuntimeError(f"forbidden credential present: {name}")
    env = {
        key: values[key]
        for key in ("PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
        if values.get(key)
    }
    for key in REQUIRED_ROOT_ENV:
        if values.get(key):
            env[key] = values[key]
    if values.get(SOURCE_MATERIALIZATION_ROOT_ENV):
        env[SOURCE_MATERIALIZATION_ROOT_ENV] = values[SOURCE_MATERIALIZATION_ROOT_ENV]
    if values.get(SOURCE_PACKAGE_ROOT_ENV):
        env[SOURCE_PACKAGE_ROOT_ENV] = values[SOURCE_PACKAGE_ROOT_ENV]
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env



def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _target_root(env: Mapping[str, str], key: str) -> Path:
    raw = str(env.get(key) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    base = Path(
        str(env.get(SOURCE_MATERIALIZATION_ROOT_ENV) or DEFAULT_SOURCE_MATERIALIZATION_ROOT)
    ).expanduser().resolve()
    return (base / DEFAULT_COMPONENT_ROOTS[key]).resolve()


def _package_path(env: Mapping[str, str], key: str) -> Path:
    store = Path(
        str(env.get(SOURCE_PACKAGE_ROOT_ENV) or DEFAULT_SOURCE_PACKAGE_ROOT)
    ).expanduser().resolve()
    return store / PACKAGE_SLUGS[key] / "package.json"


def _validate_source_package(package: Mapping[str, Any], key: str) -> list[tuple[str, bytes]]:
    component_id = COMPONENT_IDS[key]
    if package.get("schema") != PACKAGE_SCHEMA or package.get("package_version") != PACKAGE_VERSION:
        raise RuntimeError(f"{component_id}: source package schema/version mismatch")
    if package.get("component_id") != component_id:
        raise RuntimeError(f"{component_id}: source package component mismatch")
    if package.get("credential_material_included") is not False:
        raise RuntimeError(f"{component_id}: source package credential material forbidden")
    if package.get("authority_effect") != "NONE_SOURCE_TRANSPORT_ONLY":
        raise RuntimeError(f"{component_id}: source package authority effect mismatch")
    files = package.get("files")
    manifest = package.get("manifest")
    if not isinstance(files, list) or not isinstance(manifest, dict):
        raise RuntimeError(f"{component_id}: source package files/manifest missing")
    manifest_rows = manifest.get("files")
    if not isinstance(manifest_rows, list) or manifest.get("file_count") != len(files) or len(manifest_rows) != len(files):
        raise RuntimeError(f"{component_id}: source package file count mismatch")
    rows: list[dict[str, Any]] = []
    decoded: list[tuple[str, bytes]] = []
    for index, file_row in enumerate(files):
        manifest_row = manifest_rows[index]
        if not isinstance(file_row, dict) or not isinstance(manifest_row, dict):
            raise RuntimeError(f"{component_id}: source package row malformed")
        rel = str(file_row.get("path") or "")
        pure = PurePosixPath(rel)
        if not pure.parts or pure.is_absolute() or ".." in pure.parts:
            raise RuntimeError(f"{component_id}: unsafe source package path")
        for field in ("path", "sha256", "size"):
            if file_row.get(field) != manifest_row.get(field):
                raise RuntimeError(f"{component_id}: source package manifest/file mismatch")
        try:
            raw = base64.b64decode(str(file_row.get("content_base64") or ""), validate=True)
        except Exception as exc:
            raise RuntimeError(f"{component_id}: invalid source package base64") from exc
        if len(raw) != file_row.get("size") or _sha256_bytes(raw) != file_row.get("sha256"):
            raise RuntimeError(f"{component_id}: source package file integrity mismatch: {rel}")
        rows.append({"path": rel, "sha256": file_row["sha256"], "size": file_row["size"]})
        decoded.append((rel, raw))
    digest = _sha256_bytes(_canonical_bytes(rows))
    if digest != manifest.get("source_bundle_sha256"):
        raise RuntimeError(f"{component_id}: source package bundle digest mismatch")
    if package.get("source_identity") != "sha256:" + digest:
        raise RuntimeError(f"{component_id}: source package identity mismatch")
    return decoded


def _component_mismatches(key: str, root: Path) -> list[dict[str, str]]:
    mismatches: list[dict[str, str]] = []
    for rel, expected in EXPECTED_SOURCE_BLOBS[key].items():
        path = root / rel
        observed = git_blob_sha1(path.read_bytes()) if path.is_file() else "MISSING"
        if observed != expected:
            mismatches.append({
                "root": key,
                "path": rel,
                "expected_git_blob_sha1": expected,
                "observed_git_blob_sha1": observed,
            })
    return mismatches


def _materialize_local_package(env: Mapping[str, str], key: str) -> dict[str, Any]:
    package_path = _package_path(env, key)
    if not package_path.is_file():
        raise FileNotFoundError(str(package_path))
    package = load_json(package_path)
    decoded = _validate_source_package(package, key)
    destination = _target_root(env, key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.current-basis-v04-", dir=destination.parent))
    backup: Path | None = None
    try:
        for rel, raw in decoded:
            pure = PurePosixPath(rel)
            target = stage / Path(*pure.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        mismatches = _component_mismatches(key, stage)
        if mismatches:
            raise RuntimeError(
                f"{COMPONENT_IDS[key]}: package does not contain exact frozen-v0.4 execution source"
            )
        if destination.exists():
            backup = destination.parent / f".{destination.name}.pre-current-basis-v04"
            if backup.exists():
                shutil.rmtree(backup)
            os.replace(destination, backup)
        os.replace(stage, destination)
        stage = None
        if backup and backup.exists():
            shutil.rmtree(backup)
        return {
            "root": key,
            "component_id": COMPONENT_IDS[key],
            "state": "LOCAL_SOURCE_PACKAGE_MATERIALIZED",
            "package_path": str(package_path),
            "source_identity": package.get("source_identity"),
            "target_root": str(destination),
            "exact_critical_blobs_verified": True,
            "network_source_fetch_performed": False,
            "credential_read_or_acquired": False,
            "execution_authority_effect": "NONE",
            "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
        }
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def repair_from_local_packages(env: Mapping[str, str], keys: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    repaired: list[dict[str, Any]] = []
    needs: list[dict[str, str]] = []
    for key in sorted(set(keys)):
        try:
            repaired.append(_materialize_local_package(env, key))
        except FileNotFoundError:
            needs.append({
                "root": key,
                "component_id": COMPONENT_IDS[key],
                "package_path": str(_package_path(env, key)),
            })
    return repaired, needs


def source_roots(env: Mapping[str, str]) -> tuple[dict[str, Path], list[str]]:
    roots: dict[str, Path] = {}
    missing: list[str] = []
    base = Path(
        str(env.get(SOURCE_MATERIALIZATION_ROOT_ENV) or DEFAULT_SOURCE_MATERIALIZATION_ROOT)
    ).expanduser().resolve()
    for key in REQUIRED_ROOT_ENV:
        raw = str(env.get(key) or "").strip()
        candidates = []
        if raw:
            candidates.append(Path(raw).expanduser().resolve())
        candidates.append((base / DEFAULT_COMPONENT_ROOTS[key]).resolve())
        selected = next((path for path in candidates if path.is_dir()), None)
        if selected is None:
            missing.append(key)
            continue
        roots[key] = selected
    return roots, missing


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.current-basis-v04.resident-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)

    safe = clean_env(env)
    roots, missing = source_roots(safe)
    source_repairs: list[dict[str, Any]] = []
    package_needs: list[dict[str, str]] = []
    if missing:
        repairs, needs = repair_from_local_packages(safe, missing)
        source_repairs.extend(repairs)
        package_needs.extend(needs)
        roots, missing = source_roots(safe)
    if missing:
        receipt = {
            "schema": "stegverse.current-basis-v04.resident-consumption/v1",
            "state": "BLOCKED_LOCAL_SOURCE_PACKAGE_NOT_OBSERVED" if package_needs else "BLOCKED_LOCAL_SOURCE_ROOTS_NOT_OBSERVED",
            "missing_root_env": missing,
            "source_repairs": source_repairs,
            "source_package_needs": package_needs,
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "source_resolution_attempted": True,
            "network_source_fetch_performed": False,
            "credential_read_or_acquired": False,
            "user_action_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE_SOURCE_RESOLUTION_ONLY",
        }
        atomic_json(runtime / CONSUMPTION_REL, receipt)
        return receipt

    sdk = roots["STEGVERSE_SDK_SOURCE_ROOT"]
    stegcore = roots["STEGVERSE_STEGCORE_SOURCE_ROOT"]
    core_lite = roots["STEGVERSE_CORE_LITE_SOURCE_ROOT"]
    master_records = roots["STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"]

    harness = sdk / "scripts" / "run_cross_framework_current_basis_v04.py"
    manifest = sdk / "inspection" / "examples" / "cross-framework-current-basis-request.draft.json"
    current_basis = stegcore / "src" / "stegcore" / "current_basis.py"
    required = [harness, manifest, current_basis]
    absent = [str(path) for path in required if not path.is_file()]
    if absent:
        receipt = {
            "schema": "stegverse.current-basis-v04.resident-consumption/v1",
            "state": "BLOCKED_CANONICAL_SOURCE_NOT_MATERIALIZED",
            "missing_paths": absent,
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "user_action_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE",
        }
        atomic_json(runtime / CONSUMPTION_REL, receipt)
        return receipt

    observed_source_blobs, source_mismatches = verify_exact_source_identity(roots)
    if source_mismatches:
        drifted_keys = sorted({row["root"] for row in source_mismatches})
        repairs, needs = repair_from_local_packages(safe, drifted_keys)
        source_repairs.extend(repairs)
        package_needs.extend(needs)
        roots, missing_after_repair = source_roots(safe)
        observed_source_blobs, source_mismatches = verify_exact_source_identity(roots) if not missing_after_repair else ({}, source_mismatches)
    if source_mismatches:
        receipt = {
            "schema": "stegverse.current-basis-v04.resident-consumption/v1",
            "state": "BLOCKED_LOCAL_SOURCE_PACKAGE_NOT_OBSERVED" if package_needs else "BLOCKED_CANONICAL_SOURCE_IDENTITY_MISMATCH",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "observed_source_blobs": observed_source_blobs,
            "source_identity_mismatches": source_mismatches,
            "source_repairs": source_repairs,
            "source_package_needs": package_needs,
            "runtime_execution_attempted": False,
            "source_resolution_attempted": True,
            "network_source_fetch_performed": False,
            "credential_read_or_acquired": False,
            "user_action_required": False,
            "second_machine_required": False,
            "authority_effect": "NONE_SOURCE_RESOLUTION_ONLY",
        }
        atomic_json(runtime / CONSUMPTION_REL, receipt)
        return receipt

    observed_manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if observed_manifest_sha != EXPECTED_SHA256:
        raise RuntimeError("locally materialized frozen manifest identity mismatch")

    state_root = runtime / STATE_REL
    result_dir = state_root / "result"
    complete_path = result_dir / "RUN_COMPLETE.json"
    if complete_path.is_file():
        complete = load_json(complete_path)
        if complete.get("status") == "COMPLETE" and complete.get("manifest_sha256") == EXPECTED_SHA256:
            return {
                "schema": "stegverse.current-basis-v04.resident-consumption/v1",
                "state": "ALREADY_CONSUMED",
                "request_id": request["request_id"],
                "request_sha256": request_hash,
                "runtime_execution_attempted": False,
                "run_complete": complete,
                "authority_effect": "NONE",
            }

    py_path = os.pathsep.join([str(sdk), str(stegcore / "src"), str(core_lite), str(master_records)])
    child_env = dict(safe)
    child_env["PYTHONPATH"] = py_path
    state_root.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(harness),
        "--manifest", str(manifest),
        "--custody-db", str(state_root / "master-records-validation.db"),
        "--output-dir", str(result_dir),
        "--host-identity", "stegverse-sovereign-resident",
    ]
    completed = runner(
        command,
        cwd=sdk,
        capture_output=True,
        text=True,
        check=False,
        env=child_env,
        timeout=1200,
    )

    run_complete = load_json(complete_path) if complete_path.is_file() else None
    state = "COMPLETED" if (
        completed.returncode == 0
        and isinstance(run_complete, dict)
        and run_complete.get("status") == "COMPLETE"
        and run_complete.get("manifest_sha256") == EXPECTED_SHA256
        and run_complete.get("external_side_effect") is False
    ) else "ATTEMPT_RECORDED"

    receipt = {
        "schema": "stegverse.current-basis-v04.resident-consumption/v1",
        "state": state,
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "mode": MODE,
        "execution_returncode": completed.returncode,
        "runtime_execution_attempted": True,
        "run_complete_observed": isinstance(run_complete, dict),
        "run_complete": run_complete,
        "result_dir": str(result_dir),
        "source_repairs": source_repairs,
        "source_package_needs": package_needs,
        "network_source_fetch_performed": False,
        "github_token_required": False,
        "credential_authority": "TV/TVC",
        "counterpart_result_consumed": False,
        "external_consequence_authority": False,
        "repository_writeback_authority": False,
        "publication_authority": False,
        "user_action_required": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {
        "NO_REQUEST", "ALREADY_CONSUMED", "COMPLETED",
        "BLOCKED_LOCAL_SOURCE_ROOTS_NOT_OBSERVED", "BLOCKED_CANONICAL_SOURCE_NOT_MATERIALIZED",
        "BLOCKED_CANONICAL_SOURCE_IDENTITY_MISMATCH", "BLOCKED_LOCAL_SOURCE_PACKAGE_NOT_OBSERVED"
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
