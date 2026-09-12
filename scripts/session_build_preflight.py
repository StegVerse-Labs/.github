#!/usr/bin/env python3
"""Canonical StegVerse session/build pre-work entrypoint backed by StegIndex, coordination, and canonical policy context."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "stegindex_preflight_gate.py"
COORDINATION_LEDGER = ROOT / "control" / "cross-task-coordination.json"
COORDINATION_FRAGMENTS = ROOT / "control" / "cross-task-coordination.d"
POLICY_CONTEXT_REGISTRY = ROOT / "control" / "canonical-policy-context-registry.json"
CANONICAL_TASK_RECORDS = ROOT / "data" / "canonical-task-records"
EXPECTED_COORDINATION_AUTHORITY = "NONE_INDEX_PROJECTION_ONLY"
EXPECTED_POLICY_AUTHORITY = "NONE_PREWORK_INTERPRETATION_ONLY"

EXIT_READY = 0
EXIT_EXACT_DEPENDENCY = 2
EXIT_CONTINUE_MACHINE = 3


def run_preflight(goal: str, stegindex_root: str | None, contribution_class: str | None):
    cmd = [sys.executable, str(GATE), "--query", goal]
    if stegindex_root:
        cmd += ["--stegindex-root", stegindex_root]
    if contribution_class:
        cmd += ["--contribution-class", contribution_class]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "StegIndex gate failed")
    return json.loads(proc.stdout)


def run_coordination_projection(stegindex_root: str | None, *, task_id: str | None = None, predicate_id: str | None = None) -> dict:
    if not stegindex_root:
        return {"state": "STEGINDEX_ROOT_NOT_DECLARED", "coordination_consulted": False, "exact_dependency": "STEGINDEX_ROOT, STEGVERSE_REPO_ROOTS_JSON, or --stegindex-root", "authority_effect": "NONE"}
    entry = Path(stegindex_root).expanduser().resolve() / "scripts" / "resolve_cross_task_coordination.py"
    if not entry.is_file():
        return {"state": "COORDINATION_RESOLVER_UNAVAILABLE", "coordination_consulted": False, "exact_dependency": str(entry), "authority_effect": "NONE"}
    if not COORDINATION_LEDGER.is_file():
        return {"state": "COORDINATION_LEDGER_UNAVAILABLE", "coordination_consulted": False, "exact_dependency": str(COORDINATION_LEDGER), "authority_effect": "NONE"}

    cmd = [sys.executable, str(entry), "--ledger", str(COORDINATION_LEDGER), "--fragments-dir", str(COORDINATION_FRAGMENTS)]
    if task_id:
        cmd += ["--task-id", task_id]
    if predicate_id:
        cmd += ["--predicate-id", predicate_id]
    proc = subprocess.run(cmd, cwd=Path(stegindex_root), text=True, capture_output=True)
    if proc.returncode != 0:
        return {"state": "COORDINATION_RESOLUTION_FAILED", "coordination_consulted": False, "exact_dependency": proc.stderr.strip() or proc.stdout.strip() or "cross-task coordination projection", "authority_effect": "NONE"}
    projection = json.loads(proc.stdout)
    if projection.get("authority_effect") != EXPECTED_COORDINATION_AUTHORITY:
        raise RuntimeError("cross-task coordination authority invariant violation")
    return {
        "state": "RESOLVED",
        "coordination_consulted": True,
        "task_filter": task_id,
        "predicate_filter": predicate_id,
        "source_fragment_ids": projection.get("source_fragment_ids", []),
        "related_active_claims": projection.get("related_active_claims", []),
        "foreign_active_claims": projection.get("foreign_active_claims", []),
        "gaps": projection.get("gaps", []),
        "predicate_dependency_relationships": projection.get("predicate_dependency_relationships", []),
        "dependency_readiness_inferred": False,
        "candidate_consumer_execution_admission_inferred": False,
        "runtime_truth_inferred": False,
        "authority_effect": "NONE",
    }


def _local_policy_path(ref: str) -> Path | None:
    value = str(ref or "").strip()
    if not value:
        return None
    if ":" in value and not value.startswith(("./", "../")):
        repo, _, path = value.partition(":")
        if "/" in repo and path:
            if repo == "StegVerse-Labs/.github":
                return ROOT / path
            return None
    return ROOT / value


def resolve_canonical_policy_context(*, task_id: str | None, explicit_refs: list[str]) -> tuple[dict, bool]:
    """Resolve canonical interpretation policy before session inference; never infer runtime truth or authority."""
    if not POLICY_CONTEXT_REGISTRY.is_file():
        return {
            "state": "POLICY_CONTEXT_REGISTRY_UNAVAILABLE",
            "resolved": False,
            "exact_dependency": str(POLICY_CONTEXT_REGISTRY),
            "authority_effect": "NONE",
        }, False

    registry = json.loads(POLICY_CONTEXT_REGISTRY.read_text(encoding="utf-8"))
    if registry.get("authority_effect") != EXPECTED_POLICY_AUTHORITY:
        raise RuntimeError("canonical policy context authority invariant violation")

    refs: list[dict] = []
    unresolved: list[str] = []
    for row in registry.get("required_global_sources", []):
        ref = str(row.get("ref") or "").strip()
        if not ref:
            continue
        refs.append({"ref": ref, "source": "GLOBAL_REQUIRED", "required": bool(row.get("required", True))})

    task_record_ref = None
    if task_id:
        candidate = CANONICAL_TASK_RECORDS / f"{task_id}.json"
        if candidate.is_file():
            task_record_ref = str(candidate.relative_to(ROOT))
            record = json.loads(candidate.read_text(encoding="utf-8"))
            for ref in record.get("canonical_policy_refs", []):
                refs.append({"ref": str(ref), "source": "CANONICAL_TASK_RECORD", "required": True})

    for ref in explicit_refs:
        value = str(ref or "").strip()
        if value:
            refs.append({"ref": value, "source": "EXPLICIT", "required": True})

    deduped: list[dict] = []
    seen: set[str] = set()
    for row in refs:
        ref = row["ref"]
        if ref in seen:
            continue
        seen.add(ref)
        local = _local_policy_path(ref)
        exists = bool(local and local.is_file())
        resolved = exists
        if row.get("required") and not resolved:
            unresolved.append(ref)
        deduped.append({
            **row,
            "local_path": str(local.relative_to(ROOT)) if local and local.is_file() else None,
            "resolved": resolved,
        })

    complete = not unresolved
    return {
        "state": "RESOLVED" if complete else "CANONICAL_POLICY_DEPENDENCY_UNRESOLVED",
        "resolved": complete,
        "registry_ref": str(POLICY_CONTEXT_REGISTRY.relative_to(ROOT)),
        "task_record_ref": task_record_ref,
        "policy_refs": deduped,
        "unresolved_policy_refs": unresolved,
        "interpretation_guards": registry.get("interpretation_guards", []),
        "known_global_invariants": registry.get("known_global_invariants_resolved_from_task_coordination_policy", []),
        "human_policy_restatement_required": False,
        "runtime_truth_inferred": False,
        "execution_authority_inferred": False,
        "transition_authority_inferred": False,
        "credential_authority_inferred": False,
        "authority_effect": "NONE",
    }, complete


def evaluate_readme_impact(*, required: bool, material: str | None, readme_updated: bool, readme_path: str | None, no_update_reason: str | None, evidence_refs: list[str]) -> tuple[dict, bool]:
    """Fail closed on README completeness for declared functional mutation."""
    evidence = [str(item).strip() for item in evidence_refs if str(item).strip()]
    if not required:
        return {
            "required": False,
            "declared": False,
            "material_function_change": None,
            "disposition": "LEGACY_OR_NONFUNCTIONAL_GATE_NOT_REQUIRED",
            "authority_effect": "NONE",
        }, True

    if material is None:
        return {
            "required": True,
            "declared": False,
            "material_function_change": None,
            "disposition": "MATERIALITY_UNDECLARED",
            "authority_effect": "NONE",
        }, False

    is_material = material == "true"
    path = str(readme_path or "").strip()
    reason = str(no_update_reason or "").strip()
    if is_material:
        complete = bool(readme_updated and path and evidence)
        disposition = "README_UPDATED_FOR_MATERIAL_FUNCTION_CHANGE" if complete else "MATERIAL_FUNCTION_CHANGE_REQUIRES_README_UPDATE"
    else:
        complete = bool(reason and evidence)
        disposition = "NONMATERIAL_CHANGE_EVIDENCE_SUPPORTED" if complete else "NONMATERIAL_DETERMINATION_REQUIRES_REASON_AND_EVIDENCE"
    return {
        "required": True,
        "declared": True,
        "material_function_change": is_material,
        "readme_path": path or None,
        "readme_updated_in_change_set": bool(readme_updated),
        "no_readme_update_reason": reason or None,
        "evidence_refs": evidence,
        "disposition": disposition,
        "authority_effect": "NONE",
    }, complete


def evaluate_behavioral_parity(*, required: bool, superseded_ref: str | None, predicates: list[str], evidence_refs: list[str], authorized_delta_refs: list[str]) -> tuple[dict, bool]:
    """Fail closed when migration/replacement work drops prior behavior without an explicit canonical decision."""
    predicate_rows = [str(item).strip() for item in predicates if str(item).strip()]
    evidence = [str(item).strip() for item in evidence_refs if str(item).strip()]
    deltas = [str(item).strip() for item in authorized_delta_refs if str(item).strip()]
    source = str(superseded_ref or "").strip()

    if not required:
        return {
            "required": False,
            "superseded_capability_ref": source or None,
            "disposition": "NOT_A_MIGRATION_OR_REPLACEMENT",
            "authority_effect": "NONE",
        }, True

    complete = bool(source and predicate_rows and evidence)
    disposition = "BEHAVIORAL_PARITY_EVIDENCED" if complete else "BEHAVIORAL_PARITY_EVIDENCE_REQUIRED"
    return {
        "required": True,
        "superseded_capability_ref": source or None,
        "preserved_behavior_predicates": predicate_rows,
        "evidence_refs": evidence,
        "authorized_behavior_delta_refs": deltas,
        "unauthorized_behavior_loss_allowed": False,
        "behavior_delta_requires_explicit_canonical_decision": True,
        "disposition": disposition,
        "authority_effect": "NONE_COMPLETENESS_ONLY",
    }, complete


def decide(result: dict, coordination: dict):
    decision = result.get("decision")
    if decision == "CONTINUE_MACHINE_EXECUTION":
        return "CONTINUE_THROUGH_CANONICAL_OWNER", EXIT_CONTINUE_MACHINE, False
    if decision == "REUSE_OR_EXTEND_EXISTING":
        return "REUSE_EXISTING_CAPABILITY", EXIT_READY, False
    if decision == "NO_EXISTING_CAPABILITY_MATCH":
        if not coordination.get("coordination_consulted"):
            return "STOP_AT_COORDINATION_DEPENDENCY", EXIT_EXACT_DEPENDENCY, False
        return "NEW_WORK_MAY_BE_CONSIDERED", EXIT_READY, True
    if decision == "EXACT_BLOCKER_ONLY":
        return "STOP_AT_EXACT_DEPENDENCY", EXIT_EXACT_DEPENDENCY, False
    raise RuntimeError(f"unsupported StegIndex decision: {decision}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", required=True)
    parser.add_argument("--contribution-class")
    parser.add_argument("--coordination-task-id")
    parser.add_argument("--coordination-predicate-id")
    parser.add_argument("--canonical-policy-ref", action="append", default=[], help="Additional already-canonical policy source that must be resolvable before interpretation.")
    parser.add_argument("--readme-impact-required", action="store_true", help="Declare that this pre-work request may produce functional mutation and therefore requires README-impact completeness review.")
    parser.add_argument("--material-function-change", choices=("true", "false"))
    parser.add_argument("--readme-updated-in-change-set", action="store_true")
    parser.add_argument("--readme-path")
    parser.add_argument("--no-readme-update-reason")
    parser.add_argument("--readme-evidence-ref", action="append", default=[])
    parser.add_argument("--behavioral-parity-required", action="store_true", help="Require preserved behavior evidence for a migration, refactor, replacement, or native-port of an existing capability.")
    parser.add_argument("--superseded-capability-ref")
    parser.add_argument("--preserved-behavior-predicate", action="append", default=[])
    parser.add_argument("--behavioral-parity-evidence-ref", action="append", default=[])
    parser.add_argument("--authorized-behavior-delta-ref", action="append", default=[])
    parser.add_argument("--stegindex-root", default=os.environ.get("STEGINDEX_ROOT"), help="Already-materialized StegIndex checkout. No network fetch is performed.")
    args = parser.parse_args()

    preflight = run_preflight(args.goal, args.stegindex_root, args.contribution_class)
    coordination = run_coordination_projection(args.stegindex_root, task_id=args.coordination_task_id, predicate_id=args.coordination_predicate_id)
    policy_context, policy_context_complete = resolve_canonical_policy_context(
        task_id=args.coordination_task_id,
        explicit_refs=args.canonical_policy_ref,
    )
    disposition, exit_code, task_creation_permitted = decide(preflight, coordination)
    readme_impact, readme_impact_complete = evaluate_readme_impact(
        required=args.readme_impact_required,
        material=args.material_function_change,
        readme_updated=args.readme_updated_in_change_set,
        readme_path=args.readme_path,
        no_update_reason=args.no_readme_update_reason,
        evidence_refs=args.readme_evidence_ref,
    )
    behavioral_parity, behavioral_parity_complete = evaluate_behavioral_parity(
        required=args.behavioral_parity_required,
        superseded_ref=args.superseded_capability_ref,
        predicates=args.preserved_behavior_predicate,
        evidence_refs=args.behavioral_parity_evidence_ref,
        authorized_delta_refs=args.authorized_behavior_delta_ref,
    )
    if not policy_context_complete:
        disposition = "STOP_AT_CANONICAL_POLICY_DEPENDENCY"
        exit_code = EXIT_EXACT_DEPENDENCY
        task_creation_permitted = False
    if args.readme_impact_required and not readme_impact_complete:
        disposition = "STOP_AT_README_IMPACT_DEPENDENCY"
        exit_code = EXIT_EXACT_DEPENDENCY
        task_creation_permitted = False
    if args.behavioral_parity_required and not behavioral_parity_complete:
        disposition = "STOP_AT_BEHAVIORAL_PARITY_DEPENDENCY"
        exit_code = EXIT_EXACT_DEPENDENCY
        task_creation_permitted = False

    result = {
        "schema": "stegverse.session-build-preflight/v1",
        "goal": args.goal,
        "disposition": disposition,
        "task_creation_permitted": task_creation_permitted,
        "preflight": preflight,
        "cross_task_coordination": coordination,
        "canonical_policy_context": policy_context,
        "canonical_policy_context_complete": policy_context_complete,
        "human_policy_restatement_required": False,
        "readme_impact": readme_impact,
        "readme_impact_complete": readme_impact_complete,
        "behavioral_parity": behavioral_parity,
        "behavioral_parity_complete": behavioral_parity_complete,
        "canonical_policy_context_required_before_state_interpretation": True,
        "coordination_required_before_new_work": True,
        "readme_impact_required_before_functional_mutation": True,
        "behavioral_parity_required_for_migration_or_replacement": True,
        "authority_effect": "NONE_PREWORK_DECISION_ONLY",
        "network_fetch_performed": False,
        "runtime_execution_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
