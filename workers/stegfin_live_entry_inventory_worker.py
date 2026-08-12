#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "STEGFIN-LIVE-ENTRY-003"
RECEIPT_ROOT = (ROOT / "receipts" / "stegfin-live-entry").resolve()
RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def local_stegfin_roots() -> list[Path]:
    return [
        ROOT / "workloads" / "stegfin-governance",
        Path.home() / ".stegverse" / "workloads" / "stegfin-governance",
        Path("/var/lib/stegverse/workloads/stegfin-governance"),
    ]


def find_stegfin_root() -> Path | None:
    required = (
        Path("scripts/observe_live_base_inventory.py"),
        Path("stegwallet/live_pretrade.py"),
        Path("registries/base_0x_v2_candidate_2026_07.json"),
        Path("docs/STEGFIN_MIRROR_HANDOFF.md"),
    )
    for root in local_stegfin_roots():
        try:
            resolved = root.expanduser().resolve()
        except Exception:
            continue
        if all((resolved / relative).is_file() for relative in required):
            return resolved
    return None


def child_env(stegfin_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(stegfin_root),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def verified_inventory_envelope(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    inventory = value.get("inventory")
    receipt = value.get("observation_receipt")
    if not isinstance(inventory, dict) or not isinstance(receipt, dict):
        return False
    assets = inventory.get("assets")
    return (
        inventory.get("schema") == "stegwallet.base_asset_lounge_snapshot.v1"
        and inventory.get("chain_id") == "0x2105"
        and isinstance(assets, list)
        and len(assets) >= 3
        and receipt.get("schema") == "stegwallet.live_inventory_observation_receipt.v1"
        and receipt.get("state") == "INVENTORY_N_OBSERVED"
        and receipt.get("complete_current_asset_inventory") is True
        and receipt.get("provider_capability_required") is False
        and receipt.get("github_token_required") is False
        and receipt.get("github_runtime_required") is False
        and receipt.get("wallet_contacted") is False
        and receipt.get("signed") is False
        and receipt.get("broadcast") is False
        and receipt.get("trade_authority_granted") is False
        and receipt.get("authority_effect") == "NONE_OBSERVATION_ONLY"
        and receipt.get("inventory_state_hash") == inventory.get("inventory_state_hash")
        and receipt.get("boundary_state_hash") == inventory.get("boundary_state_hash")
    )


def response(
    *,
    state: str,
    transition_id: str,
    sequence: int,
    next_transition: str | None,
    evidence_refs: list[str],
    blocker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition_id,
        "transition_sequence": sequence,
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": evidence_refs,
    }
    if blocker is not None:
        value["blocker"] = blocker
    return value


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 4
    execution = handoff.get("execution") or {}
    required_caps = set(execution.get("required_capabilities") or [])
    if not {"runtime_observation", "bounded_repository_mutation"}.issubset(required_caps):
        return 5
    if "receipts/stegfin-live-entry/**" not in set(execution.get("allowed_paths") or []):
        return 6

    stegfin_root = find_stegfin_root()
    if stegfin_root is None:
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "The validated StegFin live-entry capsule is not materialized at a canonical StegVerse-local workload path.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Materialize the released StegFin workload locally; the heartbeat will discover and execute Inventory N on the next admitted cycle.",
            "machine_observable_release_condition": "find_stegfin_root resolves the StegFin observer, live-pretrade implementation, trust registry and canonical handoff locally",
            "github_token_required": False,
            "third_party_blocker": False,
        }
        durable = {
            "schema": "stegverse.stegfin-live-entry-heartbeat-receipt/v0.1",
            "task_id": EXPECTED_TASK,
            "heartbeat_epoch": epoch,
            "claim_id": claim_id,
            "fencing_token": fence,
            "state": "BLOCKED",
            "transition_id": "STEGFIN_LOCAL_WORKLOAD_NOT_MATERIALIZED",
            "fresh_inventory_n_observed": False,
            "provider_capability_release_boundary_identified": True,
            "provider_capability_authority": "TV_TVC_VAULT_ONLY",
            "github_token_required": False,
            "github_runtime_required": False,
            "blocker": blocker,
        }
        atomic_write(RECEIPT, durable)
        json.dump(response(state="BLOCKED", transition_id="STEGFIN_LOCAL_WORKLOAD_NOT_MATERIALIZED", sequence=1, next_transition="STEGFIN_INVENTORY_N_OBSERVED", evidence_refs=[str(RECEIPT.relative_to(ROOT))], blocker=blocker), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    with tempfile.TemporaryDirectory(prefix="stegfin-inventory-") as temp_dir:
        output = Path(temp_dir) / "inventory.json"
        completed = subprocess.run(
            [sys.executable, str(stegfin_root / "scripts" / "observe_live_base_inventory.py"), "--output", str(output)],
            cwd=stegfin_root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            env=child_env(stegfin_root),
        )
        if completed.returncode != 0 or not output.is_file():
            blocker = {
                "dependency_class": "RUNTIME_OBSERVATION",
                "problem_statement": "Credential-free Base Inventory N observation did not produce a verified envelope on this heartbeat cycle.",
                "solution_required": True,
                "may_remain_blocked": False,
                "next_solution_action": "Retry the exact read-only observation on the next admitted heartbeat without widening endpoint or credential authority.",
                "machine_observable_release_condition": "observe_live_base_inventory.py exits 0 and emits a verified complete Inventory N envelope",
                "github_token_required": False,
                "third_party_blocker": False,
                "returncode": completed.returncode,
                "stderr_tail": completed.stderr[-1000:] if completed.stderr else None,
            }
            durable = {
                "schema": "stegverse.stegfin-live-entry-heartbeat-receipt/v0.1",
                "task_id": EXPECTED_TASK,
                "heartbeat_epoch": epoch,
                "claim_id": claim_id,
                "fencing_token": fence,
                "state": "RETRY",
                "transition_id": "STEGFIN_INVENTORY_N_RETRY",
                "fresh_inventory_n_observed": False,
                "provider_capability_release_boundary_identified": True,
                "provider_capability_authority": "TV_TVC_VAULT_ONLY",
                "github_token_required": False,
                "github_runtime_required": False,
                "blocker": blocker,
            }
            atomic_write(RECEIPT, durable)
            json.dump(response(state="FAILED_RETRYABLE", transition_id="STEGFIN_INVENTORY_N_RETRY", sequence=1, next_transition="STEGFIN_INVENTORY_N_OBSERVED", evidence_refs=[str(RECEIPT.relative_to(ROOT))], blocker=blocker), sys.stdout, sort_keys=True)
            sys.stdout.write("\n")
            return 0
        try:
            envelope = json.loads(output.read_text(encoding="utf-8"))
        except Exception:
            envelope = None

    if not verified_inventory_envelope(envelope):
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "The StegFin observer returned data that failed the heartbeat consumer contract.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Repair the local observer/consumer contract; do not project incomplete inventory as authoritative state.",
            "machine_observable_release_condition": "verified_inventory_envelope returns true for the locally observed Inventory N",
            "github_token_required": False,
            "third_party_blocker": False,
        }
        durable = {
            "schema": "stegverse.stegfin-live-entry-heartbeat-receipt/v0.1",
            "task_id": EXPECTED_TASK,
            "heartbeat_epoch": epoch,
            "claim_id": claim_id,
            "fencing_token": fence,
            "state": "FAILED",
            "transition_id": "STEGFIN_INVENTORY_N_CONTRACT_FAILED",
            "fresh_inventory_n_observed": False,
            "provider_capability_release_boundary_identified": True,
            "provider_capability_authority": "TV_TVC_VAULT_ONLY",
            "github_token_required": False,
            "github_runtime_required": False,
            "blocker": blocker,
        }
        atomic_write(RECEIPT, durable)
        json.dump(response(state="FAILED_TERMINAL", transition_id="STEGFIN_INVENTORY_N_CONTRACT_FAILED", sequence=1, next_transition=None, evidence_refs=[str(RECEIPT.relative_to(ROOT))], blocker=blocker), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    observation = envelope["observation_receipt"]
    inventory = envelope["inventory"]
    durable = {
        "schema": "stegverse.stegfin-live-entry-heartbeat-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "state": "ACTIVE",
        "transition_id": "STEGFIN_INVENTORY_N_OBSERVED",
        "stegfin_runtime_root_recorded": False,
        "fresh_inventory_n_observed": True,
        "inventory_state_hash": inventory.get("inventory_state_hash"),
        "boundary_state_hash": inventory.get("boundary_state_hash"),
        "inventory_snapshot_id": inventory.get("snapshot_id"),
        "observed_at_utc": inventory.get("observed_at_utc"),
        "evidence_expiry_utc": inventory.get("evidence_expiry_utc"),
        "asset_count": observation.get("asset_count"),
        "provider_capability_required_for_inventory": False,
        "provider_capability_release_boundary_identified": True,
        "provider_capability_authority": "TV_TVC_VAULT_ONLY",
        "provider_capability_delivery_required_next": "INHERITED_FILE_DESCRIPTOR",
        "github_token_required": False,
        "github_runtime_required": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
        "trade_authority_granted": False,
        "next_authorized_action": "Consume only the canonical TV/TVC/vault non-exporting capability release, then enter the released StegFin carrier/native capsule path. Heartbeat must not acquire or transport the provider secret.",
    }
    atomic_write(RECEIPT, durable)
    json.dump(response(state="ACTIVE", transition_id="STEGFIN_INVENTORY_N_OBSERVED", sequence=2, next_transition="TV_TVC_PROVIDER_CAPABILITY_RELEASE", evidence_refs=[str(RECEIPT.relative_to(ROOT))]), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
