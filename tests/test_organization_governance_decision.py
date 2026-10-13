"""The organization governance decision run, against temporary repositories only.

The source mesh is a local bare repository carrying a byte copy of the request
StegVerse-org published on its refs/stegverse/federation-mesh
(pkt-5efe4b0372bbffa4d2a356fe). This repository's own mesh ref, and its
designated organization ledger ref, are on another local bare repository.
Nothing here fetches from or pushes to the network.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/organization-governance-decision"
REQUEST_KEY = "frames.d/2b5863dc2dcdf6c79d27b5b24416e318269a86fe8f6ea324a59e8f28bcef60ca.json"
REQUEST_PACKET_ID = "pkt-5efe4b0372bbffa4d2a356fe"
REQUEST_FRAME_SHA256 = "sha256:909bb21e89c7bf6d37caf19acdbf5bcdaee455f0efaec059134fef9d0b247ae1"
ANSWER_PACKET_ID = ("governance:0d3494183d1c8a62ff5ab3408b34302e82a92a7fb75e48587edfedbc51013763"
                    ":response:stegverse-labs")
MESH_REF = "refs/stegverse/federation-mesh"

# The run opens the organization ledger exactly as org-contract.json declares it.
pytestmark = pytest.mark.repository_ledger_locus


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binding = _load("mesh_source_binding_under_test", "resident-runtime/mesh_source_binding.py")
decision = _load("organization_governance_decision_under_test",
                 "resident-runtime/organization_governance_decision.py")
ledger_store = _load("ledger_store_under_test", "resident-runtime/ledger_store.py")


def _stegcore_present() -> bool:
    return importlib.util.find_spec("stegcore") is not None


def _git(*args, cwd=None, data=None):
    return subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True, check=True).stdout


@pytest.fixture(autouse=True)
def _identity(monkeypatch):
    for variable in ("STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_STORE",
                     "STEGVERSE_ORG_LEDGER_GIT_REF", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY"):
        monkeypatch.delenv(variable, raising=False)
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "StegVerse")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "210078727+StegVerse@users.noreply.github.com")


def _mesh_repo(path: Path, frames: dict[str, bytes]) -> Path:
    """A bare repository whose mesh ref carries exactly `frames`."""
    _git("init", "-q", "--bare", str(path))
    env_git = ["--git-dir", str(path)]
    entries = []
    for key, raw in sorted(frames.items()):
        oid = subprocess.run(["git", *env_git, "hash-object", "-w", "--stdin"], input=raw,
                             capture_output=True, check=True).stdout.decode().strip()
        entries.append(f"100644 blob {oid}\t{key}")
    # mktree wants one level at a time; every frame sits directly under frames.d/.
    inner = "\n".join(line.replace("frames.d/", "") for line in entries) + "\n"
    sub = subprocess.run(["git", *env_git, "mktree"], input=inner.encode(), capture_output=True,
                         check=True).stdout.decode().strip()
    tree = subprocess.run(["git", *env_git, "mktree"], input=f"040000 tree {sub}\tframes.d\n".encode(),
                          capture_output=True, check=True).stdout.decode().strip()
    commit = subprocess.run(["git", *env_git, "commit-tree", "--no-gpg-sign", tree, "-m", "mesh"],
                            capture_output=True, check=True).stdout.decode().strip()
    _git(*env_git, "update-ref", MESH_REF, commit)
    return path


def _request_bytes() -> bytes:
    return (FIXTURE / REQUEST_KEY).read_bytes()


_DECLARED_LEDGER = decision._organization_ledger


def _ledger_published_to(origin: Path):
    """The repository's own declaration, with its publication target at the local `origin`.

    In the workflow the target is this repository on GitHub; here it is the
    same temporary repository that carries the own mesh ref, so nothing
    leaves the machine.
    """
    def load():
        module = _DECLARED_LEDGER()
        declared = module.C["organization_ledger"]
        module.C["organization_ledger"] = {**declared, "propagate_target": {
            **declared["propagate_target"], "remote": str(origin)}}
        return module
    return load


def _run(tmp: Path, source: Path, origin: Path, monkeypatch, *, ledgers: Path | None = None) -> dict:
    """One execution, as the workflow runs it: fresh work, mesh and node state."""
    run = tmp / ("run-" + str(len(list(tmp.glob("run-*")))))
    ledgers = ledgers or run
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", str(ledgers / "repo-ledger"))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_DIR", str(ledgers / "organization-ledger.git"))
    monkeypatch.setattr(decision, "_organization_ledger", _ledger_published_to(origin))
    materialization = decision.materialize(
        source_url=str(source), source_ref=MESH_REF, own_url=str(origin), own_ref=MESH_REF,
        work=run / "work", mesh=run / "mesh", emitting_organization="StegVerse-org")
    cycle = decision.run_cycle(mesh=run / "mesh", node_state=run / "node",
                               repo_ledger=ledgers / "repo-ledger", materialization=materialization)
    publication = decision.publish(mesh=run / "mesh", cycle=cycle, materialization=materialization,
                                   work=run / "work", own_ref=MESH_REF, remote=str(origin))
    ledger_publication = decision.publish_ledger()
    readback = decision.read_back(own_url=str(origin), own_ref=MESH_REF, publication=publication,
                                  materialization=materialization, work=run / "work")
    ledger_readback = decision.read_back_ledger(own_url=str(origin), work=run / "work")
    return {"run": run, "ledgers": ledgers, "materialization": materialization, "cycle": cycle,
            "publication": publication, "readback": readback, "ledger_publication": ledger_publication,
            "ledger_readback": ledger_readback}


def _own_frames(origin: Path) -> dict[str, bytes]:
    tip = _git("--git-dir", str(origin), "rev-parse", MESH_REF).decode().strip()
    names = _git("--git-dir", str(origin), "ls-tree", "-r", "--name-only", tip).decode().split()
    return {name: _git("--git-dir", str(origin), "cat-file", "blob", f"{tip}:{name}") for name in names}


# --- locator parsing -------------------------------------------------------

def test_valid_locator_binds_owner_repository_and_ref():
    bound = binding.parse_mesh_root("git+https://github.com/StegVerse-org/.github#refs/stegverse/federation-mesh")
    assert bound["url"] == "https://github.com/StegVerse-org/.github"
    assert bound["ref"] == MESH_REF
    assert bound["emitting_organization"] == "StegVerse-org"


@pytest.mark.parametrize("locator,code", [
    ("", "MESH_ROOT_LOCATOR_MALFORMED"),
    ("git+https://github.com/StegVerse-org#refs/stegverse/federation-mesh", "MESH_ROOT_LOCATOR_MALFORMED"),
    ("git+https://github.com/StegVerse-org/.github", "MESH_ROOT_LOCATOR_MALFORMED"),
    ("git+https://github.com/StegVerse-org/.github#refs/stegverse/../x", "MESH_ROOT_REF_NOT_QUALIFIED"),
    ("git+https://github.com/StegVerse-org/.github#refs/stegverse/mesh.lock", "MESH_ROOT_REF_NOT_QUALIFIED"),
    ("https://github.com/StegVerse-org/.github#refs/stegverse/federation-mesh", "MESH_ROOT_SOURCE_NOT_GITHUB"),
    ("git+https://gitlab.com/StegVerse-org/.github#refs/stegverse/federation-mesh", "MESH_ROOT_SOURCE_NOT_GITHUB"),
    ("git+ssh://git@github.com/StegVerse-org/.github#refs/stegverse/federation-mesh", "MESH_ROOT_SOURCE_NOT_GITHUB"),
    ("git+https://github.com/StegVerse-org/.github#federation-mesh", "MESH_ROOT_REF_NOT_QUALIFIED"),
    ("git+https://github.com/StegVerse-org/.github#heads/main", "MESH_ROOT_REF_NOT_QUALIFIED"),
])
def test_malformed_non_github_or_unqualified_locators_fail_closed(locator, code):
    with pytest.raises(binding.MeshSourceRefused) as refused:
        binding.parse_mesh_root(locator)
    assert refused.value.failure_code == code


def test_cli_refusal_is_six_field_fail_closed(tmp_path, capsys):
    status = binding.main(["--mesh-root", "git+https://github.com/StegVerse-org/.github#main",
                           "--out", str(tmp_path / "binding.json"), "--no-probe"])
    document = json.loads((tmp_path / "binding.json").read_text())
    assert status == 1
    assert document["disposition"] == "FAIL_CLOSED"
    for field in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                  "retry_entrypoint", "owning_existing_goal", "next_attempt"):
        assert document[field]
    assert document["owning_existing_goal"] == "SDK-MR-A-VALIDATION-CUSTODY-001"
    assert document["retry_entrypoint"] == ".github/workflows/organization-governance-decision.yml"


def test_source_not_fetchable_is_refused(tmp_path):
    with pytest.raises(binding.MeshSourceRefused) as refused:
        binding.probe_anonymous(str(tmp_path / "absent.git"), MESH_REF)
    assert refused.value.failure_code == "MESH_ROOT_SOURCE_NOT_ANONYMOUSLY_FETCHABLE"
    empty = tmp_path / "empty.git"
    _git("init", "-q", "--bare", str(empty))
    with pytest.raises(binding.MeshSourceRefused) as absent:
        binding.probe_anonymous(str(empty), MESH_REF)
    assert absent.value.failure_code == "MESH_ROOT_REF_ABSENT"


# --- end to end ------------------------------------------------------------

def test_fixture_is_the_real_frame():
    frame = json.loads(_request_bytes())
    assert frame["frame_sha256"] == REQUEST_FRAME_SHA256
    assert frame["packet_id"] == REQUEST_PACKET_ID
    assert decision.node_store.frame_key(frame) == REQUEST_KEY
    assert decision.kernel.recover_packet(frame)["destination"]["service"] == "stegverse-labs.governance"


def test_end_to_end_answers_the_emitting_organization_recorded_at_both_levels(tmp_path, monkeypatch):
    if _stegcore_present():
        pytest.skip("stegcore installed: the decision would be evaluated, not FAIL_CLOSED unavailable")
    source = _mesh_repo(tmp_path / "source.git", {REQUEST_KEY: _request_bytes()})
    origin = tmp_path / "own.git"
    _git("init", "-q", "--bare", str(origin))
    out = _run(tmp_path, source, origin, monkeypatch)

    [item] = out["cycle"]["items"]
    assert item["status"] == "CONSUMED"
    application = item["application_result"]
    assert application["disposition"] == "FAIL_CLOSED"
    assert application["reason"] == "GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE"
    assert out["cycle"]["organization_ledger"]["ref"] == "refs/stegverse/organization-ledger"
    assert out["cycle"]["organization_ledger"]["remote"] == str(origin)

    # Both levels: the decision's own receipts and the crossing's.
    repository = ledger_store.PosixLedgerStore(out["ledgers"] / "repo-ledger")
    organization = ledger_store.GitLedgerStore(out["ledgers"] / "organization-ledger.git",
                                               "refs/stegverse/organization-ledger")
    for receipts in (application, item["organization_record"]):
        assert repository.exists(ledger_store.receipt_key(receipts["repository_receipt_sha256"]))
        assert organization.exists(ledger_store.receipt_key(receipts["organization_receipt_sha256"]))

    [answer] = out["publication"]["frames"]
    assert out["publication"]["published"] is True
    assert answer["packet_id"] == ANSWER_PACKET_ID
    assert answer["destination_org"] == "StegVerse-org"
    own = _own_frames(origin)
    assert list(own) == [answer["key"]]
    [read] = out["readback"]["answers"]
    assert read["recovered"] and read["request_packet_id"] == REQUEST_PACKET_ID
    assert read["destination"]["org"] == "StegVerse-org"
    assert (read["disposition"], read["reason"]) == ("FAIL_CLOSED", "GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE")
    assert read["repository_receipt_sha256"] == application["repository_receipt_sha256"]

    # The ledger is published to the designated ref after the mesh and read back fresh:
    # the decision's and the crossing's organization receipts are both on the chain.
    published = _git("--git-dir", str(origin), "rev-parse", "refs/stegverse/organization-ledger").decode().strip()
    assert out["ledger_publication"]["tip"] == published == out["ledger_readback"]["tip"]
    chain = out["ledger_readback"]["chain"]
    assert out["ledger_readback"]["verified"] is True and len(chain) == out["ledger_readback"]["chain_length"]
    for receipts in (application, item["organization_record"]):
        assert receipts["organization_receipt_sha256"] in chain


def test_replay_is_a_write_once_no_op(tmp_path, monkeypatch):
    source = _mesh_repo(tmp_path / "source.git", {REQUEST_KEY: _request_bytes()})
    origin = tmp_path / "own.git"
    _git("init", "-q", "--bare", str(origin))
    ledgers = tmp_path / "ledgers"
    first = _run(tmp_path, source, origin, monkeypatch, ledgers=ledgers)
    tip = _git("--git-dir", str(origin), "rev-parse", MESH_REF)
    own = _own_frames(origin)
    repository_before = sorted(p.name for p in (ledgers / "repo-ledger").rglob("*.json"))
    organization_before = _git("--git-dir", str(ledgers / "organization-ledger.git"), "rev-parse",
                               "refs/stegverse/organization-ledger")

    second = _run(tmp_path, source, origin, monkeypatch, ledgers=ledgers)
    assert second["materialization"]["already_answered"][0]["request"]["packet_id"] == REQUEST_PACKET_ID
    assert second["cycle"]["items"] == [] and second["cycle"]["new_frames"] == []
    assert second["publication"] == {"published": False, "reason": "NO_NEW_FRAMES_PRODUCED", "ref": MESH_REF,
                                     "parent": tip.decode().strip(), "commit": None, "frames": []}
    assert _git("--git-dir", str(origin), "rev-parse", MESH_REF) == tip
    assert _own_frames(origin) == own
    # No receipt added, so none conflicts.
    assert sorted(p.name for p in (ledgers / "repo-ledger").rglob("*.json")) == repository_before
    assert _git("--git-dir", str(ledgers / "organization-ledger.git"), "rev-parse",
                "refs/stegverse/organization-ledger") == organization_before
    # The answer already published is still read back and recovered.
    [read] = second["readback"]["answers"]
    assert read["key"] == first["publication"]["frames"][0]["key"]
    # Nothing new was appended, so the published ledger did not move.
    assert second["ledger_readback"]["tip"] == first["ledger_readback"]["tip"]


def test_tampered_frame_is_refused_and_produces_no_answer(tmp_path, monkeypatch):
    frame = json.loads(_request_bytes())
    frame["frame_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="carrier_frame_hash_mismatch"):
        decision.kernel.recover_packet(frame)
    raw = (json.dumps(frame, indent=2, sort_keys=True) + "\n").encode()
    source = _mesh_repo(tmp_path / "source.git", {REQUEST_KEY: raw})
    origin = tmp_path / "own.git"
    _git("init", "-q", "--bare", str(origin))
    out = _run(tmp_path, source, origin, monkeypatch)
    [refused] = out["materialization"]["refused_frames"]
    assert refused["key"] == REQUEST_KEY
    assert refused["reason"].startswith("recover_packet_refused:carrier_frame_hash_mismatch")
    assert out["cycle"]["items"] == [] and out["cycle"]["new_frames"] == []
    assert out["publication"]["published"] is False
    assert subprocess.run(["git", "--git-dir", str(origin), "rev-parse", "--verify", "-q", MESH_REF],
                          capture_output=True).returncode != 0


def test_frame_under_a_mismatched_key_is_refused(tmp_path):
    wrong = "frames.d/" + "1" * 64 + ".json"
    frame, packet, reason = decision.verify_frame(wrong, _request_bytes())
    assert frame is None and reason == "frame_key_mismatch"


def test_union_refuses_a_same_key_content_difference():
    original = _request_bytes()
    frame = json.loads(original)
    frame["channel"] = dict(frame["channel"], phase_slot=99)
    with pytest.raises(decision.Refusal) as refused:
        decision.union_frames({REQUEST_KEY: original}, {REQUEST_KEY: json.dumps(frame).encode()})
    assert refused.value.document["failure_code"] == "ORGANIZATION_MESH_UNION_CONFLICT"
    assert refused.value.document["owning_existing_goal"] == "SDK-MR-A-VALIDATION-CUSTODY-001"
    # The same content is a union, not a conflict.
    assert decision.union_frames({REQUEST_KEY: original}, {REQUEST_KEY: original}) == {REQUEST_KEY: original}


def test_lost_race_is_refused_not_forced(tmp_path, monkeypatch):
    source = _mesh_repo(tmp_path / "source.git", {REQUEST_KEY: _request_bytes()})
    origin = tmp_path / "own.git"
    _git("init", "-q", "--bare", str(origin))
    run = tmp_path / "race"
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", str(run / "repo-ledger"))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_DIR", str(run / "organization-ledger.git"))
    materialization = decision.materialize(
        source_url=str(source), source_ref=MESH_REF, own_url=str(origin), own_ref=MESH_REF,
        work=run / "work", mesh=run / "mesh", emitting_organization="StegVerse-org")
    cycle = decision.run_cycle(mesh=run / "mesh", node_state=run / "node", repo_ledger=run / "repo-ledger",
                               materialization=materialization)
    # Another publisher creates the ref first.
    other = _mesh_repo(tmp_path / "other.git", {"frames.d/" + "2" * 64 + ".json": b"{}\n"})
    _git("--git-dir", str(other), "push", "-q", str(origin), MESH_REF + ":" + MESH_REF)
    with pytest.raises(decision.Refusal) as refused:
        decision.publish(mesh=run / "mesh", cycle=cycle, materialization=materialization,
                         work=run / "work", own_ref=MESH_REF, remote=str(origin))
    assert refused.value.document["failure_code"] == "ORGANIZATION_MESH_PUBLISH_RACE"



def test_report_fails_closed_when_addressed_frame_has_no_decision(tmp_path):
    """A workflow must not report completion for an unhandled addressed request."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    request_key = REQUEST_KEY
    (evidence / "materialization.json").write_text(json.dumps({
        "addressed_to_organization": [request_key],
        "already_answered": [],
        "source": {"tip": "a" * 40},
    }))
    (evidence / "cycle.json").write_text(json.dumps({"items": []}))
    report, status = decision.build_report(evidence, mesh_root="fixture")
    assert status == 1
    assert report["workflow_disposition"] == "FAIL_CLOSED"
    failure = report["fail_closed"]
    assert failure["failure_code"] == "ORGANIZATION_GOVERNANCE_DECISION_MISSING"
    assert request_key in failure["failed_predicate"]
    for field in ("disposition", "failure_code", "failed_predicate",
                  "required_evidence_or_repair", "retry_entrypoint",
                  "owning_existing_goal", "next_attempt"):
        assert failure[field]
    assert report["decisions"] == []


