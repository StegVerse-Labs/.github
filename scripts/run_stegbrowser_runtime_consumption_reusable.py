#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib, importlib.util, json, os, subprocess, sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEGACY = HERE / "run_stegbrowser_runtime_consumption_reusable.legacy.py"
INGRESS_WORKER_REL = Path("workers/stegbrowser_manifest_intr_ingress.py")
TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
GOAL_ID = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001"
COSV = "40000100100000"
BINDING_RECEIPT_REL = Path("receipts/sovereign-host/stegbrowser-node-interlock-lease-runtime-binding.latest.json")

spec = importlib.util.spec_from_file_location("stegbrowser_runtime_legacy", LEGACY)
if spec is None or spec.loader is None:
    raise RuntimeError("legacy StegBrowser runtime runner loader unavailable")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BOUND: dict[str, Any] = {}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def load_node_binding(source: Path, stegos: Path, p: dict[str, Any]) -> dict[str, Any]:
    raw_ref = str(p.get("node_binding_ref") or os.environ.get("STEGVERSE_STEGBROWSER_NODE_BINDING_REF") or "").strip()
    if not raw_ref:
        mod.fail("registered_stegverse_node_binding_ref_missing")
    ref = Path(raw_ref).expanduser()
    candidates = [ref] if ref.is_absolute() else [source / ref, Path.cwd() / ref]
    path = next((c.resolve() for c in candidates if c.is_file()), None)
    if path is None:
        mod.fail("registered_stegverse_node_binding_ref_not_found")
    value = mod.load_json(path)
    genesis = value.get("genesis_receipt") if isinstance(value.get("genesis_receipt"), dict) else value
    sys.path.insert(0, str(stegos))
    from stegos.network_manifold import validate_node_genesis_receipt
    try:
        validate_node_genesis_receipt(genesis)
    except Exception as exc:
        mod.fail(f"registered_stegverse_node_receipt_invalid:{type(exc).__name__}:{exc}")
    if genesis.get("schema") != "stegos.node_handoff_receipt.v1" or genesis.get("receipt_number") != 1:
        mod.fail("registered_stegverse_node_receipt_one_required")
    node_id = genesis.get("node_id")
    interlock_id = genesis.get("interlock_id")
    receipt_sha256 = genesis.get("receipt_sha256")
    if not all(isinstance(x, str) and x for x in (node_id, interlock_id, receipt_sha256)):
        mod.fail("registered_stegverse_node_identity_incomplete")
    return {
        "node_binding_ref": str(path),
        "node_id": node_id,
        "interlock_id": interlock_id,
        "registration_receipt_sha256": receipt_sha256,
    }


