from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
VALIDATOR = ROOT / "scripts" / "validate_task_registry_global_invariants.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("task_registry_global_invariants", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_policy_requires_evidence_class_qualified_completion():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    invariants = policy["invariants"]
    assert invariants["completion_evidence_contract_version"] == "v1"
    assert invariants["completion_language_requires_evidence_class"] is True
    assert invariants["unqualified_complete_or_completed_prohibited"] is True
    assert invariants["stronger_completion_class_inference_prohibited"] is True
    assert invariants["completion_claim_requires_evidence_refs"] is True
    assert invariants["legacy_unqualified_completion_authority"] == "NONE_NON_AUTHORITATIVE_PROVENANCE_ONLY"
    assert invariants["legacy_unqualified_completion_may_support_user_facing_complete"] is False
    assert invariants["legacy_unqualified_completion_may_satisfy_terminal_predicate"] is False
    assert invariants["terminal_complete_default_evidence_class"] == "END_TO_END"
    assert invariants["completion_evidence_classes"] == [
        "SOURCE_IMPLEMENTED",
        "MERGED",
        "CI_VALIDATED",
        "SANDBOX_RUNTIME_OBSERVED",
        "EXTERNAL_PROVIDER_OBSERVED",
        "MASTER_RECORDS_RECONSTRUCTED",
        "END_TO_END",
    ]


def test_legacy_unqualified_completion_is_non_authoritative(tmp_path: Path):
    validator = load_validator()
    record = {"completion": {"claimed": True, "validated": True}}
    validator.validate_completion(tmp_path / "legacy.json", record)
    result = validator.completion_reportability(record)
    assert result["reportable_complete"] is False
    assert result["state"] == "LEGACY_UNQUALIFIED_NON_AUTHORITATIVE"


def test_v1_affirmative_completion_without_class_fails_closed(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {
                "completion_evidence_contract_version": "v1",
                "completion": {"claimed": True, "validated": True},
            },
        )


def test_v1_affirmative_completion_without_evidence_refs_fails_closed(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {
                "completion_evidence_contract_version": "v1",
                "completion": {"claimed": True, "validated": True, "evidence_class": "CI_VALIDATED"},
            },
        )


def test_weaker_class_cannot_satisfy_stronger_terminal_class(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {
                "completion_evidence_contract_version": "v1",
                "completion": {
                    "claimed": True,
                    "validated": True,
                    "evidence_class": "CI_VALIDATED",
                    "terminal_evidence_class": "SANDBOX_RUNTIME_OBSERVED",
                    "evidence_refs": ["ci://run/123"],
                },
            },
        )


def test_exact_or_stronger_class_with_evidence_is_allowed_and_reportable(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    record = {
        "completion_evidence_contract_version": "v1",
        "completion": {
            "claimed": True,
            "validated": True,
            "evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
            "terminal_evidence_class": "SANDBOX_RUNTIME_OBSERVED",
            "evidence_refs": ["master-records://receipt/abc"],
        },
    }
    validator.validate_completion(record_path, record)
    result = validator.completion_reportability(record)
    assert result["reportable_complete"] is True
    assert result["state"] == "QUALIFIED_TERMINAL_SATISFIED"


def test_end_to_end_flag_requires_end_to_end_class(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {
                "completion_evidence_contract_version": "v1",
                "completion": {
                    "claimed": True,
                    "validated": True,
                    "evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                    "terminal_evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                    "evidence_refs": ["master-records://receipt/abc"],
                    "end_to_end_complete": True,
                },
            },
        )
