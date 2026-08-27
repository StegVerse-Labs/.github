#!/usr/bin/env python3
"""Fail-closed validator for the ecosystem COSV adoption manifest.

This validator is intentionally repository-local. It validates the checked-in
projection only and never reads private repositories or grants cross-repository
execution authority.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PATH = Path("control/cosv-ecosystem-adoption-manifest.json")
ALLOWED = {
    "VECTOR_REQUIRED",
    "VECTOR_PRESENT",
    "NO_ACTIVE_TASK_SURFACE",
    "NO_REPOSITORY_OR_UNAVAILABLE",
}
NOTATION = "L R U I V G O C M T B E A P"
WIDTH = 14

def fail(message):
    raise SystemExit("COSV_ECOSYSTEM_ADOPTION_FAIL: " + message)

def main():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    if data.get("profile") != "task.v1":
        fail("profile must be task.v1")
    if data.get("notation") != NOTATION or data.get("width") != WIDTH:
        fail("canonical task.v1 notation/width mismatch")
    if data.get("authority_effect") != "NONE":
        fail("authority_effect must remain NONE")
    if data.get("credential_authority") != "TV/TVC":
        fail("credential authority must remain TV/TVC")
    if data.get("github_token_runtime_authority") != "NONE":
        fail("GitHub token runtime authority must remain NONE")
    if data.get("central_cross_private_execution_authority") is not False:
        fail("central cross-private execution authority is forbidden")

    repos = data.get("repositories")
    if not isinstance(repos, list) or not repos:
        fail("repositories must be a non-empty list")
    names = [r.get("repository") for r in repos]
    if len(names) != len(set(names)):
        fail("duplicate repository entries")
    if any(not n or "/" not in n for n in names):
        fail("invalid repository identity")
    if data.get("repository_count") != len(repos):
        fail("repository_count mismatch")

    classes = Counter()
    orgs = defaultdict(Counter)
    numerator = denominator = 0
    for r in repos:
        cls = r.get("classification")
        if cls not in ALLOWED:
            fail(f"{r.get('repository')}: invalid classification {cls!r}")
        classes[cls] += 1
        orgs[r.get("organization")][cls] += 1
        if not r.get("evidence_refs"):
            fail(f"{r.get('repository')}: evidence_refs required")
        if r.get("authority_effect") != "NONE":
            fail(f"{r.get('repository')}: authority_effect must be NONE")

        if cls in {"VECTOR_REQUIRED", "VECTOR_PRESENT"}:
            denominator += 1
            if r.get("profile") != "task.v1" or r.get("notation") != NOTATION or r.get("width") != WIDTH:
                fail(f"{r.get('repository')}: canonical task.v1 metadata required")
        if cls == "VECTOR_REQUIRED":
            if not r.get("release_condition"):
                fail(f"{r.get('repository')}: VECTOR_REQUIRED requires release_condition")
        elif cls == "VECTOR_PRESENT":
            numerator += 1
            if r.get("vector_coverage_state") != "COMPLETE":
                fail(f"{r.get('repository')}: VECTOR_PRESENT requires COMPLETE coverage")
            if not r.get("validation_refs"):
                fail(f"{r.get('repository')}: VECTOR_PRESENT requires validation_refs")
        elif cls == "NO_ACTIVE_TASK_SURFACE":
            if not r.get("no_active_task_evidence"):
                fail(f"{r.get('repository')}: exemption requires no_active_task_evidence")
        elif cls == "NO_REPOSITORY_OR_UNAVAILABLE":
            if not r.get("release_condition"):
                fail(f"{r.get('repository')}: unavailable classification requires release_condition")
            if not r.get("unavailable_scope"):
                fail(f"{r.get('repository')}: unavailable_scope required")

    expected_counts = dict(classes)
    if data.get("classification_counts") != expected_counts:
        fail(f"classification_counts mismatch: expected {expected_counts}")

    metrics = data.get("adoption_metrics") or {}
    if metrics.get("numerator_vectorized_active_task_surfaces") != numerator:
        fail("adoption numerator mismatch")
    if metrics.get("denominator_proven_active_task_surfaces") != denominator:
        fail("adoption denominator mismatch")
    if metrics.get("ratio") != f"{numerator}/{denominator}":
        fail("adoption ratio mismatch")

    projection = data.get("organization_projection")
    if not isinstance(projection, list):
        fail("organization_projection required")
    if data.get("organization_count") != len(projection):
        fail("organization_count mismatch")
    seen_orgs = set()
    for row in projection:
        org = row.get("organization")
        if org in seen_orgs:
            fail(f"duplicate organization projection: {org}")
        seen_orgs.add(org)
        actual_total = sum(1 for r in repos if r.get("organization") == org)
        if row.get("repository_count") != actual_total:
            fail(f"{org}: repository_count mismatch")
        checks = {
            "vector_required": "VECTOR_REQUIRED",
            "vector_present": "VECTOR_PRESENT",
            "no_active_task_surface": "NO_ACTIVE_TASK_SURFACE",
            "unavailable_or_not_yet_audited": "NO_REPOSITORY_OR_UNAVAILABLE",
        }
        for field, cls in checks.items():
            if row.get(field) != orgs[org][cls]:
                fail(f"{org}: {field} mismatch")

    if set(r.get("organization") for r in repos) != seen_orgs:
        fail("organization projection does not cover repository universe")

    if data.get("universe_audit_complete") is True and classes["NO_REPOSITORY_OR_UNAVAILABLE"]:
        fail("universe_audit_complete cannot be true with unavailable repositories")

    if not data.get("incomplete_adoption_release_conditions"):
        fail("incomplete adoption requires explicit release conditions")

    print(
        "COSV_ECOSYSTEM_ADOPTION_PASS "
        f"organizations={len(seen_orgs)} repositories={len(repos)} "
        f"vectorized_active_surfaces={numerator}/{denominator} "
        f"unavailable={classes['NO_REPOSITORY_OR_UNAVAILABLE']}"
    )

if __name__ == "__main__":
    main()
