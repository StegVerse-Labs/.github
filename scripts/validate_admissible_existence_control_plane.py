#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_ae_retrospective_conformance import main as validate_retrospective_conformance

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "control" / "admissible-existence-control-plane-policy.json"
EXECUTABLE_SCHEMA = "stegverse.executable-handoff/v0.1"
TERMINAL_TASK_STATES = {"COMPLETED", "SUPERSEDED", "TERMINATED"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_binding(
    binding: Any,
    prefix: str,
    policy: dict[str, Any],
    errors: list[str],
    *,
    require_task_conformance: bool = False,
) -> None:
    require(isinstance(binding, dict), f"{prefix}: admissible_existence must be object", errors)
    if not isinstance(binding, dict):
        return

    contract = policy["future_binding_contract"]
    for key in contract["required_keys"]:
        require(key in binding, f"{prefix}: admissible_existence.{key} required", errors)
    if require_task_conformance:
        for key in contract["post_task_conformance_required_keys"]:
            require(key in binding, f"{prefix}: admissible_existence.{key} required by current task-conformance contract", errors)

    phase = binding.get("phase")
    require(phase in policy["phases"], f"{prefix}: invalid AE phase {phase}", errors)
    require(binding.get("credential_authority") == "TV/TVC", f"{prefix}: AE credential authority must be TV/TVC", errors)
    require(binding.get("github_token_runtime_authority") is False, f"{prefix}: AE GitHub runtime authority must be false", errors)
    for key in ("standing_evidence_refs", "admissibility_evidence_refs", "integration_evidence_refs", "blockers"):
        require(isinstance(binding.get(key), list), f"{prefix}: admissible_existence.{key} must be list", errors)

    if phase in {"STANDING", "ADMISSIBLE", "ACTIVATED", "SUSPENDED", "SUPERSEDED", "TERMINATED"}:
        require(bool(binding.get("standing_evidence_refs")), f"{prefix}: standing evidence required for {phase}", errors)
    if phase in {"ADMISSIBLE", "ACTIVATED", "SUSPENDED", "SUPERSEDED", "TERMINATED"}:
        require(bool(binding.get("admissibility_evidence_refs")), f"{prefix}: admissibility evidence required for {phase}", errors)
    if phase in {"ACTIVATED", "SUSPENDED", "SUPERSEDED"}:
        require(bool(binding.get("integration_evidence_refs")), f"{prefix}: integration evidence required for activated lineage", errors)
        require(isinstance(binding.get("activation_proof_ref"), str) and bool(binding.get("activation_proof_ref")), f"{prefix}: activation proof required for activated lineage", errors)
    if phase == "ACTIVATED":
        require(not binding.get("blockers"), f"{prefix}: ACTIVATED may not retain blockers", errors)
    if phase == "ADMISSIBLE" and binding.get("blockers"):
        require(isinstance(binding.get("continuation_owner"), str) and bool(binding.get("continuation_owner")), f"{prefix}: blocked ADMISSIBLE requires continuation_owner", errors)

    if require_task_conformance:
        temporal_class = binding.get("temporal_class")
        relationship = binding.get("task_relationship")
        target_phase = binding.get("target_phase")
        require(temporal_class in policy["temporal_classes"], f"{prefix}: invalid temporal_class {temporal_class}", errors)
        require(relationship in policy["task_relationships"], f"{prefix}: invalid task_relationship {relationship}", errors)
        require(target_phase in policy["phases"], f"{prefix}: invalid target_phase {target_phase}", errors)

        if temporal_class == "recently_completed":
            retained = list(binding.get("standing_evidence_refs") or []) + list(binding.get("admissibility_evidence_refs") or []) + list(binding.get("integration_evidence_refs") or [])
            require(bool(retained), f"{prefix}: recently_completed requires retained phase evidence", errors)
        elif temporal_class == "current":
            require(isinstance(binding.get("continuation_owner"), str) and bool(binding.get("continuation_owner")), f"{prefix}: current task requires continuation_owner", errors)
        elif temporal_class == "future":
            require(target_phase is not None, f"{prefix}: future task requires target_phase", errors)
            require(relationship is not None, f"{prefix}: future task requires task_relationship", errors)
            require(binding.get("activation_proof_ref") in (None, ""), f"{prefix}: future task may not self-claim activation proof", errors)

    known_phase = policy.get("known_capability_phase_snapshot", {}).get(binding.get("capability_id"))
    if known_phase is not None:
        require(phase == known_phase, f"{prefix}: phase {phase} diverges from canonical known capability phase {known_phase}", errors)


def collect_registry_tasks() -> dict[str, tuple[str, dict[str, Any], dict[str, Any]]]:
    found: dict[str, tuple[str, dict[str, Any], dict[str, Any]]] = {}
    paths = [ROOT / "control" / "worker-registry.json"] + sorted((ROOT / "control" / "worker-registry.d").glob("*.json"))
    for path in paths:
        if not path.exists():
            continue
        doc = load_json(path)
        for task in doc.get("tasks") or []:
            if not isinstance(task, dict):
                continue
            task_id = task.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                continue
            found[task_id] = (str(path.relative_to(ROOT)), task, doc)
    return found


def main() -> int:
    policy = load_json(POLICY_PATH)
    errors: list[str] = []
    require(policy.get("schema") == "stegverse.admissible-existence-control-plane-policy/v1", "policy schema invalid", errors)
    require(policy.get("policy_version") == "1.1.0", "policy must be reconciled to task-conformance version 1.1.0", errors)
    require(policy.get("credential_authority") == "TV/TVC", "policy credential authority must be TV/TVC", errors)
    require(policy.get("github_token_runtime_authority") is False, "policy GitHub runtime authority must be false", errors)

    cutoff = parse_time(policy.get("effective_at"))
    task_cutoff = parse_time(policy.get("task_conformance_effective_at"))
    require(cutoff is not None, "policy effective_at invalid", errors)
    require(task_cutoff is not None, "policy task_conformance_effective_at invalid", errors)

    canonical = policy.get("canonical_stegcore") if isinstance(policy.get("canonical_stegcore"), dict) else {}
    required_canonical = (
        "capability_model_origin_commit",
        "capability_registry_origin_commit",
        "capability_registry_current_binding_commit",
        "task_conformance_merge_commit",
        "capability_handoff_current_commit",
        "task_conformance_handoff",
        "task_conformance_manifest",
        "task_conformance_verifier",
    )
    for key in required_canonical:
        require(isinstance(canonical.get(key), str) and bool(canonical.get(key)), f"canonical_stegcore.{key} required", errors)
    require(canonical.get("capability_registry_current_binding_commit") == canonical.get("task_conformance_merge_commit"), "current registry binding and task-conformance merge must share exact reconciled StegCore state", errors)

    partition = policy.get("authority_partition") if isinstance(policy.get("authority_partition"), dict) else {}
    require(partition.get("parallel_canonical_verifiers_compete") is False, "StegCore and organization conformance verifiers must be explicitly noncompeting", errors)

    registry = collect_registry_tasks()
    handoff_count = 0
    explicit_count = 0
    legacy_count = 0
    migration_required_count = 0
    task_conformant_count = 0

    for path in sorted((ROOT / "handoffs").glob("*.json")):
        handoff = load_json(path)
        if handoff.get("schema") != EXECUTABLE_SCHEMA:
            continue
        handoff_count += 1
        prefix = str(path.relative_to(ROOT))
        task = handoff.get("task") if isinstance(handoff.get("task"), dict) else {}
        task_id = task.get("task_id")
        require(isinstance(task_id, str) and bool(task_id), f"{prefix}: task_id required", errors)
        authority = handoff.get("authority") if isinstance(handoff.get("authority"), dict) else {}
        if "credential_authority" in authority:
            require(authority.get("credential_authority") == "TV/TVC", f"{prefix}: credential authority must be TV/TVC", errors)
        if "github_token_required" in authority:
            require(authority.get("github_token_required") is False, f"{prefix}: github_token_required must be false", errors)
        if "github_token_production_authority" in authority:
            require(authority.get("github_token_production_authority") in (False, "NONE"), f"{prefix}: GitHub production authority forbidden", errors)

        created = parse_time(handoff.get("created_at"))
        binding = handoff.get("admissible_existence")
        post_ae_cutover = bool(cutoff and created and created >= cutoff)
        post_task_cutover = bool(task_cutoff and created and created >= task_cutoff)

        if post_ae_cutover:
            require(binding is not None, f"{prefix}: post-policy handoff requires explicit admissible_existence binding", errors)
        if binding is not None:
            explicit_count += 1
            validate_binding(binding, prefix, policy, errors, require_task_conformance=post_task_cutover)
            if post_task_cutover:
                task_conformant_count += 1
            else:
                migration_required_count += 1
        else:
            legacy_count += 1
            migration_required_count += 1

        if isinstance(task_id, str) and task_id:
            reg = registry.get(task_id)
            require(reg is not None, f"{prefix}: executable handoff task missing from worker registry", errors)
            if reg is not None:
                reg_path, reg_task, reg_doc = reg
                require(reg_task.get("handoff_ref") == prefix, f"{reg_path}#{task_id}: handoff_ref does not bind exact handoff", errors)
                if reg_doc.get("credential_authority") is not None:
                    require(reg_doc.get("credential_authority") == "TV/TVC", f"{reg_path}: credential_authority must be TV/TVC", errors)
                if reg_doc.get("github_token_required") is not None:
                    require(reg_doc.get("github_token_required") is False, f"{reg_path}: github_token_required must be false", errors)
                reg_binding = reg_task.get("admissible_existence")
                if post_ae_cutover:
                    require(reg_binding is not None, f"{reg_path}#{task_id}: post-policy registry task requires admissible_existence binding", errors)
                if reg_binding is not None:
                    validate_binding(reg_binding, f"{reg_path}#{task_id}", policy, errors, require_task_conformance=post_task_cutover)
                    if isinstance(binding, dict):
                        for key in ("capability_id", "capability_version", "phase"):
                            require(reg_binding.get(key) == binding.get(key), f"{reg_path}#{task_id}: {key} must match handoff AE binding", errors)
                        if post_task_cutover:
                            for key in ("temporal_class", "task_relationship", "target_phase"):
                                require(reg_binding.get(key) == binding.get(key), f"{reg_path}#{task_id}: {key} must match handoff task-conformance binding", errors)

                if reg_task.get("state") in TERMINAL_TASK_STATES and isinstance(reg_binding, dict):
                    if reg_binding.get("phase") == "ACTIVATED":
                        require(bool(reg_binding.get("activation_proof_ref")), f"{reg_path}#{task_id}: completed task cannot imply ACTIVATED without proof", errors)

    for task_id, (reg_path, task, doc) in registry.items():
        binding = task.get("admissible_existence")
        if binding is not None:
            validate_binding(binding, f"{reg_path}#{task_id}", policy, errors, require_task_conformance=False)
        if doc.get("credential_authority") is not None:
            require(doc.get("credential_authority") == "TV/TVC", f"{reg_path}: credential_authority must be TV/TVC", errors)
        if doc.get("github_token_required") is not None:
            require(doc.get("github_token_required") is False, f"{reg_path}: github_token_required must be false", errors)

    # Issue #127 closes the legacy-continuation ambiguity without rewriting
    # immutable historical records. Every effective current/recent task must now
    # have an explicit retrospective classification; missing coverage is fatal.
    if validate_retrospective_conformance() != 0:
        errors.append("retrospective AE conformance classification failed")

    if errors:
        for error in errors:
            print(f"AE_CONTROL_PLANE_INVALID:{error}")
        return 1

    print(
        "AE_CONTROL_PLANE_VALIDATION_PASS "
        f"handoffs={handoff_count} registry_tasks={len(registry)} explicit_bindings={explicit_count} "
        f"legacy_projections={legacy_count} migration_required=0 retrospective_classified={len(registry)} "
        f"task_conformant={task_conformant_count} "
        f"stegcore_registry_binding={canonical['capability_registry_current_binding_commit']} "
        f"stegcore_task_conformance={canonical['task_conformance_merge_commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
