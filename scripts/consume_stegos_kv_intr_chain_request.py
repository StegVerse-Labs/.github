#!/usr/bin/env python3
"""Consume the existing StegOS relay -> Node-KV -> DEVICE_KV_INTR chain in order.

The request is intent only. This script creates no claim, fence, credential,
scheduler, route authority, or runtime owner. Each successor is visited only
after the exact authentic terminal receipt for its parent is present locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from heartbeat_runtime.intr_subsignal_runtime import (
    default_heartbeat_runtime_root,
    recover_local_intr_subsignal,
    signal_sha256,
)

REQUEST_REL = Path("control/resident-execution-request.d/stegos-kv-intr-chain-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/stegos-kv-intr-chain-consumption.latest.json")
ENTRYPOINT = Path("scripts/refresh_and_execute_resident_task.py")
CHAIN_TASK_ID = "SHWP-STEGOS-KV-INTR-CHAIN-001"
MODE = "STEGOS_KV_INTR_CHAIN"
DEVICE_KV_TASK_ID = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
STEPS = (
    ("SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
     Path("receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json"),
     "COMPLETED", "SOVEREIGN_RELAY_LEASE_OPEN"),
    ("SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
     Path("receipts/stegos-sovereign-relay/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json"),
     "COMPLETED", "RELAY_NODE_KV_CONTINUITY_VERIFIED"),
    (DEVICE_KV_TASK_ID,
     Path("receipts/device-kv-intr/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json"),
     "OBSERVED", "DEVICE_KV_INTR_OBSERVED"),
    ("SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001",
     Path("receipts/endpoint-fanout/SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001.json"),
     "OBSERVED", "ENDPOINT_FANOUT_SOVEREIGN_RUNTIME_OBSERVED"),
)
HOSTED = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN = ("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","ACTIONS_RUNTIME_TOKEN",
             "ACTIONS_ID_TOKEN_REQUEST_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","HF_TOKEN")
NONSECRET = ("PATH","HOME","LANG","LC_ALL","SSL_CERT_FILE","SSL_CERT_DIR","XDG_STATE_HOME","XDG_CONFIG_HOME",
             "LOCALAPPDATA","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT","STEGVERSE_SOVEREIGN_NODE",
             "STEGVERSE_STEGOS_ROOT","STEGVERSE_KV_SOURCE_ROOT","STEGVERSE_KV_ROOT","STEGVERSE_RELAY_RUNTIME_BASE")

def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}

def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value

def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    if any(truthy(values.get(name)) for name in HOSTED):
        raise RuntimeError("hosted environment may not execute StegOS/KV resident chain")
    if any(truthy(values.get(name)) for name in FORBIDDEN):
        raise RuntimeError("credential-bearing environment forbidden for StegOS/KV resident chain")
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env

def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": CHAIN_TASK_ID,
        "mode": MODE,
        "entrypoint": str(ENTRYPOINT),
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise RuntimeError(f"StegOS/KV resident request {key} mismatch")
    if not str(request.get("request_id") or "").strip():
        raise RuntimeError("StegOS/KV resident request_id missing")
    if request.get("steps") != [row[0] for row in STEPS]:
        raise RuntimeError("StegOS/KV resident request step order mismatch")

def _shared_signal_valid(value: Mapping[str, Any], prefix: str, values: Mapping[str, str] | None) -> bool:
    signal_ref = value.get(f"{prefix}_shared_hb_signal_ref")
    signal_digest = value.get(f"{prefix}_shared_hb_signal_sha256")
    signal_id = value.get(f"{prefix}_carrier_signal_id")
    receipt_hash = value.get(f"{prefix}_receipt_hash")
    if not all(isinstance(v, str) and v for v in (signal_ref, signal_digest, signal_id, receipt_hash)):
        return False
    root = default_heartbeat_runtime_root(values)
    try:
        recovered = recover_local_intr_subsignal(root=root, signal_ref=signal_ref)
        if not recovered:
            return False
        signal_path = (root / signal_ref).resolve()
        signal = load_json(signal_path)
    except Exception:
        return False
    expected_receipt = receipt_hash[7:] if receipt_hash.startswith("sha256:") else receipt_hash
    return (
        signal_sha256(signal) == signal_digest
        and signal.get("signal_id") == signal_id
        and signal.get("intr", {}).get("packet_receipt_hash") == expected_receipt
        and signal.get("authority", {}).get("authority_effect") == "NONE_CARRIER_ONLY"
        and signal.get("carrier", {}).get("progression_dependency") == "OSCILLATOR_ONLY"
    )


def terminal(runtime: Path, step: tuple[str, Path, str, str], values: Mapping[str, str] | None = None) -> bool:
    task_id, rel, state, transition = step
    path = runtime / rel
    if not path.is_file():
        return False
    try:
        value = load_json(path)
    except Exception:
        return False
    if value.get("state") != state or value.get("transition_id") != transition:
        return False
    if task_id == DEVICE_KV_TASK_ID:
        return (
            value.get("hb_derived_carrier_transport_observed") is True
            and value.get("request_transported_on_hb_derived_carrier") is True
            and value.get("response_transported_on_hb_derived_carrier") is True
            and value.get("request_carrier_packet_recovery_verified") is True
            and value.get("response_carrier_packet_recovery_verified") is True
            and _shared_signal_valid(value, "request", values)
            and _shared_signal_valid(value, "response", values)
        )
    return True

def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None

def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.stegos-kv-intr-chain.resident-consumption/v1","state":"NO_REQUEST",
                "runtime_execution_attempted":False,"authority_effect":"NONE"}
    request = load_json(request_path)
    validate_request(request)
    entrypoint = runtime / ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"resident targeted execution bridge missing: {entrypoint}")
    safe = clean_env(env)
    outcomes: list[dict[str, Any]] = []
    attempted = False
    blocked = None
    for step in STEPS:
        task_id, rel, _, transition = step
        if terminal(runtime, step, safe):
            outcomes.append({"task_id":task_id,"state":"ALREADY_TERMINAL","terminal_receipt":str(rel),
                             "transition_id":transition,"execution_attempted":False})
            continue
        command = [sys.executable,str(entrypoint),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",task_id]
        completed = runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=safe,timeout=600)
        attempted = True
        result = parse_last_json(completed.stdout)
        done = terminal(runtime, step, safe)
        outcomes.append({"task_id":task_id,"state":"TERMINAL_OBSERVED" if done else "ATTEMPT_RECORDED",
                         "terminal_receipt":str(rel) if done else None,
                         "transition_id":transition if done else None,"execution_attempted":True,
                         "execution_returncode":completed.returncode,
                         "execution_result_observed":isinstance(result,dict),"execution_result":result})
        if not done:
            blocked = task_id
            break
    complete = all(terminal(runtime, step, safe) for step in STEPS)
    receipt = {
        "schema":"stegverse.stegos-kv-intr-chain.resident-consumption/v1",
        "state":"COMPLETED" if complete else "ATTEMPT_RECORDED",
        "request_id":request["request_id"],"request_sha256":stable_hash(request),
        "task_id":CHAIN_TASK_ID,"mode":MODE,"steps":outcomes,"blocked_step":blocked,
        "runtime_execution_attempted":attempted,"terminal_chain_observed":complete,
        "request_granted_authority":False,"heartbeat_grants_execution_authority":False,
        "network_source_fetch_performed":False,"github_token_required":False,
        "github_token_runtime_authority":"NONE","credential_authority":"TV/TVC",
        "second_machine_required":False,"authority_effect":"NONE_REQUEST_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST","ATTEMPT_RECORDED","COMPLETED"} else 1

if __name__ == "__main__":
    raise SystemExit(main())
