#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGOS-AI-PREEXECUTION-RUNTIME-PROOF-001"
COSV = "40000100100000"


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


def parameters() -> dict[str, Any]:
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


def stage_runtime_projection(source: Path, runtime_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    if record.get("task_id") != TASK_ID or record.get("coordination_state") != "ACTIVE":
        fail("runtime_projection_source_state_invalid")
    if record.get("checkout_state") != "CHECKED_OUT":
        fail("runtime_projection_checkout_state_invalid")
    if "INGRESS_ADMITTED" not in (record.get("allowed_next_transitions") or []):
        fail("runtime_projection_ingress_not_allowed")
    claim = record.get("worker_claim") or {}
    if claim.get("authority") != "WORKERCOORDINATOR" or claim.get("claim_ref") is not None or claim.get("fence_ref") is not None:
        fail("runtime_projection_claim_boundary_invalid")

    registry_source = source / "data/canonical-task-registry.json"
    registry = load_json(registry_source)
    projected_registry = copy.deepcopy(registry)
    tasks = projected_registry.get("tasks")
    if not isinstance(tasks, list):
        fail("canonical_registry_tasks_missing")

    projected = copy.deepcopy(record)
    projected["coordination_state"] = "PROPOSED"
    projected["runtime_ingress_projection"] = {
        "source_coordination_state": "ACTIVE",
        "projected_coordination_state": "PROPOSED",
        "source_mutated": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_RUNTIME_PROJECTION_ONLY"
    }
    matches = [i for i, row in enumerate(tasks) if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    if len(matches) > 1:
        fail("canonical_task_identity_duplicated")
    if matches:
        projected_registry["tasks"][matches[0]] = copy.deepcopy(projected)
    else:
        projected_registry["tasks"].append(copy.deepcopy(projected))
        projected_registry["generation"] = int(projected_registry.get("generation", 0)) + 1

    runtime_registry = runtime_root / "data/canonical-task-registry.json"
    runtime_shard = runtime_root / "data/canonical-task-records" / f"{TASK_ID}.json"
    atomic_json(runtime_registry, projected_registry)
    atomic_json(runtime_shard, projected)
    if load_json(source / "data/canonical-task-records" / f"{TASK_ID}.json").get("coordination_state") != "ACTIVE":
        fail("canonical_source_state_mutated")
    return {
        "runtime_registry_ref": str(runtime_registry),
        "runtime_task_shard_ref": str(runtime_shard),
        "projected_coordination_state": "PROPOSED",
        "authority_effect": "NONE_RUNTIME_PROJECTION_ONLY"
    }


def find_intr_evidence(runtime_root: Path) -> Path | None:
    for path in sorted(runtime_root.rglob("*.json")):
        try:
            value = load_json(path)
        except Exception:
            continue
        if value.get("task_id") != TASK_ID:
            continue
        state = str(value.get("state") or value.get("transition_state") or "")
        if state in {"INGRESS_ADMITTED", "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED"}:
            return path
        receipt = value.get("ingress_receipt")
        if isinstance(receipt, dict) and receipt.get("state") == "INGRESS_ADMITTED":
            return path
    return None


def main() -> int:
    p = parameters()
    source = resolve_path(p.get("sovereign_source_root"), "STEGVERSE_HEARTBEAT_SOURCE_ROOT", ROOT)
    stegos_source = resolve_path(p.get("stegos_source_root"), "STEGVERSE_STEGOS_SOURCE_ROOT", source.parent / "StegOS")
    runtime_base = resolve_path(
        p.get("runtime_base"),
        "STEGVERSE_EPHEMERAL_RUNTIME_BASE",
        Path(os.environ.get("XDG_STATE_HOME", "/tmp")) / "stegverse" / "ephemeral-runtime",
    )

    record_path = source / "data/canonical-task-records" / f"{TASK_ID}.json"
    if not record_path.is_file():
        fail("canonical_task_shard_missing")
    record = load_json(record_path)
    if record.get("cosv_task_vector") != COSV:
        fail("cosv_binding_mismatch")
    if record.get("coordination_state") != "ACTIVE" or record.get("checkout_state") != "CHECKED_OUT":
        fail("canonical_task_not_active_checked_out")
    resolution = record.get("execution_substrate_resolution") or {}
    if resolution.get("selected_substrate_id") != "ADMITTED-EPHEMERAL-STEGOS-NODE":
        fail("admitted_ephemeral_stegos_node_required")
    if resolution.get("external_device_required") is not False or resolution.get("second_user_operated_device_allowed") is not False:
        fail("device_invariant_mismatch")

    if not (stegos_source / "stegos/sovereign_local_event_runtime.py").is_file():
        fail("stegos_sovereign_local_event_runtime_missing")
    if not (stegos_source / "tests/test_ai_preexecution_network_runtime.py").is_file():
        fail("stegos_preexecution_network_test_missing")

    sys.path.insert(0, str(stegos_source))
    from stegos.ephemeral_runtime_lease import AuthorityBoundary, LeaseProfile, LeaseRequest, RendezvousRequirement, RuntimeClass
    from stegos.sovereign_local_event_runtime import SovereignLocalEventRuntimeAdapter

    record_hash = sha256_bytes(record_path.read_bytes())
    registry_hash = sha256_bytes((source / "data/canonical-task-registry.json").read_bytes())
    request = LeaseRequest(
        lease_id=f"AI-PREEXEC-{record_hash[:16]}",
        trigger_id=os.environ.get("STEGVERSE_REUSABLE_TASK_INVOCATION_ID", f"AI-PREEXEC-{record_hash[:16]}"),
        operation="stegos-ai-preexecution-runtime-proof",
        implementation_ref=f"StegVerse-Labs/.github@sha256:{record_hash}",
        source_receipt_id="sha256:" + record_hash,
        consequence_id=TASK_ID,
        consequence_registry_hash="sha256:" + registry_hash,
        generation=int(record.get("generation") or 1),
        state_root_binding="sha256:" + sha256_bytes(f"{TASK_ID}|{COSV}|{record_hash}".encode()),
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
        fail("ephemeral_stegos_node_local_verification_failed")

    runtime_root = Path(str(runtime["runtime_root"]))
    projection = stage_runtime_projection(source, runtime_root, record)
    wrapper = runtime_root / "scripts/install_and_run_canonical_work_event_bootstrap.py"
    if not wrapper.is_file():
        fail("canonical_work_wrapper_not_materialized")
    proc = subprocess.run(
        [sys.executable, str(wrapper), "--task-id", TASK_ID, "--runtime-root", str(runtime_root / "runtime" / "ai-preexecution"), "--registry", str(runtime_root / "data/canonical-task-registry.json")],
        cwd=runtime_root,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC", "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE"},
        timeout=1200,
    )
    if proc.returncode != 0:
        print(proc.stdout[-4000:])
        print(proc.stderr[-4000:], file=sys.stderr)
        fail(f"canonical_work_intr_bootstrap_failed:{proc.returncode}")
    intr_evidence = find_intr_evidence(runtime_root)
    if intr_evidence is None:
        fail("canonical_work_intr_admission_evidence_not_observed")

    test_root = runtime_root / "task-test" / "StegOS"
    shutil.copytree(stegos_source, test_root, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_ai_preexecution_governance.py", "tests/test_ai_preexecution_network_runtime.py"],
        cwd=test_root,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC", "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE"},
        timeout=1200,
    )
    if tests.returncode != 0:
        print(tests.stdout[-4000:])
        print(tests.stderr[-4000:], file=sys.stderr)
        fail(f"preexecution_allow_deny_bypass_tests_failed:{tests.returncode}")

    result_path_raw = os.environ.get("STEGVERSE_REUSABLE_TASK_RESULT_PATH", "").strip()
    manifest_path_raw = os.environ.get("STEGVERSE_REUSABLE_TASK_MANIFEST", "").strip()
    if not result_path_raw or not manifest_path_raw:
        fail("reusable_task_result_binding_missing")
    manifest = load_json(Path(manifest_path_raw))
    predicates = json.loads(os.environ.get("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]"))
    satisfied = [p for p in predicates if p != "AUTHENTIC_AI_ORIGINATED_PROPOSAL_OBSERVED"]
    result = {
        "schema": "stegverse.reusable-task-runner-result/v1",
        "invocation_id": os.environ.get("STEGVERSE_REUSABLE_TASK_INVOCATION_ID"),
        "reusable_task_id": os.environ.get("STEGVERSE_REUSABLE_TASK_ID"),
        "manifest_hash": manifest.get("manifest_hash"),
        "completion_predicates_satisfied": satisfied,
        "test_runtime_observed": True,
        "authentic_external_ai_originated_proposal_observed": False,
        "ephemeral_runtime_verification": verified,
        "runtime_ingress_projection": projection,
        "intr_evidence_ref": str(intr_evidence),
        "pytest_stdout": tests.stdout[-2000:],
        "credential_authority": "TV/TVC",
        "model_output_authority": "NONE",
        "github_runtime_authority": "NONE",
        "authority_effect": "NONE"
    }
    out = Path(result_path_raw)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
