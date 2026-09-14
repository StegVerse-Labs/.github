#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
CONSUMER = Path("control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py")
CONSUMPTION_RECEIPT = Path("receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json")
TVC_RECEIPT = Path("receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json")
OBSERVER_RECEIPT = Path("var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json")


def fail(reason: str) -> None:
    print(json.dumps({"state": "BOUNDARY", "reason": reason, "authority_effect": "NONE"}, sort_keys=True))
    raise SystemExit(2)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"json_object_required:{path}")
    return value


def params() -> dict[str, Any]:
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


def resolve_path(value: object, env_name: str, fallback: Path | None = None) -> Path:
    raw = str(value or os.environ.get(env_name) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    if fallback is not None:
        return fallback.resolve()
    fail(f"required_path_missing:{env_name}")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    p = params()
    source = resolve_path(p.get("sovereign_source_root"), "STEGVERSE_HEARTBEAT_SOURCE_ROOT", ROOT)
    stegos = resolve_path(p.get("stegos_source_root"), "STEGVERSE_STEGOS_SOURCE_ROOT", source.parent / "StegOS")
    runtime_base = resolve_path(p.get("runtime_base"), "STEGVERSE_EPHEMERAL_RUNTIME_BASE", Path(os.environ.get("XDG_STATE_HOME", "/tmp")) / "stegverse" / "ephemeral-runtime")

    record_path = source / "data/canonical-task-records" / f"{TASK_ID}.json"
    registry_path = source / "data/canonical-task-registry.json"
    if not record_path.is_file() or not registry_path.is_file():
        fail("canonical_task_source_missing")
    record = load_json(record_path)
    if record.get("task_id") != TASK_ID or record.get("cosv_task_vector") != COSV:
        fail("canonical_task_identity_mismatch")
    if record.get("coordination_state") != "ACTIVE" or record.get("checkout_state") != "CHECKED_OUT":
        fail("canonical_task_not_active_checked_out")
    resolution = record.get("execution_substrate_resolution")
    if not isinstance(resolution, dict) or resolution.get("selected_substrate_id") != "ADMITTED-EPHEMERAL-STEGOS-NODE":
        fail("selected_ephemeral_stegos_substrate_required")
    if resolution.get("external_device_required") is not False or resolution.get("second_user_operated_device_allowed") is not False:
        fail("device_invariant_mismatch")

    module_root = stegos
    if not (module_root / "stegos/sovereign_local_event_runtime.py").is_file():
        fail("stegos_local_event_adapter_source_missing")
    sys.path.insert(0, str(module_root))
    from stegos.ephemeral_runtime_lease import AuthorityBoundary, LeaseProfile, LeaseRequest, RendezvousRequirement, RuntimeClass
    from stegos.sovereign_local_event_runtime import SovereignLocalEventRuntimeAdapter

    record_bytes = record_path.read_bytes()
    registry_bytes = registry_path.read_bytes()
    record_hash = sha256_bytes(record_bytes)
    registry_hash = sha256_bytes(registry_bytes)
    state_hash = sha256_bytes(f"{TASK_ID}|{COSV}|{record_hash}".encode("utf-8"))
    lease_id = f"STEGBROWSER-{record_hash[:16]}"
    request = LeaseRequest(
        lease_id=lease_id,
        trigger_id=os.environ.get("STEGVERSE_REUSABLE_TASK_INVOCATION_ID", lease_id),
        operation="stegbrowser-runtime-consumption",
        implementation_ref=f"StegVerse-Labs/.github@{record_hash}",
        source_receipt_id="sha256:" + record_hash,
        consequence_id=TASK_ID,
        consequence_registry_hash="sha256:" + registry_hash,
        generation=int(record.get("generation") or 1),
        state_root_binding="sha256:" + state_hash,
        profile=LeaseProfile.INTAKE,
        runtime_class=RuntimeClass.EVENT_EPHEMERAL,
        rendezvous=RendezvousRequirement.NOT_REQUIRED,
        persistent_host_required=False,
        participant_machine_required=False,
        developer_machine_required=False,
        max_operations=1,
        authority=AuthorityBoundary(credential_authority="TV/TVC"),
    )
    adapter = SovereignLocalEventRuntimeAdapter(sovereign_source_root=source, runtime_base=runtime_base)
    compute = adapter.provision(request)
    runtime = adapter.materialize(compute, compute["implementation_ref"])
    verified = adapter.verify_local(runtime, compute["implementation_ref"])
    if verified.get("verified") is not True:
        fail("ephemeral_runtime_local_verification_failed")

    runtime_root = Path(str(runtime["runtime_root"]))
    consumer = runtime_root / CONSUMER
    if not consumer.is_file():
        fail("canonical_work_consumer_not_materialized")
    completed = subprocess.run(
        [sys.executable, str(consumer), "--source-root", str(source), "--runtime-root", str(runtime_root)],
        cwd=runtime_root,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC", "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE"},
    )
    if completed.returncode != 0:
        print(completed.stdout[-4000:])
        print(completed.stderr[-4000:], file=sys.stderr)
        fail(f"canonical_work_consumer_failed:{completed.returncode}")

    consumption = runtime_root / CONSUMPTION_RECEIPT
    if not consumption.is_file():
        fail("canonical_work_resident_consumption_receipt_not_observed")

    result_path_raw = os.environ.get("STEGVERSE_REUSABLE_TASK_RESULT_PATH", "").strip()
    manifest_path_raw = os.environ.get("STEGVERSE_REUSABLE_TASK_MANIFEST", "").strip()
    if not result_path_raw or not manifest_path_raw:
        fail("reusable_task_result_binding_missing")
    manifest = load_json(Path(manifest_path_raw))
    predicates = json.loads(os.environ.get("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]"))
    if not isinstance(predicates, list):
        fail("completion_predicates_invalid")

    # This runner may only publish standardized completion evidence when the full
    # declared chain is actually present. Otherwise it exits at the first real
    # evidence boundary and trigger_reusable_task records that boundary.
    tvc = runtime_root / TVC_RECEIPT
    observer_candidates = [runtime_root / OBSERVER_RECEIPT, Path("/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json")]
    observer = next((x for x in observer_candidates if x.is_file()), None)
    if not tvc.is_file():
        fail("stegbrowser_tvc_source_promotion_receipt_not_observed")
    if observer is None:
        fail("runtime_observation_receipt_not_observed")
    observed = load_json(observer)
    if observed.get("state") != "OWNER_INGRESS_READY_OBSERVED" or observed.get("simultaneous_listener_observation") is not True:
        fail("owner_ingress_ready_not_observed")

    result = {
        "schema": "stegverse.reusable-task-runner-result/v1",
        "invocation_id": os.environ.get("STEGVERSE_REUSABLE_TASK_INVOCATION_ID"),
        "reusable_task_id": os.environ.get("STEGVERSE_REUSABLE_TASK_ID"),
        "manifest_hash": manifest.get("manifest_hash"),
        "completion_predicates_satisfied": predicates,
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "canonical_work_consumption_receipt": str(consumption),
        "tvc_source_promotion_receipt": str(tvc),
        "runtime_observation_receipt": str(observer),
        "ephemeral_runtime_verification": verified,
        "authority_effect": "NONE",
    }
    out = Path(result_path_raw)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