def install_binding_hooks(source: Path, resident_root: Path, stegos: Path, p: dict[str, Any]) -> None:
    node = load_node_binding(source, stegos, p)
    manifest_sha256 = str(os.environ.get("STEGVERSE_STEGBROWSER_MANIFEST_SHA256") or "").strip()
    if len(manifest_sha256) != 64:
        mod.fail("manifest_sha256_not_bound_before_node_runtime_materialization")
    basis = {
        "goal_task_id": GOAL_ID,
        "operation_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "manifest_sha256": manifest_sha256,
        "node_id": node["node_id"],
        "interlock_id": node["interlock_id"],
        "registration_receipt_sha256": node["registration_receipt_sha256"],
    }
    basis_sha256 = hashlib.sha256(canonical_bytes(basis)).hexdigest()
    BOUND.update(node | basis | {"binding_basis_sha256": basis_sha256})

    sys.path.insert(0, str(stegos))
    lease_mod = importlib.import_module("stegos.ephemeral_runtime_lease")
    runtime_mod = importlib.import_module("stegos.sovereign_local_event_runtime")
    original_lease_request = lease_mod.LeaseRequest
    original_materialize = runtime_mod.SovereignLocalEventRuntimeAdapter.materialize

    def bound_lease_request(*args, **kwargs):
        kwargs["lease_id"] = f"STEGBROWSER-{basis_sha256[:16]}"
        kwargs["source_receipt_id"] = "sha256:" + node["registration_receipt_sha256"]
        kwargs["state_root_binding"] = "sha256:" + basis_sha256
        kwargs["implementation_ref"] = str(kwargs.get("implementation_ref") or "") + f"|goal:{GOAL_ID}|node:{node['node_id']}|interlock:{node['interlock_id']}|manifest:{manifest_sha256}"
        request = original_lease_request(*args, **kwargs)
        BOUND["lease_id"] = request.lease_id
        BOUND["state_root_binding"] = request.state_root_binding
        return request

    def bound_materialize(self, compute_lease, implementation_ref):
        runtime = original_materialize(self, compute_lease, implementation_ref)
        lease_id = runtime.get("lease_id")
        runtime_id = runtime.get("runtime_id")
        if lease_id != BOUND.get("lease_id") or not isinstance(runtime_id, str) or not runtime_id:
            mod.fail("node_interlock_lease_runtime_correlation_failed")
        BOUND["runtime_id"] = runtime_id
        receipt = {
            "schema": "stegverse.stegbrowser-node-interlock-lease-runtime-binding/v1",
            "state": "INVOCATION_OWNED_EPHEMERAL_STEGOS_MATERIALIZED",
            "goal_task_id": GOAL_ID,
            "operation_task_id": TASK_ID,
            "cosv_task_vector": COSV,
            "manifest_sha256": manifest_sha256,
            "node_id": node["node_id"],
            "interlock_id": node["interlock_id"],
            "registration_receipt_sha256": node["registration_receipt_sha256"],
            "node_binding_ref": node["node_binding_ref"],
            "binding_basis_sha256": basis_sha256,
            "lease_id": lease_id,
            "runtime_id": runtime_id,
            "runtime_class": "EVENT_EPHEMERAL",
            "rendezvous_required": False,
            "external_runtime_required": False,
            "external_device_required": False,
            "authority_effect": "NONE_EVIDENCE_ONLY",
        }
        mod.atomic_json(resident_root / BINDING_RECEIPT_REL, receipt)
        return runtime

    lease_mod.LeaseRequest = bound_lease_request
    runtime_mod.SovereignLocalEventRuntimeAdapter.materialize = bound_materialize


