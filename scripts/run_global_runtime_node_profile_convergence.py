#!/usr/bin/env python3
"""Run global convergence in a frozen measurement context over HB32 retained-node profiles."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
PROFILE_REL = Path("control/runtime-node-profiles.json")
PROJECTION_REL = Path("control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json")
BASE_RUNNER_REL = Path("scripts/run_global_runtime_evidence_convergence.py")
FAILURE_BOUNDARY_REL = Path("workers/runtime_failure_boundaries.py")
MEASUREMENT_REL = Path("workers/runtime_convergence_measurement.py")
PROFILE_RECEIPT_REL = Path("receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json")
STEGCLAW_WRAPPER_REL = Path("workers/stegclaw_p4_profiled_resident_execution.py")
VACC_WRAPPER_REL = Path("workers/vacc_profiled_resident_execution.py")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _load_python_module(path: Path, module_name: str):
    require(path.is_file(), f"python module missing:{path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    require(spec is not None and spec.loader is not None, f"python module import failed:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runtime_or_source(runtime: Path, source: Path, rel: Path) -> Path:
    candidate = runtime / rel
    return candidate if candidate.is_file() else source / rel


def load_profiles(source: Path, runtime: Path) -> tuple[dict[str, Any], Path]:
    path = _runtime_or_source(runtime, source, PROFILE_REL)
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
    require(len({row.get("task_id") for row in profiles if isinstance(row, dict)}) == 18, "runtime-node task identities must be unique")
    return data, path


def _find_vacc_state(runtime: Path) -> dict[str, Any] | None:
    candidates = [runtime / "receipts/ecosystem-chat-sovereign-inference/va_conversational_runtime_process.json"]
    receipts = runtime / "receipts"
    if receipts.is_dir():
        candidates.extend(sorted(receipts.glob("**/va_conversational_runtime_process.json")))
    for path in candidates:
        if not path.is_file():
            continue
        try:
            state = load_json(path)
        except Exception:
            continue
        if state.get("schema") == "stegverse.va-conversational-runtime-process/v1":
            return {"path": str(path), "value": state}
    return None


def _run_profile_wrapper(source: Path, runtime: Path, wrapper_rel: Path, label: str, timeout: int = 7200) -> dict[str, Any]:
    wrapper = _runtime_or_source(runtime, source, wrapper_rel)
    require(wrapper.is_file(), f"{label} resident wrapper missing")
    env = os.environ.copy()
    env["STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY"] = "1"
    completed = subprocess.run(
        [sys.executable, str(wrapper), "--source-root", str(source), "--runtime-root", str(runtime)],
        cwd=runtime, capture_output=True, text=True, check=False, timeout=timeout, env=env,
    )
    result = parse_last_json(completed.stdout)
    if isinstance(result, dict):
        return {**result, "wrapper_returncode": completed.returncode, "wrapper": str(wrapper_rel)}
    return {"state":f"PROFILE_BOUND_{label}_WRAPPER_NO_RESULT","wrapper_returncode":completed.returncode,"stderr_tail":completed.stderr[-1200:]}


def resolve_profile(source: Path, runtime: Path, profile: dict[str, Any]) -> dict[str, Any]:
    task_id = str(profile.get("task_id"))
    binding = profile.get("execution_binding") or {}
    kind = binding.get("type")
    if task_id == "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023" and kind == "EXISTING_TASK_RUNTIME_WRAPPER":
        return _run_profile_wrapper(source, runtime, VACC_WRAPPER_REL, "VACC")
    if task_id == "DATA-CONTINUATION-STEGCLAW-P4" and kind == "EXISTING_TASK_RUNTIME_WRAPPER":
        return _run_profile_wrapper(source, runtime, STEGCLAW_WRAPPER_REL, "STEGCLAW", timeout=1200)
    if kind == "EXACT_PARENT_REBIND_PROFILE" and task_id == "DECISION-ENVELOPE-DE006":
        consumer_path = _runtime_or_source(runtime, source, Path(str(binding.get("consumer_ref"))))
        require(consumer_path.is_file(), "DE006 observability consumer missing")
        consumer = load_json(consumer_path)
        refs = consumer.get("evidence_bindings") or {}
        present = {name: (runtime / str(rel)).is_file() for name, rel in refs.items() if isinstance(rel, str)}
        return {
            "state":"PROFILE_BOUND_PARENT_CHAIN_PRESENT_REEXECUTION_READY" if present and all(present.values()) else "PROFILE_BOUND_PARENT_REBIND_REQUIRED",
            "required_parent_predicate":binding.get("required_parent_predicate"),
            "evidence_bindings":present,
            "measurement_only":True,
        }
    return {}


def _state_success_current(state: str) -> bool:
    value = state.upper()
    return value in {"COMPLETED","EXECUTED","OBSERVED","ADMITTED","VERIFIED","PASS","PASSED","STEGCLAW_P4_RESIDENT_EXECUTION_OBSERVED","VACC_PROFILED_RESIDENT_REQUEST_EXECUTED"}


def _derive_observations(result: Mapping[str, Any], profile: Mapping[str, Any], boundaries) -> dict[str, Any]:
    if isinstance(result.get("stage_observations"), Mapping):
        return dict(result["stage_observations"])
    resume_index = boundaries._stage_from_resume(profile.get("resume_stage"))
    observations: dict[str, Any] = {}
    state = str(result.get("state") or "UNKNOWN")
    for stage in boundaries.STAGES:
        idx, name = stage["index"], stage["stage"]
        if idx == 1:
            observations[name] = {"state":"PASS_CURRENT_RUN","basis":"profile resolved from frozen registry"}
        elif idx < resume_index:
            observations[name] = {"state":"PASS_HISTORICAL_EVIDENCE","basis":"canonical non-regression resume stage; not re-proven in this run"}
        elif idx == resume_index:
            if state.upper() == "ALREADY_CONSUMED":
                observations[name] = {"state":"PASS_HISTORICAL_EVIDENCE","basis":state}
            elif _state_success_current(state):
                observations[name] = {"state":"PASS_CURRENT_RUN","basis":state}
            else:
                observations[name] = {"state":"FAILED_CURRENT_RUN","reason":state}
        else:
            observations[name] = {"state":"NOT_REACHED"}
    return observations


def execute(source_root: Path, runtime_root: Path, *, base_executor: Callable[[Path, Path], dict[str, Any]] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    profile_data, profile_path = load_profiles(source, runtime)
    boundaries = _load_python_module(_runtime_or_source(runtime, source, FAILURE_BOUNDARY_REL), "stegverse_runtime_failure_boundaries")
    measurement = _load_python_module(_runtime_or_source(runtime, source, MEASUREMENT_REL), "stegverse_runtime_convergence_measurement")
    projection_path = _runtime_or_source(runtime, source, PROJECTION_REL)
    context = measurement.freeze_context(source, runtime, profile_path, projection_path, profile_data["profiles"])
    by_task = {row["task_id"]: row for row in profile_data["profiles"]}

    prior_measurement = os.environ.get("STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY")
    os.environ["STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY"] = "1"
    try:
        if base_executor is None:
            base = _load_python_module(_runtime_or_source(runtime, source, BASE_RUNNER_REL), "stegverse_base_global_convergence")
            base_receipt = base.execute(source, runtime)
        else:
            base_receipt = base_executor(source, runtime)
    finally:
        if prior_measurement is None:
            os.environ.pop("STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY", None)
        else:
            os.environ["STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY"] = prior_measurement

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
            "runtime_node_profile_id":profile.get("profile_id"),
            "runtime_node_origin":profile.get("node_origin"),
            "hb_protocol":profile_data["profile_policy"]["hb_protocol"],
            "node_state_class":profile_data["profile_policy"]["node_state_class"],
            "execution_session_class":profile_data["profile_policy"]["execution_session_class"],
            "node_identity_survives_session_teardown":True,
            "measurement_run_id":context["run_id"],
        })
        if lane.get("state") == "NO_REGISTERED_SELECTOR" or lane.get("execution_path") == "UNWIRED_CHILD_RUNTIME":
            resolved = resolve_profile(source, runtime, profile)
            if resolved:
                result["execution_path"] = "HB_SYNCED_STEGOS_RUNTIME_NODE_PROFILE"
                result.update(resolved)
        result["stage_observations"] = _derive_observations(result, profile, boundaries)
        profiled.append(boundaries.annotate_lane_outcome(result))

    require(not any(row.get("execution_path") == "UNWIRED_CHILD_RUNTIME" for row in profiled), "unwired child runtime remains after profile convergence")
    context = measurement.finish_context(context, runtime, profile_data["profiles"])
    receipt = {
        "schema":"stegverse.global-runtime-node-profile-convergence/v1",
        "state":"PROFILE_CONVERGENCE_MEASUREMENT_COMPLETE",
        "goal_task_id":"GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001",
        "cosv":profile_data.get("cosv"),
        "measurement_context":context,
        "member_count":len(profiled),
        "unwired_member_count":0,
        "lane_outcomes":profiled,
        "failure_boundary_summary":boundaries.summarize_failure_boundaries(profiled),
        "base_convergence_state":base_receipt.get("state"),
        "authority_effect":"NONE_PROFILE_AND_OBSERVATION_ONLY",
        "nonclaims":[
            "HISTORICAL_PASS_IS_NOT_CURRENT_RUN_PASS",
            "PROFILE_BINDING_DOES_NOT_PROVE_RUNTIME_EXECUTION",
            "HB_SYNC_DOES_NOT_GRANT_EXECUTION_AUTHORITY",
            "RETAINED_NODE_PROFILE_DOES_NOT_MINT_CLAIM_OR_FENCE",
            "FAILURE_BOUNDARY_CLASSIFICATION_DOES_NOT_ADVANCE_RUNTIME_STATE",
            "MEASUREMENT_RUN_DOES_NOT_REPAIR_OR_RETRY_AFTER_FIRST_FAILURE",
        ],
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
    print(json.dumps({"state":result["state"],"run_id":result["measurement_context"]["run_id"],"member_count":result["member_count"],"failure_boundary_summary":result["failure_boundary_summary"],"receipt":str(args.runtime_root.expanduser().resolve() / PROFILE_RECEIPT_REL)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
