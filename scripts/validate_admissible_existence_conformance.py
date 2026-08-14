#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "control" / "admissible-existence-conformance-policy.json"
HANDOFF_ROOT = ROOT / "handoffs"
REGISTRY = ROOT / "control" / "worker-registry.json"
REGISTRY_D = ROOT / "control" / "worker-registry.d"
EXECUTABLE_SCHEMA = "stegverse.executable-handoff/v0.1"
VALID_PHASES = {"DECLARED", "STANDING", "ADMISSIBLE", "ACTIVATED", "SUSPENDED", "SUPERSEDED", "TERMINATED"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def task_id_of(record: dict[str, Any]) -> str | None:
    task = record.get("task") if isinstance(record.get("task"), dict) else {}
    for value in (record.get("task_id"), task.get("task_id"), record.get("fragment_id")):
        if isinstance(value, str) and value:
            return value
    return None


def explicit_ae(record: dict[str, Any]) -> dict[str, Any] | None:
    value = record.get("admissible_existence")
    return value if isinstance(value, dict) else None


def projected_phase(record: dict[str, Any]) -> str:
    ae = explicit_ae(record)
    if ae and ae.get("phase") in VALID_PHASES:
        return str(ae["phase"])
    state = str(record.get("state", "")).upper()
    if state in {"NEW", "DECLARED", "QUEUED", "UNSTARTED", "PENDING_REGISTRATION"}:
        return "DECLARED"
    if state in {"SUSPENDED"}:
        return "SUSPENDED"
    if state in {"SUPERSEDED"}:
        return "SUPERSEDED"
    if state in {"TERMINATED", "CANCELLED", "CANCELED"}:
        return "TERMINATED"
    # Critical AE rule: completed/source-complete is not activation proof.
    if state in {"COMPLETED", "COMPLETE", "COMPLETE_RELEASED", "RELEASED_COMPLETE"}:
        return "ADMISSIBLE"
    return "ADMISSIBLE"


def authority_values(record: dict[str, Any]) -> tuple[Any, Any]:
    ae = explicit_ae(record) or {}
    authority = record.get("authority") if isinstance(record.get("authority"), dict) else {}
    credential = ae.get("credential_authority", record.get("credential_authority", authority.get("credential_authority")))
    github = ae.get("github_token_runtime_authority", record.get("github_token_runtime_authority"))
    if github is None and "github_token_required" in record:
        github = bool(record.get("github_token_required"))
    return credential, github


def validate_explicit(prefix: str, record: dict[str, Any], errors: list[str]) -> None:
    ae = explicit_ae(record)
    if not ae:
        return
    phase = ae.get("phase")
    if phase not in VALID_PHASES:
        errors.append(f"{prefix}: admissible_existence.phase invalid: {phase}")
        return
    capability_id = ae.get("capability_id")
    if not isinstance(capability_id, str) or not capability_id:
        errors.append(f"{prefix}: admissible_existence.capability_id required")
    owner = ae.get("continuation_owner")
    if phase == "ADMISSIBLE" and as_list(ae.get("blockers")) and not (isinstance(owner, str) and owner):
        errors.append(f"{prefix}: blocked ADMISSIBLE requires continuation_owner")
    if phase == "ACTIVATED":
        if not as_list(ae.get("integration_evidence_refs")):
            errors.append(f"{prefix}: ACTIVATED requires integration_evidence_refs")
        if not isinstance(ae.get("activation_proof_ref"), str) or not ae.get("activation_proof_ref"):
            errors.append(f"{prefix}: ACTIVATED requires activation_proof_ref")
        if as_list(ae.get("blockers")):
            errors.append(f"{prefix}: ACTIVATED cannot retain blockers")
    credential, github = authority_values(record)
    if credential not in (None, "TV/TVC"):
        errors.append(f"{prefix}: credential authority must be TV/TVC, got {credential}")
    if github not in (None, False, "NONE"):
        errors.append(f"{prefix}: GitHub token runtime authority prohibited, got {github}")


def iter_worker_records() -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if REGISTRY.exists():
        root = load(REGISTRY)
        for index, task in enumerate(as_list(root.get("tasks"))):
            if isinstance(task, dict):
                found.append((f"control/worker-registry.json#tasks[{index}]", task))
    if REGISTRY_D.exists():
        for path in sorted(REGISTRY_D.glob("*.json")):
            root = load(path)
            for index, task in enumerate(as_list(root.get("tasks"))):
                if isinstance(task, dict):
                    found.append((f"{path.relative_to(ROOT)}#tasks[{index}]", task))
            # Fragment-level authority constraints also apply to each task.
            if explicit_ae(root):
                found.append((str(path.relative_to(ROOT)), root))
    return found


def iter_handoffs() -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(HANDOFF_ROOT.glob("*.json")):
        root = load(path)
        if root.get("schema") == EXECUTABLE_SCHEMA:
            found.append((str(path.relative_to(ROOT)), root))
    return found


def main() -> int:
    policy = load(POLICY)
    if policy.get("schema") != "stegverse.admissible-existence-conformance-policy/v1":
        raise SystemExit("invalid AE conformance policy schema")
    semantics = policy.get("canonical_semantics") or {}
    if semantics.get("lifecycle_commit") != "7d94908be562f9f9ace05877d4507dc68c984e06":
        raise SystemExit("unexpected StegCore AE lifecycle binding")
    if semantics.get("registry_commit") != "c63b4cce408bc8b3a9c33c6417d96d959678ac19":
        raise SystemExit("unexpected StegCore AE registry binding")

    errors: list[str] = []
    projections: list[dict[str, Any]] = []
    explicit_by_task: dict[str, tuple[str, str]] = {}

    records = iter_handoffs() + iter_worker_records()
    for prefix, record in records:
        validate_explicit(prefix, record, errors)
        tid = task_id_of(record)
        phase = projected_phase(record)
        projections.append({"record": prefix, "task_id": tid, "phase": phase, "explicit": explicit_ae(record) is not None})
        ae = explicit_ae(record)
        if tid and ae and ae.get("phase") in VALID_PHASES:
            prior = explicit_by_task.get(tid)
            current = (prefix, str(ae["phase"]))
            if prior and prior[1] != current[1]:
                errors.append(f"{prefix}: explicit AE phase {current[1]} conflicts with {prior[0]} phase {prior[1]} for {tid}")
            else:
                explicit_by_task[tid] = current
        credential, github = authority_values(record)
        if credential not in (None, "TV/TVC"):
            errors.append(f"{prefix}: credential authority must be TV/TVC, got {credential}")
        if github not in (None, False, "NONE"):
            errors.append(f"{prefix}: GitHub token runtime authority prohibited, got {github}")

    if not records:
        errors.append("no HANDOFF or worker registry records discovered")

    explicit_count = sum(1 for row in projections if row["explicit"])
    legacy_count = len(projections) - explicit_count
    activated = sum(1 for row in projections if row["phase"] == "ACTIVATED")

    if errors:
        for error in errors:
            print(f"AE_CONFORMANCE_FAIL:{error}")
        print(f"AE_CONFORMANCE_SUMMARY records={len(projections)} explicit={explicit_count} legacy_projected={legacy_count} activated={activated}")
        return 1

    print(
        "AE_HANDOFF_WORKER_CONFORMANCE_PASS "
        f"records={len(projections)} explicit={explicit_count} legacy_projected={legacy_count} activated={activated} "
        "source_completion_never_implies_activation=true credential_authority=TV/TVC github_token_runtime_authority=NONE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
