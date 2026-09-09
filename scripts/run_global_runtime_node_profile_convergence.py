#!/usr/bin/env python3
"""Run the existing global convergence visitor and bind every lane to one HB32 StegOS runtime-node profile.

This is a convergence wrapper over the existing resident dispatcher/runner. It does not
create another heartbeat, scheduler, dispatcher, WorkerCoordinator, credential path, or
transition authority. The StegBrowser retained-node implementation is the state-lifecycle
reference: node identity/continuity is retained while bounded execution-session state may
be torn down. HB remains observability only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
PROFILE_REL = Path("control/runtime-node-profiles.json")
BASE_RUNNER_REL = Path("scripts/run_global_runtime_evidence_convergence.py")
PROFILE_RECEIPT_REL = Path("receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def load_base_runner(source_root: Path):
    path = source_root / BASE_RUNNER_REL
    require(path.is_file(), "base convergence runner missing")
    spec = importlib.util.spec_from_file_location("stegverse_base_global_convergence", path)
    require(spec is not None and spec.loader is not None, "base convergence runner import failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_profiles(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    path = runtime_root / PROFILE_REL
    if not path.is_file():
        path = source_root / PROFILE_REL
    data = load_json(path)
    require(data.get("schema") == "stegverse.runtime-node-profiles/v1", "runtime-node profile schema")
    require(data.get("goal_task_id") == "GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001", "runtime-node profile goal")
    policy = data.get("profile_policy") or {}
    require(policy.get("hb_protocol") == "HB32", "runtime-node profiles must use HB32")
    require(policy.get("node_state_class") == "RETAINED_STEGOS_NODE", "retained StegOS node state required")
    require(policy.get("execution_session_class") == "EPHEMERAL_OR_BOUNDED_RUNTIME_LEASE", "bounded/ephemeral session class required")
    require(policy.get("node_identity_survives_session_teardown") is True, "node identity must survive session teardown")
    require(policy.get("session_credentials_survive_teardown") is False, "session credentials may not survive teardown")
    require(policy.get("hb_is_observability_only") is True, "HB observability boundary")
    require(policy.get("hb_grants_execution_authority") is False, "HB authority forbidden")
    require(policy.get("profile_match_grants_execution_authority") is False, "profile-match authority forbidden")
    require(policy.get("worker_claim_authority") == "WORKERCOORDINATOR", "WorkerCoordinator claim authority")
    require(policy.get("credential_authority") == "TV/TVC", "TV/TVC credential authority")
    require(policy.get("transition_admission") == "INTERLOCK_INTR", "Interlock/InTr admission")
    profiles = data.get("profiles")
    require(isinstance(profiles, list) and len(profiles) == 18, "exactly 18 runtime-node profiles required")
    task_ids = [row.get("task_id") for row in profiles if isinstance(row, dict)]
    require(len(task_ids) == len(set(task_ids)) == 18, "runtime-node task identities must be unique")
    return data


def _find_vacc_state(runtime: Path) -> dict[str, Any] | None:
    direct = runtime / "receipts" / "ecosystem-chat-sovereign-inference" / "va_conversational_runtime_process.json"
    candidates = [direct]
    receipts = runtime / "receipts"
    if receipts.is_dir():
        candidates.extend(sorted(receipts.glob("**/va_conversational_runtime_process.json")))
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            state = load_json(path)
        except Exception:
            continue
        if state.get("schema") == "stegverse.va-conversational-runtime-process/v1":
            return {"path": str(path), "value": state}
    return None


def _external_root(runtime: Path, env_name: str, fallback: Path) -> Path | None:
    configured = str(os.environ.get(env_name) or "").strip()
    candidates = [Path(configured).expanduser().resolve()] if configured else []
    candidates.append((runtime / fallback).resolve())
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def resolve_unwired_profile(runtime: Path, profile: dict[str, Any]) -> dict[str, Any]:
    task_id = str(profile.get("task_id"))
    binding = profile.get("execution_binding") or {}
    kind = binding.get("type")

    if kind == "EXTERNAL_RUNTIME_PROFILE_BRIDGE" and task_id == "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023":
        observed = _find_vacc_state(runtime)
        if observed is not None:
            value = observed["value"]
            if value.get("state") == "LIVE_VERIFIED":
                return {"state": "PROFILE_BOUND_RUNTIME_LIVE_VERIFIED", "runtime_state_ref": observed["path"]}
        adapter_root = _external_root(runtime, str(binding.get("root_env")), Path("workloads/StegVerse-org/LLM-adapter"))
        if adapter_root is None:
            return {"state": "PROFILE_BOUND_EXTERNAL_RUNTIME_NOT_MATERIALIZED", "required_root_env": binding.get("root_env")}
        task_ref = adapter_root / str(binding.get("task_ref"))
        missing = [ref for ref in binding.get("required_surfaces", []) if not (adapter_root / str(ref)).is_file()]
        if not task_ref.is_file() or missing:
            return {"state": "PROFILE_BOUND_EXTERNAL_RUNTIME_SOURCE_INCOMPLETE", "adapter_root": str(adapter_root), "missing_surfaces": missing}
        return {"state": "PROFILE_BOUND_PARENT_RECONSTRUCTION_OR_ROUTE_PENDING", "adapter_root": str(adapter_root), "task_ref": str(task_ref)}

    if kind == "OBSERVABILITY_BOUND_EXTERNAL_RUNTIME" and task_id == "DATA-CONTINUATION-STEGCLAW-P4":
        external = _external_root(runtime, str(binding.get("root_env")), Path("workloads/Data-Continuation/StegClaw"))
        if external is None:
            return {"state": "PROFILE_BOUND_RESIDENT_MATERIALIZATION_PENDING", "first_runtime_predicate": binding.get("first_runtime_predicate")}
        state_path = external / str(binding.get("external_state_ref"))
        if not state_path.is_file():
            return {"state": "PROFILE_BOUND_EXTERNAL_STATE_PENDING", "external_root": str(external), "state_ref": str(state_path)}
        state = load_json(state_path)
        predicate_map = state.get("predicate_map") or {}
        first = str(binding.get("first_runtime_predicate"))
        value = predicate_map.get(first) if isinstance(predicate_map, dict) else None
        observed = value.get("observed") if isinstance(value, dict) else None
        return {
            "state": "PROFILE_BOUND_RUNTIME_PREDICATE_OBSERVED" if observed is True else "PROFILE_BOUND_RUNTIME_PREDICATE_PENDING",
            "external_state_ref": str(state_path),
            "first_runtime_predicate": first,
            "observed": observed,
        }

    if kind == "EXACT_PARENT_REBIND_PROFILE" and task_id == "DECISION-ENVELOPE-DE006":
        consumer_path = runtime / str(binding.get("consumer_ref"))
        if not consumer_path.is_file():
            consumer_path = ROOT / str(binding.get("consumer_ref"))
        require(consumer_path.is_file(), "DE006 observability consumer missing")
        consumer = load_json(consumer_path)
        refs = consumer.get("evidence_bindings") or {}
        present = {name: (runtime / str(rel)).is_file() for name, rel in refs.items() if isinstance(rel, str)}
        if all(present.values()) and present:
            return {"state": "PROFILE_BOUND_PARENT_CHAIN_PRESENT_REEXECUTION_READY", "evidence_bindings": present}
        return {
            "state": "PROFILE_BOUND_PARENT_REBIND_REQUIRED",
            "required_parent_predicate": binding.get("required_parent_predicate"),
            "reusable_device_evidence_task": binding.get("reusable_device_evidence_task"),
            "evidence_bindings": present,
        }

    raise RuntimeError(f"FAIL_CLOSED: unsupported unwired runtime-node binding:{task_id}:{kind}")


def execute(
    source_root: Path,
    runtime_root: Path,
    *,
    base_executor: Callable[[Path, Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    profile_data = load_profiles(source, runtime)
    by_task = {row["task_id"]: row for row in profile_data["profiles"]}

    if base_executor is None:
        base = load_base_runner(source)
        base_receipt = base.execute(source, runtime)
    else:
        base_receipt = base_executor(source, runtime)
    require(base_receipt.get("schema") == "stegverse.global-runtime-evidence-convergence/v1", "base convergence receipt schema")
    outcomes = base_receipt.get("lane_outcomes")
    require(isinstance(outcomes, list) and len(outcomes) == 18, "base convergence must contain 18 lane outcomes")

    profiled: list[dict[str, Any]] = []
    for lane in outcomes:
        task_id = lane.get("task_id")
        require(isinstance(task_id, str) and task_id in by_task, f"missing runtime-node profile:{task_id}")
        profile = by_task[task_id]
        result = dict(lane)
        result.update({
            "runtime_node_profile_id": profile.get("profile_id"),
            "runtime_node_origin": profile.get("node_origin"),
            "hb_protocol": profile_data["profile_policy"]["hb_protocol"],
            "node_state_class": profile_data["profile_policy"]["node_state_class"],
            "execution_session_class": profile_data["profile_policy"]["execution_session_class"],
            "node_identity_survives_session_teardown": True,
        })
        if lane.get("state") == "NO_REGISTERED_SELECTOR" or lane.get("execution_path") == "UNWIRED_CHILD_RUNTIME":
            resolved = resolve_unwired_profile(runtime, profile)
            result["execution_path"] = "HB_SYNCED_STEGOS_RUNTIME_NODE_PROFILE"
            result.update(resolved)
        profiled.append(result)

    require(not any(row.get("execution_path") == "UNWIRED_CHILD_RUNTIME" for row in profiled), "unwired child runtime remains after profile convergence")
    receipt = {
        "schema": "stegverse.global-runtime-node-profile-convergence/v1",
        "state": "PROFILE_CONVERGENCE_VISIT_COMPLETE",
        "goal_task_id": "GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001",
        "cosv": profile_data.get("cosv"),
        "baseline_milestone": profile_data.get("baseline_milestone"),
        "hb_protocol": profile_data["profile_policy"]["hb_protocol"],
        "member_count": len(profiled),
        "unwired_member_count": 0,
        "lane_outcomes": profiled,
        "base_convergence_state": base_receipt.get("state"),
        "authority_effect": "NONE_PROFILE_AND_OBSERVATION_ONLY",
        "nonclaims": [
            "PROFILE_BINDING_DOES_NOT_PROVE_RUNTIME_EXECUTION",
            "HB_SYNC_DOES_NOT_GRANT_EXECUTION_AUTHORITY",
            "RETAINED_NODE_PROFILE_DOES_NOT_MINT_CLAIM_OR_FENCE",
            "CURRENT_DEVICE_OR_PROVIDER_RUNTIME_EVIDENCE_REMAINS_REQUIRED_WHERE_UNOBSERVED"
        ]
    }
    out = runtime / PROFILE_RECEIPT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = execute(args.source_root, args.runtime_root)
    print(json.dumps({
        "state": result["state"],
        "member_count": result["member_count"],
        "unwired_member_count": result["unwired_member_count"],
        "hb_protocol": result["hb_protocol"],
        "receipt": str((args.runtime_root.expanduser().resolve() / PROFILE_RECEIPT_REL)),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