def test_report_refuses_local_decision_without_fresh_ref_readback(tmp_path):
    """A local ALLOW is not proof of an authenticated receiver return."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "materialization.json").write_text(json.dumps({
        "addressed_to_organization": [REQUEST_KEY], "already_answered": []
    }))
    (evidence / "cycle.json").write_text(json.dumps({"items": [{
        "frame_key": REQUEST_KEY, "request_packet_id": REQUEST_PACKET_ID,
        "application_result": {"disposition": "ALLOW"},
    }]}))
    report, status = decision.build_report(evidence, mesh_root="fixture")
    assert status == 1
    assert report["workflow_disposition"] == "FAIL_CLOSED"
    assert report["fail_closed"]["failure_code"] == "ORGANIZATION_GOVERNANCE_READBACK_NOT_VERIFIED"
    assert report["decisions"][0]["disposition"] == "ALLOW"


def test_report_names_the_crossing_predicate_for_a_refused_addressed_frame(tmp_path):
    """A crossing refused FAIL_CLOSED keeps its own predicate; it is not reported as a missing decision."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "materialization.json").write_text(json.dumps({
        "addressed_to_organization": [REQUEST_KEY], "already_answered": []
    }))
    (evidence / "cycle.json").write_text(json.dumps({"items": [{
        "frame_key": REQUEST_KEY, "status": "REFUSED", "disposition": "FAIL_CLOSED",
        "failed_predicate": "FIXTURE_CROSSING_PRECONDITION"}]}))
    report, status = decision.build_report(evidence, mesh_root="fixture")
    assert status == 1
    failure = report["fail_closed"]
    assert failure["failure_code"] == "ORGANIZATION_CROSSING_FAIL_CLOSED"
    assert "FIXTURE_CROSSING_PRECONDITION" in failure["failed_predicate"]


