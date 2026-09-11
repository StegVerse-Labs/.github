import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ece", ROOT / "scripts" / "evaluate_ecosystem_continuity.py")
ece = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ece)

REGISTRY = {
    "schema": "stegverse.ecosystem-continuity-registry.v1",
    "components": [
        {
            "component_id": "critical",
            "authority_owner": "owner/a",
            "predicates": [{"predicate_id": "p", "continuity_critical": True, "max_age_seconds": 60}],
        },
        {
            "component_id": "noncritical",
            "authority_owner": "owner/b",
            "predicates": [{"predicate_id": "q", "continuity_critical": False, "max_age_seconds": 60}],
        },
    ],
}


def run(obs):
    return ece.evaluate(REGISTRY, {"observations": obs}, "2026-09-11T20:00:00Z")


def o(component, predicate, state="PASS", age=1, evidence=None):
    return {"component_id": component, "predicate_id": predicate, "state": state, "evidence_age_seconds": age, "evidence": evidence or [f"receipt:{component}:{predicate}"]}


def test_continuous():
    r = run([o("critical", "p"), o("noncritical", "q")])
    assert r["continuity_state"] == "CONTINUOUS"
    assert r["authority_effect"] == "NONE_DIAGNOSTIC_ONLY"


def test_noncritical_degradation_preserves_continuity():
    r = run([o("critical", "p"), o("noncritical", "q", "DEGRADED")])
    assert r["continuity_state"] == "CONTINUOUS_WITH_DEGRADATION"


def test_critical_failure_interrupts():
    r = run([o("critical", "p", "FAIL"), o("noncritical", "q")])
    assert r["continuity_state"] == "INTERRUPTED"


def test_missing_critical_observation_is_at_risk_not_failure():
    r = run([o("noncritical", "q")])
    assert r["continuity_state"] == "AT_RISK"
    f = next(x for x in r["findings"] if x["component_id"] == "critical")
    assert f["observation_state"] == "NOT_OBSERVED"


def test_stale_critical_evidence_is_at_risk():
    r = run([o("critical", "p", age=61), o("noncritical", "q")])
    assert r["continuity_state"] == "AT_RISK"
    assert r["findings"][0]["observation_state"] == "STALE"


def test_invalid_observation_state_makes_evaluation_indeterminate():
    r = run([o("critical", "p", "MAGIC"), o("noncritical", "q")])
    assert r["continuity_state"] == "INDETERMINATE"
    assert r["completeness"]["evaluation_errors"] == 1


def test_finding_identity_is_deterministic():
    obs = [o("critical", "p"), o("noncritical", "q")]
    a = run(obs)
    b = run(obs)
    assert [x["finding_id"] for x in a["findings"]] == [x["finding_id"] for x in b["findings"]]


def test_dispatch_does_not_prove_recovery_by_contract():
    r = run([o("critical", "p", "FAIL"), o("noncritical", "q")])
    f = next(x for x in r["findings"] if x["component_id"] == "critical")
    assert f["remediation_state"] == "DETECTED"
    assert f["observation_state"] == "FAIL"
    assert r["continuity_state"] == "INTERRUPTED"


def test_verified_recovery_requires_new_pass_observation():
    failed = run([o("critical", "p", "FAIL"), o("noncritical", "q")])
    recovered = run([o("critical", "p", "PASS", evidence=["receipt:recovery-observation"]), o("noncritical", "q")])
    assert failed["continuity_state"] == "INTERRUPTED"
    assert recovered["continuity_state"] == "CONTINUOUS"
    assert failed["evaluation_id"] != recovered["evaluation_id"]
