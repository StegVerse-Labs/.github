#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
RESIDENT_RUNTIME = Path(__file__).resolve().parents[1] / "resident-runtime"
VERIFY_ENTRYPOINT = "workers/ecosystem_chat_orphan_recovery_worker.py::verify_released_claim_organization_receipt"
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

def canonical_master_records_ref(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    for root in master_records_roots():
        try:
            relative = resolved.relative_to(root.resolve())
        except ValueError:
            continue
        return f"master-records/orchestration:{relative.as_posix()}"
    return None

def canonical_checkpoint_hash(checkpoint: dict | None) -> str | None:
    if not isinstance(checkpoint, dict):
        return None
    value = dict(checkpoint)
    value.pop("checkpoint_sha256", None)
    return stable_hash(value)

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
                and custody.get("authority_effect") == "NONE"
            ):
                # Master Records acceptance and reconstruction status are evidence only.
                return path, record
    return None, None


def _organization_custody():
    """The existing Organization ledger verifier, imported the way its callers import it."""
    if str(RESIDENT_RUNTIME) not in sys.path:
        sys.path.insert(0, str(RESIDENT_RUNTIME))
    import organization_batch_custody
    return organization_batch_custody


SATISFYING_EDGE = (
    "The G20 claim release (claim " + OLD_CLAIM + ", fencing token 20, released) is appended to the "
    "Organization ledger under its lock as a canonical state receipt whose subject is " + PARENT_TASK + ", "
    "and the lifecycle custody record carries organization_receipt.organization_receipt_sha256 and "
    "organization_receipt.state_receipt_sha256 for that append; the ledger root is supplied as "
    "STEGVERSE_ORG_LEDGER_ROOT or invocation organization_ledger_root."
)


def verify_released_claim_organization_receipt(record: dict | None, *, root=None) -> tuple[dict | None, dict | None]:
    """Verify the released G20 claim against its Organization receipt, never Master Records PASS.

    Returns (verified Organization receipt row, None) or (None, typed refusal).
    The receipt is read back from the Organization ledger (`root`, else
    STEGVERSE_ORG_LEDGER_ROOT; never a host path), bound to the release's exact
    state receipt, and the retained source receipt must name the parent task
    and the released claim and fence. A refusal is DENY or FAIL_CLOSED with its
    failed predicate, satisfying edge and retry entrypoint; nothing is committed.
    """
    custody = _organization_custody()

    def refused(exc) -> tuple[None, dict]:
        refusal = exc.refusal()
        refusal["satisfying_edge"] = SATISFYING_EDGE
        if refusal["disposition"] == "FAIL_CLOSED":
            refusal["retry_entrypoint"] = VERIFY_ENTRYPOINT
        return None, refusal

    binding = (record or {}).get("organization_receipt")
    if not isinstance(binding, dict):
        # The historical v2 lifecycle custody record carries no Organization receipt.
        return refused(custody.OrganizationReceiptRefused("RELEASED_CLAIM_ORGANIZATION_RECEIPT_ABSENT", deterministic=False))
    try:
        row, source = custody.verified_organization_source_receipt(
            root, binding.get("organization_receipt_sha256"),
            state_receipt_sha256=binding.get("state_receipt_sha256"))
        evidence = source.get("transition_evidence") if isinstance(source.get("transition_evidence"), dict) else {}
        if not (source.get("subject_or_correlation_id") == PARENT_TASK
                and evidence.get("claim_id") == OLD_CLAIM
                and evidence.get("fencing_token") == OLD_FENCE
                and evidence.get("released") is True):
            raise custody.OrganizationReceiptRefused("RELEASED_CLAIM_ORGANIZATION_RECEIPT_CLAIM_MISMATCH",
                                                     deterministic=True, detail=OLD_CLAIM)
    except custody.OrganizationReceiptRefused as exc:
        return refused(exc)
    return row, None

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
        and checkpoint.get("checkpoint_sha256") == canonical_checkpoint_hash(checkpoint)
    )
    old_authority_ended = bool(
        isinstance(parent, dict)
        and parent.get("claim_id") is None
        and parent.get("worker_id") is None
        and parent.get("state") == "BLOCKED"
        and {"WORKER_ORPHANED", "OLD_AUTHORITY_RELEASED", "RECOVERY_RECONSTRUCTION_REQUIRED"}.issubset(set(parent.get("archive_reason_codes") or []))
    )
    custody_path, custody = find_lifecycle_custody()
    custody_ref = canonical_master_records_ref(custody_path)
    custody_present = custody is not None and custody_ref is not None
    organization_row, organization_refusal = verify_released_claim_organization_receipt(
        custody, root=invocation.get("organization_ledger_root"))
    custody_valid = organization_row is not None

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
        "checkpoint_sha256": checkpoint.get("checkpoint_sha256") if checkpoint else None,
        "checkpoint_valid": checkpoint_valid,
        "old_authority_ended": old_authority_ended,
        "master_records_organization_record_ref": custody_ref,
        "master_records_organization_record_record_hash": custody.get("record_hash") if custody else None,
        "master_records_organization_record_valid": custody_present,
        "master_records_role": "EVIDENCE_ONLY_NOT_A_GATE",
        "released_claim_organization_receipt_sha256": organization_row["receipt_sha256"] if organization_row else None,
        "released_claim_organization_receipt_verified": custody_valid,
        "released_claim_organization_receipt_refusal": organization_refusal,
        "old_authority_reused": False,
        "successor_authority_granted": False,
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "authority_effect": "NONE",
        "state": "PASS" if passed else "BLOCKED",
        "next_transition": "SEPARATE_HIGHER_FENCE_PARENT_SUCCESSOR_AUTHORIZATION" if passed else "G20_RELEASE_ORGANIZATION_RECEIPT_REQUIRED",
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    atomic_write(RECEIPT, receipt)

    blocker = None
    if not passed:
        next_action = SATISFYING_EDGE + " Then re-run the recovery-only heartbeat worker."
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "The released G20 claim is not verified against its Organization receipt." if not custody_valid else "Orphan lifecycle checkpoint or ended-authority predicates did not validate.",
            "refusal": organization_refusal,
            "solution_required": True,
            "may_remain_blocked": False,
            "workaround_candidates": [SATISFYING_EDGE],
            "next_solution_action": next_action,
            "machine_observable_release_condition": "orphan-recovery-HB28.json reaches state PASS with released_claim_organization_receipt_verified=true and old_authority_ended=true",
            "github_token_required": False,
            "third_party_blocker": False,
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if passed else "BLOCKED",
        "transition_id": "ORPHAN_LIFECYCLE_RECONSTRUCTED" if passed else "RELEASED_CLAIM_ORGANIZATION_RECEIPT_REFUSED",
        "transition_sequence": 1,
        "expected_next_transition": None if passed else "ORPHAN_LIFECYCLE_RECONSTRUCTED",
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json",
        "evidence_refs": [CHECKPOINT_REF, "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json"] + ([custody_ref] if custody_ref else []),
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "orphan_lifecycle_reconstruction"},
    }
    json.dump(response, __import__("sys").stdout, sort_keys=True)
    __import__("sys").stdout.write("\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
