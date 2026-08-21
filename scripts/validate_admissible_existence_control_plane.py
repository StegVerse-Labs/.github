#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_ae_retrospective_conformance import main as validate_retrospective_conformance

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "control" / "admissible-existence-control-plane-policy.json"
RETROSPECTIVE_PATH = ROOT / "control" / "admissible-existence-retrospective-conformance.json"
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


def has_task_conformance_contract(binding: Any, policy: dict[str, Any]) -> bool:
    if not isinstance(binding, dict):
        return False
    keys = policy["future_binding_contract"]["post_task_conformance_required_keys"]
    return all(key in binding for key in keys)


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
            require(
                key in binding,
                f"{prefix}: admissible_existence.{key} required by current task-conformance contract",
                errors,
            )
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
        require(
            isinstance(binding.get("activation_proof_ref"), str) and bool(binding.get("activation_proof_ref")),
            f"{prefix}: activation proof required for activated lineage",
            errors,
        )
    if phase == "ACTIVATED":
        require(not binding.get("blockers"), f"{prefix}: ACTIVATED may not retain blockers", errors)
    if phase == "ADMISSIBLE" and binding.get("blockers"):
        require(
            isinstance(binding.get("continuation_owner"), str) and bool(binding.get("continuation_owner")),
            f"{prefix}: blocked ADMISSIBLE requires continuation_owner",
            errors,
        )
    if require_task_conformance:
        temporal_class = binding.get("temporal_class")
        relationship = binding.get("task_relationship")
        target_phase = binding.get("target_phase")
        require(temporal_class in policy["temporal_classes"], f"{prefix}: invalid temporal_class {temporal_class}", errors)
        require(relationship in policy["task_relationships"], f"{prefix}: invalid task_relationship {relationship}", errors)
        require(target_phase in policy["phases"], f"{prefix}: invalid target_phase {target_phase}", errors)
        if temporal_class == "recently_completed":
            retained = (
                list(binding.get("standing_evidence_refs") or [])
                + list(binding.get("admissibility_evidence_refs") or [])
                + list(binding.get("integration_evidence_refs") or [])
            )
            require(bool(retained), f"{prefix}: recently_completed requires retained phase evidence", errors)
        elif temporal_class == "current":
            require(
                isinstance(binding.get("continuation_owner"), str) and bool(binding.get("continuation_owner")),
                f"{prefix}: current task requires continuation_owner",
                errors,
            )
        elif temporal_class == "future":
            require(target_phase is not None, f"{prefix}: future task requires target_phase", errors)
            require(relationship is not None, f"{prefix}: future task requires task_relationship", errors)
            require(
                binding.get("activation_proof_ref") in (None, ""),
                f"{prefix}: future task may not self-claim activation proof",
                errors,
            )
    known_phase = policy.get("known_capability_phase_snapshot", {}).get(binding.get("capability_id"))
    if known_phase is not None:
        require(
            phase == known_phase,
            f"{prefix}: phase {phase} diverges from canonical known capability phase {known_phase}",
            errors,
        )


