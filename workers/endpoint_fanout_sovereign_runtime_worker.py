#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Mapping

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001"
PARENT_TASK_ID = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
PARENT_RECEIPT = ROOT / "receipts/device-kv-intr/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json"
RECEIPT = ROOT / "receipts/endpoint-fanout/SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(dict(value), handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    os.replace(temp, path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def find_kv_root() -> Path | None:
    candidates: list[Path] = []
    explicit = os.getenv("STEGVERSE_KV_SOURCE_ROOT")
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend([
        ROOT.parent / "continuity-vault-kit",
        ROOT / "continuity-vault-kit",
        ROOT / "StegVerse-Labs" / "continuity-vault-kit",
        ROOT.parent.parent / "continuity-vault-kit",
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (
            (resolved / "tools/run_endpoint_fanout_probe.py").is_file()
            and (resolved / "runtime/kv_interlock_endpoint.py").is_file()
        ):
            return resolved
    return None


def blocker(problem: str, action: str, release: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": action,
        "machine_observable_release_condition": release,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "human_action_required": False,
    }


def worker_response(state: str, transition: str, epoch: int, *, blocked: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "ENDPOINT_FANOUT_SOVEREIGN_RUNTIME_OBSERVED",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 8,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [
            str(RECEIPT.relative_to(ROOT)),
            str(PARENT_RECEIPT.relative_to(ROOT)),
            "workers/endpoint_fanout_sovereign_runtime_worker.py",
            "docs/ENDPOINT_FANOUT_LIVE_RUNTIME_MIRROR_HANDOFF.md",
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "endpoint_fanout_sovereign_runtime",
        },
    }
    if blocked is not None:
        result["blocker"] = blocked
    return result


def write_blocked(base: dict[str, Any], reason: str, problem: str, action: str, release: str, epoch: int) -> int:
    value = {
        **base,
        "state": "BLOCKED",
        "transition_id": reason,
        "observed_at": now_iso(),
        "blocker": blocker(problem, action, release),
    }
    atomic_json(RECEIPT, value)
    json.dump(worker_response("BLOCKED", reason, epoch, blocked=value["blocker"]), sys.stdout)
    print()
    return 0


def validate_fanout(result: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if result.get("schema") != "stegverse.endpoint-fanout-probe-result.v1":
        raise ValueError("fanout result schema mismatch")
    if result.get("pass") is not True or result.get("report_count") != 2:
        raise ValueError("fanout result must pass with exactly two reports")
    reports = result.get("reports")
    if not isinstance(reports, Mapping) or set(reports) != {
        "kv_interlock_endpoint_status", "master_records_travel"
    }:
        raise ValueError("fanout report set mismatch")
    kv = reports["kv_interlock_endpoint_status"]
    travel = reports["master_records_travel"]
    if not isinstance(kv, Mapping) or not isinstance(travel, Mapping):
        raise ValueError("fanout reports must be objects")
    if kv.get("endpoint_status") != "PASS":
        raise ValueError("KV endpoint status report not PASS")
    if kv.get("canonical_state_changed") is not False:
        raise ValueError("KV endpoint report claims canonical mutation")
    if kv.get("execution_authority") != "NONE" or kv.get("credential_authority") != "TV/TVC":
        raise ValueError("KV endpoint report authority boundary mismatch")
    returned = kv.get("return_interlock")
    if not isinstance(returned, Mapping):
        raise ValueError("KV endpoint status Interlock return missing")
    expected = {
        "operation": "COMMIT_CANDIDATE",
        "decision": "ALLOW_BOUNDED_CONTEXT",
        "candidate_type": "ENDPOINT_STATUS_REPORT",
        "candidate_only": True,
        "canonical_state_changed": False,
        "authority_effect": "NONE",
    }
    for key, wanted in expected.items():
        if returned.get(key) != wanted:
            raise ValueError(f"KV status Interlock return {key} mismatch")
    if travel.get("schema") != "stegverse.master-records.travel-report.v1":
        raise ValueError("Master Records travel report schema mismatch")
    if travel.get("authority_effect") != "NONE":
        raise ValueError("Master Records travel report authority escalation")
    return dict(kv), dict(travel)


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    epoch = invocation.get("heartbeat_epoch")
    if (
        invocation.get("schema") != "stegverse.worker-invocation/v0.1"
        or task.get("task_id") != TASK_ID
        or not isinstance(epoch, int)
    ):
        return 2
    claim_id = task.get("claim_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 3

    base = {
        "schema": "stegverse.endpoint-fanout.sovereign-runtime-evidence/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "github_token_used": False,
        "non_tv_tvc_secret_or_token_used": False,
        "network_source_fetch_performed": False,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "canonical_kv_mutation": False,
        "provider_operation_authorized": False,
        "live_master_records_external_custody_claimed": False,
        "authority_effect": "NONE",
    }

    parent = load_json(PARENT_RECEIPT)
    if not parent or parent.get("state") != "OBSERVED" or parent.get("transition_id") != "DEVICE_KV_INTR_OBSERVED":
        return write_blocked(
            base,
            "DEVICE_KV_INTR_PARENT_REQUIRED",
            "Authentic DEVICE_KV_INTR_OBSERVED parent receipt is not present.",
            "Allow the existing StegOS/KV resident chain to complete DEVICE_KV_INTR observation.",
            "parent receipt state=OBSERVED and transition_id=DEVICE_KV_INTR_OBSERVED",
            epoch,
        )
    parent_transport_ok = (
        parent.get("credential_authority") == "TV/TVC"
        and parent.get("canonical_kv_mutation") is False
        and parent.get("hb_derived_carrier_transport_observed") is True
        and parent.get("request_transported_on_hb_derived_carrier") is True
        and parent.get("response_transported_on_hb_derived_carrier") is True
        and parent.get("request_carrier_packet_recovery_verified") is True
        and parent.get("response_carrier_packet_recovery_verified") is True
        and isinstance(parent.get("request_shared_hb_signal_ref"), str)
        and bool(parent.get("request_shared_hb_signal_ref"))
        and isinstance(parent.get("response_shared_hb_signal_ref"), str)
        and bool(parent.get("response_shared_hb_signal_ref"))
        and isinstance(parent.get("request_shared_hb_signal_sha256"), str)
        and bool(parent.get("request_shared_hb_signal_sha256"))
        and isinstance(parent.get("response_shared_hb_signal_sha256"), str)
        and bool(parent.get("response_shared_hb_signal_sha256"))
    )
    if not parent_transport_ok:
        return write_blocked(
            base,
            "DEVICE_KV_INTR_PARENT_AUTHORITY_REPAIR_REQUIRED",
            "Parent DEVICE_KV_INTR receipt does not satisfy the current exact HB-derived transport/recovery evidence boundary.",
            "Allow the current StegOS/KV chain consumer to re-observe or repair DEVICE_KV under current source before endpoint fanout.",
            "parent preserves TV/TVC, canonical_kv_mutation=false, exact request/response HB-derived transport/recovery=true, and non-empty shared-HB signal refs/digests",
            epoch,
        )

    kv_root = find_kv_root()
    if kv_root is None:
        return write_blocked(
            base,
            "LOCAL_KV_SOURCE_MATERIALIZATION_REQUIRED",
            "Current continuity-vault-kit source is not materialized on the sovereign resident.",
            "Materialize current source through the existing credential-free local source path.",
            "tools/run_endpoint_fanout_probe.py and runtime/kv_interlock_endpoint.py resolve locally",
            epoch,
        )

    tool = kv_root / "tools/run_endpoint_fanout_probe.py"
    with tempfile.TemporaryDirectory(prefix="stegverse-endpoint-fanout-") as tmp:
        output = Path(tmp) / "result.json"
        probe_id = f"sovereign-{fence}-{str(parent.get('request_id') or 'device-kv')[-24:]}"
        completed = subprocess.run(
            [
                sys.executable,
                str(tool),
                "--value",
                "stegverse-sovereign-endpoint-fanout-probe",
                "--probe-id",
                probe_id,
                "--output",
                str(output),
            ],
            cwd=kv_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env={
                k: v
                for k, v in os.environ.items()
                if k in {"PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH"}
            },
        )
        if completed.returncode != 0 or not output.is_file():
            return write_blocked(
                base,
                "ENDPOINT_FANOUT_EXECUTION_REPAIR_REQUIRED",
                f"Canonical endpoint fanout probe failed on sovereign resident with return code {completed.returncode}.",
                "Repair the exact current-source probe/runtime defect and retry under a fresh fence.",
                "canonical endpoint fanout probe returns 0 and writes a PASS result",
                epoch,
            )
        result = load_json(output)
        if result is None:
            return write_blocked(
                base,
                "ENDPOINT_FANOUT_RESULT_REPAIR_REQUIRED",
                "Endpoint fanout result was not a readable JSON object.",
                "Repair current source/result persistence and retry.",
                "fanout result JSON object is readable and validates",
                epoch,
            )

    try:
        kv_report, travel_report = validate_fanout(result)
    except Exception as exc:
        return write_blocked(
            base,
            "ENDPOINT_FANOUT_VALIDATION_REPAIR_REQUIRED",
            f"Sovereign endpoint fanout result failed closed validation: {type(exc).__name__}: {exc}",
            "Repair the exact two-report implementation and rerun under a fresh fence.",
            "two reports validate and KV return Interlock remains candidate-only/non-mutating",
            epoch,
        )

    receipt = {
        **base,
        "state": "OBSERVED",
        "transition_id": "ENDPOINT_FANOUT_SOVEREIGN_RUNTIME_OBSERVED",
        "observed_at": now_iso(),
        "parent_receipt_sha256": sha256_hex(parent),
        "source_root": str(kv_root),
        "source_tool": "tools/run_endpoint_fanout_probe.py",
        "probe_id": result["probe"]["probe_id"],
        "probe_sha256": sha256_hex(result["probe"]),
        "result_sha256": sha256_hex(result),
        "report_count": 2,
        "kv_status_report_sha256": sha256_hex(kv_report),
        "kv_endpoint_status": kv_report["endpoint_status"],
        "kv_status_return_operation": kv_report["return_interlock"]["operation"],
        "kv_status_return_candidate_type": kv_report["return_interlock"]["candidate_type"],
        "kv_status_return_candidate_only": kv_report["return_interlock"]["candidate_only"],
        "kv_status_return_canonical_state_changed": kv_report["return_interlock"]["canonical_state_changed"],
        "kv_status_return_candidate_ref": kv_report["return_interlock"]["writeback_candidate_ref"],
        "master_records_travel_report_sha256": sha256_hex(travel_report),
        "master_records_travel_hop_count": len(travel_report.get("hops") or []),
        "master_records_local_contract_custody_state": (
            (travel_report.get("master_records_result") or {}).get("custody_status")
        ),
        "same_result_reconstructed": True,
    }
    atomic_json(RECEIPT, receipt)
    if load_json(RECEIPT) != receipt:
        return 5
    json.dump(worker_response("COMPLETED", "ENDPOINT_FANOUT_SOVEREIGN_RUNTIME_OBSERVED", epoch), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
