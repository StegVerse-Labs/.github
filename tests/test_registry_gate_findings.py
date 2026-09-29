"""Registry-gate failures must reach the Healer as findings, not as prose."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from registry_gate_findings import evaluation, finding  # noqa: E402

# docs/ECOSYSTEM_CONTINUITY_HEALER_INTAKE_CONTRACT.md
INTAKE_FIELDS = {
    "finding_id", "component_id", "predicate_id", "observation_state",
    "severity", "continuity_critical", "evidence_references",
    "evidence_age_seconds", "authority_owner", "remediation_class",
    "diagnostic_detail",
}

GATES = [
    "scripts/audit_execution_substrate_resolution.py",
    "scripts/validate_task_record_actionable_disposition.py",
]


def sample(**overrides):
    row = dict(gate="TEST_GATE", task_id="TASK-001", predicate_id="STOP_TEST",
               detail="something is unactionable", evidence=["data/x.json"],
               repair="do the thing", retry_entrypoint="script.py --strict")
    row.update(overrides)
    return finding(**row)


def test_finding_carries_every_intake_field():
    assert INTAKE_FIELDS <= set(sample())


def test_finding_id_is_deterministic_in_the_failure():
    assert sample()["finding_id"] == sample()["finding_id"]
    assert sample()["finding_id"] != sample(task_id="TASK-002")["finding_id"]
    # Evidence order must not change identity.
    a = sample(evidence=["b.json", "a.json"])
    b = sample(evidence=["a.json", "b.json"])
    assert a["finding_id"] == b["finding_id"]


def test_severity_is_capped_below_critical():
    """A conformance gate says a record is untrustworthy, not that a system is down."""
    assert sample()["severity"] == "HIGH"
    assert sample()["continuity_critical"] is False


def test_finding_carries_its_own_repair_edge():
    row = sample()
    assert row["remediation_class"] == "DISPATCHABLE"
    assert row["required_evidence_or_repair"]
    assert row["retry_entrypoint"]


def test_finding_grants_no_authority():
    assert sample()["authority_effect"] == "NONE_FINDING_ONLY"
    assert evaluation("TEST_GATE", [])["grants_execution_authority"] is False


def test_evaluation_identity_follows_its_findings():
    one = evaluation("TEST_GATE", [sample()])
    assert one["evaluation_id"] == evaluation("TEST_GATE", [sample()])["evaluation_id"]
    assert one["evaluation_id"] != evaluation("TEST_GATE", [])["evaluation_id"]
    assert one["finding_count"] == 1


def test_both_gates_emit_a_valid_empty_set_when_green():
    for gate in GATES:
        result = subprocess.run([sys.executable, gate, "--findings"],
                                cwd=ROOT, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["schema"] == "stegverse.registry-gate-finding-set/v1"
        assert payload["finding_count"] == 0, f"{gate} is not green: {payload}"
        assert payload["findings"] == []