def load_none_impact_projections(policy: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    document = load_json(RETROSPECTIVE_PATH)
    require(
        document.get("schema") == "stegverse.admissible-existence-retrospective-conformance/v1",
        "retrospective AE projection schema invalid",
        errors,
    )
    projections: dict[str, dict[str, Any]] = {}
    for entry in document.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        task_id = entry.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        if entry.get("ae_impact") == "NONE":
            projections[task_id] = entry
    return projections


def validate_none_impact_projection(
    projection: dict[str, Any],
    task_id: str,
    prefix: str,
    policy: dict[str, Any],
    errors: list[str],
) -> None:
    required = policy["future_binding_contract"]["none_impact_required_projection_keys"]
    for key in required:
        require(key in projection, f"{prefix}#{task_id}: NONE-impact projection missing {key}", errors)
    require(projection.get("task_id") == task_id, f"{prefix}#{task_id}: NONE-impact task_id mismatch", errors)
    require(projection.get("ae_impact") == "NONE", f"{prefix}#{task_id}: NONE-impact projection must declare NONE", errors)
    require(
        projection.get("temporal_class") in policy["temporal_classes"],
        f"{prefix}#{task_id}: invalid NONE-impact temporal_class {projection.get('temporal_class')}",
        errors,
    )
    require(
        projection.get("task_relationship") in policy["task_relationships"],
        f"{prefix}#{task_id}: invalid NONE-impact task_relationship {projection.get('task_relationship')}",
        errors,
    )
    require(
        projection.get("result") in policy["none_impact_projection"]["allowed_results"],
        f"{prefix}#{task_id}: invalid NONE-impact result {projection.get('result')}",
        errors,
    )
    require(
        isinstance(projection.get("rationale"), str) and bool(projection.get("rationale")),
        f"{prefix}#{task_id}: ae_impact NONE requires rationale",
        errors,
    )
    if projection.get("temporal_class") == "current":
        require(
            isinstance(projection.get("continuation_owner"), str) and bool(projection.get("continuation_owner")),
            f"{prefix}#{task_id}: current NONE-impact task requires continuation_owner",
            errors,
        )
    require(
        projection.get("phase") in (None, ""),
        f"{prefix}#{task_id}: ae_impact NONE may not claim capability phase {projection.get('phase')}",
        errors,
    )
    require(
        projection.get("capability_id") in (None, ""),
        f"{prefix}#{task_id}: ae_impact NONE may not claim capability_id",
        errors,
    )


def validate_stale_binding_on_none_task(
    binding: Any,
    task_id: str,
    prefix: str,
    errors: list[str],
    reconciliations: list[str],
) -> None:
    if binding is None:
        return
    require(isinstance(binding, dict), f"{prefix}#{task_id}: stale NONE-impact binding must be object", errors)
    if not isinstance(binding, dict):
        return
    require(
        binding.get("credential_authority") in (None, "TV/TVC"),
        f"{prefix}#{task_id}: stale binding credential authority must remain TV/TVC",
        errors,
    )
    require(
        binding.get("github_token_runtime_authority") in (None, False),
        f"{prefix}#{task_id}: stale binding may not grant GitHub runtime authority",
        errors,
    )
    require(
        binding.get("phase") != "ACTIVATED",
        f"{prefix}#{task_id}: NONE-impact task may not retain an ACTIVATED capability binding",
        errors,
    )
    require(
        binding.get("activation_proof_ref") in (None, ""),
        f"{prefix}#{task_id}: NONE-impact task may not retain activation proof",
        errors,
    )
    reconciliations.append(
        f"{prefix}#{task_id}: repository-specific capability-shaped binding is superseded for organization conformance by explicit ae_impact=NONE projection; owner-side metadata reconciliation remains required"
    )


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
            if isinstance(task_id, str) and task_id:
                found[task_id] = (str(path.relative_to(ROOT)), task, doc)
    return found


def main() -> int:
    policy = load_json(POLICY_PATH)
    errors: list[str] = []
    reconciliations: list[str] = []
    require(policy.get("schema") == "stegverse.admissible-existence-control-plane-policy/v1", "policy schema invalid", errors)
    require(policy.get("policy_version") == "1.2.0", "policy must be reconciled to continuation-conformance version 1.2.0", errors)
    require(policy.get("credential_authority") == "TV/TVC", "policy credential authority must be TV/TVC", errors)
    require(policy.get("github_token_runtime_authority") is False, "policy GitHub runtime authority must be false", errors)
    require(policy.get("ae_impacts") == ["CAPABILITY", "NONE"], "policy must support canonical CAPABILITY/NONE AE impact classes", errors)
    cutoff = parse_time(policy.get("effective_at"))
    task_cutoff = parse_time(policy.get("task_conformance_effective_at"))
    require(cutoff is not None, "policy effective_at invalid", errors)
    require(task_cutoff is not None, "policy task_conformance_effective_at invalid", errors)
    canonical = policy.get("canonical_stegcore") if isinstance(policy.get("canonical_stegcore"), dict) else {}
    for key in (
        "capability_model_origin_commit",
        "capability_registry_origin_commit",
        "capability_registry_current_binding_commit",
        "task_conformance_merge_commit",
        "capability_handoff_current_commit",
        "task_conformance_handoff",
        "task_conformance_manifest",
        "task_conformance_verifier",
        "continuation_conformance_release_commit",
        "continuation_conformance_handoff",
        "continuation_conformance_policy",
        "continuation_conformance_verifier",
    ):
        require(isinstance(canonical.get(key), str) and bool(canonical.get(key)), f"canonical_stegcore.{key} required", errors)
    require(
        canonical.get("capability_registry_current_binding_commit") == canonical.get("task_conformance_merge_commit"),
        "current registry binding and task-conformance merge must share exact reconciled StegCore state",
        errors,
    )
    require(
        canonical.get("continuation_conformance_release_commit") == "78d00ca0e977af3e666c2acec431b111aea0deef",
        "canonical StegCore continuation-conformance release binding drifted",
        errors,
    )
    partition = policy.get("authority_partition") if isinstance(policy.get("authority_partition"), dict) else {}
    require(
        partition.get("parallel_canonical_verifiers_compete") is False,
        "StegCore and organization conformance verifiers must be explicitly noncompeting",
        errors,
    )

    none_projections = load_none_impact_projections(policy, errors)
    registry = collect_registry_tasks()
    handoff_count = 0
    explicit_count = 0
    none_impact_count = 0
    legacy_count = 0
    migration_required_count = 0
    task_conformant_count = 0
    explicitly_migrated_count = 0

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
            require(
                authority.get("github_token_production_authority") in (False, "NONE"),
                f"{prefix}: GitHub production authority forbidden",
                errors,
            )

        created = parse_time(handoff.get("created_at"))
        binding = handoff.get("admissible_existence")
        post_ae_cutover = bool(cutoff and created and created >= cutoff)
        post_task_cutover = bool(task_cutoff and created and created >= task_cutoff)
        explicit_task_migration = has_task_conformance_contract(binding, policy)
        task_contract_required = post_task_cutover or explicit_task_migration
        projection = none_projections.get(task_id) if isinstance(task_id, str) else None

        if projection is not None:
            none_impact_count += 1
            validate_none_impact_projection(projection, str(task_id), prefix, policy, errors)
            validate_stale_binding_on_none_task(binding, str(task_id), prefix, errors, reconciliations)
            task_conformant_count += 1
        else:
            if post_ae_cutover:
                require(binding is not None, f"{prefix}: post-policy capability-impacting handoff requires explicit admissible_existence binding", errors)
            if binding is not None:
                explicit_count += 1
                validate_binding(binding, prefix, policy, errors, require_task_conformance=task_contract_required)
                if task_contract_required:
                    task_conformant_count += 1
                    if not post_task_cutover:
                        explicitly_migrated_count += 1
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

                if projection is not None:
                    validate_none_impact_projection(projection, task_id, reg_path, policy, errors)
                    validate_stale_binding_on_none_task(reg_binding, task_id, reg_path, errors, reconciliations)
                else:
                    if post_ae_cutover:
                        require(reg_binding is not None, f"{reg_path}#{task_id}: post-policy capability-impacting registry task requires admissible_existence binding", errors)
                    if task_contract_required:
                        require(reg_binding is not None, f"{reg_path}#{task_id}: current/migrated capability task requires admissible_existence binding", errors)
                    if reg_binding is not None:
                        validate_binding(
                            reg_binding,
                            f"{reg_path}#{task_id}",
                            policy,
                            errors,
                            require_task_conformance=task_contract_required,
                        )
                        if isinstance(binding, dict):
                            for key in ("capability_id", "capability_version", "phase"):
                                require(
                                    reg_binding.get(key) == binding.get(key),
                                    f"{reg_path}#{task_id}: {key} must match handoff AE binding",
                                    errors,
                                )
                            if task_contract_required:
                                for key in ("temporal_class", "task_relationship", "target_phase"):
                                    require(
                                        reg_binding.get(key) == binding.get(key),
                                        f"{reg_path}#{task_id}: {key} must match handoff task-conformance binding",
                                        errors,
                                    )
                if (
                    reg_task.get("state") in TERMINAL_TASK_STATES
                    and isinstance(reg_binding, dict)
                    and reg_binding.get("phase") == "ACTIVATED"
                ):
                    require(
                        bool(reg_binding.get("activation_proof_ref")),
                        f"{reg_path}#{task_id}: completed task cannot imply ACTIVATED without proof",
                        errors,
                    )

    for task_id, (reg_path, task, doc) in registry.items():
        projection = none_projections.get(task_id)
        binding = task.get("admissible_existence")
        if projection is not None:
            validate_none_impact_projection(projection, task_id, reg_path, policy, errors)
            validate_stale_binding_on_none_task(binding, task_id, reg_path, errors, reconciliations)
        elif binding is not None:
            validate_binding(
                binding,
                f"{reg_path}#{task_id}",
                policy,
                errors,
                require_task_conformance=has_task_conformance_contract(binding, policy),
            )
        if doc.get("credential_authority") is not None:
            require(doc.get("credential_authority") == "TV/TVC", f"{reg_path}: credential_authority must be TV/TVC", errors)
        if doc.get("github_token_required") is not None:
            require(doc.get("github_token_required") is False, f"{reg_path}: github_token_required must be false", errors)

    if validate_retrospective_conformance() != 0:
        errors.append("retrospective AE conformance classification failed")
    if errors:
        for error in errors:
            print(f"AE_CONTROL_PLANE_INVALID:{error}")
        return 1

    for reconciliation in sorted(set(reconciliations)):
        print(f"AE_CONTROL_PLANE_RECONCILIATION_REQUIRED:{reconciliation}")
    print(
        "AE_CONTROL_PLANE_VALIDATION_PASS "
        f"handoffs={handoff_count} registry_tasks={len(registry)} explicit_bindings={explicit_count} "
        f"none_impact_projections={none_impact_count} legacy_projections={legacy_count} "
        f"migration_required={migration_required_count} task_conformant={task_conformant_count} "
        f"explicitly_migrated={explicitly_migrated_count} retrospective_classified={len(registry)} "
        f"stegcore_registry_binding={canonical['capability_registry_current_binding_commit']} "
        f"stegcore_task_conformance={canonical['task_conformance_merge_commit']} "
        f"stegcore_continuation_conformance={canonical['continuation_conformance_release_commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
