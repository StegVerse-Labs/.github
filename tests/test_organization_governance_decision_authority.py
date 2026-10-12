"""The decision authority (StegCore) install of organization-governance-decision.yml.

Offline only. StegCore is private and is not installed here, so nothing in this
file claims a StegCore decision: the installed record is exercised with the
import and the version lookup replaced, and every other assertion is about the
workflow text, the single pin, and the refusals that guard the install.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/organization-governance-decision.yml"
PIN = ROOT / "org-runtime/decision-authority.json"
INSTALL_STEP = "Install the decision authority (StegCore) when this run may read it"
VERIFY_STEP = "Verify the TV/TVC materialization of the decision authority (StegCore)"
RECORD_ABSENT_STEP = "Record that the decision authority (StegCore) was not installed"
PRESENT = "${{ inputs.decision_authority_source != '' && inputs.decision_authority_receipt != '' }}"
ABSENT = "${{ inputs.decision_authority_source == '' || inputs.decision_authority_receipt == '' }}"


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


decision = _load("organization_governance_decision_authority_under_test",
                 "resident-runtime/organization_governance_decision.py")


def _pin() -> dict:
    return json.loads(PIN.read_text(encoding="utf-8"))


def _steps() -> dict[str, str]:
    """Each named step of the workflow, as its text block."""
    text = WORKFLOW.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=      - )", text.split("\n    steps:\n", 1)[1])
    named = {}
    for block in blocks:
        match = re.search(r"^      - name: (.+)$", block, re.M) or re.search(r"^        name: (.+)$", block, re.M)
        if match:
            named[match.group(1).strip()] = block
    return named


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def _source(tmp_path: Path, dependencies: list[str], name: str = "stegcore") -> tuple[Path, str]:
    source = tmp_path / "StegCore"
    source.mkdir()
    deps = ", ".join(json.dumps(spec) for spec in dependencies)
    (source / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nrequires-python = ">=3.11"\ndependencies = [{deps}]\n', encoding="utf-8")
    _git("init", "-q", cwd=source)
    _git("add", "pyproject.toml", cwd=source)
    _git("-c", "user.name=StegVerse", "-c", "user.email=210078727+StegVerse@users.noreply.github.com",
         "commit", "-q", "-m", "fixture", cwd=source)
    return source, _git("rev-parse", "HEAD", cwd=source)


DECLARED = ["pydantic>=2.7", "fastapi", "uvicorn", "jsonschema"]


def test_pin_is_one_full_commit_with_exact_requirements():
    pin = _pin()
    assert pin["repository"] == "StegVerse-Labs/StegCore"
    assert pin["package"] == "stegcore"
    assert re.fullmatch(r"[0-9a-f]{40}", pin["commit"])
    assert all(re.fullmatch(r"[A-Za-z0-9._-]+==[A-Za-z0-9.]+", spec) for spec in pin["requirements"])
    assert sorted(decision._requirement_name(s) for s in pin["requirements"]) == \
        sorted(decision._requirement_name(s) for s in DECLARED)
    credential = pin["read_credential"]
    assert (credential["authority"], credential["capability_id"]) == ("TV/TVC", "tvc.private-source-read.v1")
    assert credential["repository_secret_allowed"] is False and credential["github_generated_token_allowed"] is False
    assert credential["caller_repository"] == "StegVerse-Labs/.github"
    assert credential["request"].endswith(".json") and pin["commit"][:8] in credential["materialization_id"]


def test_workflow_takes_the_commit_from_the_pin_and_never_restates_it():
    pin = _pin()
    text = WORKFLOW.read_text(encoding="utf-8")
    assert pin["commit"] not in text
    assert pin["commit"][:7] not in text
    for path in ("resident-runtime/organization_governance_decision.py", "resident-runtime/governance_endpoint.py"):
        assert pin["commit"] not in (ROOT / path).read_text(encoding="utf-8")


def test_install_runs_only_from_a_verified_tv_tvc_materialization_and_absence_is_recorded():
    steps = _steps()
    verify = steps[VERIFY_STEP]
    assert f"if: {PRESENT}" in verify
    assert 'authority-materialization --receipt "$DECISION_AUTHORITY_RECEIPT"' in verify
    assert f"if: {PRESENT}" in steps[INSTALL_STEP]
    absent = steps[RECORD_ABSENT_STEP]
    assert f"if: {ABSENT}" in absent
    assert absent.rstrip().endswith("evaluator")
    assert "pip" not in absent
    order = list(steps)
    assert order.index(VERIFY_STEP) < order.index(INSTALL_STEP) < order.index("Run the cycle")
    assert order.index(RECORD_ABSENT_STEP) < order.index("Run the cycle")


def test_no_repository_secret_or_github_token_reaches_the_decision_authority():
    # TV policy tv.private-source-read.v1: TV/TVC is the only credential authority.
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets." not in text
    assert "STEGCORE_READ_TOKEN" not in text
    assert "token:" not in "\n".join(_steps()[name] for name in (VERIFY_STEP, INSTALL_STEP))


def test_install_never_installs_an_unpinned_ref():
    install = _steps()[INSTALL_STEP]
    pip_lines = [line.strip() for line in install.splitlines() if "pip install" in line]
    assert pip_lines == ['python -m pip install -r "$RUNNER_TEMP/stegcore-requirements.txt"',
                         'python -m pip install --no-deps "$source"']
    assert 'source="$DECISION_AUTHORITY_SOURCE"' in install
    assert install.index("authority-requirements") < install.index("pip install")
    assert "git+" not in install and "@main" not in install
    assert install.rstrip().endswith("evaluator --installed")


def test_requirements_refuse_a_checkout_that_is_not_the_pin(tmp_path):
    source, _ = _source(tmp_path, DECLARED)
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_requirements(source, _pin())
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_SOURCE_NOT_PINNED"


def test_requirements_are_exactly_the_declared_dependencies(tmp_path):
    source, head = _source(tmp_path, DECLARED)
    pin = {**_pin(), "commit": head}
    assert decision.authority_requirements(source, pin) == pin["requirements"]


@pytest.mark.parametrize("declared,requirements", [
    (DECLARED + ["requests"], None),
    (DECLARED[:-1], None),
    (DECLARED, ["fastapi==0.116.1", "jsonschema>=4", "pydantic==2.11.7", "uvicorn==0.35.0"]),
])
def test_requirements_refuse_any_unpinned_or_undeclared_dependency(tmp_path, declared, requirements):
    source, head = _source(tmp_path, declared)
    pin = {**_pin(), "commit": head}
    if requirements is not None:
        pin["requirements"] = requirements
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_requirements(source, pin)
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_REQUIREMENTS_NOT_PINNED"


def test_evaluator_record_without_a_tv_tvc_materialization():
    pin = _pin()
    record = decision.evaluator_record(pin, installed=False)
    assert (record["installed"], record["reason"]) == (False, "STEGCORE_TVC_MATERIALIZATION_NOT_PROVIDED")
    assert record["dependency"].startswith("BLOCKED_DEPENDENCY: a TV/TVC tvc.private-source-read.v1")
    assert pin["read_credential"]["request"] in record["dependency"]


def _receipt(pin: dict, **overrides) -> dict:
    credential = pin["read_credential"]
    receipt = {"schema": "stegverse.tvc-private-source-read-result/v1", "capability_id": credential["capability_id"],
               "credential_authority": "TV/TVC", "caller_repository": credential["caller_repository"],
               "source_repository": pin["repository"], "consumer_task": credential["consumer_task"],
               "reference_mode": "IMMUTABLE_COMMIT", "exact_ref": "commit:" + pin["commit"],
               "authorized_exact_sha": pin["commit"], "observed_exact_sha": pin["commit"],
               "operation": "PRIVATE_REPOSITORY_READ_ONLY", "credential_available": True,
               "materialization_state": "COMPLETE", "result": "AUTHORIZED_EXECUTED_READ_ONLY",
               "completed_at": "2026-10-11T00:00:00Z"}
    receipt.update({name: False for name in decision.TVC_BOUNDARIES_FALSE})
    receipt.update(overrides)
    return receipt


def test_a_tv_tvc_receipt_for_the_pinned_commit_is_verified(tmp_path):
    pin = _pin()
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(_receipt(pin)))
    verified = decision.authority_materialization(path, pin)
    assert (verified["verified"], verified["commit"]) == (True, pin["commit"])


@pytest.mark.parametrize("overrides", [
    {"observed_exact_sha": "0" * 40}, {"authorized_exact_sha": "0" * 40}, {"credential_value_exposed": True},
    {"github_generated_token_substituted": True}, {"non_tv_tvc_credential_used": True}, {"write_authority": True},
    {"caller_repository": "StegVerse-Labs/elsewhere"}, {"source_repository": "StegVerse-Labs/Other"},
    {"materialization_state": "PARTIAL"}, {"result": "BLOCKED_DEPENDENCY"}, {"credential_authority": "GitHub"},
])
def test_a_tv_tvc_receipt_that_does_not_match_the_pin_is_refused(tmp_path, overrides):
    pin = _pin()
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(_receipt(pin, **overrides)))
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_materialization(path, pin)
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_MATERIALIZATION_NOT_VERIFIED"
    assert sorted(overrides)[0] in refused.value.document["failed_predicate"]


def test_a_missing_tv_tvc_receipt_is_refused(tmp_path):
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_materialization(tmp_path / "absent.json", _pin())
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_MATERIALIZATION_RECEIPT_ABSENT"


def test_evaluator_record_when_installed_names_commit_and_version(monkeypatch):
    from importlib import metadata
    imported = []
    monkeypatch.setattr(decision.importlib, "import_module", imported.append)
    monkeypatch.setattr(metadata, "version", lambda package: "0.0.0-under-test" if package == "stegcore" else None)
    pin = _pin()
    assert decision.evaluator_record(pin, installed=True) == {
        "installed": True, "commit": pin["commit"], "version": "0.0.0-under-test"}
    assert imported == ["stegcore.steggate"]


def test_evaluator_record_refuses_an_install_that_does_not_import():
    if importlib.util.find_spec("stegcore") is not None:
        pytest.skip("StegCore is installed here")
    with pytest.raises(decision.Refusal) as refused:
        decision.evaluator_record(_pin(), installed=True)
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_INSTALL_UNVERIFIED"


def test_report_names_which_evaluator_decided(tmp_path):
    evidence = tmp_path / "evidence"
    assert decision.main(["--evidence", str(evidence), "evaluator"]) == 0
    assert json.loads((evidence / "evaluator.json").read_text())["installed"] is False
    report, _ = decision.build_report(evidence, mesh_root="git+https://github.com/StegVerse-org/.github#refs/x")
    assert report["decision_authority_installed"] is False
    assert report["decision_authority_commit"] is None
    assert report["evaluator"]["reason"] == "STEGCORE_TVC_MATERIALIZATION_NOT_PROVIDED"
    installed = {"installed": True, "commit": _pin()["commit"], "version": "0.0.0-under-test"}
    (evidence / "evaluator.json").write_text(json.dumps(installed))
    report, _ = decision.build_report(evidence, mesh_root="git+https://github.com/StegVerse-org/.github#refs/x")
    assert report["decision_authority_installed"] is True
    assert report["decision_authority_commit"] == _pin()["commit"]
