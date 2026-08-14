#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "STEGFIN-CONTINUITY-CARRIER-007"
RECEIPT = ROOT / "receipts" / "stegfin-continuity" / f"{TASK_ID}.json"
RUNTIME_READY_STATE = "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND"
EXPECTED_PROVIDER_ROUTE = "https://tvc.stegverse.org/v1/provider-operation"
EXPECTED_TVC_BLOBS = {
    "tvc_provider_operation_broker.py": "1f56925fccb5e7e3121aa35b37f782cfe558034a",
    "app/main.py": "1f3cd71eea6a182ae0c492b748d9ba3e7bc83d4f",
    "scripts/tvc_provider_operation_broker.py": "daed1b66c7a831e557ab811010732d17203aae50",
}


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def candidates(env_name: str, repo_name: str) -> list[Path]:
    values: list[Path] = []
    explicit = os.environ.get(env_name)
    if explicit:
        values.append(Path(explicit))
    values.extend([
        ROOT / "workloads" / repo_name,
        Path.home() / ".stegverse" / "workloads" / repo_name,
        Path.home() / ".stegverse" / "source" / repo_name,
        Path("/var/lib/stegverse/workloads") / repo_name,
        Path("/var/lib/stegverse/source") / repo_name,
    ])
    return values


def find_root(env_name: str, repo_name: str, required: tuple[str, ...]) -> Path | None:
    for candidate in candidates(env_name, repo_name):
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        if all((root / item).is_file() for item in required):
            return root
    return None


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def validate_exact_tvc_source(tvc_root: Path, expected: dict[str, str] | None = None) -> list[str]:
    failures: list[str] = []
    for relative, expected_sha in (expected or EXPECTED_TVC_BLOBS).items():
        path = tvc_root / relative
        if not path.is_file():
            failures.append(f"missing validated TVC source: {relative}")
            continue
        actual = git_blob_sha1(path)
        if actual != expected_sha:
            failures.append(f"validated TVC source drift: {relative}")
    return failures


def runtime_receipt_candidates(tvc_root: Path) -> list[Path]:
    values: list[Path] = []
    explicit = os.environ.get("STEGVERSE_TVC_RUNTIME_OBSERVER_RECEIPT")
    if explicit:
        values.append(Path(explicit).expanduser())
    values.extend([
        tvc_root / "artifacts" / "tvc-runtime-boundary-observation.json",
        tvc_root / "receipts" / "runtime" / "TVC-CAPABILITY-RUNTIME-002.json",
    ])
    return values


def load_runtime_release_receipt(tvc_root: Path) -> tuple[dict[str, Any] | None, str]:
    selected: Path | None = None
    for candidate in runtime_receipt_candidates(tvc_root):
        try:
            path = candidate.resolve()
        except Exception:
            continue
        if path.is_file():
            selected = path
            break
    if selected is None:
        return None, "primary TV/TVC runtime readiness receipt is absent"
    try:
        value = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "primary TV/TVC runtime readiness receipt is malformed"
    if not isinstance(value, dict):
        return None, "primary TV/TVC runtime readiness receipt must be an object"
    return value, str(selected)


