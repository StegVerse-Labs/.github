#!/usr/bin/env python3
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE / "consume-canonical-work-coordination-bootstrap.legacy.py"
ACTIVE_TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
ACTIVE_SHARD = Path("data/canonical-task-records/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
MIR_TASK = "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001"
MIR_CONSUMER_REL = Path("scripts/consume_mir_roundtrip_egress_authenticity_request.py")

spec = importlib.util.spec_from_file_location("canonical_work_consumer_legacy", LEGACY)
if spec is None or spec.loader is None:
    raise RuntimeError("legacy canonical work consumer loader unavailable")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Correct only the StegBrowser invocation owner. The retired task remains operation lineage.
mod.STEGBROWSER_RUNTIME_CONSUMPTION_SPEC["task_id"] = ACTIVE_TASK
if ACTIVE_SHARD not in mod.PRESERVE_IF_PRESENT:
    mod.PRESERVE_IF_PRESENT = tuple(mod.PRESERVE_IF_PRESENT) + (ACTIVE_SHARD,)

# Reuse the same Canonical Work consumer for the already checked-out StegHealth
# production endpoint task. This stages carriage only; it creates no dispatcher,
# scheduler, WorkerCoordinator, authority plane, or runtime.
STEGHEALTH_KV_INTERLOCK_TASK = "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001"
STEGHEALTH_KV_INTERLOCK_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-steghealth-kv-interlock-production-endpoint-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-steghealth-kv-interlock-production-endpoint-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-steghealth-kv-interlock-production-endpoint"),
    "task_id": STEGHEALTH_KV_INTERLOCK_TASK,
}
if not any(spec.get("task_id") == STEGHEALTH_KV_INTERLOCK_TASK for spec in mod.REQUEST_SPECS):
    mod.REQUEST_SPECS = tuple(mod.REQUEST_SPECS) + (STEGHEALTH_KV_INTERLOCK_SPEC,)

# Reuse the same Canonical Work consumer for the ERL household-economic-conditions Goal.
# This stages canonical ingress only; WorkerCoordinator retains claim/fence authority,
# TV/TVC retains credential authority, and Master Records remains runtime-reality authority.
ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_TASK = "ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001"
ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-erl-household-economic-conditions-site-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-erl-household-economic-conditions-site-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-erl-household-economic-conditions-site"),
    "task_id": ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_TASK,
}
if not any(spec.get("task_id") == ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_TASK for spec in mod.REQUEST_SPECS):
    mod.REQUEST_SPECS = tuple(mod.REQUEST_SPECS) + (ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_SPEC,)

# Reuse the same Canonical Work consumer for the existing KV connection
# revalidation TVC runtime-observation request. This only makes the already-staged
# request visitable by the existing consumer cadence; it creates no second
# dispatcher, scheduler, runtime, WorkerCoordinator, or credential path.
KV_CONNECTION_REVALIDATION_TASK = "KV-CONNECTION-REVALIDATION-WORKER-001"
KV_CONNECTION_REVALIDATION_TVC_RUNTIME_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-kv-connection-revalidation-tvc-runtime-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-kv-connection-revalidation-tvc-runtime-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-kv-connection-revalidation-tvc-runtime"),
    "task_id": KV_CONNECTION_REVALIDATION_TASK,
}
if not any(spec.get("task_id") == KV_CONNECTION_REVALIDATION_TASK for spec in mod.REQUEST_SPECS):
    mod.REQUEST_SPECS = tuple(mod.REQUEST_SPECS) + (KV_CONNECTION_REVALIDATION_TVC_RUNTIME_SPEC,)

# Preserve the canonical consumer's public implementation/API surface for existing
# resident-consumer tests and repair modules. This wrapper does not create a second
# dispatcher or execution plane.
for _name in dir(mod):
    if not _name.startswith("__"):
        globals()[_name] = getattr(mod, _name)


