#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEGACY = HERE / "run_stegbrowser_runtime_consumption_reusable.legacy.py"
INGRESS_WORKER_REL = Path("workers/stegbrowser_manifest_intr_ingress.py")
TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"

spec = importlib.util.spec_from_file_location("stegbrowser_runtime_legacy", LEGACY)
if spec is None or spec.loader is None:
    raise RuntimeError("legacy StegBrowser runtime runner loader unavailable")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def stage_after_claim(source: Path, runtime_root: Path, record: dict):
    allowed = record.get("allowed_next_transitions") or []
    if "ENTER_GOVERNED_INTR_TRANSPORT" not in allowed:
        mod.fail("governed_intr_transport_transition_not_allowed")
    worker = runtime_root / INGRESS_WORKER_REL
    if not worker.is_file():
        worker = source / INGRESS_WORKER_REL
    completed = subprocess.run(
        [sys.executable, str(worker), "--source-root", str(source), "--runtime-root", str(runtime_root)],
        cwd=runtime_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=1200,
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
    if result.get("invocation_request_nonce") != NONCE:
        mod.fail("workercoordinator_claim_fence_invocation_nonce_mismatch")
    claim_id, fence = result.get("claim_id"), result.get("fencing_token")
    if not isinstance(claim_id, str) or not isinstance(fence, int) or not claim_id.endswith(f"-G{fence}"):
        mod.fail("workercoordinator_claim_fence_not_observed")
    correlation_keys = (
        "manifest_sha256", "node_id", "interlock_id", "registration_receipt_sha256",
        "lease_id", "runtime_id", "state_root_binding", "node_interlock_runtime_binding_sha256",
    )
    if result.get("node_interlock_lease_runtime_correlation_verified") is not True:
        mod.fail("node_interlock_lease_runtime_correlation_not_verified")
    if any(not isinstance(result.get(key), str) or not result[key] for key in correlation_keys):
        mod.fail("node_interlock_lease_runtime_correlation_incomplete")

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
        "invocation_request_nonce":NONCE,
        "workercoordinator_claim_fence_observed":True,
        "claim_ref":claim_id,
        "fence_ref":fence,
        "organization_local_intr_ingress_receipt_verified":True,
        "organization_local_receipt_ref":result.get("organization_local_receipt_ref"),
        "authentic_intr_ingress_observed":True,
        "node_interlock_lease_runtime_correlation_verified":True,
        **{key: result[key] for key in correlation_keys},
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
    rc = mod.main()
    try:
        p = mod.params()
        resident_root = mod.resolve_path(p.get("runtime_root") or p.get("resident_runtime_root"), "STEGVERSE_HEARTBEAT_ROOT")
        boundary_path = resident_root / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"
        if boundary_path.is_file():
            boundary = mod.load_json(boundary_path)
            projection = boundary.get("runtime_ingress_projection") or {}
            if projection.get("workercoordinator_claim_fence_observed") is True and projection.get("authentic_intr_ingress_observed") is True:
                boundary["workercoordinator_claim_fence_observed"] = True
                boundary["claim_ref"] = projection.get("claim_ref")
                boundary["fence_ref"] = projection.get("fence_ref")
                boundary["organization_local_intr_ingress_receipt_verified"] = True
                boundary["authentic_intr_ingress_observed"] = True
                boundary["node_interlock_lease_runtime_correlation_verified"] = projection.get("node_interlock_lease_runtime_correlation_verified")
                for key in ("manifest_sha256", "node_id", "interlock_id", "registration_receipt_sha256", "lease_id", "runtime_id", "state_root_binding", "node_interlock_runtime_binding_sha256"):
                    boundary[key] = projection.get(key)
                boundary["next_required_predicate"] = "ROUND_TRIP_1_DECLARED_MIRROR_REFLECTION"
                mod.atomic_json(boundary_path, boundary)
                print(json.dumps(boundary, sort_keys=True))
    except Exception as exc:
        mod.fail(f"post_ingress_boundary_reconciliation_failed:{type(exc).__name__}:{exc}")
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