def validate_runtime_release_receipt(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_false = {
        "consumer_credential_supplied": False,
        "github_token_required": False,
        "provider_secret_used": False,
        "provider_secret_exported": False,
        "non_tv_tvc_secret_or_token_used": False,
        "protected_values_observed": False,
        "provider_operation_attempted": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
    }
    if value.get("state") != RUNTIME_READY_STATE:
        failures.append("observer state is not READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND")
    if value.get("credential_authority") != "TV/TVC":
        failures.append("credential authority is not TV/TVC")
    for key, expected_value in expected_false.items():
        if value.get(key) is not expected_value:
            failures.append(f"{key} must be false")
    if value.get("provider_operation_route") != EXPECTED_PROVIDER_ROUTE:
        failures.append("provider-operation route is not the canonical TVC route")

    probes = value.get("probes")
    if not isinstance(probes, dict):
        failures.append("runtime observation probes are missing")
        return failures
    provider_get = probes.get("provider_get")
    provider_post = probes.get("provider_invalid_post")
    ingress_get = probes.get("ingress_get")
    ingress_post = probes.get("ingress_empty_post")
    if not isinstance(provider_get, dict) or provider_get.get("status_code") != 405:
        failures.append("provider GET fail-closed proof missing")
    if not isinstance(provider_post, dict) or provider_post.get("status_code") != 403 or provider_post.get("detail") != "unexpected request schema":
        failures.append("provider invalid-request canonical schema rejection missing")
    if not isinstance(ingress_get, dict) or ingress_get.get("status_code") != 405:
        failures.append("governed ingress GET fail-closed proof missing")
    if not isinstance(ingress_post, dict) or ingress_post.get("status_code") != 503 or ingress_post.get("detail") != "tvc_capability_unavailable":
        failures.append("governed ingress empty-POST fail-closed proof missing")
    return failures


def response(state: str, transition: str, refs: list[str], blocker: dict[str, Any] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY" if state != "COMPLETE" else None,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": refs,
    }
    if blocker is not None:
        value["blocker"] = blocker
    return value


def blocked(problem: str, release: str, next_action: str) -> int:
    blocker = {
        "dependency_class": "CONTINUITY_RUNTIME",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "machine_observable_release_condition": release,
        "next_solution_action": next_action,
        "human_action_required": False,
        "github_token_required": False,
        "third_party_blocker": False,
    }
    write(RECEIPT, {
        "schema": "stegverse.stegfin-continuity-worker-receipt.v1",
        "task_id": TASK_ID,
        "state": "ACTIVE_SOLUTION_REQUIRED",
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_used": False,
        "provider_secret_exported": False,
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
        "blocker": blocker,
    })
    json.dump(response("BLOCKED", "STEGFIN_CONTINUITY_RUNTIME_REQUIRED", [str(RECEIPT.relative_to(ROOT))], blocker), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        return 3
    worker_instance = str(task.get("worker_instance_id") or task.get("claim_id") or "stegfin-continuity-worker")

    stegfin = find_root("STEGVERSE_STEGFIN_SOURCE_ROOT", "stegfin-governance", (
        "scripts/run_continuity_pretrade.py",
        "configs/base_validation_entry_trade_request.json",
        "docs/STEGFIN_MIRROR_HANDOFF.md",
    ))
    tv = find_root("STEGVERSE_TV_SOURCE_ROOT", "TV", (
        "roles_templates/stegwallet_trading_runtime_policy.json",
        "policies/stegwallet_base_0x_quote_capability_policy.json",
    ))
    tvc = find_root("STEGVERSE_TVC_SOURCE_ROOT", "TVC", (
        "scripts/tvc_stegwallet_trading_gate_cli.py",
        "scripts/tvc_issue_stegwallet_quote_lease.py",
        "docs/PROVIDER_CAPABILITY_RESOLUTION_MIRROR_HANDOFF.md",
    ))
    if stegfin is None or tv is None or tvc is None:
        return blocked(
            "Released local StegFin/TV/TVC source is not materialized on this continuity carrier.",
            "all three source roots resolve required canonical surfaces",
            "Resolve already-released source through StegVerse continuity storage; do not use GitHub credentials or hosted checkout as production authority.",
        )

    source_failures = validate_exact_tvc_source(tvc)
    if source_failures:
        return blocked(
            "Materialized TVC provider source is not the exact validated release: " + "; ".join(source_failures),
            "the materialized TVC broker, app binding and broker transport script match the exact validated Git blob identities",
            "Materialize the canonical validated TVC source through StegVerse continuity storage; do not bypass drift with a credential or alternate broker.",
        )

    runtime_receipt, runtime_receipt_ref = load_runtime_release_receipt(tvc)
    if runtime_receipt is None:
        return blocked(
            runtime_receipt_ref,
            "TVC-CAPABILITY-RUNTIME-002 persists READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND with every no-secret/no-wallet predicate",
            "Allow the already-claimed TVC repository-native observer to persist the non-secret primary-runtime receipt; do not infer readiness from endpoint presence alone.",
        )
    runtime_failures = validate_runtime_release_receipt(runtime_receipt)
    if runtime_failures:
        return blocked(
            "Primary TV/TVC runtime readiness receipt failed validation: " + "; ".join(runtime_failures),
            "the TVC runtime observer receipt satisfies the canonical READY state, exact route/probe posture, and every no-secret/no-wallet predicate",
            "Keep the worker blocked and let TVC-CAPABILITY-RUNTIME-002 reconcile the primary runtime; do not widen credential or execution authority.",
        )

    broker_endpoint = os.environ.get("STEGVERSE_TV_TVC_BROKER_ENDPOINT")
    if not broker_endpoint:
        local = Path("/run/stegverse/vault-broker.sock")
        if local.exists():
            broker_endpoint = str(local)
    if not broker_endpoint or not (broker_endpoint.startswith("https://") or broker_endpoint.startswith("/")):
        return blocked(
            "No TV/TVC provider-operation broker transport is observable on this carrier after runtime readiness was proven.",
            "STEGVERSE_TV_TVC_BROKER_ENDPOINT is an HTTPS TV/TVC endpoint or the local private broker socket exists",
            "Use the already-proven TV/TVC runtime binding to expose/discover its broker transport; do not request a provider token from the user.",
        )

    minimal_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": os.pathsep.join([str(ROOT), str(stegfin), str(tv), str(tvc)]),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": os.environ.get("HOME", str(Path.home())),
    }
    heartbeat_state = ROOT / "control" / "heartbeat-state.json"
    with tempfile.TemporaryDirectory(prefix="stegfin-continuity-worker-") as tmp:
        tmp_root = Path(tmp)
        claim = tmp_root / "claim.json"
        claim_command = [
            sys.executable,
            str(ROOT / "scripts" / "acquire_stegfin_continuity_claim.py"),
            "--carrier-id", worker_instance,
            "--heartbeat-state", str(heartbeat_state),
            "--output", str(claim),
        ]
        claimed = subprocess.run(claim_command, cwd=ROOT, env=minimal_env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, check=False)
        if claimed.returncode != 0:
            return blocked(
                "Continuity collision scope could not be acquired.",
                "no active resident or continuity claim owns the validation lineage",
                "Recheck canonical claim/lease state and retry; never run a second trade lineage concurrently.",
            )
        output = stegfin / "reports" / "continuity_pretrade" / f"carrier-{worker_instance.replace('/', '_')}"
        run_command = [
            sys.executable,
            str(stegfin / "scripts" / "run_continuity_pretrade.py"),
            "--claim", str(claim),
            "--tv-root", str(tv),
            "--tvc-root", str(tvc),
            "--broker-endpoint", broker_endpoint,
            "--output", str(output),
        ]
        completed = subprocess.run(run_command, cwd=stegfin, env=minimal_env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=420, check=False)
        if completed.returncode != 0:
            return blocked(
                "Bounded continuity pretrade did not reach the wallet handoff on this attempt.",
                "run_continuity_pretrade.py exits 0 with WALLET_HANDOFF_READY under the current claim",
                "Use the emitted fail-closed evidence to resolve the exact TV/TVC, observation, quote, allowance or simulation condition; do not widen authority.",
            )
        continuity_receipt = output / "continuity-receipt.json"
        if not continuity_receipt.is_file():
            return blocked("Continuity runner emitted no terminal receipt.", "continuity-receipt.json exists", "Retry the bounded continuity runner without changing authority.")
        result = json.loads(continuity_receipt.read_text(encoding="utf-8"))
        terminal_ok = (
            result.get("state") == "WALLET_HANDOFF_READY"
            and result.get("credential_authority") == "TV/TVC"
            and result.get("non_tv_tvc_secret_or_token_used") is False
            and result.get("provider_secret_exported") is False
            and result.get("signed") is False
            and result.get("broadcast") is False
        )
        if not terminal_ok:
            return blocked(
                "Continuity receipt did not satisfy the full wallet-handoff authority boundary.",
                "terminal receipt is WALLET_HANDOFF_READY with credential_authority=TV/TVC, non_tv_tvc_secret_or_token_used=false, provider_secret_exported=false, signed=false and broadcast=false",
                "Repair the bounded continuity contract; never accept secret export, sign or broadcast from the worker.",
            )

    durable = {
        "schema": "stegverse.stegfin-continuity-worker-receipt.v1",
        "task_id": TASK_ID,
        "state": "COMPLETE",
        "transition_id": "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY",
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_used": False,
        "provider_secret_exported": False,
        "runtime_release_receipt": runtime_receipt_ref,
        "validated_tvc_source_blobs": EXPECTED_TVC_BLOBS,
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
        "wallet_handoff_bundle_sha256": result.get("wallet_handoff_bundle_sha256"),
        "signed": False,
        "broadcast": False,
    }
    write(RECEIPT, durable)
    json.dump(response("COMPLETE", "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY", [str(RECEIPT.relative_to(ROOT)), runtime_receipt_ref, str(continuity_receipt)]), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
