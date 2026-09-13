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
    assert invariants["completion_language_requires_evidence_class"] is True
    assert invariants["unqualified_complete_or_completed_prohibited"] is True
    assert invariants["stronger_completion_class_inference_prohibited"] is True
    assert invariants["completion_claim_requires_evidence_refs"] is True
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


def test_affirmative_completion_without_class_fails_closed(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(record_path, {"completion": {"claimed": True, "validated": True}})


def test_affirmative_completion_without_evidence_refs_fails_closed(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {"completion": {"claimed": True, "validated": True, "evidence_class": "CI_VALIDATED"}},
        )


def test_weaker_class_cannot_satisfy_stronger_terminal_class(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {
                "completion": {
                    "claimed": True,
                    "validated": True,
                    "evidence_class": "CI_VALIDATED",
                    "terminal_evidence_class": "SANDBOX_RUNTIME_OBSERVED",
                    "evidence_refs": ["ci://run/123"],
                }
            },
        )


def test_exact_or_stronger_class_with_evidence_is_allowed(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    validator.validate_completion(
        record_path,
        {
            "completion": {
                "claimed": True,
                "validated": True,
                "evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                "terminal_evidence_class": "SANDBOX_RUNTIME_OBSERVED",
                "evidence_refs": ["master-records://receipt/abc"],
            }
        },
    )


def test_end_to_end_flag_requires_end_to_end_class(tmp_path: Path):
    validator = load_validator()
    record_path = tmp_path / "task.json"
    with pytest.raises(SystemExit):
        validator.validate_completion(
            record_path,
            {
                "completion": {
                    "claimed": True,
                    "validated": True,
                    "evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                    "terminal_evidence_class": "MASTER_RECORDS_RECONSTRUCTED",
                    "evidence_refs": ["master-records://receipt/abc"],
                    "end_to_end_complete": True,
                }
            },
        )
