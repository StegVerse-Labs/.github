"""The COMPONENT_010 request builder refuses until the canonical records declare its manifest."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_optical_component_010_org_request.py"
SPEC = importlib.util.spec_from_file_location("build_optical_component_010_org_request", SCRIPT)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)

SIX_FIELDS = ("disposition", "failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _records(tmp_path: Path, declaration: dict | None = None) -> Path:
    for relative in (builder.TASK_RECORD, builder.COMPONENT_PROFILE):
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, tmp_path / relative)
    if declaration is not None:
        path = tmp_path / builder.TASK_RECORD
        record = json.loads(path.read_text(encoding="utf-8"))
        record["component_010_manifest_declaration"] = declaration
        path.write_text(json.dumps(record), encoding="utf-8")
    return tmp_path


def _declaration() -> dict:
    payload = {"task_id": builder.GOAL, "session_id": "s", "actor_kind": "a",
               "checkin_context_or_exact_registry_disposition": "c"}
    return {
        "transition_id": builder.TRANSITION,
        "manifest": {"source_framework": "f", "source_output_id": "o", "created_at": "t",
                     "declared_intent": "i", "requested_consequence": "q", "payload": payload,
                     "extensions": {"stegverse_route": {"route_id": "r"}}},
        "standing": {"mode": "ESTABLISH_GENESIS", "node_ref": "StegVerse-Labs/.github", "predecessor": None},
    }


def _refusal(**kwargs) -> dict:
    with pytest.raises(builder.Refusal) as caught:
        builder.build_request(**kwargs)
    return caught.value.record


def test_current_records_fail_closed_naming_every_undeclared_input():
    record = _refusal()
    for field in SIX_FIELDS:
        assert record[field], field
    assert record["disposition"] == "FAIL_CLOSED"
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"
    assert record["owning_existing_goal"] == "OPTICAL-PHYSICAL-STATE-REPLAY-RESEARCH-001"
    assert record["consequence_committed"] is False
    assert record["declarations_found"] == 0
    component = "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010."
    assert set(record["missing_inputs"]) == {
        component + "session_id", component + "actor_kind",
        component + "checkin_context_or_exact_registry_disposition",
        *builder.SDK_MANIFEST_INPUTS, *builder.STANDING_INPUTS}
    # The task id is the canonical goal, so it is never reported missing.
    assert component + "task_id" not in record["missing_inputs"]
    assert "ORGANIZATION_LEDGER_LOCK" in record["satisfying_edge"]


def test_main_builds_from_the_organization_root_and_writes_nothing_on_refusal(tmp_path, capsys):
    root = _records(tmp_path)
    assert builder.main(["--organization-root", str(root)]) == 2
    assert not (root / builder.REQUEST_PATH).exists()
    printed = json.loads(capsys.readouterr().out)
    assert printed["failure_code"] == "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"


def test_main_reads_the_records_of_the_organization_root_it_is_given(tmp_path, capsys):
    # A root without the canonical records is refused; the script's own
    # checkout is never read in its place.
    assert builder.main(["--organization-root", str(tmp_path)]) == 2
    printed = json.loads(capsys.readouterr().out)
    assert printed["failure_code"] == "COMPONENT_010_CANONICAL_RECORDS_UNREADABLE"
    assert str(tmp_path.resolve()) in printed["detail"]
    for field in SIX_FIELDS:
        assert printed[field], field
    assert not (tmp_path / builder.REQUEST_PATH).exists()


def test_a_partial_declaration_still_names_what_it_lacks(tmp_path):
    declaration = _declaration()
    del declaration["manifest"]["payload"]["session_id"]
    del declaration["standing"]
    record = _refusal(root=_records(tmp_path, declaration))
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"
    assert record["declarations_found"] == 1
    assert set(record["missing_inputs"]) == {
        "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010.session_id", *builder.STANDING_INPUTS}


def test_a_build_manifest_form_is_not_built_here(tmp_path):
    declaration = _declaration()
    declaration["build_manifest"] = {}
    record = _refusal(root=_records(tmp_path, declaration))
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"


def test_a_complete_declaration_refuses_until_its_digests_are_pinned(tmp_path):
    root = _records(tmp_path, _declaration())
    record = _refusal(root=root, canonical_of=lambda m: "c" * 64, validate_of=lambda m: None,
                      pins={"MANIFEST_FILE_SHA256": None, "CANONICAL_MANIFEST_SHA256": None,
                            "REQUEST_FILE_SHA256": None})
    assert record["failure_code"] == "COMPONENT_010_REQUEST_DIGEST_NOT_PINNED"
    assert record["failed_predicate"] == "MANIFEST_FILE_SHA256 is pinned in this builder"


def test_a_pinned_declaration_builds_a_deterministic_request_bound_to_the_canonical_digest(tmp_path):
    root = _records(tmp_path, _declaration())
    manifest = json.loads(builder.manifest_file_bytes(_declaration()["manifest"]))
    canonical = "c" * 64
    pins = {"MANIFEST_FILE_SHA256": hashlib.sha256(builder.manifest_file_bytes(manifest)).hexdigest(),
            "CANONICAL_MANIFEST_SHA256": canonical, "REQUEST_FILE_SHA256": None}
    unpinned = _refusal(root=root, canonical_of=lambda m: canonical, validate_of=lambda m: None, pins=pins)
    assert unpinned["failure_code"] == "COMPONENT_010_REQUEST_DIGEST_NOT_PINNED"
    pins["REQUEST_FILE_SHA256"] = unpinned["observed_sha256"]
    request, data = builder.build_request(root=root, canonical_of=lambda m: canonical, validate_of=lambda m: None, pins=pins)
    again = builder.build_request(root=root, canonical_of=lambda m: canonical, validate_of=lambda m: None,
                          pins=copy.deepcopy(pins))[1]
    assert data == again
    assert request["schema"] == "stegverse.organization-transition-request/v1"
    assert request["expected_canonical_manifest_sha256"] == canonical
    assert ("manifest" in request) and ("build_manifest" not in request)
    assert request["owning_existing_goal"] and "predecessor" in request["standing"]
    assert builder.REQUEST_PATH.startswith(".stegverse/transition-requests/")


def test_a_digest_that_drifts_from_its_pin_is_refused(tmp_path):
    root = _records(tmp_path, _declaration())
    record = _refusal(root=root, canonical_of=lambda m: "c" * 64, validate_of=lambda m: None,
                      pins={"MANIFEST_FILE_SHA256": "0" * 64, "CANONICAL_MANIFEST_SHA256": None,
                            "REQUEST_FILE_SHA256": None})
    assert record["failure_code"] == "COMPONENT_010_REQUEST_DIGEST_MISMATCH"
    assert record["expected_sha256"] == "0" * 64


def _fill(value, sentinel):
    if isinstance(value, dict):
        return {k: _fill(v, sentinel) for k, v in value.items()}
    return sentinel


@pytest.mark.parametrize("sentinel", ["OWNER_PLACEHOLDER", "OWNER_PLACEHOLDER_SESSION", "<session id>", "", "  "])
def test_an_all_placeholder_declaration_is_refused_before_any_digest(tmp_path, sentinel):
    declaration = _fill(_declaration(), sentinel)
    declaration["transition_id"] = builder.TRANSITION

    def never(manifest):
        raise AssertionError("no digest or contract check runs on a placeholder declaration")

    record = _refusal(root=_records(tmp_path, declaration), canonical_of=never, validate_of=never)
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"
    assert record["declarations_found"] == 1
    expected = {
        "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010." + n
        for n in ("session_id", "actor_kind", "checkin_context_or_exact_registry_disposition")
    } | set(builder.SDK_MANIFEST_INPUTS) | set(builder.STANDING_INPUTS)
    if not sentinel.strip():
        # Emptiness nested inside an object is not itself a placeholder; the
        # empty session fields inside the payload are still each reported.
        expected -= {"manifest.payload_or_payload_commitment", "manifest.extensions.stegverse_route"}
    assert set(record["missing_inputs"]) == expected


def test_a_placeholder_nested_in_a_declared_value_is_missing(tmp_path):
    declaration = _declaration()
    declaration["manifest"]["extensions"]["stegverse_route"] = {"route_id": "<route>"}
    declaration["manifest"]["payload"]["actor_kind"] = {"kind": "OWNER_PLACEHOLDER"}
    record = _refusal(root=_records(tmp_path, declaration))
    assert set(record["missing_inputs"]) == {
        "manifest.extensions.stegverse_route", "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010.actor_kind",
        # actor_kind is inside the payload, so the payload carries a placeholder too.
        "manifest.payload_or_payload_commitment"}


def test_a_manifest_the_ingress_contract_refuses_is_refused_before_any_digest(tmp_path):
    def invalid(manifest):
        raise ValueError("manifest_profile must be stegverse.ingress-manifest")

    def never(manifest):
        raise AssertionError("no canonical digest for a manifest the ingress would refuse")

    record = _refusal(root=_records(tmp_path, _declaration()), canonical_of=never, validate_of=invalid)
    for field in SIX_FIELDS:
        assert record[field], field
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_CONTRACT_INVALID"
    assert "validate_ingress_manifest" in record["failed_predicate"]
    assert "manifest_profile" in record["detail"]


def test_the_default_contract_check_is_the_ingress_sdk_and_refuses_without_it(tmp_path, monkeypatch):
    def unavailable(*_):
        raise ModuleNotFoundError("No module named 'stegverse'")

    monkeypatch.setattr(builder, "ingress_module", unavailable)
    record = _refusal(root=_records(tmp_path, _declaration()))
    assert record["failure_code"] == "COMPONENT_010_INGRESS_SDK_UNAVAILABLE"
    assert record["consequence_committed"] is False


def test_a_placeholder_anywhere_in_the_manifest_is_missing(tmp_path):
    declaration = _declaration()
    declaration["manifest"]["source_instance"] = "placeholder-instance"
    declaration["manifest"]["context_refs"] = ["TODO: link the session", "https://example.invalid/ok"]
    declaration["manifest"]["manifest_labels"] = {"owner": "tbd"}
    declaration["standing"]["node_ref"] = "TBD"
    record = _refusal(root=_records(tmp_path, declaration))
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"
    assert set(record["missing_inputs"]) == {
        "manifest.source_instance", "manifest.context_refs[0]", "manifest.manifest_labels.owner",
        "standing.node_ref"}


def test_an_ingress_derivation_refusal_is_a_six_field_refusal(tmp_path):
    def mismatch(manifest):
        raise ValueError("MANIFEST_PROCESSING_CAPABILITY_ROUTE_MISMATCH: manifest processing capability "
                         "does not select governance")

    root = _records(tmp_path, _declaration())
    record = _refusal(root=root, canonical_of=mismatch, validate_of=lambda m: None)
    for field in SIX_FIELDS:
        assert record[field], field
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INGRESS_CANONICAL_REFUSED"
    assert "MANIFEST_PROCESSING_CAPABILITY_ROUTE_MISMATCH" in record["detail"]
    assert record["consequence_committed"] is False
    assert not (root / builder.REQUEST_PATH).exists()


# StegVerse-SDK inspection/examples/external-framework-generic-manifest.json at
# d6873d84dddc91ef6b26774336b05c8e1f4042c0, the SDK commit org-runtime-boundary.yml
# pins, copied unchanged (sha256 e15ec3fd92da469c5c9d544784727cb00787badca7300a80d5eb2049c0237354).
SDK_EXAMPLE = ROOT / "tests" / "fixtures" / "sdk-external-framework-generic-manifest.json"
SDK_EXAMPLE_SHA256 = "e15ec3fd92da469c5c9d544784727cb00787badca7300a80d5eb2049c0237354"
requires_sdk = pytest.mark.skipif(
    importlib.util.find_spec("stegverse") is None,
    reason="StegVerse-SDK is not installed here; the ingress validator and derivation are the SDK's own")


def test_the_sdk_example_fixture_is_the_pinned_sdk_file():
    assert hashlib.sha256(SDK_EXAMPLE.read_bytes()).hexdigest() == SDK_EXAMPLE_SHA256


def _sdk_declaration() -> dict:
    from stegverse.manifest_contract import canonical_sha256

    manifest = json.loads(SDK_EXAMPLE.read_text(encoding="utf-8"))
    manifest["payload"] = _declaration()["manifest"]["payload"]
    manifest["hashes"]["payload_sha256"] = canonical_sha256(manifest["payload"])
    return {"transition_id": builder.TRANSITION, "manifest": manifest,
            "standing": _declaration()["standing"]}


def _sdk_root(tmp_path: Path, declaration: dict) -> Path:
    root = _records(tmp_path, declaration)
    for directory in ("resident-runtime", "org-runtime", "org-boundary", ".stegverse"):
        (root / directory).symlink_to(ROOT / directory, target_is_directory=True)
    return root


@requires_sdk
def test_a_manifest_the_real_sdk_admits_reaches_the_pin_stage(tmp_path):
    root = _sdk_root(tmp_path, _sdk_declaration())
    record = _refusal(root=root)
    assert record["failure_code"] == "COMPONENT_010_REQUEST_DIGEST_NOT_PINNED"
    assert record["failed_predicate"] == "MANIFEST_FILE_SHA256 is pinned in this builder"
    assert not (root / builder.REQUEST_PATH).exists()


@requires_sdk
def test_a_capability_its_route_does_not_select_is_refused_with_six_fields(tmp_path):
    declaration = _sdk_declaration()
    declaration["manifest"]["processing"]["capability"] = "ecosystem_diagnostic"
    root = _sdk_root(tmp_path, declaration)
    assert builder.main(["--organization-root", str(root)]) == 2
    assert not (root / builder.REQUEST_PATH).exists()
    record = _refusal(root=root)
    for field in SIX_FIELDS:
        assert record[field], field
    assert record["failure_code"] == "COMPONENT_010_MANIFEST_INGRESS_CANONICAL_REFUSED"
    assert "MANIFEST_PROCESSING_CAPABILITY_ROUTE_MISMATCH" in record["detail"]
