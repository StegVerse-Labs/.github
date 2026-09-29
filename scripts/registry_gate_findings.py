#!/usr/bin/env python3
"""Shape registry-gate failures as Healer-intake findings, not prose.

`docs/ECOSYSTEM_CONTINUITY_HEALER_INTAKE_CONTRACT.md` names the fields
StegVerse-Healer consumes as repair-dispatch input: deterministic finding ID,
evaluation ID, component/predicate, observation state, severity,
continuity-critical flag, evidence references, evidence age, canonical
authority owner, remediation class, and diagnostic detail.

A red registry gate reaches that path through a CI failure email. Emitting a
prose log line makes the graph depend on parsing English, which is the same
defect as a stringified exception: it cannot be aggregated, and two runs of
the same failure need not produce the same identifier. These findings are
deterministic in the failure, so a repeat of one failure is one finding.

Severity is deliberately capped below CRITICAL. A registry conformance gate
reports that a record cannot be trusted, not that a running system is down;
dispatching at CRITICAL for a source-state finding would overstate it.

The finding, evaluation and severity helpers are imported from the existing
ECE emitter rather than restated, so the two cannot drift. Non-authorizing:
this mints no receipt, confers no admission and observes no runtime.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_ecosystem_continuity import (  # noqa: E402
    _canonical_bytes,
    _finding_id,
    _remediation_class,
    _severity,
)

OBSERVATION_STATE = "FAIL"
# A conformance gate says a record is untrustworthy, not that a system is down.
CONTINUITY_CRITICAL = False


def finding(*, gate: str, task_id: str, predicate_id: str, detail: str,
            evidence: Iterable[str], repair: str, retry_entrypoint: str) -> dict[str, Any]:
    """One Healer-intake finding for one registry-gate failure."""
    evidence = sorted(set(evidence))
    return {
        "finding_id": _finding_id(task_id, predicate_id, OBSERVATION_STATE, evidence),
        "component_id": task_id,
        "predicate_id": predicate_id,
        "gate": gate,
        "observation_state": OBSERVATION_STATE,
        "severity": _severity(OBSERVATION_STATE, CONTINUITY_CRITICAL),
        "continuity_critical": CONTINUITY_CRITICAL,
        "evidence_references": evidence,
        # Source-derived, not observed: there is no observation to age.
        "evidence_age_seconds": None,
        "authority_owner": task_id,
        "remediation_class": _remediation_class(OBSERVATION_STATE),
        "diagnostic_detail": detail,
        # The gate knows the repair it is demanding, so it carries it rather
        # than leaving the Healer to infer one.
        "required_evidence_or_repair": repair,
        "retry_entrypoint": retry_entrypoint,
        "authority_effect": "NONE_FINDING_ONLY",
    }


def evaluation(gate: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap findings with a deterministic evaluation identity."""
    identity = {"gate": gate, "findings": [f["finding_id"] for f in findings]}
    return {
        "schema": "stegverse.registry-gate-finding-set/v1",
        "gate": gate,
        "evaluation_id": "rgf_" + hashlib.sha256(_canonical_bytes(identity)).hexdigest()[:24],
        "finding_count": len(findings),
        "findings": findings,
        "healer_intake": "docs/ECOSYSTEM_CONTINUITY_HEALER_INTAKE_CONTRACT.md",
        "grants_execution_authority": False,
        "authority_effect": "NONE_FINDING_ONLY",
    }