def test_report_refuses_verified_but_unrelated_receiver_answer(tmp_path):
    """A fresh verified ref cannot satisfy a different packet's decision."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "materialization.json").write_text(json.dumps({
        "addressed_to_organization": [REQUEST_KEY], "already_answered": []
    }))
    (evidence / "cycle.json").write_text(json.dumps({"items": [{
        "frame_key": REQUEST_KEY, "request_packet_id": REQUEST_PACKET_ID,
        "application_result": {
            "disposition": "DENY",
            "repository_receipt_sha256": "sha256:repo",
            "organization_receipt_sha256": "sha256:org"
        }
    }]}))
    (evidence / "readback.json").write_text(json.dumps({
        "verified": True, "answers": [{
            "request_packet_id": "unrelated-packet", "disposition": "DENY",
            "repository_receipt_sha256": "sha256:repo",
            "organization_receipt_sha256": "sha256:org"
        }]
    }))
    report, status = decision.build_report(evidence, mesh_root="fixture")
    assert status == 1
    assert report["fail_closed"]["failure_code"] == "ORGANIZATION_GOVERNANCE_ANSWER_BINDING_MISMATCH"


def test_report_accepts_matching_verified_receiver_answer(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "materialization.json").write_text(json.dumps({
        "addressed_to_organization": [REQUEST_KEY], "already_answered": []
    }))
    (evidence / "cycle.json").write_text(json.dumps({"items": [{
        "frame_key": REQUEST_KEY, "request_packet_id": REQUEST_PACKET_ID,
        "application_result": {
            "disposition": "DENY",
            "repository_receipt_sha256": "sha256:repo",
            "organization_receipt_sha256": "sha256:org"
        }
    }]}))
    (evidence / "readback.json").write_text(json.dumps({
        "verified": True, "answers": [{
            "request_packet_id": REQUEST_PACKET_ID, "disposition": "DENY",
            "repository_receipt_sha256": "sha256:repo",
            "organization_receipt_sha256": "sha256:org"
        }]
    }))
    (evidence / "ledger_readback.json").write_text(json.dumps({
        "verified": True, "chain": ["sha256:genesis", "sha256:org"]}))
    report, status = decision.build_report(evidence, mesh_root="fixture")
    assert status == 0
    assert report["workflow_disposition"] == "COMPLETED"


def test_report_malformed_fresh_ref_answers_fail_closed(tmp_path):
    for answers in ({"unexpected": "mapping"}, ["not-an-answer"], [None]):
        evidence = tmp_path / "evidence"
        evidence.mkdir(exist_ok=True)
        (evidence / "materialization.json").write_text(json.dumps({
            "addressed_to_organization": [REQUEST_KEY], "already_answered": []
        }))
        (evidence / "cycle.json").write_text(json.dumps({"items": [{
            "frame_key": REQUEST_KEY, "request_packet_id": REQUEST_PACKET_ID,
            "application_result": {"disposition": "DENY",
                                   "repository_receipt_sha256": "sha256:repo",
                                   "organization_receipt_sha256": "sha256:org"}
        }]}))
        (evidence / "readback.json").write_text(json.dumps({
            "verified": True, "answers": answers
        }))
        report, status = decision.build_report(evidence, mesh_root="fixture")
        assert status == 1
        assert report["workflow_disposition"] == "FAIL_CLOSED"
        failure = report["fail_closed"]
        assert failure["failure_code"] == "ORGANIZATION_GOVERNANCE_ANSWER_BINDING_MISMATCH"
        for field in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                      "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            assert failure[field]


def test_report_refuses_a_decision_whose_receipt_is_not_on_the_published_ledger(tmp_path):
    """The deciding receipt is evidence only once read back from the published ledger ref."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "materialization.json").write_text(json.dumps({
        "addressed_to_organization": [REQUEST_KEY], "already_answered": []}))
    (evidence / "cycle.json").write_text(json.dumps({"items": [{
        "frame_key": REQUEST_KEY, "request_packet_id": REQUEST_PACKET_ID,
        "application_result": {"disposition": "DENY", "repository_receipt_sha256": "sha256:repo",
                               "organization_receipt_sha256": "sha256:org"}}]}))
    (evidence / "readback.json").write_text(json.dumps({
        "verified": True, "answers": [{"request_packet_id": REQUEST_PACKET_ID, "disposition": "DENY",
                                       "repository_receipt_sha256": "sha256:repo",
                                       "organization_receipt_sha256": "sha256:org"}]}))
    for ledger in (None, {"verified": True, "chain": ["sha256:genesis"]}, {"verified": False, "chain": ["sha256:org"]}):
        target = evidence / "ledger_readback.json"
        if ledger is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(json.dumps(ledger))
        report, status = decision.build_report(evidence, mesh_root="fixture")
        assert status == 1
        assert report["fail_closed"]["failure_code"] == "ORGANIZATION_LEDGER_READBACK_NOT_VERIFIED"
        assert REQUEST_PACKET_ID in report["fail_closed"]["failed_predicate"]


