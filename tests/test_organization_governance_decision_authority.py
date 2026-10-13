"""The decision authority (StegCore) install of organization-governance-decision.yml.

Offline only. StegCore is not fetched or installed here (the fetch is exercised
against a local fixture repository), so nothing in this file claims a StegCore decision: the installed record is exercised with the
import and the version lookup replaced, and every other assertion is about the
workflow text, the single pin, and the refusals that guard the install.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/organization-governance-decision.yml"
PIN = ROOT / "org-runtime/decision-authority.json"
INSTALL_STEP = "Fetch and install the decision authority (StegCore) at the pin"


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
    assert (credential["authority"], credential["repository_visibility"], credential["fetch"]) == \
        ("NONE", "PUBLIC", "ANONYMOUS_PINNED_COMMIT")
    assert credential["repository_secret_allowed"] is False and credential["github_generated_token_allowed"] is False


def test_workflow_takes_the_commit_from_the_pin_and_never_restates_it():
    pin = _pin()
    text = WORKFLOW.read_text(encoding="utf-8")
    assert pin["commit"] not in text
    assert pin["commit"][:7] not in text
    for path in ("resident-runtime/organization_governance_decision.py", "resident-runtime/governance_endpoint.py"):
        assert pin["commit"] not in (ROOT / path).read_text(encoding="utf-8")


def test_every_run_fetches_and_installs_the_decision_authority_before_the_cycle():
    steps = _steps()
    install = steps[INSTALL_STEP]
    assert "if:" not in install
    assert "inputs.decision_authority" not in WORKFLOW.read_text(encoding="utf-8")
    assert install.index("set -eu") < install.index("authority-fetch") < install.index("authority-requirements") \
        < install.index("pip install")
    assert 'source="$RUNNER_TEMP/stegcore"' in install
    order = list(steps)
    assert order.index("Materialize the durable queue") < order.index(INSTALL_STEP) < order.index("Run the cycle")


def test_no_repository_secret_or_github_token_reaches_the_decision_authority():
    # StegCore is public: it is read with no credential at all.
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets." not in text
    assert "STEGCORE_READ_TOKEN" not in text
    assert "token:" not in _steps()[INSTALL_STEP]


def test_install_never_installs_an_unpinned_ref():
    install = _steps()[INSTALL_STEP]
    pip_lines = [line.strip() for line in install.splitlines() if "pip install" in line]
    assert pip_lines == ['python -m pip install -r "$RUNNER_TEMP/stegcore-requirements.txt"',
                         'python -m pip install --no-deps "$source"']
    assert install.index("authority-requirements") < install.index("pip install")
    assert "git+" not in install and "@main" not in install
    assert install.rstrip().endswith('evaluator --installed --source "$source"')


def test_requirements_refuse_a_checkout_that_is_not_the_pin(tmp_path):
    source, _ = _source(tmp_path, DECLARED)
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_requirements(source, _pin())
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_SOURCE_NOT_PINNED"


def test_requirements_refuse_a_pinned_checkout_changed_after_checkout(tmp_path):
    source, head = _source(tmp_path, DECLARED)
    (source / "stegcore.py").write_text("changed = True\n", encoding="utf-8")
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_requirements(source, {**_pin(), "commit": head})
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_SOURCE_NOT_PINNED"
    assert "working_tree_not_clean" in refused.value.document["failed_predicate"]


def test_the_installed_source_is_an_absolute_path_never_a_bare_name():
    # pip reads a bare name as a requirement, and an unrelated "stegcore" is on PyPI.
    install = _steps()[INSTALL_STEP]
    assert 'source="$RUNNER_TEMP/' in install
    assert 'pip install --no-deps "$source"' in install


def test_authority_fetch_checks_out_exactly_the_pinned_commit(tmp_path):
    origin, head = _source(tmp_path, DECLARED)
    pin = {**_pin(), "commit": head}
    fetched = decision.authority_fetch(tmp_path / "fetched", pin, url=origin.as_uri())
    assert (fetched["commit"], fetched["credential"]) == (head, "NONE_ANONYMOUS")
    assert fetched["source"] == str((tmp_path / "fetched").resolve())
    assert _git("rev-parse", "HEAD", cwd=tmp_path / "fetched") == head
    assert _git("status", "--porcelain", cwd=tmp_path / "fetched") == ""
    assert decision.authority_requirements(tmp_path / "fetched", pin) == pin["requirements"]


def test_authority_fetch_refuses_a_commit_the_repository_does_not_have(tmp_path):
    origin, _ = _source(tmp_path, DECLARED)
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_fetch(tmp_path / "fetched", {**_pin(), "commit": "0" * 40}, url=origin.as_uri())
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_NOT_ANONYMOUSLY_FETCHABLE"


def test_authority_fetch_refuses_an_existing_destination(tmp_path):
    origin, head = _source(tmp_path, DECLARED)
    (tmp_path / "fetched").mkdir()
    with pytest.raises(decision.Refusal) as refused:
        decision.authority_fetch(tmp_path / "fetched", {**_pin(), "commit": head}, url=origin.as_uri())
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_FETCH_DESTINATION_EXISTS"


def test_authority_fetch_cli_records_its_evidence(tmp_path, monkeypatch):
    origin, head = _source(tmp_path, DECLARED)
    monkeypatch.setattr(decision, "decision_authority_pin", lambda path=None: {**_pin(), "commit": head})
    real = decision.authority_fetch
    monkeypatch.setattr(decision, "authority_fetch", lambda dest, pin: real(dest, pin, url=origin.as_uri()))
    evidence = tmp_path / "evidence"
    assert decision.main(["--evidence", str(evidence), "authority-fetch", "--dest", str(tmp_path / "fetched")]) == 0
    assert json.loads((evidence / "authority_fetch.json").read_text())["commit"] == head


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


def test_evaluator_record_when_not_installed():
    pin = _pin()
    record = decision.evaluator_record(pin, installed=False)
    assert (record["installed"], record["reason"]) == (False, "STEGCORE_NOT_INSTALLED")
    assert record["dependency"].startswith("BLOCKED_DEPENDENCY: " + pin["repository"])


class _Installed:
    def __init__(self, direct_url):
        self.direct_url = direct_url

    def read_text(self, name):
        return json.dumps(self.direct_url) if name == "direct_url.json" and self.direct_url is not None else None


def _installed(monkeypatch, direct_url):
    from importlib import metadata
    imported = []
    monkeypatch.setattr(decision.importlib, "import_module", imported.append)
    monkeypatch.setattr(metadata, "version", lambda package: "0.0.0-under-test" if package == "stegcore" else None)
    monkeypatch.setattr(metadata, "distribution", lambda package: _Installed(direct_url))
    return imported


def test_evaluator_record_when_installed_names_commit_and_version(monkeypatch, tmp_path):
    imported = _installed(monkeypatch, {"url": tmp_path.resolve().as_uri(), "dir_info": {}})
    pin = _pin()
    assert decision.evaluator_record(pin, installed=True, source=tmp_path) == {
        "installed": True, "commit": pin["commit"], "version": "0.0.0-under-test"}
    assert imported == ["stegcore.steggate"]


@pytest.mark.parametrize("direct_url", [
    None,  # installed by name from an index: pip writes no direct_url.json
    {"url": "file:///elsewhere", "dir_info": {}},
    {"url": "https://files.pythonhosted.org/packages/stegcore-2.0.11-py3-none-any.whl", "archive_info": {}},
])
def test_evaluator_record_refuses_an_install_not_from_the_verified_checkout(monkeypatch, tmp_path, direct_url):
    _installed(monkeypatch, direct_url)
    with pytest.raises(decision.Refusal) as refused:
        decision.evaluator_record(_pin(), installed=True, source=tmp_path)
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_INSTALL_UNVERIFIED"
    assert "installed_from" in refused.value.document["failed_predicate"]


def test_evaluator_record_refuses_an_install_without_its_source(monkeypatch, tmp_path):
    _installed(monkeypatch, {"url": tmp_path.resolve().as_uri(), "dir_info": {}})
    with pytest.raises(decision.Refusal) as refused:
        decision.evaluator_record(_pin(), installed=True)
    assert refused.value.document["failure_code"] == "DECISION_AUTHORITY_INSTALL_UNVERIFIED"


def test_a_local_install_records_its_checkout_as_its_origin(tmp_path):
    # The binding the evaluator relies on, from a real (offline, --no-deps) pip install.
    source, _ = _source(tmp_path, [], name="stegverse-origin-fixture")
    (source / "pyproject.toml").write_text(
        '[project]\nname = "stegverse-origin-fixture"\nversion = "0"\n'
        '[build-system]\nrequires = []\nbuild-backend = "fixture_backend"\nbackend-path = ["."]\n', encoding="utf-8")
    (source / "fixture_backend.py").write_text(FIXTURE_BACKEND, encoding="utf-8")
    target = tmp_path / "site"
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "--no-index", "--no-build-isolation",
                    "--target", str(target), str(source)], check=True, capture_output=True, text=True)
    direct_url = json.loads(next(target.glob("*.dist-info/direct_url.json")).read_text())
    assert direct_url["url"] == source.resolve().as_uri()


FIXTURE_BACKEND = '''
import base64, hashlib, zipfile

NAME = "stegverse_origin_fixture-0"


def _record(entries):
    rows = []
    for path, data in entries:
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        rows.append(f"{path},sha256={digest},{len(data)}")
    rows.append(NAME + ".dist-info/RECORD,,")
    return "\\n".join(rows) + "\\n"


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    filename = NAME + "-py3-none-any.whl"
    entries = [(NAME + ".dist-info/METADATA", b"Metadata-Version: 2.1\\nName: stegverse-origin-fixture\\nVersion: 0\\n"),
               (NAME + ".dist-info/WHEEL", b"Wheel-Version: 1.0\\nGenerator: fixture\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n")]
    with zipfile.ZipFile(wheel_directory + "/" + filename, "w") as wheel:
        for path, data in entries:
            wheel.writestr(path, data)
        wheel.writestr(NAME + ".dist-info/RECORD", _record(entries))
    return filename
'''


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
    assert report["evaluator"]["reason"] == "STEGCORE_NOT_INSTALLED"
    installed = {"installed": True, "commit": _pin()["commit"], "version": "0.0.0-under-test"}
    (evidence / "evaluator.json").write_text(json.dumps(installed))
    report, _ = decision.build_report(evidence, mesh_root="git+https://github.com/StegVerse-org/.github#refs/x")
    assert report["decision_authority_installed"] is True
    assert report["decision_authority_commit"] == _pin()["commit"]