def stage_after_claim(source: Path, runtime_root: Path, record: dict):
    allowed = record.get("allowed_next_transitions") or []
    if "ENTER_GOVERNED_INTR_TRANSPORT" not in allowed:
        mod.fail("governed_intr_transport_transition_not_allowed")
    required = ("node_id", "interlock_id", "registration_receipt_sha256", "lease_id", "runtime_id", "manifest_sha256")
    if not all(isinstance(BOUND.get(k), str) and BOUND.get(k) for k in required):
        mod.fail("node_interlock_lease_runtime_binding_not_observed")
    worker = runtime_root / INGRESS_WORKER_REL
    if not worker.is_file():
        worker = source / INGRESS_WORKER_REL
    env = dict(os.environ)
    env.update({
        "STEGVERSE_STEGBROWSER_NODE_ID": BOUND["node_id"],
        "STEGVERSE_STEGBROWSER_INTERLOCK_ID": BOUND["interlock_id"],
        "STEGVERSE_STEGBROWSER_REGISTRATION_RECEIPT_SHA256": BOUND["registration_receipt_sha256"],
        "STEGVERSE_STEGBROWSER_LEASE_ID": BOUND["lease_id"],
        "STEGVERSE_STEGBROWSER_RUNTIME_ID": BOUND["runtime_id"],
        "STEGVERSE_STEGBROWSER_MANIFEST_SHA256": BOUND["manifest_sha256"],
    })
    completed = subprocess.run(
        [sys.executable, str(worker), "--source-root", str(source), "--runtime-root", str(runtime_root)],
        cwd=runtime_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=1200,
        env=env,
    )
    result = None
    for line in reversed([x.strip() for x in completed.stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            result = value
            break
    if completed.returncode != 0 or not isinstance(result, dict) or result.get("state") != "AUTHENTIC_INTR_INGRESS_OBSERVED":
        mod.fail("organization_local_intr_ingress_not_observed")
    for key in ("node_id", "interlock_id", "lease_id", "runtime_id"):
        if result.get(key) != BOUND[key]:
            mod.fail(f"organization_local_intr_ingress_{key}_mismatch")
    claim_id, fence = result.get("claim_id"), result.get("fencing_token")
    if not isinstance(claim_id, str) or not isinstance(fence, int) or not claim_id.endswith(f"-G{fence}"):
        mod.fail("workercoordinator_claim_fence_not_observed")

    registry = mod.load_json(source / "data/canonical-task-registry.json")
    projected_registry = mod.copy.deepcopy(registry)
    tasks = projected_registry.get("tasks")
    if not isinstance(tasks, list):
        mod.fail("canonical_registry_tasks_missing")
    indexes = [i for i,row in enumerate(tasks) if isinstance(row,dict) and row.get("task_id") == TASK_ID]
    if len(indexes) > 1:
        mod.fail("canonical_task_identity_duplicated_in_registry")
    projected_record = mod.copy.deepcopy(record)
    projected_record["coordination_state"] = "PROPOSED"
    projected_record["runtime_ingress_projection"] = {
        "source_coordination_state":"ACTIVE",
        "projected_coordination_state":"PROPOSED",
        "operation_lineage_task_id":mod.OPERATION_LINEAGE_TASK_ID,
        "node_id":BOUND["node_id"],
        "interlock_id":BOUND["interlock_id"],
        "lease_id":BOUND["lease_id"],
        "runtime_id":BOUND["runtime_id"],
        "workercoordinator_claim_fence_observed":True,
        "claim_ref":claim_id,
        "fence_ref":fence,
        "organization_local_intr_ingress_receipt_verified":True,
        "organization_local_receipt_ref":result.get("organization_local_receipt_ref"),
        "authentic_intr_ingress_observed":True,
        "source_mutated":False,
        "claim_or_fence_minted":False,
        "authority_effect":"NONE_RUNTIME_PROJECTION_ONLY"
    }
    if indexes:
        projected_registry["tasks"][indexes[0]] = mod.copy.deepcopy(projected_record)
    runtime_registry = runtime_root / "data/canonical-task-registry.json"
    runtime_shard = runtime_root / "data/canonical-task-records" / f"{TASK_ID}.json"
    mod.atomic_json(runtime_registry, projected_registry)
    mod.atomic_json(runtime_shard, projected_record)
    return projected_record["runtime_ingress_projection"] | {
        "runtime_registry_ref":str(runtime_registry),
        "runtime_task_shard_ref":str(runtime_shard),
    }

mod.stage_runtime_ingress_projection = stage_after_claim


def main() -> int:
    try:
        p = mod.params()
        source = mod.resolve_path(p.get("sovereign_source_root") or p.get("source_root"), "STEGVERSE_HEARTBEAT_SOURCE_ROOT", ROOT)
        resident_root = mod.resolve_path(p.get("runtime_root") or p.get("resident_runtime_root"), "STEGVERSE_HEARTBEAT_ROOT")
        stegos = mod.resolve_path(p.get("stegos_source_root"), "STEGVERSE_STEGOS_SOURCE_ROOT", source.parent / "StegOS")
        install_binding_hooks(source, resident_root, stegos, p)
        rc = mod.main()
        boundary_path = resident_root / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
        if boundary_path.is_file():
            boundary = mod.load_json(boundary_path)
            projection = boundary.get("runtime_ingress_projection") or {}
            if projection.get("workercoordinator_claim_fence_observed") is True and projection.get("authentic_intr_ingress_observed") is True:
                boundary["node_id"] = BOUND.get("node_id")
                boundary["interlock_id"] = BOUND.get("interlock_id")
                boundary["lease_id"] = BOUND.get("lease_id")
                boundary["runtime_id"] = BOUND.get("runtime_id")
                boundary["workercoordinator_claim_fence_observed"] = True
                boundary["claim_ref"] = projection.get("claim_ref")
                boundary["fence_ref"] = projection.get("fence_ref")
                boundary["organization_local_intr_ingress_receipt_verified"] = True
                boundary["authentic_intr_ingress_observed"] = True
                boundary["next_required_predicate"] = "ROUND_TRIP_1_DECLARED_MIRROR_REFLECTION"
                mod.atomic_json(boundary_path, boundary)
                print(json.dumps(boundary, sort_keys=True))
        return rc
    except SystemExit:
        raise
    except Exception as exc:
        mod.fail(f"node_interlock_binding_or_post_ingress_reconciliation_failed:{type(exc).__name__}:{exc}")

if __name__ == "__main__":
    raise SystemExit(main())
