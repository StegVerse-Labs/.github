#!/usr/bin/env python3
"""Deterministic, non-authorizing StegVerse ecosystem continuity evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EVALUATOR_VERSION = "0.1.0"
OBSERVATION_STATES = {
    "PASS", "FAIL", "DEGRADED", "UNKNOWN", "NOT_OBSERVED", "STALE", "UNREACHABLE", "PROBE_REQUIRED"
}


def _canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _finding_id(component_id, predicate_id, observation_state, evidence):
    payload = {
        "component_id": component_id,
        "predicate_id": predicate_id,
        "observation_state": observation_state,
        "evidence": sorted(evidence),
    }
    return "ecef_" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()[:24]


def _severity(state, critical):
    if state == "PASS":
        return "INFO"
    if state == "FAIL":
        return "CRITICAL" if critical else "HIGH"
    if state in {"UNREACHABLE", "STALE"}:
        return "HIGH" if critical else "MEDIUM"
    if state in {"UNKNOWN", "NOT_OBSERVED", "PROBE_REQUIRED"}:
        return "HIGH" if critical else "LOW"
    return "MEDIUM"


def _remediation_class(state):
    if state == "PASS":
        return "NONE"
    if state in {"UNKNOWN", "NOT_OBSERVED", "PROBE_REQUIRED", "STALE", "UNREACHABLE"}:
        return "DISPATCHABLE"
    return "DISPATCHABLE"


def evaluate(registry, observations, evaluated_at):
    registry_sha = hashlib.sha256(_canonical_bytes(registry)).hexdigest()
    observation_map = {
        (o["component_id"], o["predicate_id"]): o for o in observations.get("observations", [])
    }
    findings = []
    registered = 0
    observed = 0
    evaluation_errors = 0
    critical_fail = False
    critical_uncertain = False
    noncritical_problem = False

    for component in registry.get("components", []):
        component_id = component["component_id"]
        owner = component["authority_owner"]
        for predicate in component.get("predicates", []):
            registered += 1
            predicate_id = predicate["predicate_id"]
            critical = bool(predicate.get("continuity_critical"))
            obs = observation_map.get((component_id, predicate_id))
            if obs is None:
                state = "NOT_OBSERVED"
                evidence = []
                age = None
            else:
                observed += 1
                state = obs.get("state", "UNKNOWN")
                if state not in OBSERVATION_STATES:
                    state = "UNKNOWN"
                    evaluation_errors += 1
                evidence = list(obs.get("evidence", []))
                age = obs.get("evidence_age_seconds")
                max_age = predicate.get("max_age_seconds")
                if state == "PASS" and max_age is not None and age is not None and age > max_age:
                    state = "STALE"

            if critical and state == "FAIL":
                critical_fail = True
            elif critical and state != "PASS":
                critical_uncertain = True
            elif not critical and state != "PASS":
                noncritical_problem = True

            findings.append({
                "schema": "stegverse.ecosystem-continuity-finding.v1",
                "finding_id": _finding_id(component_id, predicate_id, state, evidence),
                "component_id": component_id,
                "predicate_id": predicate_id,
                "observation_state": state,
                "severity": _severity(state, critical),
                "continuity_critical": critical,
                "evidence": sorted(evidence),
                "evidence_age_seconds": age,
                "authority_owner": owner,
                "remediation_class": _remediation_class(state),
                "remediation_state": "UNASSIGNED" if state == "PASS" else "DETECTED",
                "detail": obs.get("detail", "") if obs else "No authentic observation supplied."
            })

    if evaluation_errors:
        continuity = "INDETERMINATE"
    elif critical_fail:
        continuity = "INTERRUPTED"
    elif critical_uncertain:
        continuity = "AT_RISK"
    elif noncritical_problem:
        continuity = "CONTINUOUS_WITH_DEGRADATION"
    else:
        continuity = "CONTINUOUS"

    identity = {
        "evaluated_at": evaluated_at,
        "registry_sha256": registry_sha,
        "findings": [f["finding_id"] for f in findings],
    }
    return {
        "schema": "stegverse.ecosystem-continuity-evaluation.v1",
        "evaluation_id": "ece_" + hashlib.sha256(_canonical_bytes(identity)).hexdigest()[:24],
        "evaluated_at": evaluated_at,
        "evaluator_version": EVALUATOR_VERSION,
        "registry_sha256": registry_sha,
        "continuity_state": continuity,
        "completeness": {
            "registered_predicates": registered,
            "observed_predicates": observed,
            "evaluation_errors": evaluation_errors,
        },
        "findings": findings,
        "authority_effect": "NONE_DIAGNOSTIC_ONLY",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registry", required=True)
    p.add_argument("--observations", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--evaluated-at", default=None)
    args = p.parse_args()
    registry = json.loads(Path(args.registry).read_text())
    observations = json.loads(Path(args.observations).read_text())
    evaluated_at = args.evaluated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result = evaluate(registry, observations, evaluated_at)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
