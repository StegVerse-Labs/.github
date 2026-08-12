#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "STEGFIN-LIVE-PRETRADE-005"
UPSTREAM_TASK = "STEGFIN-LIVE-ENTRY-003"
UPSTREAM_RECEIPT = (ROOT / "receipts" / "stegfin-live-entry" / f"{UPSTREAM_TASK}.json").resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "stegfin-live-pretrade").resolve()
RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def inventory_is_fresh(inventory: dict[str, Any], *, now: datetime | None = None) -> bool:
    if (
        inventory.get("task_id") != UPSTREAM_TASK
        or inventory.get("transition_id") != "STEGFIN_INVENTORY_N_OBSERVED"
        or inventory.get("fresh_inventory_n_observed") is not True
        or inventory.get("github_token_required") is not False
    ):
        return False
    observed = parse_utc(inventory.get("observed_at_utc"))
    expiry = parse_utc(inventory.get("evidence_expiry_utc"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return observed is not None and expiry is not None and observed <= current < expiry


def candidate_roots(explicit_env: str, name: str) -> list[Path]:
    values: list[Path] = []
    explicit = os.environ.get(explicit_env)
    if explicit:
        values.append(Path(explicit))
    values.extend([
        ROOT / "workloads" / name,
        Path.home() / ".stegverse" / "workloads" / name,
        Path("/var/lib/stegverse/workloads") / name,
        Path.home() / ".stegverse" / "source" / name,
        Path("/var/lib/stegverse/source") / name,
    ])
    unique: list[Path] = []
    seen: set[str] = set()
    for item in values:
        try:
            key = str(item.expanduser().resolve())
        except Exception:
            key = str(item)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def find_root(explicit_env: str, name: str, required: tuple[str, ...]) -> Path | None:
    for candidate in candidate_roots(explicit_env, name):
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        if all((root / item).is_file() for item in required):
            return root
    return None


def minimal_env(*roots: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": os.pathsep.join(str(root) for root in roots),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=timeout, env=env)


def response(*, state: str, transition_id: str, sequence: int, next_transition: str | None, evidence_refs: list[str], blocker: dict[str, Any] | None = None) -> dict[str, Any]:
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


def emit_blocked(epoch: int, claim_id: str, fence: int, transition: str, dependency_class: str, problem: str, release: str, next_action: str) -> int:
    blocker = {
        "dependency_class": dependency_class,
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": next_action,
        "machine_observable_release_condition": release,
        "github_token_required": False,
        "third_party_blocker": False,
    }
    durable = {
        "schema": "stegverse.stegfin-live-pretrade-heartbeat-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "state": "BLOCKED",
        "transition_id": transition,
        "credential_authority": "TV/TVC",
        "provider_capability_authority": "TV_TVC_VAULT_ONLY",
        "github_token_required": False,
        "github_runtime_required": False,
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
        "blocker": blocker,
    }
    atomic_write(RECEIPT, durable)
    json.dump(response(state="BLOCKED", transition_id=transition, sequence=1, next_transition="STEGFIN_PRETRADE_WALLET_HANDOFF_READY", evidence_refs=[str(RECEIPT.relative_to(ROOT))], blocker=blocker), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def protected_provider_capability(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    return stat.S_IMODE(path.stat().st_mode) & 0o077 == 0


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def checked(step: str, completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "")[-1400:]
        raise RuntimeError(f"{step} failed rc={completed.returncode}: {tail}")


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
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int) or fence < 1:
        return 4
    if "stegfin_external_pretrade_preparation" not in set((handoff.get("execution") or {}).get("required_capabilities") or []):
        return 5

    if not UPSTREAM_RECEIPT.is_file():
        return emit_blocked(epoch, claim_id, fence, "STEGFIN_INVENTORY_N_NOT_PRESENT", "UPSTREAM_TASK", "Fresh Inventory N predecessor receipt is absent.", "receipts/stegfin-live-entry/STEGFIN-LIVE-ENTRY-003.json exists with transition_id STEGFIN_INVENTORY_N_OBSERVED and unexpired evidence", "Allow the existing STEGFIN-LIVE-ENTRY-003 machine worker to complete; do not recreate Inventory N here.")
    try:
        inventory = load(UPSTREAM_RECEIPT)
    except Exception:
        inventory = {}
    if not inventory_is_fresh(inventory):
        return emit_blocked(epoch, claim_id, fence, "STEGFIN_INVENTORY_N_NOT_FRESH", "UPSTREAM_TASK", "Inventory N predecessor receipt is absent, malformed, expired, future-dated, or not an authoritative no-token observation.", "upstream receipt validates as complete Inventory N and observed_at_utc <= now < evidence_expiry_utc", "Retry only the canonical Inventory-N worker under its existing claim/authority.")

    stegfin = find_root("STEGVERSE_STEGFIN_SOURCE_ROOT", "stegfin-governance", (
        "scripts/build_sovereign_validation_trade_request.py", "scripts/build_tv_tvc_registry_approval.py", "scripts/build_sovereign_live_pretrade_e1.py",
        "scripts/run_tv_tvc_sovereign_pretrade.py", "scripts/run_governed_pretrade.py", "registries/base_0x_v2_candidate_2026_07.json", "docs/STEGFIN_MIRROR_HANDOFF.md",
    ))
    tv = find_root("STEGVERSE_TV_SOURCE_ROOT", "TV", (
        "roles_templates/stegwallet_trading_runtime_policy.json", "policies/stegwallet_base_0x_quote_capability_policy.json", "docs/STEGWALLET_TRADING_POLICY_MIRROR_HANDOFF.md",
    ))
    tvc = find_root("STEGVERSE_TVC_SOURCE_ROOT", "TVC", (
        "scripts/tvc_stegwallet_trading_gate_cli.py", "scripts/tvc_resolve_provider_capability.py", "scripts/tvc_issue_stegwallet_quote_lease.py", "docs/PROVIDER_CAPABILITY_RESOLUTION_MIRROR_HANDOFF.md",
    ))
    if stegfin is None or tv is None or tvc is None:
        return emit_blocked(epoch, claim_id, fence, "STEGFIN_TV_TVC_LOCAL_SOURCE_NOT_PRESENT", "INTERNAL_CAPABILITY", "One or more released local StegFin/TV/TVC trees are not materialized on the sovereign carrier.", "find_root resolves all three released local trees with the required canonical surfaces", "Materialize the already-released StegFin/TV/TVC trees through the existing sovereign workload mechanism; no GitHub token or hosted checkout is authorized.")

    provider_file = stegfin / "runtime-secrets" / "provider_0x"
    if not protected_provider_capability(provider_file):
        return emit_blocked(epoch, claim_id, fence, "TV_TVC_PROVIDER_CAPABILITY_NOT_READY", "TV_TVC_CAPABILITY", "The TV/TVC-managed non-exportable 0x provider capability is absent or its local file protection is invalid.", "runtime-secrets/provider_0x is a regular non-symlink file with no group/other permission bits", "TV/TVC and the existing vault boundary materialize/repair the protected provider capability; do not pass a credential value through heartbeat environment, argv, JSON, repository state or GitHub secrets.")

    env = minimal_env(stegfin, tv, tvc)
    runtime_parent = stegfin / "runtime" / "heartbeat-pretrade"
    runtime_parent.mkdir(parents=True, exist_ok=True)
    pretrade_output_rel = f"reports/live_pretrade/heartbeat-{epoch}-G{fence}"
    pretrade_output = stegfin / pretrade_output_rel

    try:
        with tempfile.TemporaryDirectory(prefix="input-", dir=runtime_parent) as temporary:
            runtime = Path(temporary)
            trade_request = runtime / "trade-request.json"
            tvc_gate = runtime / "tvc-trading-gate.json"
            registry_approval = runtime / "registry-approval.json"
            route_request = runtime / "provider-route-request.json"
            route_receipt = runtime / "provider-route-receipt.json"
            quote_policy = runtime / "tv-quote-policy.json"
            lease_request = runtime / "quote-lease-request.json"
            quote_lease = runtime / "tvc-quote-lease.json"
            relationship = runtime / "relationship-standing.json"
            e1 = runtime / "carrier-e1.json"
            carrier_receipt = runtime / "carrier-binding-receipt.json"

            shutil.copyfile(tv / "policies" / "stegwallet_base_0x_quote_capability_policy.json", quote_policy)
            os.chmod(quote_policy, 0o600)

            completed = run([sys.executable, str(stegfin / "scripts" / "build_sovereign_validation_trade_request.py"), "--inventory-receipt", str(UPSTREAM_RECEIPT), "--claim-id", claim_id, "--fence", str(fence), "--output", str(trade_request)], cwd=stegfin, env=env)
            checked("trade request", completed)
            completed = run([sys.executable, str(tvc / "scripts" / "tvc_stegwallet_trading_gate_cli.py"), "--tv-policy", str(tv / "roles_templates" / "stegwallet_trading_runtime_policy.json"), "--trade-request", str(trade_request), "--output", str(tvc_gate)], cwd=tvc, env=env)
            checked("TVC trading preparation gate", completed)
            completed = run([sys.executable, str(stegfin / "scripts" / "build_tv_tvc_registry_approval.py"), "--registry", str(stegfin / "registries" / "base_0x_v2_candidate_2026_07.json"), "--tv-policy", str(tv / "roles_templates" / "stegwallet_trading_runtime_policy.json"), "--tvc-gate", str(tvc_gate), "--inventory-receipt", str(UPSTREAM_RECEIPT), "--claim-id", claim_id, "--fence", str(fence), "--output", str(registry_approval)], cwd=stegfin, env=env)
            checked("TV/TVC registry approval", completed)

            write_json(route_request, {
                "schema_version": "stegverse.tvc.provider-capability-request.v1", "request_id": f"stegfin-base-quote:{claim_id}:G{fence}", "capability": "base.quote.0x", "consumer": "StegVerse-Labs/stegfin-governance",
                "provider_inventory": [{"provider_id": "zeroex-base-primary", "provider_class": "zeroex_v2", "model_class": None, "capabilities": ["base.quote.0x"], "available": True, "priority": 10, "route_ref": "https://api.0x.org/swap/allowance-holder/quote"}],
                "secret_material_present": False, "github_token_required": False,
            })
            completed = run([sys.executable, str(tvc / "scripts" / "tvc_resolve_provider_capability.py"), "--request", str(route_request), "--output", str(route_receipt)], cwd=tvc, env=env)
            checked("TVC provider capability resolution", completed)

            now = datetime.now(timezone.utc).replace(microsecond=0)
            write_json(lease_request, {"trade_request": load(trade_request), "request_nonce": f"{claim_id}:G{fence}:HB{epoch}", "requested_at_utc": now.isoformat().replace("+00:00", "Z"), "expiry_utc": (now + timedelta(seconds=240)).isoformat().replace("+00:00", "Z")})
            completed = run([sys.executable, str(tvc / "scripts" / "tvc_issue_stegwallet_quote_lease.py"), "--policy", str(quote_policy), "--request", str(lease_request), "--out", str(quote_lease)], cwd=tvc, env=env)
            checked("TVC quote lease", completed)

            completed = run([sys.executable, str(stegfin / "scripts" / "build_sovereign_live_pretrade_e1.py"), "--inventory-receipt", str(UPSTREAM_RECEIPT), "--tv-quote-policy", str(quote_policy), "--tvc-quote-lease", str(quote_lease), "--trade-request", str(trade_request), "--trust-registry", str(stegfin / "registries" / "base_0x_v2_candidate_2026_07.json"), "--registry-approval", str(registry_approval), "--provider-route-receipt", str(route_receipt), "--claim-id", claim_id, "--fence", str(fence), "--relationship-receipt", str(relationship), "--output", str(e1), "--pretrade-output", pretrade_output_rel], cwd=stegfin, env=env)
            checked("sovereign E1", completed)

            completed = run([sys.executable, str(stegfin / "scripts" / "run_tv_tvc_sovereign_pretrade.py"), "--route-receipt", str(route_receipt), "--e1", str(e1), "--receipt", str(carrier_receipt)], cwd=stegfin, env=env, timeout=180)
            checked("TV/TVC sovereign pretrade launch", completed)

            status_path = pretrade_output / "status.json"
            handoff_path = pretrade_output / "10_wallet_handoff.json"
            if not status_path.is_file() or not handoff_path.is_file():
                raise RuntimeError("governed pretrade did not emit status + wallet handoff")
            status = load(status_path)
            wallet_handoff = load(handoff_path)
            decision = status.get("decision")
            if decision not in {"USER_APPROVAL_REQUIRED", "USER_SWAP_SIGNATURE_REQUIRED"}:
                raise RuntimeError(f"governed pretrade did not reach USER_ONLY boundary: {decision}")
            if status.get("signed") is not False or status.get("broadcast") is not False:
                raise RuntimeError("pretrade status authority drift")
            if status.get("credential_authority") != "TV/TVC" or status.get("github_token_required") is not False or status.get("provider_secret_exported") is not False:
                raise RuntimeError("pretrade credential boundary drift")
            bundle_hash = wallet_handoff.get("bundle_sha256")
            if not isinstance(bundle_hash, str) or status.get("wallet_handoff_bundle_sha256") != bundle_hash:
                raise RuntimeError("wallet handoff commitment mismatch")
            route = load(route_receipt)
            lease = load(quote_lease)
            launch_lines = [line for line in completed.stdout.splitlines() if line.strip()]
            launch_receipt = json.loads(launch_lines[-1]) if launch_lines else {}
            if launch_receipt.get("credential_authority") != "TV/TVC" or launch_receipt.get("github_token_required") is not False:
                raise RuntimeError("launcher authority drift")

            atomic_write(RECEIPT, {
                "schema": "stegverse.stegfin-live-pretrade-heartbeat-receipt/v0.1", "task_id": EXPECTED_TASK, "heartbeat_epoch": epoch, "claim_id": claim_id, "fencing_token": fence,
                "state": "COMPLETE", "transition_id": "STEGFIN_PRETRADE_WALLET_HANDOFF_READY", "source_inventory_claim_id": inventory.get("claim_id"), "source_inventory_fencing_token": inventory.get("fencing_token"),
                "inventory_state_hash": inventory.get("inventory_state_hash"), "boundary_state_hash": inventory.get("boundary_state_hash"), "provider_route_receipt_hash": route.get("receipt_hash"), "tvc_quote_lease_receipt_sha256": lease.get("receipt_sha256"),
                "pretrade_decision": decision, "wallet_handoff_bundle_sha256": bundle_hash, "wallet_handoff_local_ref": str(handoff_path.relative_to(stegfin)), "fresh_quote_required_after_approval_settlement": status.get("fresh_quote_required_after_approval_settlement") is True,
                "credential_authority": "TV/TVC", "provider_capability_authority": "TV_TVC_VAULT_ONLY", "provider_capability_delivery": "INHERITED_FILE_DESCRIPTOR",
                "provider_secret_value_recorded": False, "provider_secret_hash_recorded": False, "provider_secret_path_recorded": False, "github_token_required": False, "github_runtime_required": False,
                "wallet_signing_authority": "USER_ONLY", "broadcast_authority": "USER_ONLY", "signed": False, "broadcast": False, "settled": False, "next_authorized_action": status.get("next_step"),
            })
    except subprocess.TimeoutExpired as exc:
        return emit_blocked(epoch, claim_id, fence, "STEGFIN_PRETRADE_RETRY", "RUNTIME_EXECUTION", f"Bounded pretrade process timed out: {exc}", "a subsequent bounded run reaches the USER_ONLY wallet handoff within the task runtime window", "Retry on the next admitted heartbeat without widening credential, network, wallet or execution authority.")
    except Exception as exc:
        return emit_blocked(epoch, claim_id, fence, "STEGFIN_PRETRADE_RETRY", "RUNTIME_EXECUTION", f"Governed external pretrade failed closed: {str(exc)[-1400:]}", "the exact TV/TVC -> vault -> governed pretrade chain emits a hash-bound USER_ONLY wallet handoff", "Retry or repair only the named canonical StegFin/TV/TVC source surfaces; do not introduce alternate secrets, tokens, provider routes, signers or broadcasters.")

    json.dump(response(state="COMPLETE", transition_id="STEGFIN_PRETRADE_WALLET_HANDOFF_READY", sequence=2, next_transition="USER_ONLY_WALLET_ACTION", evidence_refs=[str(RECEIPT.relative_to(ROOT))]), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
