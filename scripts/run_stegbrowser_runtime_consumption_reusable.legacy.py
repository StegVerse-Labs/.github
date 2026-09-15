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
TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
OPERATION_LINEAGE_TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
MANIFEST_REL = Path("control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
BOOTSTRAP_WRAPPER = Path("scripts/install_and_run_canonical_work_event_bootstrap.py")
BOOTSTRAP_RUNTIME_REL = Path("runtime/canonical-work-stegbrowser-runtime-consumption")
BOOTSTRAP_RECEIPT_REL = BOOTSTRAP_RUNTIME_REL / "receipts/sovereign-host/canonical-work-event-bootstrap.latest.json"
CUSTODY_RECEIPT = Path("receipts/sovereign-host/stegbrowser-runtime-consumption-evidence-custody.latest.json")
NODE_RUNTIME_BINDING_RECEIPT = Path("receipts/sovereign-host/stegbrowser-node-interlock-runtime-binding.latest.json")


def fail(reason: str) -> None:
    print(json.dumps({"state": "BOUNDARY", "reason": reason, "task_id": TASK_ID, "operation_lineage_task_id": OPERATION_LINEAGE_TASK_ID, "authority_effect": "NONE"}, sort_keys=True))
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


def atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_bytes(raw)
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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def retain_node_runtime_binding(runtime_root: Path, resident_root: Path, value: dict[str, Any]) -> None:
    atomic_json(runtime_root / NODE_RUNTIME_BINDING_RECEIPT, value)
    raw = (runtime_root / NODE_RUNTIME_BINDING_RECEIPT).read_bytes()
    atomic_bytes(resident_root / NODE_RUNTIME_BINDING_RECEIPT, raw)
    if (resident_root / NODE_RUNTIME_BINDING_RECEIPT).read_bytes() != raw:
        fail("node_runtime_binding_resident_retention_failed")


def stage_runtime_ingress_projection(source: Path, runtime_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    if record.get("task_id") != TASK_ID or record.get("coordination_state") != "ACTIVE":
        fail("runtime_ingress_projection_source_state_invalid")
    if record.get("checkout_state") != "CHECKED_OUT":
        fail("runtime_ingress_projection_checkout_state_invalid")
    if "INGRESS_ADMITTED" not in (record.get("allowed_next_transitions") or []):
        fail("runtime_ingress_projection_transition_not_allowed")
    claim = record.get("worker_claim") or {}
    if claim.get("authority") != "WORKERCOORDINATOR" or claim.get("projection_only") is not True:
        fail("runtime_ingress_projection_claim_authority_invalid")
    if claim.get("claim_ref") is not None or claim.get("fence_ref") is not None:
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
        "operation_lineage_task_id": OPERATION_LINEAGE_TASK_ID,
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
        "operation_lineage_task_id": OPERATION_LINEAGE_TASK_ID,
        "source_mutated": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_RUNTIME_PROJECTION_ONLY",
    }


def retain_bootstrap_evidence(ephemeral_root: Path, resident_root: Path, bootstrap: Path) -> dict[str, Any]:
    if resident_root == ephemeral_root:
        fail("resident_runtime_must_be_distinct_from_ephemeral_runtime")
    raw = bootstrap.read_bytes()
    target = resident_root / BOOTSTRAP_RECEIPT_REL
    atomic_bytes(target, raw)
    if target.read_bytes() != raw:
        fail("resident_bootstrap_evidence_exact_copy_failed")
    custody = {
        "schema": "stegverse.stegbrowser-runtime-consumption-evidence-custody/v2",
        "state": "AUTHENTIC_INTR_INGRESS_EVIDENCE_RETAINED_IN_EXISTING_RESIDENT_RUNTIME",
        "task_id": TASK_ID,
        "operation_lineage_task_id": OPERATION_LINEAGE_TASK_ID,
        "cosv_task_vector": COSV,
        "ephemeral_runtime_root": str(ephemeral_root),
        "resident_runtime_root": str(resident_root),
        "evidence": [{"source_ref": str(bootstrap), "resident_ref": str(target), "sha256": sha256_bytes(raw), "exact_bytes_retained": True}],
        "source_receipt_mutated": False,
        "claim_or_fence_minted": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_EVIDENCE_CUSTODY_ONLY",
    }
    atomic_json(resident_root / CUSTODY_RECEIPT, custody)
    return custody


def main() -> int:
    p = params()
    source = resolve_path(p.get("sovereign_source_root") or p.get("source_root"), "STEGVERSE_HEARTBEAT_SOURCE_ROOT", ROOT)
    resident_root = resolve_path(p.get("runtime_root") or p.get("resident_runtime_root"), "STEGVERSE_HEARTBEAT_ROOT")
    stegos = resolve_path(p.get("stegos_source_root"), "STEGVERSE_STEGOS_SOURCE_ROOT", source.parent / "StegOS")
    runtime_base = resolve_path(p.get("runtime_base"), "STEGVERSE_EPHEMERAL_RUNTIME_BASE", Path(os.environ.get("XDG_STATE_HOME", "/tmp")) / "stegverse" / "ephemeral-runtime")
    node_receipt_path = resolve_path(p.get("node_genesis_receipt"), "STEGVERSE_NODE_GENESIS_RECEIPT")

    record_path = source / "data/canonical-task-records" / f"{TASK_ID}.json"
    registry_path = source / "data/canonical-task-registry.json"
    manifest_path = source / MANIFEST_REL
    if not record_path.is_file() or not registry_path.is_file() or not manifest_path.is_file():
        fail("canonical_task_or_manifest_source_missing")
    if not node_receipt_path.is_file():
        fail("registered_stegverse_node_receipt_1_missing")
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

    if not (stegos / "stegos/sovereign_local_event_runtime.py").is_file() or not (stegos / "stegos/network_manifold.py").is_file():
        fail("stegos_local_event_or_node_validator_source_missing")
    sys.path.insert(0, str(stegos))
    from stegos.ephemeral_runtime_lease import AuthorityBoundary, LeaseProfile, LeaseRequest, RendezvousRequirement, RuntimeClass
    from stegos.network_manifold import validate_node_genesis_receipt
    from stegos.sovereign_local_event_runtime import SovereignLocalEventRuntimeAdapter

    genesis = load_json(node_receipt_path)
    try:
        validate_node_genesis_receipt(genesis)
    except Exception as exc:
        fail(f"registered_stegverse_node_receipt_1_invalid:{type(exc).__name__}:{exc}")
    node_id = str(genesis.get("node_id") or "")
    interlock_id = str(genesis.get("interlock_id") or "")
    registration_receipt_sha256 = str(genesis.get("receipt_sha256") or "")
    if not node_id or not interlock_id or not registration_receipt_sha256:
        fail("registered_stegverse_node_binding_incomplete")

    manifest_sha256 = sha256_bytes(manifest_path.read_bytes())
    expected_manifest_sha256 = str(os.environ.get("STEGVERSE_STEGBROWSER_MANIFEST_SHA256") or "").strip()
    if expected_manifest_sha256 and expected_manifest_sha256 != manifest_sha256:
        fail("manifest_sha256_binding_mismatch")

    record_hash = sha256_bytes(record_path.read_bytes())
    registry_hash = sha256_bytes(registry_path.read_bytes())
    binding_basis = {
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "manifest_sha256": manifest_sha256,
        "node_id": node_id,
        "interlock_id": interlock_id,
        "registration_receipt_sha256": registration_receipt_sha256,
    }
    binding_sha256 = sha256_bytes(canonical_bytes(binding_basis))
    state_hash = sha256_bytes(canonical_bytes({**binding_basis, "record_sha256": record_hash, "registry_sha256": registry_hash}))
    lease_id = f"STEGBROWSER-{binding_sha256[:24]}"
    request = LeaseRequest(
        lease_id=lease_id,
        trigger_id=os.environ.get("STEGVERSE_REUSABLE_TASK_INVOCATION_ID", lease_id),
        operation="stegbrowser-runtime-consumption-remediation",
        implementation_ref=f"StegVerse-Labs/.github@{record_hash}",
        source_receipt_id="sha256:" + registration_receipt_sha256,
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
    runtime_id = str(runtime.get("runtime_id") or "")
    if not runtime_id or runtime.get("lease_id") != lease_id:
        fail("execution_time_runtime_identity_binding_failed")
    node_runtime_binding = {
        "schema": "stegverse.stegbrowser-node-interlock-runtime-binding/v1",
        "state": "NODE_INTERLOCK_LEASE_RUNTIME_BOUND",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "manifest_sha256": manifest_sha256,
        "node_id": node_id,
        "interlock_id": interlock_id,
        "registration_receipt_sha256": registration_receipt_sha256,
        "lease_id": lease_id,
        "runtime_id": runtime_id,
        "state_root_binding": request.state_root_binding,
        "binding_sha256": binding_sha256,
        "runtime_class": "EVENT_EPHEMERAL",
        "rendezvous_requirement": "NOT_REQUIRED",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_IDENTITY_BINDING_ONLY",
    }
    retain_node_runtime_binding(runtime_root, resident_root, node_runtime_binding)

    ingress_projection = stage_runtime_ingress_projection(source, runtime_root, record)
    wrapper = runtime_root / BOOTSTRAP_WRAPPER
    if not wrapper.is_file():
        fail("canonical_work_bootstrap_wrapper_not_materialized")
    bootstrap_runtime = runtime_root / BOOTSTRAP_RUNTIME_REL
    completed = subprocess.run(
        [sys.executable, str(wrapper), "--runtime-root", str(bootstrap_runtime), "--task-id", TASK_ID, "--registry", str(runtime_root / "data/canonical-task-registry.json")],
        cwd=runtime_root,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC", "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE"},
    )
    if completed.returncode != 0:
        print(completed.stdout[-4000:])
        print(completed.stderr[-4000:], file=sys.stderr)
        fail(f"canonical_work_intr_bootstrap_failed:{completed.returncode}")

    bootstrap = runtime_root / BOOTSTRAP_RECEIPT_REL
    if not bootstrap.is_file():
        fail("canonical_work_intr_bootstrap_receipt_missing")
    bootstrap_value = load_json(bootstrap)
    if bootstrap_value.get("state") != "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED" or bootstrap_value.get("task_id") != TASK_ID:
        fail("canonical_work_intr_admission_not_observed")
    custody = retain_bootstrap_evidence(runtime_root, resident_root, bootstrap)

    boundary = {
        "schema": "stegverse.stegbrowser-runtime-remediation-boundary/v1",
        "state": "AUTHENTIC_INTR_INGRESS_OBSERVED",
        "task_id": TASK_ID,
        "operation_lineage_task_id": OPERATION_LINEAGE_TASK_ID,
        "cosv_task_vector": COSV,
        "node_interlock_runtime_binding": node_runtime_binding,
        "runtime_ingress_projection": ingress_projection,
        "canonical_work_intr_bootstrap_receipt": str(resident_root / BOOTSTRAP_RECEIPT_REL),
        "evidence_custody": custody,
        "workercoordinator_claim_fence_observed": False,
        "governed_return_packet_received": False,
        "return_record_durably_recorded": False,
        "final_allowed_transport_exit_transition_observed": False,
        "successful_data_transport_round_trip_identified": False,
        "next_required_predicate": "CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED",
        "runtime_observed": True,
        "completion_evidence_observed": False,
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_BOUNDARY_EVIDENCE_ONLY"
    }
    boundary_path = resident_root / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
    atomic_json(boundary_path, boundary)
    print(json.dumps(boundary, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
