#!/usr/bin/env python3
"""Consume the bounded ERL active-research resident request without inventing transport.

The consumer validates the canonical resident request, self-materializes only the
exact ERL source dependencies from an already-local canonical source root, applies
and verifies the idempotent resident-source preparation, and, when the local ERL
source/dispatch are available, materializes the exact deterministic binding and
acquisition envelope into write-once resident-local sidecars. It performs no
network source fetch, transport submission, hop-receipt fabrication, or provider
operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REQUEST_REL = Path("control/resident-execution-request.d/erl-active-research-intr-runtime-binding-001.json")
PREP = Path("scripts/prepare_erl_active_research_intr_runtime_source.py")
OUTPUT_DIR = Path("intr-payloads/erl-active-research")
RECEIPT_REL = Path("receipts/sovereign-host/erl-active-research-intr-binding-consumption.latest.json")
TASK_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
COSV = "40000100100000"
MODE = "ERL_ACTIVE_RESEARCH_INTR_RUNTIME_BINDING"
PATH = ["EXTERNAL_SYSTEM", "STEGOS_ECOSYSTEM", "DEVICE_SYSTEM", "KV"]
OWNER_TASK = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
OWNER_REF = "StegVerse-Labs/continuity-vault-kit#79"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")
SOURCE_DEPENDENCIES = (
    Path("scripts/install_sovereign_heartbeat_service.py"),
    Path("scripts/prepare_erl_active_research_intr_runtime_source.py"),
    Path("scripts/install_erl_active_research_universal_intr_route.py"),
    Path("scripts/install_erl_device_kv_prior_lineage.py"),
    Path("scripts/install_erl_resident_request_wiring.py"),
    Path("scripts/materialize_erl_active_research_intr_resident_local_input.py"),
    Path("scripts/submit_erl_active_research_intr_binding.py"),
    Path("scripts/submit_erl_active_research_intr_binding_local.py"),
    Path("workers/erl_active_research_transport.py"),
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def write_once(path: Path, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"write_once_collision:{path}")
        return
    path.write_text(rendered, encoding="utf-8")
    if path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"write_once_readback_mismatch:{path}")


def write_latest(path: Path, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    if path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"latest_readback_mismatch:{path}")


def atomic_copy_exact(source: Path, target: Path) -> bool:
    raw = source.read_bytes()
    expected = hashlib.sha256(raw).hexdigest()
    if target.is_file() and file_sha256(target) == expected:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name("." + target.name + ".erl-source.tmp")
    tmp.write_bytes(raw)
    if file_sha256(tmp) != expected:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"source_dependency_temp_readback_mismatch:{target}")
    os.replace(tmp, target)
    if file_sha256(target) != expected:
        raise RuntimeError(f"source_dependency_readback_mismatch:{target}")
    return True


def materialize_source_dependencies(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if not source.is_dir():
        raise RuntimeError("canonical_local_source_root_missing")
    if source == runtime:
        raise RuntimeError("source_root_and_runtime_root_must_be_distinct")
    copied: list[str] = []
    verified: list[str] = []
    digests: dict[str, str] = {}
    for rel in SOURCE_DEPENDENCIES:
        src = source / rel
        if not src.is_file():
            raise RuntimeError(f"canonical_local_source_dependency_missing:{rel.as_posix()}")
        dst = runtime / rel
        if atomic_copy_exact(src, dst):
            copied.append(rel.as_posix())
        else:
            verified.append(rel.as_posix())
        if not dst.is_file() or file_sha256(dst) != file_sha256(src):
            raise RuntimeError(f"source_dependency_parity_failed:{rel.as_posix()}")
        digests[rel.as_posix()] = "sha256:" + file_sha256(dst)
    return {
        "source_root": str(source),
        "runtime_root": str(runtime),
        "copied": copied,
        "verified": verified,
        "digests": digests,
        "network_source_fetch_attempted": False,
        "authority_effect": "NONE_LOCAL_SOURCE_MATERIALIZATION_ONLY",
    }


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "mode": MODE,
        "entrypoint": str(PREP),
        "canonical_boundary_path": PATH,
        "terminal_runtime_owner_task": OWNER_TASK,
        "terminal_downstream_owner_ref": OWNER_REF,
        "provider_operation_reexecution_authorized": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, val in expected.items():
        if request.get(key) != val:
            raise RuntimeError(f"ERL resident request {key} mismatch")
    if not str(request.get("request_id") or "").strip():
        raise RuntimeError("ERL resident request_id missing")
    if not str(request.get("erl_group_id") or "").strip() or not str(request.get("erl_source_id") or "").strip():
        raise RuntimeError("ERL resident group/source identity missing")


def parse_json(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    if start < 0:
        raise RuntimeError("ERL binding builder JSON missing")
    value = json.loads(stdout[start:])
    if not isinstance(value, dict):
        raise RuntimeError("ERL binding builder result invalid")
    return value


def safe_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    if any(truthy(values.get(name)) for name in HOSTED):
        raise RuntimeError("hosted environment may not consume sovereign ERL request")
    if any(truthy(values.get(name)) for name in FORBIDDEN):
        raise RuntimeError("GitHub credential-bearing environment forbidden")
    return values


def run_prep(prep: Path, runtime: Path, values: Mapping[str, str], *, runner=subprocess.run) -> tuple[bool, str]:
    applied = runner([sys.executable, str(prep)], cwd=runtime, capture_output=True, text=True, check=False, env=dict(values), timeout=120)
    if applied.returncode != 0:
        return False, (applied.stderr or applied.stdout).strip()
    checked = runner([sys.executable, str(prep), "--check"], cwd=runtime, capture_output=True, text=True, check=False, env=dict(values), timeout=120)
    if checked.returncode != 0:
        return False, (checked.stderr or checked.stdout).strip()
    return True, (checked.stdout or applied.stdout).strip()


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.erl-active-research.resident-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    request = load(request_path)
    validate_request(request)
    values = safe_env(env)
    source_materialization = materialize_source_dependencies(source_root, runtime)
    prep = runtime / PREP
    if not prep.is_file():
        raise RuntimeError("ERL resident source preparation entrypoint missing after local source materialization")
    prepared, prep_detail = run_prep(prep, runtime, values, runner=runner)
    if not prepared:
        receipt = {
            "schema":"stegverse.erl-active-research.resident-consumption/v1","state":"SOURCE_PREPARATION_REQUIRED",
            "request_id":request["request_id"],"task_id":TASK_ID,"cosv_task_vector":COSV,
            "runtime_execution_attempted":False,"transport_submission_attempted":False,"provider_operation_attempted":False,
            "source_dependencies_materialized":True,"source_materialization":source_materialization,
            "source_preparation_applied":True,"source_preparation_check_passed":False,"source_preparation_detail":prep_detail,
            "network_source_fetch_attempted":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE",
            "heartbeat_grants_execution_authority":False,"second_machine_required":False,"authority_effect":"NONE_WAIT_STATE"
        }
        write_latest(runtime / RECEIPT_REL, receipt)
        return receipt
    erl_root_raw = str(values.get("STEGVERSE_ERL_ROOT") or "").strip()
    dispatch_raw = str(values.get("STEGVERSE_ERL_ACTIVE_RESEARCH_DISPATCH_PATH") or "").strip()
    if not erl_root_raw or not dispatch_raw:
        receipt = {
            "schema":"stegverse.erl-active-research.resident-consumption/v1","state":"INPUT_NOT_MATERIALIZED",
            "request_id":request["request_id"],"task_id":TASK_ID,"cosv_task_vector":COSV,
            "runtime_execution_attempted":False,"transport_submission_attempted":False,"provider_operation_attempted":False,
            "source_dependencies_materialized":True,"source_materialization":source_materialization,
            "source_preparation_applied":True,"source_preparation_check_passed":True,
            "missing_inputs":[name for name,val in (("STEGVERSE_ERL_ROOT",erl_root_raw),("STEGVERSE_ERL_ACTIVE_RESEARCH_DISPATCH_PATH",dispatch_raw)) if not val],
            "network_source_fetch_attempted":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,
            "second_machine_required":False,"authority_effect":"NONE_WAIT_STATE"
        }
        write_latest(runtime / RECEIPT_REL, receipt)
        return receipt
    erl_root = Path(erl_root_raw).expanduser().resolve()
    dispatch = Path(dispatch_raw).expanduser().resolve()
    builder = erl_root / "scripts/build_active_research_intr_binding.py"
    if not builder.is_file() or not dispatch.is_file():
        raise RuntimeError("local ERL builder/dispatch missing")
    source_id = str(request["erl_source_id"])
    envelope_rel = OUTPUT_DIR / f"{source_id}.envelope.json"
    binding_rel = OUTPUT_DIR / f"{source_id}.binding.json"
    payload_ref = "runtime-local:" + envelope_rel.as_posix()
    completed = runner([
        sys.executable, str(builder), "--dispatch", str(dispatch), "--group-id", str(request["erl_group_id"]),
        "--source-id", source_id, "--payload-ref", payload_ref
    ], cwd=erl_root, capture_output=True, text=True, check=False, env=values, timeout=120)
    if completed.returncode != 0:
        raise RuntimeError("ERL binding builder failed: " + (completed.stderr or completed.stdout).strip())
    binding = parse_json(completed.stdout)
    if binding.get("schema") != "stegverse.erl.active-research-intr-binding/v1" or binding.get("expected_boundary_path") != PATH:
        raise RuntimeError("ERL binding contract mismatch")
    if binding.get("runtime_receipts_present") is not False or binding.get("transport_execution_claimed") is not False:
        raise RuntimeError("ERL binding promoted runtime evidence")
    envelope = binding.get("acquisition_envelope")
    if not isinstance(envelope, dict) or sha_uri(envelope) != binding.get("acquisition_envelope_sha256"):
        raise RuntimeError("ERL acquisition envelope hash mismatch")
    mat = binding.get("materialization_request")
    if not isinstance(mat, dict) or mat.get("boundary_path") != PATH or mat.get("credential_authority") != "TV/TVC" or mat.get("github_token_runtime_authority") != "NONE" or mat.get("authority_transfer") is not False:
        raise RuntimeError("ERL materialization request authority/path mismatch")
    write_once(runtime / envelope_rel, envelope)
    write_once(runtime / binding_rel, binding)
    receipt = {
        "schema":"stegverse.erl-active-research.resident-consumption/v1","state":"BINDING_MATERIALIZED_AWAITING_AUTHENTIC_INTR_SUBMISSION",
        "request_id":request["request_id"],"task_id":TASK_ID,"cosv_task_vector":COSV,
        "group_id":request["erl_group_id"],"source_id":source_id,"binding_ref":binding_rel.as_posix(),"envelope_ref":envelope_rel.as_posix(),
        "binding_hash":binding.get("binding_hash"),"payload_hash":mat.get("payload_hash"),"packet_id":mat.get("packet_id"),"operation_id":mat.get("operation_id"),
        "runtime_execution_attempted":False,"transport_submission_attempted":False,"provider_operation_attempted":False,
        "runtime_receipts_present":False,"source_dependencies_materialized":True,"source_materialization":source_materialization,
        "source_preparation_applied":True,"source_preparation_check_passed":True,"network_source_fetch_attempted":False,
        "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"second_machine_required":False,
        "authority_effect":"NONE_BINDING_MATERIALIZATION_ONLY"
    }
    write_latest(runtime / RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
