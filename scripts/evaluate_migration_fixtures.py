#!/usr/bin/env python3
"""Lift a migration fixture set written against the 1673cb5f draft schemas and validate it against the current ones.

  python3 scripts/evaluate_migration_fixtures.py --fixtures <dir with sv-issues.jsonl, sv-changes.jsonl[, expected-schema-gaps.json]>

Lifting applies only sv_migration's published rules (nothing is filled in to pass). Each record is checked by the
JSON schema (schema_subset) and by the validator. When expected-schema-gaps.json is present, every listed gap is
reported CLEARED (its record now validates) or REMAINS (with the reason). Read-only; prints JSON. Stdlib, no clock.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(n, p):
    if n in sys.modules:
        return sys.modules[n]
    s = importlib.util.spec_from_file_location(n, ROOT / p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m


wi = _load("sv_work_items", "resident-runtime/sv_work_items.py")
mg = _load("sv_migration", "resident-runtime/sv_migration.py")
ss = _load("schema_subset", "resident-runtime/schema_subset.py")
SCHEMAS = {k: json.loads((ROOT / f"schemas/{k}.schema.json").read_text()) for k in ("sv-issue.v1", "sv-change.v1", "canonical-task-work-items.v1")}


def _check(rec, schema, validator):
    errs = ss.validate(rec, schema)
    try:
        validator(rec); refusal = None
    except wi.Refusal as r:
        refusal = {k: r.record.get(k) for k in ("failure_code", "failed_predicate", "required_evidence_or_repair")} | \
                  {k: r.record[k] for k in ("fields", "found", "unknown") if k in r.record}
    return {"schema_errors": [list(e) for e in errs], "refusal": refusal, "valid": not errs and refusal is None}


def evaluate(fixtures: Path) -> dict:
    v0_issues = [json.loads(l) for l in (fixtures / "sv-issues.jsonl").read_text().splitlines() if l.strip()]
    v0_changes = [json.loads(l) for l in (fixtures / "sv-changes.jsonl").read_text().splitlines() if l.strip()]
    lifted = [mg.lift_v0_issue(r) for r in v0_issues]
    issues, remap = mg.merge_issues(lifted)
    changes = [mg.lift_v0_change(r, remap) for r in v0_changes]
    rid = {}
    out_issues = {}
    for r in issues:
        out_issues[r["issue_id"]] = _check(r, SCHEMAS["sv-issue.v1"], wi.validate_issue)
    for old, new in remap.items():
        rid[old] = new
    out_changes = {}
    for v0, r in zip(v0_changes, changes):
        key = "PR#%s" % (v0.get("projection") or {}).get("pr")
        out_changes[key] = _check(r, SCHEMAS["sv-change.v1"], wi.validate_change)
    items = wi.work_items_record(issues + changes)
    items_errs = ss.validate(items, SCHEMAS["canonical-task-work-items.v1"])
    report = {"lifted": {"sv_issue_in": len(v0_issues), "sv_issue_out": len(issues), "merged_restatements": len(v0_issues) - len(issues),
                         "sv_change": len(changes), "work_items": len(items["work_items"]), "goal_index_keys": sorted(items["goal_index"])},
              "issues_valid": sum(v["valid"] for v in out_issues.values()), "changes_valid": sum(v["valid"] for v in out_changes.values()),
              "work_items_schema_errors": [list(e) for e in items_errs],
              "invalid": {**{k: v for k, v in out_issues.items() if not v["valid"]}, **{k: v for k, v in out_changes.items() if not v["valid"]}}}
    gaps_file = fixtures / "expected-schema-gaps.json"
    if gaps_file.exists():
        gaps = json.loads(gaps_file.read_text())["gaps"]
        res = {"CLEARED": 0, "REMAINS": 0, "remaining": []}
        for g in gaps:
            if g["file"] == "sv-issues.jsonl":
                st = out_issues.get(rid.get(g["record"], g["record"]))
            elif g["file"] == "sv-changes.jsonl":
                st = out_changes.get(g["record"])
            else:
                st = {"valid": not items_errs, "refusal": None, "schema_errors": items_errs}
            if st and st["valid"]:
                res["CLEARED"] += 1
            else:
                res["REMAINS"] += 1
                res["remaining"].append({**g, "reason": st})
        report["expected_gaps"] = {"total": len(gaps), **res}
    return report


def main(argv=None) -> int:
    a = argparse.ArgumentParser(); a.add_argument("--fixtures", required=True, type=Path); args = a.parse_args(argv)
    print(json.dumps(evaluate(args.fixtures), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
