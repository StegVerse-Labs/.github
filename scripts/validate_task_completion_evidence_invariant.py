#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
RECORDS = ROOT / "data" / "canonical-task-records"

COMPLETION_CLASSES = [
    "SOURCE_IMPLEMENTED",
    "MERGED",
    "CI_VALIDATED",
    "SANDBOX_RUNTIME_OBSERVED",
    "EXTERNAL_PROVIDER_OBSERVED",
    "MASTER_RECORDS_RECONSTRUCTED",
    "END_TO_END",
]
RANK = {value: index for index, value in enumerate(COMPLETION_CLASSES)}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def completion_reportability(record: dict) -> dict[str, object]:
    completion = record.get("completion")
    if not isinstance(completion, dict):
        return {"reportable_complete": False, "state": "NO_COMPLETION_CLAIM"}

    claimed = completion.get("claimed") is True
    validated = completion.get("validated") is True
    if not (claimed or validated):
        return {"reportable_complete": False, "state": "NOT_CLAIMED"}

    contract_version = completion.get("evidence_contract_version") or record.get("completion_evidence_contract_version")
    evidence_class = completion.get("evidence_class")
    if contract_version != "v1" or evidence_class not in RANK:
        return {
            "reportable_complete": False,
            "state": "LEGACY_UNQUALIFIED_NON_AUTHORITATIVE",
            "authority": "NONE_NON_AUTHORITATIVE_PROVENANCE_ONLY",
        }

    terminal_class = completion.get("terminal_evidence_class")
    if terminal_class in RANK:
        satisfied = RANK[evidence_class] >= RANK[terminal_class]
    else:
        satisfied = evidence_class == "END_TO_END"

    return {
        "reportable_complete": satisfied,
        "state": "QUALIFIED_TERMINAL_SATISFIED" if satisfied else "QUALIFIED_PARTIAL_EVIDENCE",
        "evidence_class": evidence_class,
        "terminal_evidence_class": terminal_class,
    }


def validate_completion(path: Path, record: dict) -> None:
    completion = record.get("completion")
    if not isinstance(completion, dict):
        return

    claimed = completion.get("claimed") is True
    validated = completion.get("validated") is True
    if not (claimed or validated):
        return

    contract_version = completion.get("evidence_contract_version") or record.get("completion_evidence_contract_version")
    contract_engaged = contract_version == "v1" or any(
        key in completion for key in ("evidence_class", "terminal_evidence_class", "evidence_refs", "end_to_end_complete")
    )
    if not contract_engaged:
        return

    if contract_version != "v1":
        fail(f"{path.name}: reconciled completion requires evidence contract v1")
    if validated and not claimed:
        fail(f"{path.name}: validated completion requires claimed completion")

    evidence_class = completion.get("evidence_class")
    if evidence_class not in RANK:
        fail(f"{path.name}: completion.evidence_class is missing or invalid")

    evidence_refs = completion.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(isinstance(x, str) and x for x in evidence_refs):
        fail(f"{path.name}: affirmative completion requires non-empty completion.evidence_refs")

    terminal_class = completion.get("terminal_evidence_class")
    if terminal_class is not None:
        if terminal_class not in RANK:
            fail(f"{path.name}: unknown terminal evidence class {terminal_class}")
        if RANK[evidence_class] < RANK[terminal_class]:
            fail(f"{path.name}: {evidence_class} is weaker than terminal class {terminal_class}")

    if completion.get("end_to_end_complete") is True and evidence_class != "END_TO_END":
        fail(f"{path.name}: end_to_end_complete=true requires END_TO_END evidence class")


def validate_policy(policy: dict) -> None:
    invariants = policy.get("invariants") or {}
    required = {
        "completion_evidence_contract_version": "v1",
        "completion_language_requires_evidence_class": True,
        "unqualified_complete_or_completed_prohibited": True,
        "stronger_completion_class_inference_prohibited": True,
        "completion_claim_requires_evidence_refs": True,
        "new_or_reconciled_completion_requires_contract_version": True,
        "legacy_unqualified_completion_authority": "NONE_NON_AUTHORITATIVE_PROVENANCE_ONLY",
        "legacy_unqualified_completion_may_support_user_facing_complete": False,
        "legacy_unqualified_completion_may_satisfy_terminal_predicate": False,
        "terminal_complete_default_evidence_class": "END_TO_END",
    }
    for key, expected in required.items():
        if invariants.get(key) != expected:
            fail(f"global invariant {key} mismatch")
    if invariants.get("completion_evidence_classes") != COMPLETION_CLASSES:
        fail("completion evidence class list mismatch")
    if invariants.get("completion_evidence_strength_order") != COMPLETION_CLASSES:
        fail("completion evidence strength order mismatch")


def main() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    validate_policy(policy)

    legacy = 0
    qualified = 0
    for path in sorted(RECORDS.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        validate_completion(path, record)
        state = completion_reportability(record).get("state")
        if state == "LEGACY_UNQUALIFIED_NON_AUTHORITATIVE":
            legacy += 1
        elif state in {"QUALIFIED_TERMINAL_SATISFIED", "QUALIFIED_PARTIAL_EVIDENCE"}:
            qualified += 1

    print("TASK_COMPLETION_EVIDENCE_INVARIANT_PASS")
    print(f"LEGACY_UNQUALIFIED_NON_AUTHORITATIVE={legacy}")
    print(f"QUALIFIED_COMPLETION_RECORDS={qualified}")


if __name__ == "__main__":
    main()