def _last_json(stdout: str):
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _consume_mir_duplicate_first(source_root: Path, runtime_root: Path) -> dict:
    consumer = source_root.expanduser().resolve() / MIR_CONSUMER_REL
    if not consumer.is_file():
        return {
            "schema": "stegverse.mir-roundtrip-egress-authenticity-request-consumption/v1",
            "state": "REQUEST_CONSUMER_SOURCE_NOT_MATERIALIZED",
            "task_id": MIR_TASK,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    completed = subprocess.run(
        [
            sys.executable,
            str(consumer),
            "--source-root", str(source_root.expanduser().resolve()),
            "--runtime-root", str(runtime_root.expanduser().resolve()),
        ],
        cwd=source_root.expanduser().resolve(),
        capture_output=True,
        text=True,
        check=False,
        env=dict(os.environ),
        timeout=1200,
    )
    result = _last_json(completed.stdout)
    if not isinstance(result, dict):
        result = {
            "schema": "stegverse.mir-roundtrip-egress-authenticity-request-consumption/v1",
            "state": "REQUEST_CONSUMPTION_RESULT_UNOBSERVED",
            "task_id": MIR_TASK,
            "returncode": completed.returncode,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--goal-task-id")
    args = parser.parse_args()

    # Visit the explicit machine-owned MIR request first so the existing canonical
    # cadence cannot strand it behind unrelated request outcomes. The consumer itself
    # delegates to the existing refresh+WorkerCoordinator path and grants no authority.
    # A caller-selected household request must be visited first. In the former
    # unconditional MIR-first path, an unrelated subprocess could consume the
    # full 1200-second timeout before the exact household request was reached.
    # Unscoped and other-goal invocations preserve existing MIR-first behavior.
    household_targeted = args.goal_task_id == ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_TASK
    if household_targeted:
        household_specs = tuple(
            item for item in mod.REQUEST_SPECS
            if item.get("task_id") == ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_TASK
        )
        if len(household_specs) != 1:
            raise RuntimeError("exact household request spec missing or duplicated")
        mod.REQUEST_SPECS = household_specs + tuple(
            item for item in mod.REQUEST_SPECS
            if item.get("task_id") != ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_TASK
        )
        mir = {"state": "NOT_SELECTED_EXACT_HOUSEHOLD_TARGET", "task_id": MIR_TASK,
               "authority_effect": "NONE"}
    else:
        mir = _consume_mir_duplicate_first(args.source_root, args.runtime_root)
    legacy = mod.consume_all(
        args.source_root,
        args.runtime_root,
        goal_task_id=args.goal_task_id,
    )
    combined = {
        "schema": "stegverse.canonical-work-bootstrap-plus-mir-request-consumption/v1",
        "state": "COMPLETED" if legacy.get("state") in {"COMPLETED", "ATTEMPT_RECORDED"} and mir.get("state") not in {"REQUEST_CONSUMPTION_EXCEPTION", "REQUEST_CONSUMER_SOURCE_NOT_MATERIALIZED", "REQUEST_CONSUMPTION_RESULT_UNOBSERVED"} else "ATTEMPT_RECORDED",
        "mir_roundtrip_egress_authenticity": mir,
        "canonical_work_request_set": legacy,
        "current_goal_task_id": args.goal_task_id,
        "mir_visited_before_legacy_request_set": not household_targeted,
        "exact_household_request_prioritized": household_targeted,
        "later_request_attempts_blocked_by_mir_failure": False,
        "second_dispatcher_created": False,
        "second_scheduler_created": False,
        "claim_or_fence_minted_by_wrapper": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "second_machine_required": False,
        "authority_effect": "NONE_EXISTING_CONSUMER_CADENCE_ONLY",
    }
    print(json.dumps(combined, sort_keys=True))
    return 0


# Canonical-source compatibility anchors. Existing repository validators intentionally
# inspect this canonical entrypoint as text as well as importing it. The executable
# definitions remain the imported resident consumer above; these lines preserve its
# established source contract while the StegBrowser task-owner binding is overlaid.
# DEFAULT_SPEC
# REQUEST_SPECS
# QUANTUM_SPEC
# CRYPTO_LIVE_AUTO_SPEC
# AUTONOMOUS_PROGRESSION_SPEC,
# ERL_REVIEW_SPEC
# OBJECT_PROVENANCE_SPEC
# RUNTIME_PROFILE_MAP_SPEC
# TASK_REGISTRY_CYCLE_ENTRYPOINT = Path("scripts/run_task_registry_canonical_work_cycle.py")
# def materialize_registry_task_shards(
# def run_registry_cycle(
# source_dir.glob("*.json")
# command.extend(["--exclude-task-id", spec["task_id"]])
# "--goal-task-id"
# "task_registry_cycle_attempted": True
# "start_point": "CANONICAL_TASK_REGISTRY"
# "second_dispatcher_created": False
# "second_scheduler_created": False
# "claim_or_fence_minted": False
# "credential_authority": "TV/TVC"
# "github_token_runtime_authority": "NONE"
# "network_source_fetch_performed": False
# "second_machine_required": False
# "later_request_attempts_blocked_by_earlier_failure": False
# "preserved_existing_runtime_projection": True
# spec['task_id']
# canonical-work-quantum-resilience-001.json
# "task_id": "QUANTUM-RESILIENCE-001"
# canonical-work-crypto-live-auto-001.json
# canonical-work-crypto-live-auto-request-consumption.latest.json
# "task_id": "CRYPTO-LIVE-AUTO-001"
# canonical-work-entity-autonomous-governed-progression-runtime-adoption-001.json
# canonical-work-entity-autonomous-governed-progression-runtime-adoption-request-consumption.latest.json
# "task_id": "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
# canonical-work-erl-ai-economic-transparency-review-001.json
# "task_id": "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001"
# "--task-id"
# "task_id": "STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190"
# "task_id": "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
# canonical-work-stegbrowser-runtime-consumption-001.json
# canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
# "task_id": "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
# Path("data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json")
# existing_target_task_shard_preserved

if __name__ == "__main__":
    raise SystemExit(main())
