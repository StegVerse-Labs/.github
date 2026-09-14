#!/usr/bin/env python3
from __future__ import annotations

import copy
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


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


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


def stage_runtime_ingress_projection(source: Path, runtime_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Stage only the runtime-local PROPOSED projection required by Canonical Work ingress.

    The canonical Goal remains ACTIVE/CHECKED_OUT in source. Canonical Work's existing
    ingress bootstrap correctly requires a PROPOSED task before Interlock/InTr can
    emit INGRESS_ADMITTED. The resident consumer preserves an existing runtime
    registry/shard, so this projection bridges those two state domains without
    rewriting canonical source or minting execution authority.
    """
    if record.get("task_id") != TASK_ID or record.get("coordination_state") != "ACTIVE":
        fail("runtime_ingress_projection_source_state_invalid")
    if record.get("checkout_state") != "CHECKED_OUT":
        fail("runtime_ingress_projection_checkout_state_invalid")
    if "INGRESS_ADMITTED" not in (record.get("allowed_next_transitions") or []):
        fail("runtime_ingress_projection_transition_not_allowed")
    claim = record.get("worker_claim") or {}
    if claim.get("authority") != "WORKERCOORDINATOR" or claim.get("claim_ref") is not None or claim.get("fence_ref") is not None:
        fail("runtime_ingress_projection_claim_boundary_invalid")

    registry_source = source / "data/canonical-task-registry.json"
    registry = load_json(registry_source)
    projected_registry = copy.deepcopy(registry)
    tasks = projected_registry.get("tasks")
    if not isinstance(tasks, list):
        fail("canonical_registry_tasks_missing")
    indexes = [index for index, row in enumerate(tasks) if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    if len(indexes) > 1:
        fail("canonical_task_identity_duplicated_in_registry")

    projected_record = copy.deepcopy(record)
    projected_record["coordination_state"] = "PROPOSED"
    projected_record["runtime_ingress_projection"] = {
        "source_coordination_state": "ACTIVE",
        "projected_coordination_state": "PROPOSED",
        "source_mutated": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_RUNTIME_PROJECTION_ONLY",
    }

    if indexes:
        projected_registry["tasks"][indexes[0]] = copy.deepcopy(projected_record)
    runtime_registry = runtime_root / "data/canonical-task-registry.json"
    runtime_shard = runtime_root / "data/canonical-task-records" / f"{TASK_ID}.json"
    atomic_json(runtime_registry, projected_registry)
    atomic_json(runtime_shard, projected_record)

    if load_json(source / "data/canonical-task-records" / f"{TASK_ID}.json").get("coordination_state") != "ACTIVE":
        fail("canonical_source_state_mutated_during_projection")
    return {
        "runtime_registry_ref": str(runtime_registry),
        "runtime_task_shard_ref": str(runtime_shard),
        "source_coordination_state": "ACTIVE",
        "projected_coordination_state": "PROPOSED",
        "source_mutated": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_RUNTIME_PROJECTION_ONLY",
    }


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
    ingress_projection = stage_runtime_ingress_projection(source, runtime_root, record)
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
    consumption_value = load_json(consumption)
    if consumption_value.get("state") != "COMPLETED" or consumption_value.get("task_id") != TASK_ID:
        fail("canonical_work_resident_consumption_receipt_invalid")
    bootstrap_ref = consumption_value.get("bootstrap_receipt_ref")
    if not isinstance(bootstrap_ref, str) or not Path(bootstrap_ref).is_file():
        fail("canonical_work_intr_bootstrap_receipt_missing")
    bootstrap_value = load_json(Path(bootstrap_ref))
    if bootstrap_value.get("state") != "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED" or bootstrap_value.get("task_id") != TASK_ID:
        fail("canonical_work_intr_admission_not_observed")

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
        "canonical_work_intr_bootstrap_receipt": str(bootstrap_ref),
        "runtime_ingress_projection": ingress_projection,
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
