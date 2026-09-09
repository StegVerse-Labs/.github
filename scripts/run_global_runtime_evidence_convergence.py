#!/usr/bin/env python3
"""Execute the current global runtime-evidence resume projection on one sovereign resident cycle.

This runner reuses already-existing resident consumers and task-specific bounded
consumers. It does not create a second scheduler or dispatcher. Canonical Work
ingress for CryptoBot, StegBrowser, and Runtime Profile Map is handled by the
existing canonical_work_coordination consumer before this runner is invoked.

Each member is resumed from its projected first unresolved stage. A member is
reported as NO_COMPATIBLE_RESIDENT_EXECUTION_PATH only after checking the shared
dispatcher, an already-existing task-specific local consumer, and Canonical Work.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PROJECTION_REL = Path("control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json")
DISPATCHER_REL = Path("scripts/dispatch_resident_execution_requests.py")
DISPATCH_RECEIPT_REL = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
RECEIPT_REL = Path("receipts/sovereign-host/global-runtime-evidence-convergence.latest.json")

# Existing selectors only. canonical_work_coordination is intentionally excluded
# to prevent recursion: this runner is invoked after Runtime Profile Map Canonical
# Work ingress has completed.
TASK_SELECTORS: dict[str, tuple[str, ...]] = {
    "SHWP-HIL-SOVEREIGN-RECEIVER-001": ("hil",),
    "SV-DN1-SOVEREIGN-EXECUTION-CHAIN-001": ("sv_dn1", "sv_dn1_publication"),
    "SHWP-ECOSYSTEM-CHAT-INFERENCE-001": ("ecosystem_chat",),
    "SHWP-DEVICE-KV-INTR-OBSERVATION-001": ("stegos_kv_intr_chain",),
    # Endpoint Fanout is the fourth terminal step of the same already-merged chain.
    "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001": ("stegos_kv_intr_chain",),
    "SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001": ("stegverse001_bounded_autonomy",),
    "SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001": ("sv002_public_observation",),
    "GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001": ("governed_multilane_manifold_activation",),
    "SHWP-GLM53-SOVEREIGN-LANE-001": ("glm53_sovereign_lane",),
    "SV011-PHASE5-RESIDENT-BRIDGE-001": ("sv011_phase5_source_materialization", "sv011_phase5"),
    "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001": (
        "runtime_profile_map",
        "runtime_profile_map_custody",
        "runtime_profile_map_reconciliation",
        "runtime_profile_map_transition_readiness",
        "runtime_profile_map_governance_review",
    ),
    "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001": ("native_email_action_monitor",),
}

# Existing task-specific local consumers that are already registered in their own
# worker/process-adapter surfaces but are not exposed as generic dispatcher names.
DIRECT_CONSUMERS: dict[str, Path] = {
    "GADI-RESIDENT-EXECUTION-001": Path("control/resident-execution-request.d/consume-gadi-resident-execution.py"),
}

CANONICAL_WORK_ONLY = {
    "CRYPTO-LIVE-AUTO-001": Path("receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json"),
    "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001": Path("receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json"),
}

NO_EXECUTION_PATH_REASON = {
    "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023": "current VACC task is machine-owned and has implemented LLM-adapter/TVC runtime surfaces, but no exact .github resident consumer entrypoint is materialized for this task identity",
    "DATA-CONTINUATION-STEGCLAW-P4": "StegClaw P4 has shared resident observability but no exact resident request-consumption/execution consumer attributable to the StegClaw path",
    "DECISION-ENVELOPE-DE006": "DE-006 has resident observability and prior device-local execution evidence, but exact parent rebinding/re-execution is not exposed as a compatible resident consumer",
}

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_MICRO_NODE_ROOT",
    "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT", "STEGVERSE_STEGOPS_ORCHESTRATOR_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_HIL_STATE_ROOT", "STEGVERSE_HIL_RECEIVER_PORT", "STEGVERSE_VAULT_AGENT_SOCKET",
    "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET", "STEGVERSE_ARA_MAIL_RECIPIENT",
    "STEGVERSE_ARA_MAIL_SENDER", "STEGVERSE_SV_DN1_SOURCE_ROOT",
    "STEGVERSE_SOURCE_MATERIALIZATION_ROOT", "STEGVERSE_SOURCE_PACKAGE_ROOT",
    "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT", "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT",
    "STEGVERSE_SV_DN1_INTR_STATE_ROOT", "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT", "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT", "STEGVERSE_BOOTSTRAP_V1_INTR_ROUTE_CONFIG",
    "STEGVERSE_STEGOS_ROOT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT",
    "STEGVERSE_SITE_ROOT", "STEGVERSE_STEGINDEX_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_HEALER_ROOT", "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_EVALUATOR_INTR_PORT",
    "STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
    "STEGVERSE_SV002_OBSERVE_PORT", "STEGVERSE_RELAY_RUNTIME_BASE", "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT", "STEGVERSE_GTG_ROOT", "STEGVERSE_AE_ROOT",
    "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT", "STEGVERSE_SELF_CHAR_MODEL_ID", "STEGVERSE_OLLAMA_MODEL",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT", "STEGVERSE_RESIDENT_SOURCE_MANIFEST",
    "STEGVERSE_MASTER_RECORDS_ROOT", "STEGVERSE_ORG_CONTROL_ROOT", "STEGVERSE_SV002_ORG_ROOT",
    "STEGVERSE_SV001_AUTONOMY_LEASE", "STEGVERSE_SV011_ORG_ROOT",
    "STEGVERSE_SV011_MATERIALIZED_ROOT", "STEGVERSE_GLM53_ENDPOINT",
    "STEGVERSE_GLM53_MODEL_PATH", "STEGVERSE_GLM53_RUNTIME_IDENTITY",
    "STEGVERSE_GLM53_ENERGY_KWH", "STEGVERSE_GLM53_HARDWARE_AMORTIZATION_USD",
    "STEGVERSE_GLM53_ENERGY_COST_USD", "STEGVERSE_GLM53_STORAGE_NETWORK_RUNTIME_OVERHEAD_USD",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not execute sovereign convergence: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def canonical_work_state(runtime: Path, task_id: str) -> dict[str, Any] | None:
    rel = CANONICAL_WORK_ONLY.get(task_id)
    if rel is None:
        return None
    path = runtime / rel
    return load_json(path) if path.is_file() else None


def run_direct_consumer(source: Path, runtime: Path, rel: Path, safe_env: Mapping[str, str], *, runner=subprocess.run) -> dict[str, Any]:
    runtime_consumer = runtime / rel
    source_consumer = source / rel
    consumer = runtime_consumer if runtime_consumer.is_file() else source_consumer
    if not consumer.is_file():
        return {"state": "DIRECT_CONSUMER_NOT_MATERIALIZED", "consumer_ref": rel.as_posix(), "attempted": False}
    command = [sys.executable, str(consumer), "--source-root", str(source), "--runtime-root", str(runtime)]
    try:
        completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=dict(safe_env), timeout=1200)
        result = parse_last_json(completed.stdout)
        return {
            "state": result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT",
            "consumer_ref": rel.as_posix(),
            "returncode": completed.returncode,
            "attempted": True,
            "result": result,
        }
    except Exception as exc:
        return {"state": "DIRECT_CONSUMER_EXCEPTION", "consumer_ref": rel.as_posix(), "attempted": True, "error_type": type(exc).__name__}


def execute(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    projection_path = runtime / PROJECTION_REL
    if not projection_path.is_file():
        projection_path = source / PROJECTION_REL
    projection = load_json(projection_path)
    if projection.get("goal_task_id") != "GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001":
        raise RuntimeError("global convergence projection goal mismatch")
    members = projection.get("members")
    if not isinstance(members, list) or len(members) != 18:
        raise RuntimeError("global convergence projection must contain exactly 18 current members")

    selectors: list[str] = []
    for row in members:
        task_id = row.get("task_id") if isinstance(row, dict) else None
        if isinstance(task_id, str):
            for selector in TASK_SELECTORS.get(task_id, ()):
                if selector not in selectors:
                    selectors.append(selector)

    safe_env = clean_exec_env(env)
    dispatcher = runtime / DISPATCHER_REL
    if not dispatcher.is_file():
        raise RuntimeError("resident dispatcher not materialized")
    command = [sys.executable, str(dispatcher), "--source-root", str(source), "--runtime-root", str(runtime)]
    for selector in selectors:
        command.extend(["--only-consumer", selector])
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=dict(safe_env), timeout=7200)
    dispatch_receipt_path = runtime / DISPATCH_RECEIPT_REL
    dispatch_receipt = load_json(dispatch_receipt_path) if dispatch_receipt_path.is_file() else None
    by_consumer: dict[str, dict[str, Any]] = {}
    if isinstance(dispatch_receipt, dict):
        for outcome in dispatch_receipt.get("outcomes", []):
            if isinstance(outcome, dict) and isinstance(outcome.get("consumer"), str):
                by_consumer[outcome["consumer"]] = outcome

    direct_results = {
        task_id: run_direct_consumer(source, runtime, rel, safe_env, runner=runner)
        for task_id, rel in DIRECT_CONSUMERS.items()
        if any(isinstance(row, dict) and row.get("task_id") == task_id for row in members)
    }

    lane_outcomes: list[dict[str, Any]] = []
    for member in members:
        task_id = member["task_id"]
        projected = {
            "lane": member["lane"],
            "task_id": task_id,
            "resume_stage": member["resume_stage"],
            "adopted_solutions": member["adopt"],
        }
        task_selectors = TASK_SELECTORS.get(task_id, ())
        if task_selectors:
            selector_results = [by_consumer.get(selector) for selector in task_selectors]
            states = [row.get("state") if isinstance(row, dict) else "SELECTOR_NOT_VISITED" for row in selector_results]
            lane_outcomes.append({
                **projected,
                "execution_path": "REGISTERED_RESIDENT_SELECTOR",
                "selectors": list(task_selectors),
                "selector_states": states,
                "selector_results": selector_results,
                "state": states[0] if len(states) == 1 else "MULTI_STAGE:" + ">".join(states),
            })
            continue
        if task_id in direct_results:
            result = direct_results[task_id]
            lane_outcomes.append({**projected, "execution_path": "EXISTING_TASK_SPECIFIC_RESIDENT_CONSUMER", "state": result.get("state"), "consumer_result": result})
            continue
        cw = canonical_work_state(runtime, task_id)
        if cw is not None:
            lane_outcomes.append({**projected, "execution_path": "CANONICAL_WORK_INGRESS", "state": cw.get("state", "UNKNOWN"), "canonical_work_receipt": str(CANONICAL_WORK_ONLY[task_id])})
            continue
        reason = NO_EXECUTION_PATH_REASON.get(task_id, "no compatible resident execution path found")
        lane_outcomes.append({**projected, "execution_path": "UNWIRED_CHILD_RUNTIME", "state": "NO_COMPATIBLE_RESIDENT_EXECUTION_PATH", "reason": reason})

    state_counts = Counter(str(row.get("state")) for row in lane_outcomes)
    stage_counts = Counter(str(row.get("resume_stage")) for row in lane_outcomes if row.get("state") not in {"COMPLETED", "ALREADY_CONSUMED"})
    common_runtime_state = next(iter(state_counts)) if len(state_counts) == 1 else None
    unwired = [row["task_id"] for row in lane_outcomes if row.get("state") == "NO_COMPATIBLE_RESIDENT_EXECUTION_PATH"]
    receipt = {
        "schema": "stegverse.global-runtime-evidence-convergence/v1",
        "state": "CONVERGENCE_VISIT_COMPLETE" if isinstance(dispatch_receipt, dict) else "CONVERGENCE_DISPATCH_INCOMPLETE",
        "goal_task_id": projection["goal_task_id"],
        "cosv": projection.get("cosv"),
        "member_count": len(lane_outcomes),
        "registered_selector_count": len(selectors),
        "selected_consumers": selectors,
        "task_specific_direct_consumer_count": len(direct_results),
        "dispatcher_returncode": completed.returncode,
        "dispatch_receipt_observed": isinstance(dispatch_receipt, dict),
        "lane_outcomes": lane_outcomes,
        "unwired_member_count": len(unwired),
        "unwired_members": unwired,
        "runtime_state_counts": dict(sorted(state_counts.items())),
        "unresolved_resume_stage_counts": dict(sorted(stage_counts.items())),
        "all_members_same_runtime_state": len(state_counts) == 1,
        "common_runtime_state": common_runtime_state,
        "cross_task_receipt_reuse_inferred": False,
        "mechanism_reuse_projection_applied": True,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_scheduler_created": False,
        "second_dispatcher_created": False,
        "second_machine_required": False,
        "authority_effect": "NONE_EXECUTION_VISIT_AND_OBSERVATION_ONLY",
    }
    atomic_json(runtime / RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute global runtime evidence convergence through existing resident consumers.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = execute(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "CONVERGENCE_VISIT_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
