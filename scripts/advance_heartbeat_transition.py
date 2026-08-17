#!/usr/bin/env python3
"""Advance the canonical heartbeat by one bounded state transition.

This producer exists for the state-transition continuity model.  It does not
require an always-on external host and it does not grant physical-carrier,
worker, credential, route, wallet, or custody authority.  The canonical legacy
HB29 file remains immutable; v12 writes the successor into the separated carrier
state.  The independently admitted WorkerCoordinator observes that successor on
its current or next execution opportunity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = Path("management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json")
LEGACY_REL = Path("control/heartbeat-state.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CONTROL_PLANE_REL = Path("control/worker-control-plane-coordination.json")
CUTOVER_REL = Path("receipts/heartbeat-schema-cutover/HB29.json")
DEFAULT_RECEIPT_REL = Path("receipts/heartbeat-transition-continuity/latest.json")
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
SAFE_CHILD_ENV = {
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "PATH",
    "PYTHONPATH",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "XDG_CONFIG_HOME",
    "XDG_STATE_HOME",
    "LOCALAPPDATA",
    "UID",
    "STEGVERSE_HEARTBEAT_ROOT",
}


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def active_leases(control_plane: dict[str, Any]) -> list[dict[str, Any]]:
    coordination = control_plane.get("worker_coordination") or {}
    rows = coordination.get("active_leases") or []
    return [row for row in rows if isinstance(row, dict)]


def no_duplicate_claim_or_fence(control_plane: dict[str, Any]) -> bool:
    rows = active_leases(control_plane)
    claims = [row.get("claim_id") for row in rows if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in rows if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in rows if row.get("worker_instance_id")]
    return (
        len(claims) == len(set(claims))
        and len(fences) == len(set(fences))
        and len(instances) == len(set(instances))
    )


def clean_child_env(env: dict[str, str] | None = None) -> dict[str, str]:
    values = os.environ if env is None else env
    return {name: values[name] for name in SAFE_CHILD_ENV if values.get(name)}


def advance(root: Path, receipt_path: Path, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    receipt_path = receipt_path.expanduser().resolve()
    contract_path = root / CONTRACT_REL
    legacy_path = root / LEGACY_REL
    carrier_path = root / CARRIER_REL
    control_plane_path = root / CONTROL_PLANE_REL
    cutover_path = root / CUTOVER_REL
    runner_path = root / "scripts" / "run_heartbeat_runtime.py"

    receipt: dict[str, Any] = {
        "schema": "stegverse.heartbeat-state-transition-receipt/v1",
        "contract_ref": str(CONTRACT_REL),
        "legacy_state_ref": str(LEGACY_REL),
        "carrier_state_ref": str(CARRIER_REL),
        "worker_control_plane_ref": str(CONTROL_PLANE_REL),
        "continuity_model": "STATE_TRANSITION_CONTINUITY",
        "sole_permitted_user_physical_carrier": "CURRENT_USER_IPHONE",
        "transition_compute_grants_physical_carrier_identity": False,
        "always_on_external_host_required": False,
        "wall_clock_continuous_process_required": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_forwarded": False,
        "hosted_environment_rejected": False,
        "state": "FAIL_CLOSED",
        "reason": None,
    }

    if hosted_environment(env):
        receipt["hosted_environment_rejected"] = True
        receipt["reason"] = "HOSTED_ENVIRONMENT_CANNOT_PRODUCE_SOVEREIGN_TRANSITION"
        atomic_write(receipt_path, receipt)
        return receipt

    required = [contract_path, legacy_path, runner_path, root / "heartbeat_runtime" / "engine_v12.py"]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        receipt["reason"] = "CANONICAL_TRANSITION_SOURCE_INCOMPLETE"
        receipt["missing_source"] = missing
        atomic_write(receipt_path, receipt)
        return receipt

    contract = load_json(contract_path)
    if (
        contract.get("continuity_model") != "STATE_TRANSITION_CONTINUITY"
        or contract.get("legacy_epoch") != 29
        or contract.get("first_successor_epoch") != 30
        or contract.get("always_on_external_host_required") is not False
    ):
        receipt["reason"] = "STATE_TRANSITION_CONTRACT_INVALID"
        atomic_write(receipt_path, receipt)
        return receipt

    legacy_before = legacy_path.read_bytes()
    legacy = json.loads(legacy_before.decode("utf-8"))
    if int(legacy.get("epoch", -1)) != 29:
        receipt["reason"] = "LEGACY_HB29_SOURCE_INVALID"
        atomic_write(receipt_path, receipt)
        return receipt

    before_epoch = 29
    before_generation = int(legacy.get("generation", 29))
    if carrier_path.is_file():
        before = load_json(carrier_path)
        before_epoch = int(before.get("epoch", -1))
        before_generation = int(before.get("generation", -1))
        if before_epoch < 30:
            receipt["reason"] = "EXISTING_CARRIER_STATE_BELOW_HB30"
            atomic_write(receipt_path, receipt)
            return receipt

    command = [
        sys.executable,
        str(runner_path),
        "--root",
        str(root),
        "--cycles",
        "1",
        "--interval-ms",
        "0",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        env=clean_child_env(env),
    )
    receipt["transition_command"] = command
    receipt["transition_returncode"] = completed.returncode
    if completed.returncode != 0:
        receipt["reason"] = "CARRIER_TRANSITION_EXECUTION_FAILED"
        receipt["stderr_tail"] = completed.stderr[-2000:]
        atomic_write(receipt_path, receipt)
        return receipt

    if not carrier_path.is_file() or not control_plane_path.is_file():
        receipt["reason"] = "CARRIER_TRANSITION_OUTPUT_INCOMPLETE"
        atomic_write(receipt_path, receipt)
        return receipt

    after = load_json(carrier_path)
    control_plane = load_json(control_plane_path)
    legacy_after = legacy_path.read_bytes()
    after_epoch = int(after.get("epoch", -1))
    after_generation = int(after.get("generation", -1))
    expected_min_epoch = 30 if before_epoch == 29 else before_epoch + 1
    legacy_unchanged = legacy_after == legacy_before
    no_duplicates = no_duplicate_claim_or_fence(control_plane)
    cutover_bound = cutover_path.is_file() if before_epoch == 29 else True

    predicates = {
        "legacy_hb29_unchanged": legacy_unchanged and sha256_bytes(legacy_after) == sha256_bytes(legacy_before),
        "carrier_epoch_at_least_30": after_epoch >= expected_min_epoch,
        "carrier_generation_non_regressing": after_generation >= before_generation,
        "worker_control_plane_observed": control_plane.get("schema") == "stegverse.worker-control-plane-coordination/v1",
        "no_duplicate_claim_or_fence": no_duplicates,
        "state_reconstruction_pass": legacy_unchanged and cutover_bound and after_epoch >= expected_min_epoch,
    }
    receipt.update({
        "legacy_state_sha256": sha256_bytes(legacy_before),
        "carrier_epoch_before": before_epoch,
        "carrier_generation_before": before_generation,
        "carrier_epoch_after": after_epoch,
        "carrier_generation_after": after_generation,
        "cutover_receipt_observed": cutover_bound,
        "predicates": predicates,
        "all_carrier_transition_predicates_pass": all(predicates.values()),
    })
    if all(predicates.values()):
        receipt["state"] = "CARRIER_TRANSITION_COMPLETE"
        receipt["reason"] = "HB29_TO_V12_SUCCESSOR_TRANSITION_VERIFIED" if before_epoch == 29 else "V12_SUCCESSOR_TRANSITION_VERIFIED"
    else:
        receipt["state"] = "REVIEW_REQUIRED"
        receipt["reason"] = "CARRIER_TRANSITION_PREDICATES_INCOMPLETE"

    atomic_write(receipt_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt-path", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    receipt_path = (args.receipt_path or (root / DEFAULT_RECEIPT_REL)).expanduser().resolve()
    result = advance(root, receipt_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") == "CARRIER_TRANSITION_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
