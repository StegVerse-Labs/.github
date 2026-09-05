#!/usr/bin/env python3
"""Dispatch bounded resident execution requests independently.

This dispatcher is transport-free and non-authorizing. It does not mint claims,
fences, credentials, heartbeat authority, publication authority, or runtime
authority. Each request-specific consumer remains responsible for validating its
own request and invoking only its already-admitted execution path.

A failed or blocked request never prevents later independent requests from being
visited. Consumers retain their own exactly-once semantics. Callers may select an
exact subset of registered consumers; unknown selectors fail before any consumer
is invoked.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_REL = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_HIL_STATE_ROOT", "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_VAULT_AGENT_SOCKET", "STEGVERSE_ARA_MAIL_RECIPIENT",
    "STEGVERSE_ARA_MAIL_SENDER", "STEGVERSE_SV_DN1_SOURCE_ROOT",
    "STEGVERSE_SOURCE_MATERIALIZATION_ROOT", "STEGVERSE_SOURCE_PACKAGE_ROOT",
    "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT", "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT",
    "STEGVERSE_SV_DN1_INTR_STATE_ROOT", "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT", "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_INTR_ROUTE_CONFIG", "STEGVERSE_STEGOS_ROOT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT",
    "STEGVERSE_SITE_ROOT", "STEGVERSE_STEGINDEX_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_HEALER_ROOT",
    "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_EVALUATOR_INTR_PORT",
    "STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
    "STEGVERSE_SV002_OBSERVE_PORT", "STEGVERSE_RELAY_RUNTIME_BASE", "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT", "STEGVERSE_GTG_ROOT", "STEGVERSE_AE_ROOT",
    "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT", "STEGVERSE_SELF_CHAR_MODEL_ID",
    "STEGVERSE_OLLAMA_MODEL", "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT",
    "STEGVERSE_RESIDENT_SOURCE_MANIFEST", "STEGVERSE_MASTER_RECORDS_ROOT",
    "STEGVERSE_ORG_CONTROL_ROOT", "STEGVERSE_SV002_ORG_ROOT",
    "STEGVERSE_SV001_AUTONOMY_LEASE",
    "STEGVERSE_SV011_ORG_ROOT",
    "STEGVERSE_SV011_MATERIALIZED_ROOT",
    "STEGVERSE_GLM53_ENDPOINT", "STEGVERSE_GLM53_MODEL_PATH", "STEGVERSE_GLM53_RUNTIME_IDENTITY",
    "STEGVERSE_GLM53_ENERGY_KWH", "STEGVERSE_GLM53_HARDWARE_AMORTIZATION_USD",
    "STEGVERSE_GLM53_ENERGY_COST_USD", "STEGVERSE_GLM53_STORAGE_NETWORK_RUNTIME_OVERHEAD_USD",
)
CONSUMERS = (
    ("ecosystem_chat", "scripts/consume_resident_execution_request.py"),
    ("g18", "scripts/consume_g18_resident_execution_request.py"),
    ("hil", "scripts/consume_hil_resident_execution_request.py"),
    ("evaluator_intr", "scripts/consume_evaluator_intr_resident_execution_request.py"),
    ("sv002_public_observation", "scripts/consume_sv002_public_observation_request.py"),
    ("ara_graph", "scripts/consume_ara_graph_resident_execution_request.py"),
    ("cmc028_root_custody", "scripts/consume_cmc028_resident_execution_request.py"),
    ("sv_dn1", "scripts/consume_sv_dn1_resident_execution_request.py"),
    ("sv_dn1_publication", "scripts/consume_sv_dn1_publication_resident_request.py"),
    ("stegos_kv_intr_chain", "scripts/consume_stegos_kv_intr_chain_request.py"),
    ("bootstrap_v1_release_prep", "scripts/consume_bootstrap_v1_release_prep_request.py"),
    ("bootstrap_v1_intr_bundle_delivery", "scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py"),
    ("tvc_broker_validation", "scripts/consume_tvc_broker_validation_request.py"),
    ("sv002_self_characterization", "scripts/consume_sv002_self_characterization_request.py"),
    ("sv002_org_runtime_activation", "scripts/consume_sv002_org_runtime_activation_request.py"),
    ("healer_sovereign_scheduler", "scripts/consume_healer_sovereign_scheduler_request.py"),
    ("universal_governance_enforced_reference", "scripts/consume_universal_governance_enforced_reference_request.py"),
    ("cross_framework_current_basis_v04", "scripts/consume_cross_framework_current_basis_v04_request.py"),
    ("stegverse001_bounded_autonomy", "scripts/consume_stegverse001_bounded_autonomy_request.py"),
    ("one_shot_resident_stack_activation", "scripts/consume_one_shot_resident_stack_activation_request.py"),
    ("sv011_phase5_source_materialization", "scripts/consume_sv011_phase5_source_materialization_request.py"),
    ("sv011_phase5", "scripts/consume_sv011_phase5_resident_execution_request.py"),
    ("glm53_sovereign_lane", "scripts/consume_glm53_sovereign_lane_request.py"),
    ("erl_ai_economic_transparency_review", "scripts/consume_erl_ai_economic_transparency_review_request.py"),
    ("org_claim_allocator", "scripts/consume_org_claim_allocator_request.py"),
    ("canonical_work_coordination", "scripts/consume_canonical_work_coordination_bootstrap_request.py"),
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not dispatch sovereign resident requests: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def select_consumers(only_consumers: tuple[str, ...] | None) -> tuple[tuple[str, str], ...]:
    if not only_consumers:
        return CONSUMERS
    by_name = {name: rel for name, rel in CONSUMERS}
    unknown = sorted(set(only_consumers) - set(by_name))
    if unknown:
        raise RuntimeError("unknown resident consumer selector(s): " + ",".join(unknown))
    requested = set(only_consumers)
    return tuple((name, rel) for name, rel in CONSUMERS if name in requested)


def dispatch(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
    only_consumers: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    safe_env = clean_exec_env(env)
    selected = select_consumers(only_consumers)
    outcomes: list[dict[str, Any]] = []

    for name, rel in selected:
        consumer = runtime / rel
        if not consumer.is_file():
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": "CONSUMER_NOT_MATERIALIZED", "returncode": None, "result": None, "attempted": False})
            continue
        command = [sys.executable, str(consumer), "--source-root", str(source), "--runtime-root", str(runtime)]
        try:
            completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=safe_env, timeout=1200)
            result = parse_last_json(completed.stdout)
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT", "returncode": completed.returncode, "result": result, "attempted": True})
        except Exception as exc:
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": "DISPATCH_EXCEPTION", "returncode": None, "result": None, "attempted": True, "error_type": type(exc).__name__})

    missing = [row["consumer"] for row in outcomes if row["state"] == "CONSUMER_NOT_MATERIALIZED"]
    exceptions = [row["consumer"] for row in outcomes if row["state"] == "DISPATCH_EXCEPTION"]
    request_failures = [row["consumer"] for row in outcomes if row["state"] not in {"NO_REQUEST", "ALREADY_CONSUMED", "ATTEMPT_RECORDED", "COMPLETED"}]
    receipt = {
        "schema": "stegverse.resident-request-dispatch/v1",
        "state": "DISPATCH_COMPLETE" if not missing and not exceptions else "DISPATCH_INCOMPLETE",
        "source_root": str(source), "runtime_root": str(runtime),
        "registered_consumer_count": len(CONSUMERS), "consumer_count": len(selected),
        "selected_consumers": [name for name, _ in selected],
        "selection_scope": "ALL_REGISTERED" if only_consumers is None else "EXACT_SELECTOR",
        "consumers_visited": len(outcomes), "missing_consumers": missing,
        "dispatch_exceptions": exceptions, "request_failures": request_failures,
        "outcomes": outcomes, "request_failure_blocks_later_requests": False,
        "network_source_fetch_performed": False, "credential_authority": "TV/TVC",
        "github_token_required": False, "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False, "request_dispatch_grants_authority": False,
        "second_machine_required": False, "authority_effect": "NONE_DISPATCH_ONLY",
    }
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch bounded resident execution requests.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--only-consumer", action="append", default=None)
    args = parser.parse_args()
    receipt = dispatch(args.source_root, args.runtime_root, only_consumers=tuple(args.only_consumer) if args.only_consumer else None)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "DISPATCH_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