# Every ACTION is by manifest: a committed decision request supplies the emitting
# organization's mesh, and the push that lands it starts the run; no dispatch is
# required and none is awaited.
def _decision_request(tmp_path, monkeypatch, **overrides):
    document = {"schema": binding.DECISION_REQUEST_SCHEMA, "owning_existing_goal": "SDK-MR-A-VALIDATION-CUSTODY-001",
                "mesh_root": "git+https://github.com/StegVerse-org/.github#refs/stegverse/federation-mesh"}
    document.update(overrides)
    relative = binding.DECISION_REQUEST_DIR + "R1.json"
    (tmp_path / binding.DECISION_REQUEST_DIR).mkdir(parents=True, exist_ok=True)
    (tmp_path / relative).write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return relative


def test_a_committed_decision_request_supplies_the_mesh_without_a_dispatch(tmp_path, monkeypatch):
    result = binding.resolve_mesh_root("", [_decision_request(tmp_path, monkeypatch)])
    assert result["disposition"] == "ALLOW"
    assert result["mesh_root"] == "git+https://github.com/StegVerse-org/.github#refs/stegverse/federation-mesh"
    assert result["source"].startswith("COMMITTED_DECISION_REQUEST:")


def test_a_dispatched_mesh_is_used_unchanged():
    result = binding.resolve_mesh_root("git+https://github.com/StegVerse-org/.github#refs/x", [])
    assert (result["disposition"], result["source"]) == ("ALLOW", "WORKFLOW_DISPATCH")


