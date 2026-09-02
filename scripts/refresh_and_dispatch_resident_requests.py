#!/usr/bin/env python3
"""Refresh already-local sovereign worker source, then dispatch one bounded request once.

This is a portable, transport-free execution bridge for an already-existing sovereign
resident. It composes the existing local source refresh and generic resident-request
dispatcher, but selects exactly one explicitly admitted consumer. The historical default
remains the cross-framework current-basis v0.4 consumer; HIL and SV-DN-1 may be selected
explicitly without visiting unrelated work. Explicit SV002 self-characterization and public-observation selectors are also admitted without changing the historical default. It creates no scheduler, heartbeat, claim,
fence, credential path, or runtime authority.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_REL = Path("scripts/dispatch_resident_execution_requests.py")
DISPATCH_RECEIPT_REL = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
RECEIPT_REL = Path("receipts/sovereign-host/resident-refresh-dispatch.latest.json")
SV_DN1_BROWSER_LOCATOR_REL = Path("control/sv-dn1-browser-observation-locator.json")
TARGET_CONSUMER = "cross_framework_current_basis_v04"
ALLOWED_TARGET_CONSUMERS = (TARGET_CONSUMER, "hil", "sv_dn1", "sv_dn1_publication", "stegos_kv_intr_chain", "sv002_self_characterization", "sv002_public_observation", "sv002_org_runtime_activation", "healer_sovereign_scheduler", "universal_governance_enforced_reference")
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "HF_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
)
NONSECRET_FORWARD = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT", "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT", "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_HIL_STATE_ROOT",
    "STEGVERSE_HIL_RECEIVER_PORT", "STEGVERSE_VAULT_AGENT_SOCKET",
    "STEGVERSE_ARA_MAIL_RECIPIENT", "STEGVERSE_ARA_MAIL_SENDER",
    "STEGVERSE_SV_DN1_SOURCE_ROOT", "STEGVERSE_SOURCE_MATERIALIZATION_ROOT",
    "STEGVERSE_SOURCE_PACKAGE_ROOT", "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT", "STEGVERSE_SV_DN1_INTR_STATE_ROOT",
    "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT",
    "STEGVERSE_SDK_SOURCE_ROOT", "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_STEGOS_ROOT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT", "STEGVERSE_SITE_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_EVALUATOR_INTR_PORT",
    "STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
    "STEGVERSE_SV002_OBSERVE_PORT", "STEGVERSE_RELAY_RUNTIME_BASE",
    "STEGVERSE_TT_ROOT", "STEGVERSE_RTG_ROOT", "STEGVERSE_GTG_ROOT",
    "STEGVERSE_AE_ROOT", "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT",
    "STEGVERSE_SELF_CHAR_MODEL_ID", "STEGVERSE_OLLAMA_MODEL",
    "STEGVERSE_HEALER_ROOT", "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_RESIDENT_SOURCE_MANIFEST", "STEGVERSE_MASTER_RECORDS_ROOT",
    "STEGVERSE_ORG_CONTROL_ROOT", "STEGVERSE_SV002_ORG_ROOT",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def default_runtime_root(env: Mapping[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not refresh+dispatch sovereign resident requests: " + ",".join(sorted(hosted)))
    credentials = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(values.get(name))]
    if credentials:
        raise RuntimeError("credential-bearing environment forbidden for portable resident dispatch: " + ",".join(sorted(credentials)))
    env = {name: values[name] for name in NONSECRET_FORWARD if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    temp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def persist_sv_dn1_browser_locator(runtime: Path, safe_env: Mapping[str, str], target_consumer: str) -> bool:
    if target_consumer != "sv_dn1":
        return False
    raw = str(safe_env.get("STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE") or "").strip()
    if not raw:
        return False
    bundle = Path(raw).expanduser().resolve()
    if not bundle.is_file():
        raise RuntimeError(f"SV-DN-1 browser observation bundle missing: {bundle}")
    atomic_json(runtime / SV_DN1_BROWSER_LOCATOR_REL, {
        "schema": "stegverse.sv-dn1.browser-observation-locator/v1",
        "state": "AVAILABLE_LOCAL_ONLY",
        "bundle_path": str(bundle),
        "credential_material_included": False,
        "network_fetch_performed": False,
        "authority_effect": "NONE_LOCAL_EVIDENCE_LOCATOR_ONLY",
    })
    return True


def refresh_and_dispatch(
    source_root: Path,
    runtime_root: Path,
    *,
    target_consumer: str = TARGET_CONSUMER,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if target_consumer not in ALLOWED_TARGET_CONSUMERS:
        raise RuntimeError("unsupported portable resident consumer: " + target_consumer)
    safe = clean_exec_env(env)

    refresh_receipt = refresh(source, runtime)
    if refresh_receipt.get("network_fetch_performed") is not False:
        raise RuntimeError("resident source refresh unexpectedly used network transport")
    if refresh_receipt.get("credential_read_or_acquired") is not False:
        raise RuntimeError("resident source refresh unexpectedly acquired a credential")
    if refresh_receipt.get("mutable_runtime_state_preserved") is not True:
        raise RuntimeError("resident source refresh did not preserve mutable runtime state")

    browser_locator_persisted = persist_sv_dn1_browser_locator(runtime, safe, target_consumer)

    dispatcher = runtime / DISPATCHER_REL
    if not dispatcher.is_file():
        raise RuntimeError("resident request dispatcher not materialized after refresh")

    completed = runner(
        [sys.executable, str(dispatcher), "--source-root", str(source), "--runtime-root", str(runtime), "--only-consumer", target_consumer],
        cwd=runtime, capture_output=True, text=True, check=False, env=safe, timeout=3600,
    )
    dispatch_path = runtime / DISPATCH_RECEIPT_REL
    dispatch_receipt = load_json(dispatch_path) if dispatch_path.is_file() else None
    dispatch_observed = isinstance(dispatch_receipt, dict)
    exact_selection = (
        dispatch_observed
        and dispatch_receipt.get("selection_scope") == "EXACT_SELECTOR"
        and dispatch_receipt.get("selected_consumers") == [target_consumer]
        and dispatch_receipt.get("consumer_count") == 1
    )
    state = "REFRESH_AND_DISPATCH_COMPLETE" if completed.returncode == 0 and dispatch_observed and exact_selection and dispatch_receipt.get("state") == "DISPATCH_COMPLETE" else "REFRESH_COMPLETE_DISPATCH_INCOMPLETE"

    receipt = {
        "schema": "stegverse.resident-refresh-dispatch/v1", "state": state,
        "source_root": str(source), "runtime_root": str(runtime), "refresh_receipt": refresh_receipt,
        "dispatcher_ref": str(DISPATCHER_REL), "target_consumer": target_consumer,
        "sv_dn1_browser_locator_persisted": browser_locator_persisted,
        "exact_consumer_selection_observed": bool(exact_selection), "unrelated_consumers_dispatched": False,
        "dispatch_returncode": completed.returncode, "dispatch_receipt_observed": dispatch_observed,
        "dispatch_receipt": dispatch_receipt, "runtime_execution_possible_in_target_consumer": True,
        "bridge_grants_execution_authority": False, "bridge_mints_claim_or_fence": False,
        "source_refresh_is_runtime_execution": False, "network_source_fetch_performed": False,
        "credential_read_or_acquired": False, "github_token_required": False,
        "github_token_runtime_authority": "NONE", "credential_authority": "TV/TVC",
        "third_party_scheduler_required": False, "systemd_required": False,
        "second_machine_required": False, "authority_effect": "NONE_REFRESH_AND_TARGETED_DISPATCH_BRIDGE_ONLY",
    }
    atomic_json(runtime / RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh already-local sovereign worker source and dispatch exactly one bounded resident request once.")
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runtime-root", type=Path, default=default_runtime_root())
    parser.add_argument("--only-consumer", choices=ALLOWED_TARGET_CONSUMERS, default=TARGET_CONSUMER)
    args = parser.parse_args()
    receipt = refresh_and_dispatch(args.source_root, args.runtime_root, target_consumer=args.only_consumer)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "REFRESH_AND_DISPATCH_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
