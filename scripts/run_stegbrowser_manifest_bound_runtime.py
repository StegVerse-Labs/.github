#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
COSV = "40000100100000"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
RUNNER_REL = Path("scripts/run_stegbrowser_runtime_consumption_reusable.py")
BINDING_RECEIPT_REL = Path("receipts/sovereign-host/stegbrowser-manifest-binding.latest.json")


def fail(reason: str) -> None:
    print(json.dumps({"state":"BOUNDARY","reason":reason,"task_id":TASK_ID,"authority_effect":"NONE"}, sort_keys=True))
    raise SystemExit(2)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"json_load_failed:{path}:{exc}")
    if not isinstance(value, dict):
        fail(f"json_object_required:{path}")
    return value


def params() -> dict:
    raw = os.environ.get("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "")
    if not raw:
        fail("reusable_task_parameters_missing")
    try:
        value = json.loads(raw)
    except Exception:
        fail("reusable_task_parameters_invalid_json")
    if not isinstance(value, dict):
        fail("reusable_task_parameters_object_required")
    return value


def resolve_root(value: object, env_name: str, fallback: Path | None = None) -> Path:
    raw = str(value or os.environ.get(env_name) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    if fallback is not None:
        return fallback.resolve()
    fail(f"required_path_missing:{env_name}")


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema") != "stegverse.interlock-intr-manifest/v1":
        fail("manifest_schema_mismatch")
    if manifest.get("task_id") != TASK_ID or manifest.get("cosv_task_vector") != COSV:
        fail("manifest_task_cosv_mismatch")
    if manifest.get("path_source") != "MANIFEST" or manifest.get("route_owner") != "STEGVERSE":
        fail("manifest_route_owner_or_source_invalid")
    if manifest.get("endpoint_discovery_required") is not False or manifest.get("receiver_discovery_required") is not False:
        fail("manifest_discovery_must_be_false")
    if manifest.get("undeclared_endpoint_or_receiver_substitution_allowed") is not False:
        fail("manifest_substitution_must_be_forbidden")
    outbound = manifest.get("outbound") or {}
    if outbound.get("ecosystem_boundary") != "STEGVERSE_ECOSYSTEM":
        fail("manifest_outbound_ecosystem_mismatch")
    if outbound.get("interlock_intr_endpoint") != "STEGVERSE_OWNED_INTR_EGRESS_ENDPOINT":
        fail("manifest_outbound_endpoint_mismatch")
    if outbound.get("receiver") != "STEGVERSE_OWNED_MIRROR_REFLECTOR" or outbound.get("receiver_role") != "OWNED_MIRROR_REFLECTOR":
        fail("manifest_owned_mirror_receiver_mismatch")
    if outbound.get("expected_action") != "REFLECT_DECLARED_RECORDS_PACKET":
        fail("manifest_reflection_action_mismatch")
    rt1 = manifest.get("round_trip_1") or {}
    if rt1.get("return_target") != "MASTER_RECORDS_RECORDING_SURFACE" or rt1.get("terminal_predicate") != "SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED":
        fail("manifest_round_trip_1_contract_mismatch")
    between = manifest.get("between_round_trips") or {}
    if between.get("processing_boundary") != "STEGVERSE_OWNED_MIRROR_BOUNDARY":
        fail("manifest_mirror_boundary_mismatch")
    rt2 = manifest.get("round_trip_2") or {}
    if rt2.get("interlock_intr_endpoint") != "STEGVERSE_OWNED_INTR_ECOSYSTEM_RETURN_ENDPOINT":
        fail("manifest_round_trip_2_endpoint_mismatch")
    if rt2.get("receiver") != "STEGVERSE_ECOSYSTEM" or rt2.get("terminal_predicate") != "SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED":
        fail("manifest_round_trip_2_contract_mismatch")
    if manifest.get("overall_terminal_predicate") != "SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED":
        fail("manifest_overall_terminal_predicate_mismatch")


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    p = params()
    source = resolve_root(p.get("sovereign_source_root") or p.get("source_root"), "STEGVERSE_HEARTBEAT_SOURCE_ROOT", ROOT)
    resident_root = resolve_root(p.get("runtime_root") or p.get("resident_runtime_root"), "STEGVERSE_HEARTBEAT_ROOT")
    manifest_path = source / MANIFEST_REL
    runner_path = source / RUNNER_REL
    if not manifest_path.is_file():
        fail("manifest_missing")
    if not runner_path.is_file():
        fail("runtime_runner_missing")
    manifest = load_json(manifest_path)
    validate_manifest(manifest)
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    binding = {
        "schema":"stegverse.stegbrowser-manifest-binding/v1",
        "state":"MANIFEST_BOUND_TO_INVOCATION",
        "task_id":TASK_ID,
        "cosv_task_vector":COSV,
        "manifest_ref":str(manifest_path),
        "manifest_sha256":digest,
        "invocation_request_nonce":NONCE,
        "route_owner":"STEGVERSE",
        "outbound_interlock_intr_endpoint":manifest["outbound"]["interlock_intr_endpoint"],
        "far_end_receiver":manifest["outbound"]["receiver"],
        "far_end_receiver_role":manifest["outbound"]["receiver_role"],
        "round_trip_1_return_target":manifest["round_trip_1"]["return_target"],
        "mirror_processing_boundary":manifest["between_round_trips"]["processing_boundary"],
        "round_trip_2_interlock_intr_endpoint":manifest["round_trip_2"]["interlock_intr_endpoint"],
        "round_trip_2_receiver":manifest["round_trip_2"]["receiver"],
        "endpoint_discovery_required":False,
        "receiver_discovery_required":False,
        "undeclared_endpoint_or_receiver_substitution_allowed":False,
        "authority_effect":"NONE_ROUTE_BINDING_ONLY"
    }
    atomic_json(resident_root / BINDING_RECEIPT_REL, binding)
    env = dict(os.environ)
    env["STEGVERSE_REUSABLE_TASK_INVOCATION_ID"] = f"MANIFEST-{digest[:24]}"
    env["STEGVERSE_STEGBROWSER_INVOCATION_NONCE"] = NONCE
    env["STEGVERSE_STEGBROWSER_MANIFEST_SHA256"] = digest
    completed = subprocess.run([sys.executable, str(runner_path)], cwd=source, env=env, text=True, capture_output=False, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
