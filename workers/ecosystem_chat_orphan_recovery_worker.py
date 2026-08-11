#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"
PARENT_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
OLD_CLAIM = "SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20"
OLD_FENCE = 20
CHECKPOINT_REF = "checkpoints/workers/SHWP-ECOSYSTEM-CHAT-INFERENCE-001/HB25-G20.json"
RECEIPT = ROOT / "receipts" / "ecosystem-chat-sovereign-inference" / "orphan-recovery-HB28.json"


def stable_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        name = stream.name
    os.replace(name, path)


def master_records_roots() -> list[Path]:
    values: list[Path] = []
    override = os.environ.get("STEGVERSE_MASTER_RECORDS_ROOT")
    if override:
        values.append(Path(override).expanduser().resolve())
    values.extend([
        ROOT / "workloads" / "master-records" / "orchestration",
        ROOT / "workloads" / "orchestration",
        Path.home() / ".stegverse" / "workloads" / "master-records" / "orchestration",
        Path("/var/lib/stegverse/workloads/master-records/orchestration"),
    ])
    return values


def find_lifecycle_custody() -> tuple[Path | None, dict | None]:
    for root in master_records_roots():
        directory = root / "custody" / "worker-lifecycle"
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            record = load_json(path)
            if not record:
                continue
            claim = record.get("claim") or {}
            source = record.get("source") or {}
            custody = record.get("custody") or {}
            if (
                record.get("schema") == "stegverse.worker_lifecycle_custody.v2"
                and source.get("task_id") == PARENT_TASK
                and claim.get("claim_id") == OLD_CLAIM
                and claim.get("fencing_token") == OLD_FENCE
                and claim.get("released") is True
                and custody.get("status") == "ACCEPTED_FOR_CUSTODY"
                and custody.get("reconstruction_status") == "PASS"
                and custody.get("authority_effect") == "NONE"
            ):
                return path, record
    return None, None


def main() -> int:
    invocation = json.load(__import__("sys").stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if task.get("task_id") != EXPECTED_TASK or not isinstance(epoch, int):
        return 3
    required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if required != {"orphan_lifecycle_reconstruction"}:
        return 4
    claim_id = task.get("claim_id")
    fence = ((task.get("heartbeat_timing") or {}).get("fencing_token"))
    if not isinstance(claim_id, str) or not isinstance(fence, int) or fence <= OLD_FENCE:
        return 5

    checkpoint = load_json(ROOT / CHECKPOINT_REF)
    registry = load_json(ROOT / "control" / "worker-registry.json") or {}
    parent = next((x for x in registry.get("tasks", []) if x.get("task_id") == PARENT_TASK), None)
    checkpoint_valid = bool(
        checkpoint
        and checkpoint.get("task_id") == PARENT_TASK
        and checkpoint.get("claim_id") == OLD_CLAIM
        and checkpoint.get("fencing_token") == OLD_FENCE
        and checkpoint.get("heartbeat_epoch") == 25
    )
    old_authority_ended = bool(
        isinstance(parent, dict)
        and parent.get("claim_id") is None
        and parent.get("worker_id") is None
        and parent.get("state") == "BLOCKED"
        and {"WORKER_ORPHANED", "OLD_AUTHORITY_RELEASED", "RECOVERY_RECONSTRUCTION_REQUIRED"}.issubset(set(parent.get("archive_reason_codes") or []))
    )
    custody_path, custody = find_lifecycle_custody()
    custody_valid = custody is not None

    passed = checkpoint_valid and old_authority_ended and custody_valid
    receipt = {
        "schema": "stegverse.orphan-lifecycle-reconstruction-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "parent_task_id": PARENT_TASK,
        "heartbeat_epoch": epoch,
        "recovery_claim_id": claim_id,
        "recovery_fencing_token": fence,
        "old_claim_id": OLD_CLAIM,
        "old_fencing_token": OLD_FENCE,
        "checkpoint_ref": CHECKPOINT_REF,
        "checkpoint_sha256": stable_hash(checkpoint) if checkpoint else None,
        "checkpoint_valid": checkpoint_valid,
        "old_authority_ended": old_authority_ended,
        "master_records_custody_ref": str(custody_path) if custody_path else None,
        "master_records_custody_valid": custody_valid,
        "old_authority_reused": False,
        "successor_authority_granted": False,
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "authority_effect": "NONE",
        "state": "PASS" if passed else "BLOCKED",
        "next_transition": "SEPARATE_HIGHER_FENCE_PARENT_SUCCESSOR_AUTHORIZATION" if passed else "MASTER_RECORDS_G20_LIFECYCLE_CUSTODY_REQUIRED",
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    atomic_write(RECEIPT, receipt)

    blocker = None
    if not passed:
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "Canonical Master Records G20 worker-lifecycle custody/reconstruction PASS is not locally materialized." if not custody_valid else "Orphan lifecycle checkpoint or ended-authority predicates did not validate.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Materialize canonical master-records/orchestration lifecycle custody for the ended G20 worker and re-run the recovery-only heartbeat worker.",
            "machine_observable_release_condition": "orphan-recovery-HB28.json reaches state PASS with master_records_custody_valid=true and old_authority_ended=true",
            "github_token_required": False,
            "third_party_blocker": False,
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if passed else "BLOCKED",
        "transition_id": "ORPHAN_LIFECYCLE_RECONSTRUCTED" if passed else "MASTER_RECORDS_CUSTODY_NOT_PROVEN",
        "transition_sequence": 1,
        "expected_next_transition": None if passed else "ORPHAN_LIFECYCLE_RECONSTRUCTED",
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json",
        "evidence_refs": [CHECKPOINT_REF, "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json"] + ([str(custody_path)] if custody_path else []),
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "orphan_lifecycle_reconstruction"},
    }
    json.dump(response, __import__("sys").stdout, sort_keys=True)
    __import__("sys").stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
