#!/usr/bin/env python3
"""Static fail-closed validation for the StegVerse Canonical Work Coordination System.

This validates source contracts only. It does not claim live Interlock/InTr task
admission, WorkerCoordinator execution ownership, Master Records reconciliation,
runtime-profile observation, or runtime closure.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_SCHEMA = ROOT / "schemas" / "canonical-task-record.schema.json"
RECON_SCHEMA = ROOT / "schemas" / "task-master-records-reconciliation.schema.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
POLICY = ROOT / "data" / "task-coordination-policy.json"
HANDOFF = ROOT / "docs" / "CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md"
WORKER_REGISTRY = ROOT / "control" / "worker-registry.json"
RUNTIME_MAP = ROOT / "control" / "runtime-profile-map.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_CLOSED: {message}")


OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = "python scripts/validate_canonical_work_coordination.py"
_TYPE_NAMES = {dict: "object", list: "array"}


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return _TYPE_NAMES.get(type(value), type(value).__name__)


def fail_malformed(source: str, field: str, expected: str, actual: str, row_owner: str | None = None) -> None:
    """Fail closed with the six-field record instead of raising a traceback."""
    owner = OWNING_GOAL if row_owner is None else f"{OWNING_GOAL} (row owner: {row_owner})"
    raise SystemExit(
        "\n".join(
            [
                f"FAIL_CLOSED: malformed field {field}: expected {expected}, got {actual}",
                "failure_code: CANONICAL_WORK_COORDINATION_MALFORMED_FIELD",
                f"failed_predicate: {field} must be a JSON {expected} ({source})",
                f"required_evidence_or_repair: repair {field} in {source} to a JSON {expected}; this validator does not modify data",
                f"retry_entrypoint: {RETRY_ENTRYPOINT}",
                f"owning_existing_goal: {owner}",
                "next_attempt: after the owning record is repaired, re-run retry_entrypoint",
            ]
        )
    )


def require_type(value: object, expected: type, source: str, field: str, row_owner: str | None = None) -> None:
    if not isinstance(value, expected):
        fail_malformed(source, field, _TYPE_NAMES[expected], _json_type(value), row_owner)


# Row fields this validator requires. Single source: the canonical task schema
# ``required`` list (schemas/canonical-task-record.schema.json). A field required
# here but absent from that list is allowed only as a declared discrepancy; it
# stays FAIL_CLOSED and is reported with its joint-discovery question until the
# question is answered (by amending the schema or this validator).
VALIDATOR_ROW_REQUIRED_FIELDS = ("task_id", "correlation_id", "worker_claim", "runtime_requirements")
DECLARED_SCHEMA_VALIDATOR_DISCREPANCIES = {
    "runtime_requirements": "Q-R-k",
}
DISCREPANCY_FAILURE_CODE = "CANONICAL_WORK_SCHEMA_VALIDATOR_REQUIRED_FIELD_DISCREPANCY"


def schema_row_required(task_schema: dict) -> tuple[set[str], dict[str, str]]:
    """Return (schema-required fields, active discrepancies) or fail closed."""
    schema_required = task_schema.get("required")
    require_type(schema_required, list, _rel(TASK_SCHEMA), "required")
    require(all(isinstance(f, str) for f in schema_required), "task schema required list must contain field names")
    required = set(schema_required)
    undeclared = [
        field for field in VALIDATOR_ROW_REQUIRED_FIELDS
        if field not in required and field not in DECLARED_SCHEMA_VALIDATOR_DISCREPANCIES
    ]
    require(not undeclared, f"validator requires row fields absent from task schema required list without a declared discrepancy: {undeclared}")
    active = {
        field: question for field, question in DECLARED_SCHEMA_VALIDATOR_DISCREPANCIES.items()
        if field not in required
    }
    return required, active


def schema_nested_required(task_props: dict, field: str) -> list[str]:
    """Nested required list for an object-typed row field, from the schema."""
    nested = task_props.get(field, {})
    require_type(nested, dict, _rel(TASK_SCHEMA), f"properties.{field}")
    nested_required = nested.get("required")
    require_type(nested_required, list, _rel(TASK_SCHEMA), f"properties.{field}.required")
    return list(nested_required)


def fail_discrepancy(task_id: str, field: str, question: str, message: str) -> None:
    """Schema/validator required-field discrepancy: FAIL_CLOSED with six fields."""
    raise SystemExit(
        "\n".join(
            [
                f"FAIL_CLOSED: {message}",
                f"failure_code: {DISCREPANCY_FAILURE_CODE}",
                (
                    f"failed_predicate: {field} is required by scripts/validate_canonical_work_coordination.py "
                    f"(VALIDATOR_ROW_REQUIRED_FIELDS) but not by schemas/canonical-task-record.schema.json required; row {task_id} lacks it"
                ),
                (
                    f"required_evidence_or_repair: answer {question}: either add {field} to the schema required list "
                    f"(with row values sourced from task owners) or remove it from VALIDATOR_ROW_REQUIRED_FIELDS; "
                    "this validator modifies neither data nor schema"
                ),
                f"retry_entrypoint: {RETRY_ENTRYPOINT}",
                f"owning_existing_goal: {OWNING_GOAL} (row owner: {task_id}); joint discovery question {question}",
                f"next_attempt: after {question} is answered, re-run retry_entrypoint",
            ]
        )
    )


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    try:
        return _main()
    except (AttributeError, TypeError, KeyError) as exc:
        # Backstop: any remaining malformed shape fails closed, never a traceback.
        fail_malformed("canonical work coordination sources", "unclassified field", "expected shape", f"{type(exc).__name__}: {exc}")
    return 1


def _main() -> int:
    task_schema = load_json(TASK_SCHEMA)
    recon_schema = load_json(RECON_SCHEMA)
    registry = load_json(REGISTRY)
    policy = load_json(POLICY)
    worker_registry = load_json(WORKER_REGISTRY)
    runtime_map = load_json(RUNTIME_MAP)
    handoff = HANDOFF.read_text(encoding="utf-8")
    for path, document in (
        (TASK_SCHEMA, task_schema),
        (RECON_SCHEMA, recon_schema),
        (REGISTRY, registry),
        (POLICY, policy),
        (WORKER_REGISTRY, worker_registry),
        (RUNTIME_MAP, runtime_map),
    ):
        require_type(document, dict, _rel(path), "<document root>")

    require(registry.get("schema") == "stegverse.canonical-task-registry/v1", "canonical registry schema missing")
    require(registry.get("authoritative_roles", {}).get("execution_claim_and_fence") == "control/worker-registry.json / WorkerCoordinator", "registry must reference WorkerCoordinator for claim/fence authority")
    require(registry.get("authoritative_roles", {}).get("observed_reality_and_reconstruction") == "ORGANIZATION_LEDGER_FOR_OBSERVED_REALITY; MASTER_RECORDS_RECONSTRUCTION_ONLY", "organization-ledger reality / Master Records reconstruction boundary missing")
    require(registry.get("authoritative_roles", {}).get("governed_task_ingress_egress") == "INTERLOCK_INTR", "Interlock/InTr ingress-egress authority missing")

    task_props = task_schema.get("properties", {})
    _schema_required, active_discrepancies = schema_row_required(task_schema)
    runtime_requirement_fields = schema_nested_required(task_props, "runtime_requirements")
    runtime_requirement_props = task_props["runtime_requirements"].get("properties", {})
    for field in runtime_requirement_fields:
        if field == "capabilities":
            continue
        require(
            runtime_requirement_props.get(field, {}).get("type") == "boolean",
            f"task schema runtime_requirements.{field} type is not supported by this validator",
        )
    authority_props = task_props.get("authority_model", {}).get("properties", {})
    require(authority_props.get("task_registry_mints_execution_authority", {}).get("const") is False, "task schema must deny registry execution authority")
    require(authority_props.get("worker_claim_authority", {}).get("const") == "WORKERCOORDINATOR", "task schema must bind WorkerCoordinator claim authority")
    require(authority_props.get("master_records_reality_authority", {}).get("const") is False, "task schema must deny Master Records reality authority")

    runtime_resolution_props = task_props.get("runtime_resolution", {}).get("properties", {})
    require(runtime_resolution_props.get("projection_only", {}).get("const") is True, "runtime resolution must be projection-only")
    require(runtime_resolution_props.get("selection_grants_authority", {}).get("const") is False, "runtime resolution must deny selection authority")

    recon_states = set(recon_schema.get("properties", {}).get("state", {}).get("enum", []))
    expected_states = {"CONSISTENT", "TASK_AHEAD_OF_EVIDENCE", "REALITY_AHEAD_OF_TASK", "CONFLICT", "UNKNOWN", "ORPHANED_EVENT"}
    require(recon_states == expected_states, "reconciliation states are incomplete or drifted")

    invariants = set(policy.get("invariants", []))
    for invariant in {
        "ONE_CANONICAL_WORK_TRUTH_MANY_PROJECTIONS",
        "TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY",
        "WORKERCOORDINATOR_OWNS_EXECUTION_CLAIM_AND_FENCE",
        "ORGANIZATION_LEDGER_OWNS_OBSERVED_REALITY_MASTER_RECORDS_RECONSTRUCTION_ONLY",
        "RUNTIME_PROFILE_MAP_IS_DISCOVERY_AND_COMPATIBILITY_PROJECTION_ONLY",
        "RUNTIME_PROFILE_MATCH_DOES_NOT_GRANT_TASK_ADMISSION_OR_EXECUTION_AUTHORITY",
        "COMPLETION_CLAIM_REQUIRES_RECONCILIATION_BEFORE_CLOSURE",
        "MISSING_EVIDENCE_IS_NOT_PROOF_OF_NON_OCCURRENCE",
        "HANDOFFS_ARE_PROJECTIONS_NOT_INDEPENDENT_TRUTH",
    }:
        require(invariant in invariants, f"missing coordination invariant: {invariant}")

    runtime_discovery = policy.get("runtime_profile_map", {})
    require(runtime_discovery.get("ref") == "control/runtime-profile-map.json", "canonical runtime map policy binding missing")
    require(runtime_discovery.get("capability_match_grants_authority") is False, "runtime profile match must not grant authority")
    require(runtime_discovery.get("workercoordinator_admission_still_required") is True, "WorkerCoordinator admission must remain required")
    require(runtime_discovery.get("interlock_intr_transition_admission_still_required") is True, "Interlock/InTr transition admission must remain required")

    require(isinstance(worker_registry.get("tasks"), list), "existing WorkerCoordinator registry tasks missing")
    require(worker_registry.get("schema") == "stegverse.heartbeat-worker-registry/v0.1", "unexpected WorkerCoordinator registry schema")
    require(runtime_map.get("schema") == "stegverse.runtime-profile-map/v1", "runtime profile map schema missing")
    require(runtime_map.get("authority", {}).get("map_grants_execution_authority") is False, "runtime map cannot grant execution authority")
    require(runtime_map.get("authority", {}).get("capability_match_grants_authority") is False, "runtime map match cannot grant authority")

    task_ids: set[str] = set()
    correlation_ids: set[str] = set()
    tasks = registry.get("tasks", [])
    require_type(tasks, list, _rel(REGISTRY), "tasks")
    for index, task in enumerate(tasks):
        require_type(task, dict, _rel(REGISTRY), f"tasks[{index}]")
        task_id = task.get("task_id")
        correlation_id = task.get("correlation_id")
        require(isinstance(task_id, str) and task_id, "task_id missing")
        require(isinstance(correlation_id, str) and correlation_id, f"correlation_id missing for {task_id}")
        require(task_id not in task_ids, f"duplicate task_id: {task_id}")
        task_ids.add(task_id)
        correlation_ids.add(correlation_id)

        claim = task.get("worker_claim", {})
        require_type(claim, dict, _rel(REGISTRY), f"tasks[{task_id}].worker_claim", task_id)
        require(claim.get("authority") == "WORKERCOORDINATOR", f"{task_id}: claim authority drift")
        require(claim.get("projection_only") is True, f"{task_id}: registry claim must be projection-only")

        requirements = task.get("runtime_requirements")
        if not isinstance(requirements, dict) and "runtime_requirements" in active_discrepancies:
            fail_discrepancy(task_id, "runtime_requirements", active_discrepancies["runtime_requirements"],
                             f"{task_id}: runtime requirements missing")
        require(isinstance(requirements, dict), f"{task_id}: runtime requirements missing")
        if "capabilities" in runtime_requirement_fields:
            require(isinstance(requirements.get("capabilities"), list), f"{task_id}: runtime capabilities missing")
        for flag in runtime_requirement_fields:
            if flag == "capabilities":
                continue
            require(isinstance(requirements.get(flag), bool), f"{task_id}: runtime requirement {flag} must be boolean")

        resolution = task.get("runtime_resolution")
        if resolution is not None:
            require_type(resolution, dict, _rel(REGISTRY), f"tasks[{task_id}].runtime_resolution", task_id)
            require(resolution.get("projection_only") is True, f"{task_id}: runtime resolution not projection-only")
            require(resolution.get("selection_grants_authority") is False, f"{task_id}: runtime resolution grants authority")
            require(resolution.get("map_generation") == runtime_map.get("generation"), f"{task_id}: stale runtime-map generation projection")
            profiles = runtime_map.get("profiles", [])
            require_type(profiles, list, _rel(RUNTIME_MAP), "profiles")
            for p_index, profile in enumerate(profiles):
                require_type(profile, dict, _rel(RUNTIME_MAP), f"profiles[{p_index}]")
            known_profiles = {p.get("profile_id") for p in profiles}
            candidate_ids = resolution.get("candidate_profile_ids", [])
            require_type(candidate_ids, list, _rel(REGISTRY), f"tasks[{task_id}].runtime_resolution.candidate_profile_ids", task_id)
            require(set(candidate_ids).issubset(known_profiles), f"{task_id}: runtime resolution references unknown profile")

        completion = task.get("completion", {})
        require_type(completion, dict, _rel(REGISTRY), f"tasks[{task_id}].completion", task_id)
        state = task.get("coordination_state")
        if state == "CLOSED":
            require(completion.get("claimed") is True, f"{task_id}: CLOSED without completion claim")
            require(completion.get("validated") is True, f"{task_id}: CLOSED without validated completion")
            require(bool(completion.get("reconciliation_ref")), f"{task_id}: CLOSED without reconciliation reference")

        for list_field in ("blockers", "dependencies"):
            items = task.get(list_field, [])
            require_type(items, list, _rel(REGISTRY), f"tasks[{task_id}].{list_field}", task_id)
            for i_index, item in enumerate(items):
                require_type(item, dict, _rel(REGISTRY), f"tasks[{task_id}].{list_field}[{i_index}]", task_id)
        blocker_dependency_ids = {item.get("dependency_id") for item in task.get("blockers", [])}
        dependency_ids = {item.get("dependency_id") for item in task.get("dependencies", [])}
        require(blocker_dependency_ids.issubset(dependency_ids), f"{task_id}: blocker references non-existent dependency")

    required_handoff_phrases = [
        "one canonical work truth and many projections",
        "WorkerCoordinator remains authoritative for executable claim/fence ownership",
        "Task Registry and Master Records are intentionally comparable but not interchangeable",
        "A human action is represented once as a canonical dependency object",
        "Handoffs become projections of canonical coordination state",
    ]
    handoff_lower = handoff.lower()
    for phrase in required_handoff_phrases:
        require(phrase.lower() in handoff_lower, f"handoff missing required statement: {phrase}")

    print("PASS: canonical work coordination source contract is internally consistent")
    print(f"INFO: canonical task records={len(task_ids)} correlations={len(correlation_ids)}")
    print(f"INFO: existing WorkerCoordinator task records={len(worker_registry.get('tasks', []))}")
    print(f"INFO: runtime profile map profiles={len(runtime_map.get('profiles', []))} generation={runtime_map.get('generation')}")
    print("NONCLAIM: live Interlock/InTr, WorkerCoordinator, runtime-profile observation, Master Records organization-record reconciliation, and InTr closure are not proven")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
