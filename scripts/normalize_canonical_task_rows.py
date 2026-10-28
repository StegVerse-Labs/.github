#!/usr/bin/env python3
"""Read-only worker_claim / runtime_resolution normalization report (Q-R-j).

``--check`` is the only mode. For every canonical task row that fails the
canonical work coordination validator's worker_claim, runtime_requirements or
runtime_resolution predicates, it reports the delta between the row and the
normalization target, then prints a deterministic JSON report and a six-field
summary. It never writes the registry, schema, runtime map or any other source.

Targets (proposals for the registry-editing lane; this tool applies nothing):

* worker_claim: the canonical projection in TASK_REGISTRY_CANONICAL_INVARIANTS.md
  L46-L53 ({WORKERCOORDINATOR, claim_ref null, fence_ref null, projection_only
  true}), the same value commit dfcb305f applied to
  SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001. The schema constants
  (schemas/canonical-task-record.schema.json properties.worker_claim) are read
  from the schema, not restated here.
* runtime_resolution: null when the row is not schema-valid or fails the
  validator's projection, generation or profile predicates (the schema type is
  ["object", "null"]). Non-schema keys are listed so their destination can be
  decided; this tool does not choose one.
* runtime_requirements: reported only, never normalized. The validator requires
  it but the schema's required list does not (Q-R-k).

Exit codes: 0 when the report is produced (deltas are reported, not enforced,
unless --enforce); 1 on --enforce with deltas; 1 always when a source cannot be
read or the report cannot be produced. Standard library only.

Not truth, not legal determination, not execution authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
TASK_SCHEMA = ROOT / "schemas" / "canonical-task-record.schema.json"
RUNTIME_MAP = ROOT / "control" / "runtime-profile-map.json"
REPORT_SCHEMA = "stegverse.canonical-task-row-normalization-check/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = "python scripts/normalize_canonical_task_rows.py --check"
WORKER_CLAIM_BASIS = ("TASK_REGISTRY_CANONICAL_INVARIANTS.md L46-L53; precedent dfcb305f "
                      "(SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001); schema properties.worker_claim")
RESOLUTION_BASIS = ("schemas/canonical-task-record.schema.json properties.runtime_resolution "
                    "(type object|null, additionalProperties false); "
                    "scripts/validate_canonical_work_coordination.py runtime_resolution predicates")
RUNTIME_REQUIREMENTS_FLAGS = ("mutation_required", "deployment_required", "current_observation_required")
DISCLAIMER = "not truth, not legal determination, not execution authority"


class SourceError(Exception):
    """A source could not be read or has an unusable shape."""


def _load(path: Path) -> tuple[Any, str]:
    try:
        raw = path.read_bytes()
        return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"{path}: {exc}") from exc


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def worker_claim_target(schema: dict) -> dict:
    props = schema.get("properties", {}).get("worker_claim", {})
    if not isinstance(props, dict) or not isinstance(props.get("properties"), dict):
        raise SourceError("schema properties.worker_claim.properties missing")
    claim_props = props["properties"]
    try:
        authority = claim_props["authority"]["const"]
        projection_only = claim_props["projection_only"]["const"]
    except (KeyError, TypeError) as exc:
        raise SourceError(f"schema worker_claim constants missing: {exc!r}") from exc
    required = props.get("required")
    if not isinstance(required, list):
        raise SourceError("schema worker_claim.required missing")
    target: dict[str, Any] = {"authority": authority, "projection_only": projection_only}
    for key in required:
        target.setdefault(key, None)  # claim_ref / fence_ref: null projection (L46-L53)
    return dict(sorted(target.items()))


def worker_claim_delta(claim: Any, projection: dict) -> dict[str, Any]:
    """Delta against the canonical projection.

    L46-L53 prescribe null claim_ref/fence_ref only when no authentic
    WorkerCoordinator claim/fence has been observed. This tool cannot observe
    that, so an existing string ref is kept in the target and flagged for a
    check instead of being nulled.
    """
    target = dict(projection)
    if isinstance(claim, dict):
        for ref in ("claim_ref", "fence_ref"):
            if ref in target and isinstance(claim.get(ref), str):
                target[ref] = claim[ref]
    target = dict(sorted(target.items()))
    entry: dict[str, Any] = {"target": target, "basis": WORKER_CLAIM_BASIS}
    if not isinstance(claim, dict):
        entry["current"] = claim
        entry["kind"] = "ABSENT" if claim is _ABSENT else "NOT_OBJECT"
        if claim is _ABSENT:
            entry["current"] = None
        entry["changes"] = sorted(target)
        entry["needs_change"] = True
        return entry
    changes = sorted(k for k in set(target) | set(claim) if claim.get(k, _ABSENT) != target.get(k, _ABSENT))
    entry["current"] = dict(sorted(claim.items()))
    entry["changes"] = changes
    entry["needs_change"] = bool(changes)
    kinds = []
    if claim.get("authority") != target["authority"]:
        kinds.append("AUTHORITY_DRIFT")
    if claim.get("projection_only") is not target["projection_only"]:
        kinds.append("PROJECTION_ONLY_DRIFT")
    if any(k not in claim for k in target):
        kinds.append("MISSING_KEYS")
    if any(k not in target for k in claim):
        kinds.append("EXTRA_KEYS")
    if any(claim.get(k) is not None for k in ("claim_ref", "fence_ref")):
        kinds.append("NONNULL_REF_REQUIRES_OBSERVED_CLAIM_CHECK")
    entry["kind"] = "+".join(kinds) if kinds else "CONFORMS"
    return entry


class _Absent:
    def __repr__(self) -> str:
        return "<absent>"


_ABSENT = _Absent()


def resolution_delta(resolution: Any, schema: dict, runtime_map: dict) -> dict[str, Any] | None:
    if resolution is None or resolution is _ABSENT:
        return None
    entry: dict[str, Any] = {"target": None, "basis": RESOLUTION_BASIS}
    if not isinstance(resolution, dict):
        entry.update(current_type=type(resolution).__name__, violations=["NOT_OBJECT_OR_NULL"], non_schema_keys=[])
        return entry
    allowed = set(schema.get("properties", {}).get("runtime_resolution", {}).get("properties", {}))
    violations = []
    non_schema = sorted(k for k in resolution if k not in allowed)
    if non_schema:
        violations.append("NON_SCHEMA_KEYS")
    if resolution.get("projection_only") is not True:
        violations.append("PROJECTION_ONLY_NOT_TRUE")
    if resolution.get("selection_grants_authority") is not False:
        violations.append("SELECTION_GRANTS_AUTHORITY_NOT_FALSE")
    if resolution.get("map_generation") != runtime_map.get("generation"):
        violations.append("STALE_OR_MISSING_MAP_GENERATION")
    known = {p.get("profile_id") for p in runtime_map.get("profiles", []) if isinstance(p, dict)}
    candidates = resolution.get("candidate_profile_ids", [])
    if not isinstance(candidates, list) or not set(candidates).issubset(known):
        violations.append("UNKNOWN_OR_MALFORMED_PROFILE_IDS")
    if not violations:
        return None
    entry.update(current_keys=sorted(resolution), violations=violations, non_schema_keys=non_schema,
                 non_schema_key_destination="UNDECIDED_Q-R-j")
    return entry


def requirements_status(requirements: Any) -> str | None:
    if requirements is _ABSENT:
        return "ABSENT"
    if not isinstance(requirements, dict):
        return "NOT_OBJECT"
    if not isinstance(requirements.get("capabilities"), list):
        return "CAPABILITIES_MISSING"
    if any(not isinstance(requirements.get(f), bool) for f in RUNTIME_REQUIREMENTS_FLAGS):
        return "FLAG_NOT_BOOLEAN"
    return None


def build_report(registry_path: Path, schema_path: Path, runtime_map_path: Path) -> dict[str, Any]:
    registry, registry_sha = _load(registry_path)
    schema, schema_sha = _load(schema_path)
    runtime_map, map_sha = _load(runtime_map_path)
    for name, doc in (("registry", registry), ("schema", schema), ("runtime map", runtime_map)):
        if not isinstance(doc, dict):
            raise SourceError(f"{name} root is not a JSON object")
    tasks = registry.get("tasks")
    if not isinstance(tasks, list):
        raise SourceError("registry tasks is not an array")
    target = worker_claim_target(schema)

    rows = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise SourceError(f"registry tasks[{index}] is not an object")
        claim = worker_claim_delta(task.get("worker_claim", _ABSENT), target)
        resolution = resolution_delta(task.get("runtime_resolution", _ABSENT), schema, runtime_map)
        requirements = requirements_status(task.get("runtime_requirements", _ABSENT))
        reasons = []
        if claim["needs_change"]:
            reasons.append("WORKER_CLAIM")
        if requirements:
            reasons.append("RUNTIME_REQUIREMENTS_PENDING_Q-R-k")
        if resolution:
            reasons.append("RUNTIME_RESOLUTION")
        if not reasons:
            continue
        row: dict[str, Any] = {"index": index, "task_id": task.get("task_id"), "reasons": reasons}
        if claim["needs_change"]:
            row["worker_claim"] = claim
        if resolution:
            row["runtime_resolution"] = resolution
        if requirements:
            row["runtime_requirements"] = {"status": requirements, "disposition": "NOT_NORMALIZED_PENDING_Q-R-k"}
        rows.append(row)

    def count(predicate) -> int:
        return sum(1 for r in rows if predicate(r))

    claim_or_requirements = count(lambda r: "WORKER_CLAIM" in r["reasons"]
                                  or "RUNTIME_REQUIREMENTS_PENDING_Q-R-k" in r["reasons"])
    summary = {
        "rows_total": len(tasks),
        "rows_in_scope": len(rows),
        "rows_worker_claim_or_runtime_requirements": claim_or_requirements,
        "rows_runtime_resolution_only": count(lambda r: r["reasons"] == ["RUNTIME_RESOLUTION"]),
        "worker_claim_delta_rows": count(lambda r: "worker_claim" in r),
        "worker_claim_absent": count(lambda r: r.get("worker_claim", {}).get("kind") == "ABSENT"),
        "worker_claim_not_object": count(lambda r: r.get("worker_claim", {}).get("kind") == "NOT_OBJECT"),
        "worker_claim_authority_drift": count(lambda r: "AUTHORITY_DRIFT" in r.get("worker_claim", {}).get("kind", "")),
        "worker_claim_projection_only_drift": count(lambda r: "PROJECTION_ONLY_DRIFT" in r.get("worker_claim", {}).get("kind", "")),
        "worker_claim_missing_keys_only": count(lambda r: r.get("worker_claim", {}).get("kind") == "MISSING_KEYS"),
        "worker_claim_nonnull_refs_requiring_check": count(
            lambda r: "NONNULL_REF" in r.get("worker_claim", {}).get("kind", "")),
        "runtime_resolution_delta_rows": count(lambda r: "runtime_resolution" in r),
        "runtime_resolution_non_schema_key_rows": count(
            lambda r: bool(r.get("runtime_resolution", {}).get("non_schema_keys"))),
        "runtime_requirements_pending_q_r_k_rows": count(lambda r: "runtime_requirements" in r),
    }
    return {
        "schema": REPORT_SCHEMA,
        "mode": "check",
        "writes_performed": False,
        "sources": {
            "registry": {"path": _rel(registry_path), "sha256": registry_sha, "generation": registry.get("generation")},
            "task_schema": {"path": _rel(schema_path), "sha256": schema_sha},
            "runtime_map": {"path": _rel(runtime_map_path), "sha256": map_sha, "generation": runtime_map.get("generation")},
        },
        "worker_claim_target": target,
        "summary": summary,
        "rows": rows,
        "disclaimer": DISCLAIMER,
    }


def six_fields(report: dict[str, Any] | None, error: str | None) -> dict[str, str]:
    if error is not None:
        return {
            "disposition": "FAIL_CLOSED",
            "failure_code": "CANONICAL_TASK_ROW_NORMALIZATION_CHECK_SOURCE_UNREADABLE",
            "failed_predicate": f"sources readable as JSON objects with a tasks array: {error}",
            "required_evidence_or_repair": "restore a readable registry, task schema and runtime map; this tool writes none of them",
            "retry_entrypoint": RETRY_ENTRYPOINT,
            "owning_existing_goal": OWNING_GOAL,
            "next_attempt": "after the source is readable, re-run retry_entrypoint",
        }
    s = report["summary"]
    if s["rows_in_scope"] == 0:
        return {"disposition": "PASS", "rows_in_scope": "0"}
    return {
        "disposition": "FAIL_CLOSED",
        "failure_code": "CANONICAL_TASK_ROWS_REQUIRE_NORMALIZATION",
        "failed_predicate": (
            f"{s['rows_in_scope']} of {s['rows_total']} rows deviate: worker_claim {s['worker_claim_delta_rows']}, "
            f"runtime_resolution {s['runtime_resolution_delta_rows']}, runtime_requirements pending Q-R-k "
            f"{s['runtime_requirements_pending_q_r_k_rows']} ({s['rows_worker_claim_or_runtime_requirements']} "
            f"worker_claim/runtime_requirements + {s['rows_runtime_resolution_only']} runtime_resolution only)"
        ),
        "required_evidence_or_repair": (
            "registry-editing lane applies the reported worker_claim targets (TASK_REGISTRY_CANONICAL_INVARIANTS.md "
            "L46-L53, precedent dfcb305f) and decides runtime_resolution non-schema key destinations (Q-R-j) at a "
            "fenced generation; runtime_requirements awaits Q-R-k; this check writes nothing"
        ),
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": f"{OWNING_GOAL}; joint discovery questions Q-R-j, Q-R-k",
        "next_attempt": "after a registry generation that applies the normalization, re-run retry_entrypoint",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="required; the only mode (read-only)")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--schema", type=Path, default=TASK_SCHEMA)
    parser.add_argument("--runtime-map", type=Path, default=RUNTIME_MAP)
    parser.add_argument("--report", type=Path, help="also write the JSON report here (never a source path)")
    parser.add_argument("--enforce", action="store_true", help="exit 1 when rows need normalization")
    args = parser.parse_args(argv)
    if not args.check:
        print("FAIL_CLOSED: only --check is supported; this tool never writes sources", file=sys.stderr)
        return 1
    try:
        report = build_report(args.registry, args.schema, args.runtime_map)
        error = None
    except SourceError as exc:
        report, error = None, str(exc)
    summary = six_fields(report, error)
    try:
        if report is not None:
            text = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if args.report is not None:
                protected = {p.resolve() for p in (args.registry, args.schema, args.runtime_map)}
                if args.report.resolve() in protected:
                    raise SourceError("--report must not point at a source file")
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(text, encoding="utf-8")
            else:
                sys.stdout.write(text)
        lines = [f"{k}: {v}" for k, v in summary.items()]
        print("\n".join(lines))
        step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if step_summary:
            with open(step_summary, "a", encoding="utf-8") as fh:
                fh.write("### Canonical task row normalization check (read-only, Q-R-j)\n\n")
                fh.write("\n".join(f"- {line}" for line in lines) + "\n")
                if report is not None:
                    fh.write("\n```json\n" + json.dumps(report["summary"], indent=2, sort_keys=True) + "\n```\n")
        if summary["disposition"] != "PASS":
            print(f"::warning title=Canonical task row normalization::{summary['failure_code']}")
    except (OSError, SourceError) as exc:
        print(f"FAIL_CLOSED: CANONICAL_TASK_ROW_NORMALIZATION_CHECK_REPORT_ERROR: {exc}", file=sys.stderr)
        return 1
    if error is not None:
        return 1
    return 1 if (args.enforce and summary["disposition"] != "PASS") else 0


if __name__ == "__main__":
    raise SystemExit(main())
