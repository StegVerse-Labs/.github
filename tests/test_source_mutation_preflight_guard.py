import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_source_mutation_preflight.py"
spec = importlib.util.spec_from_file_location("source_mutation_guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


def _install_policy_fixture(tmp_path, monkeypatch):
    (tmp_path / "control").mkdir()
    (tmp_path / "data" / "canonical-task-records").mkdir(parents=True)
    (tmp_path / "receipts" / "preflight").mkdir(parents=True)
    policy = {
        "required_global_sources": [
            {"ref": "docs/GLOBAL.md", "required": True},
        ]
    }
    (tmp_path / "control" / "canonical-policy-context-registry.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    task = {
        "task_id": "TASK-1",
        "canonical_policy_refs": ["docs/DOMAIN.md"],
    }
    (tmp_path / "data" / "canonical-task-records" / "TASK-1.json").write_text(
        json.dumps(task), encoding="utf-8"
    )
    receipt = {
        "schema": guard.EXPECTED_SCHEMA,
        "state": "PASS_FUNCTIONAL_MUTATION_ADMISSIBLE",
        "preflight_completed_before_source_mutation": True,
        "base_commit": "base",
        "goal_task_id": "TASK-1",
        "canonical_sources_resolved": ["docs/GLOBAL.md", "docs/DOMAIN.md"],
        "authorized_mutation_scope": ["src/"],
    }
    receipt_path = tmp_path / "receipts" / "preflight" / "TASK-1.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(
        guard, "POLICY_REGISTRY", tmp_path / "control" / "canonical-policy-context-registry.json"
    )
    monkeypatch.setattr(guard, "TASK_SHARDS", tmp_path / "data" / "canonical-task-records")
    monkeypatch.setattr(guard, "TASK_REGISTRY", tmp_path / "data" / "canonical-task-registry.json")
    return "receipts/preflight/TASK-1.json"


def test_scope_supports_exact_and_prefix_paths():
    assert guard.path_authorized("scripts/a.py", ["scripts/"])
    assert guard.path_authorized("README.md", ["README.md"])
    assert not guard.path_authorized("workers/a.py", ["scripts/"])


def test_receipt_must_precede_first_protected_mutation(tmp_path, monkeypatch):
    receipt = _install_policy_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(guard, "first_change_commit", lambda base, path: "same")
    findings = guard.validate_receipt(
        receipt, base_sha="base", protected_paths=["src/change.py"]
    )
    assert any("same commit" in finding for finding in findings)


def test_prior_receipt_with_complete_policy_and_scope_passes(tmp_path, monkeypatch):
    receipt = _install_policy_fixture(tmp_path, monkeypatch)

    def first_change(base, path):
        return "receipt-commit" if path.startswith("receipts/preflight/") else "source-commit"

    monkeypatch.setattr(guard, "first_change_commit", first_change)
    monkeypatch.setattr(guard, "is_ancestor", lambda older, newer: older == "receipt-commit" and newer == "source-commit")
    findings = guard.validate_receipt(
        receipt, base_sha="base", protected_paths=["src/change.py"]
    )
    assert findings == []


def test_missing_task_policy_ref_fails_closed(tmp_path, monkeypatch):
    receipt = _install_policy_fixture(tmp_path, monkeypatch)
    payload_path = tmp_path / receipt
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["canonical_sources_resolved"] = ["docs/GLOBAL.md"]
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(guard, "first_change_commit", lambda base, path: "receipt-commit")
    findings = guard.validate_receipt(
        receipt, base_sha="base", protected_paths=["src/change.py"]
    )
    assert any("required canonical policy sources not resolved" in finding for finding in findings)
