#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023"
PROFILE_ID = "runtime-node:vacp-sovereign-provider-realignment-023"
DISPATCHER_REL = Path("scripts/dispatch_resident_execution_requests.py")
OUTPUT_REL = Path("receipts/sovereign-host/vacc-profiled-resident-execution.latest.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
PROBE_MESSAGE = "What evidence is generally needed to establish service connection for a VA disability claim?"


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required: {path}")
    return value


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require_resident_env() -> None:
    active = [name for name in HOSTED_ENV if truthy(os.environ.get(name))]
    if active:
        raise RuntimeError("hosted environment may not execute VACC sovereign runtime: " + ",".join(sorted(active)))


def find_live_runtime(runtime: Path) -> tuple[Path, dict[str, Any]] | None:
    candidates = [runtime / "receipts/ecosystem-chat-sovereign-inference/va_conversational_runtime_process.json"]
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
        if (
            state.get("schema") == "stegverse.va-conversational-runtime-process/v1"
            and state.get("state") == "LIVE_VERIFIED"
            and state.get("credential_authority") == "TV/TVC"
            and state.get("credential_requirement") == "NONE"
            and state.get("github_token_required") is False
            and isinstance(state.get("endpoint"), str)
        ):
            return path, state
    return None


def advance_parent_runtime(source: Path, runtime: Path) -> dict[str, Any]:
    dispatcher = runtime / DISPATCHER_REL
    if not dispatcher.is_file():
        dispatcher = source / DISPATCHER_REL
    if not dispatcher.is_file():
        return {"state":"VACC_PARENT_DISPATCHER_NOT_MATERIALIZED"}
    env = {k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN"}}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    completed = subprocess.run(
        [sys.executable, str(dispatcher), "--source-root", str(source), "--runtime-root", str(runtime), "--only-consumer", "ecosystem_chat"],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        timeout=7200,
        env=env,
    )
    return {"state":"PARENT_RUNTIME_VISITED","returncode":completed.returncode,"stdout_tail":completed.stdout[-1200:],"stderr_tail":completed.stderr[-1200:]}


def response_hash_valid(response: dict[str, Any]) -> bool:
    expected = response.get("response_hash")
    if not isinstance(expected, str):
        return False
    candidate = dict(response)
    candidate.pop("response_hash", None)
    return expected == stable_hash(candidate)


def response_verified(response: dict[str, Any] | None) -> bool:
    return bool(
        isinstance(response, dict)
        and response.get("schema") == "stegverse.va_claims.runtime/v1"
        and isinstance(response.get("response"), str) and response.get("response").strip()
        and response.get("provider_usage_custody_recorded") is True
        and response.get("provider_usage_reconstruction_pass") is True
        and response.get("transition_reconstruction_pass") is True
        and response.get("same_execution") is True
        and response.get("github_token_required") is False
        and response.get("credential_requirement") == "NONE"
        and response.get("authority_effect") is False
        and response.get("activation_effect") is False
        and response_hash_valid(response)
    )


def post_probe(endpoint: str) -> dict[str, Any]:
    payload = {
        "message": PROBE_MESSAGE,
        "session_id": "vacc-profiled-runtime-proof",
        "route_scope": "VA_CLAIMS_CHAT",
        "requested_capability": "COORDINATED_VA_RESOURCES_LLM",
        "source_policy": "ADMITTED_OFFICIAL_VA_ONLY",
        "private_document_context": False,
        "filing_requested": False,
        "authority_required": True,
        "receipt_required": True,
        "transition_identity": {
            "transition_id": TASK_ID + ":PROFILED_RUNTIME_EXECUTION",
            "event_id": TASK_ID + ":PROFILED_RUNTIME_MEASUREMENT",
            "runtime_node_profile_id": PROFILE_ID,
        },
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/api/va-claims/v1/chat",
        data=raw,
        method="POST",
        headers={"content-type":"application/json","accept":"application/json","user-agent":"StegVerse-VACC-Profiled-Resident/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as result:
            value = json.loads(result.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return {"state":"VACC_PROFILED_REQUEST_FAILED","detail":f"{type(exc).__name__}:{exc}"}
    return value if isinstance(value, dict) else {"state":"VACC_PROFILED_REQUEST_NON_OBJECT"}


def prior_verified(path: Path, state_path: Path, state: dict[str, Any]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        receipt = load_json(path)
    except Exception:
        return None
    response = receipt.get("response")
    if (
        receipt.get("schema") == "stegverse.vacc-profiled-resident-execution/v1"
        and receipt.get("state") == "VACC_PROFILED_RESIDENT_REQUEST_EXECUTED"
        and receipt.get("task_id") == TASK_ID
        and receipt.get("runtime_node_profile_id") == PROFILE_ID
        and receipt.get("runtime_state_ref") == str(state_path)
        and receipt.get("endpoint") == state.get("endpoint")
        and response_verified(response if isinstance(response, dict) else None)
    ):
        return receipt
    return None


def execute(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    require_resident_env()
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    live = find_live_runtime(runtime)
    parent_visit = None
    if live is None:
        parent_visit = advance_parent_runtime(source, runtime)
        live = find_live_runtime(runtime)
    if live is None:
        return {
            "schema":"stegverse.vacc-profiled-resident-execution/v1",
            "state":"VACC_PROFILED_PARENT_RUNTIME_PENDING",
            "task_id":TASK_ID,
            "runtime_node_profile_id":PROFILE_ID,
            "parent_visit":parent_visit,
            "github_token_required":False,
            "credential_authority":"TV/TVC",
        }
    state_path, state = live
    output = runtime / OUTPUT_REL
    prior = prior_verified(output, state_path, state)
    if prior is not None:
        return {**prior, "reused":True}
    response = post_probe(str(state["endpoint"]))
    if not response_verified(response):
        return {
            "schema":"stegverse.vacc-profiled-resident-execution/v1",
            "state":"VACC_PROFILED_LIVE_RUNTIME_REQUEST_NOT_VERIFIED",
            "task_id":TASK_ID,
            "runtime_node_profile_id":PROFILE_ID,
            "runtime_state_ref":str(state_path),
            "endpoint":state.get("endpoint"),
            "response":response,
            "github_token_required":False,
            "credential_authority":"TV/TVC",
        }
    receipt = {
        "schema":"stegverse.vacc-profiled-resident-execution/v1",
        "state":"VACC_PROFILED_RESIDENT_REQUEST_EXECUTED",
        "task_id":TASK_ID,
        "runtime_node_profile_id":PROFILE_ID,
        "runtime_state_ref":str(state_path),
        "endpoint":state["endpoint"],
        "probe_message_sha256":hashlib.sha256(PROBE_MESSAGE.encode("utf-8")).hexdigest(),
        "response":response,
        "provider_usage_custody_recorded":True,
        "provider_usage_reconstruction_pass":True,
        "transition_reconstruction_pass":True,
        "same_execution":True,
        "github_token_required":False,
        "credential_authority":"TV/TVC",
        "credential_requirement":"NONE",
        "activation_effect":False,
        "authority_effect":"NONE_EVIDENCE_ONLY",
        "reused":False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = execute(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