@pytest.mark.parametrize("overrides", [{"schema": "other"}, {"mesh_root": ""}, {"mesh_root": "git+x#refs/a\nX=1"},
                                       {"owning_existing_goal": ""}])
def test_an_invalid_decision_request_fails_closed_with_six_fields(tmp_path, monkeypatch, overrides):
    result = binding.resolve_mesh_root("", [_decision_request(tmp_path, monkeypatch, **overrides)])
    assert result["disposition"] == "FAIL_CLOSED"
    for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                  "owning_existing_goal", "next_attempt"):
        assert result[field]


def test_a_run_resolves_exactly_one_committed_decision_request():
    assert binding.resolve_mesh_root("", [])["failure_code"] == "DECISION_REQUEST_NOT_SINGULAR"
    two = [binding.DECISION_REQUEST_DIR + "a.json", binding.DECISION_REQUEST_DIR + "b.json"]
    assert binding.resolve_mesh_root("", two)["failure_code"] == "DECISION_REQUEST_NOT_SINGULAR"


def test_the_workflow_starts_on_a_committed_decision_request_and_resolves_before_binding():
    text = (ROOT / ".github/workflows/organization-governance-decision.yml").read_text(encoding="utf-8")
    trigger = text.split("on:", 1)[1].split("concurrency:", 1)[0]
    assert ".stegverse/governance-decision-requests/**" in trigger
    assert "      MESH_ROOT: ${{ inputs.mesh_root }}" not in text  # no job-level dispatch-only binding
    assert text.index("--resolve-changed") < text.index("- name: Bind the source")
