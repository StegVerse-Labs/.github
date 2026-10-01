"""ORGANIZATION-ROLE-DEPLOYMENT-PACKET-001 source regressions.

Source validation only. Nothing here claims runtime observation or deploys anything
to another organization.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "data" / "organization-role-deployment" / "packet.v1.json"
VERIFIER = ROOT / "scripts" / "verify_organization_role_deployment.py"
DOC = ROOT / "docs" / "ORGANIZATION_ROLE_PER_ORG_DEPLOYMENT.md"

REPO_RECEIPT = "stegverse.repo-transition-receipt/v1"
CANONICAL_RECEIPT = "stegverse.canonical-state-transition-receipt/v1"
NON_ALLOW_FIELDS = (
    "failure_code", "failed_predicate", "required_evidence_or_repair",
    "retry_entrypoint", "owning_existing_goal", "next_attempt",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_verifier(org_root: Path) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--org-root", str(org_root)],
        cwd=ROOT, text=True, capture_output=True,
    )
    return proc.returncode, json.loads(proc.stdout)


def write_org(root: Path, *, contract: dict | None, aggregator: str | None,
              declaration: bool = True, register: bool = True) -> Path:
    """Materialize a minimal organization .github tree for verification."""
    if contract is not None:
        path = root / ".stegverse" / "transition-ledger" / "org-contract.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    if aggregator is not None:
        path = root / "resident-runtime" / "aggregate_repo_transition.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(aggregator, encoding="utf-8")
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    if declaration:
        (data / "organization-role-runtime-reality-deployment.json").write_text(
            json.dumps({"schema": "stegverse.organization-role-runtime-reality-deployment/v1"}),
            encoding="utf-8")
    if register:
        (data / "organization-role-exemption-register.json").write_text(
            json.dumps({"schema": "stegverse.organization-role-exemption-register/v1"}),
            encoding="utf-8")
    return root


def deployed_contract(organization: str = "Example-Org") -> dict:
    return {
        "schema": "stegverse.organization-transition-ledger-contract/v1",
        "organization": organization,
        "ledger_level": "ORGANIZATION",
        "consumes": [REPO_RECEIPT, CANONICAL_RECEIPT],
        "emits": "stegverse.organization-transition-receipt/v1",
        "organization_scope_rule":
            "EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT",
        "preserves_source_transition_receipt": True,
        "append_only_receipts": True,
        "runtime_reality_authority": "Organization",
        "ledger_root_is_organization_runtime_reality_locus": True,
        "ledger_lock": "ORGANIZATION_LEDGER_LOCK",
        "write_mode": "MANIFEST_DIRECTED_APPEND",
        "propagation_role": "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER",
        "propagation_gates_organization_runtime_reality": False,
        "propagation_receiver_unavailable_disposition":
            "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "always_on_receiver_required": False,
        "authority_effect": "NONE_CONTRACT_ONLY",
    }


GENERIC_AGGREGATOR = (
    "allowed = C.get('consumes')\n"
    "if isinstance(allowed, str): allowed = [allowed]\n"
    "if schema not in allowed: raise ValueError('mismatch')\n"
    f"# handles {CANONICAL_RECEIPT} by its own digest\n"
)
REPO_ONLY_AGGREGATOR = (
    "def verify_repo(receipt):\n"
    f"    if receipt.get('schema') != '{REPO_RECEIPT}':\n"
    "        raise SystemExit('repo receipt schema mismatch')\n"
)


def test_packet_grants_no_authority_and_mutates_no_other_organization():
    packet = load(PACKET)
    assert packet["schema"] == "stegverse.organization-role-deployment-packet/v1"
    assert packet["authority_effect"] == "NONE_PACKET_ONLY"
    assert packet["evidence_class"] == "SOURCE_IMPLEMENTED"
    assert packet["deployment_is_per_organization"] is True
    assert packet["packet_mutates_other_organizations"] is False
    assert "MUTATE_ANY_OTHER_ORGANIZATION" in packet["this_packet_does_not"]
    assert "CLAIM_RUNTIME_OBSERVATION" in packet["this_packet_does_not"]
    assert "REQUIRE_AN_EXTERNAL_MACHINE_OR_SECOND_DEVICE" in packet["this_packet_does_not"]


def test_target_state_requires_both_receipt_schemas():
    required = load(PACKET)["target_state"]["organization_ledger_contract"]["required"]
    assert required["consumes_includes"] == [REPO_RECEIPT, CANONICAL_RECEIPT]
    assert required["runtime_reality_authority"] == "Organization"
    assert required["propagation_role"] == "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER"
    assert required["propagation_gates_organization_runtime_reality"] is False
    assert required["always_on_receiver_required"] is False


def test_packet_points_at_a_real_reference_implementation():
    reference = load(PACKET)["reference_implementation"]
    for key in ("contract", "aggregator", "declaration", "exemption_register", "invariant_block"):
        assert (ROOT / reference[key]).exists(), f"reference {key} missing: {reference[key]}"


def test_reference_organization_passes_its_own_verifier():
    """The organization the packet points at must itself be deployed."""
    code, result = run_verifier(ROOT)
    assert code == 0, result
    assert result["disposition"] == "ALLOW"
    assert result["state"] == "DEPLOYED"
    assert result["organization"] == "StegVerse-Labs"
    assert result["findings"] == []


def test_verifier_observes_no_runtime_and_contacts_nothing():
    _, result = run_verifier(ROOT)
    assert result["runtime_observed"] is False
    assert result["receiver_contacted"] is False
    assert result["external_machine_required"] is False
    assert result["consequence_committed"] is False
    assert result["authority_effect"] == "NONE_VERIFICATION_ONLY"


def test_a_fully_deployed_organization_passes(tmp_path):
    write_org(tmp_path, contract=deployed_contract(), aggregator=GENERIC_AGGREGATOR)
    code, result = run_verifier(tmp_path)
    assert code == 0, result["findings"]
    assert result["state"] == "DEPLOYED"
    assert result["organization"] == "Example-Org"


def test_repository_only_contract_is_reported_as_dropping_canonical_transitions(tmp_path):
    contract = deployed_contract()
    contract["consumes"] = REPO_RECEIPT  # the older single-schema generation
    write_org(tmp_path, contract=contract, aggregator=REPO_ONLY_AGGREGATOR)
    code, result = run_verifier(tmp_path)
    assert code == 1
    codes = {f["failure_code"] for f in result["findings"]}
    assert "ORGANIZATION_CONTRACT_CONSUMES_INCOMPLETE" in codes
    assert "AGGREGATOR_REJECTS_NON_REPOSITORY_SOURCE" in codes
    consumes_finding = next(
        f for f in result["findings"] if f["failure_code"] == "ORGANIZATION_CONTRACT_CONSUMES_INCOMPLETE"
    )
    assert consumes_finding["missing_schemas"] == [CANONICAL_RECEIPT]
    assert "dropped" in consumes_finding["required_evidence_or_repair"]


def test_contract_driven_aggregator_passes_without_naming_the_canonical_schema(tmp_path):
    """The generalization removes hard-coded schema names; the check must not demand one.

    An aggregator that gates on the contract's consumes list never needs to mention
    stegverse.canonical-state-transition-receipt/v1 in its own source. An earlier
    revision of this verifier tested for that literal and so failed the correct
    implementation while passing a hard-coded one.
    """
    contract_driven = (
        "def verify_source(receipt):\n"
        "    schema = receipt.get('schema')\n"
        "    allowed = C.get('consumes')\n"
        "    if isinstance(allowed, str): allowed = [allowed]\n"
        "    if schema not in (allowed or []):\n"
        "        raise SystemExit('organization source receipt schema mismatch')\n"
    )
    assert CANONICAL_RECEIPT not in contract_driven
    write_org(tmp_path, contract=deployed_contract(), aggregator=contract_driven)
    code, result = run_verifier(tmp_path)
    assert code == 0, result["findings"]
    assert result["state"] == "DEPLOYED"


def test_an_aggregator_naming_only_the_repository_schema_still_fails(tmp_path):
    """The opposite case: hard-coded admission is the defect, literal or not."""
    write_org(tmp_path, contract=deployed_contract(), aggregator=REPO_ONLY_AGGREGATOR)
    code, result = run_verifier(tmp_path)
    assert code == 1
    finding = next(
        f for f in result["findings"] if f["failure_code"] == "AGGREGATOR_REJECTS_NON_REPOSITORY_SOURCE"
    )
    assert finding["observed_contract_driven_admission"] is False
    assert finding["failed_predicate"] == "AGGREGATOR_ADMITS_BY_THE_CONTRACT_CONSUMES_LIST"


def test_aggregator_hard_reject_is_located_by_line(tmp_path):
    write_org(tmp_path, contract=deployed_contract(), aggregator=REPO_ONLY_AGGREGATOR)
    _, result = run_verifier(tmp_path)
    finding = next(
        f for f in result["findings"] if f["failure_code"] == "AGGREGATOR_REJECTS_NON_REPOSITORY_SOURCE"
    )
    assert finding["observed_hard_reject"] is True
    assert finding["observed_line"] == 2


def test_missing_declaration_and_register_are_separate_findings(tmp_path):
    write_org(tmp_path, contract=deployed_contract(), aggregator=GENERIC_AGGREGATOR,
              declaration=False, register=False)
    code, result = run_verifier(tmp_path)
    assert code == 1
    codes = {f["failure_code"] for f in result["findings"]}
    assert "ORGANIZATION_ROLE_DECLARATION_ABSENT" in codes
    assert "ORGANIZATION_ROLE_EXEMPTION_REGISTER_ABSENT" in codes


def test_absent_contract_is_an_actionable_finding_not_a_crash(tmp_path):
    write_org(tmp_path, contract=None, aggregator=None)
    code, result = run_verifier(tmp_path)
    assert code == 1
    codes = {f["failure_code"] for f in result["findings"]}
    assert "ORGANIZATION_LEDGER_CONTRACT_ABSENT" in codes
    assert "ORGANIZATION_AGGREGATOR_ABSENT" in codes
    assert result["organization"] is None


def test_every_finding_carries_the_full_non_allow_vocabulary(tmp_path):
    """No finding may be a bare blocker: each names its repair and its next attempt."""
    contract = deployed_contract()
    contract["consumes"] = REPO_RECEIPT
    del contract["organization_scope_rule"]
    contract["preserves_source_transition_receipt"] = False
    contract["runtime_reality_authority"] = "Master Records"
    write_org(tmp_path, contract=contract, aggregator=REPO_ONLY_AGGREGATOR,
              declaration=False, register=False)
    _, result = run_verifier(tmp_path)
    assert result["finding_count"] >= 6
    for item in result["findings"]:
        for field in NON_ALLOW_FIELDS:
            assert isinstance(item.get(field), str) and item[field], (field, item)


def test_no_repair_text_names_a_machine_or_a_receiver(tmp_path):
    """A gap here is a source defect, never a machine dependency."""
    contract = deployed_contract()
    contract["consumes"] = REPO_RECEIPT
    write_org(tmp_path, contract=contract, aggregator=REPO_ONLY_AGGREGATOR,
              declaration=False, register=False)
    _, result = run_verifier(tmp_path)
    for item in result["findings"]:
        repair = item["required_evidence_or_repair"].lower()
        for forbidden in ("ingress url", "reachable", "unreachable", "device",
                          "second machine", "always-on", "awaiting"):
            assert forbidden not in repair, (forbidden, item["failure_code"])


def test_register_records_measurement_not_instruction():
    register = load(PACKET)["organization_register"]
    by_name = {o["organization"]: o for o in register["organizations"]}
    assert by_name["StegVerse-Labs"]["state"] == "DEPLOYED"
    org = by_name["StegVerse-org"]
    assert org["state"] == "RECORDING_MECHANISM_PRESENT_ROLE_NOT_DEPLOYED"
    assert org["observed_commit"]
    assert org["observed_on"]
    # The mechanism is present; it is the role and the generalization that are absent.
    assert any("aggregate_repo_transition.py" in p for p in org["present"])
    gap_codes = {g["failure_code"] for g in org["gaps"]}
    assert "ORGANIZATION_CONTRACT_CONSUMES_REPOSITORY_RECEIPTS_ONLY" in gap_codes
    assert "AGGREGATOR_REJECTS_NON_REPOSITORY_SOURCE" in gap_codes
    assert register["organizations_not_yet_measured"]


def test_the_constraint_is_selection_timing_not_one_organization_per_session():
    """A session may deploy to many organizations; what it cannot do is reach a
    dot-named repository it was not created with."""
    reaching = load(PACKET)["reaching_target_organizations"]
    assert reaching["constraint"] == "SELECTION_TIMING_NOT_COUNT"
    assert reaching["one_session_may_deploy_to_many_organizations"] is True
    assert reaching["every_target_dot_github_must_be_selected_at_session_creation"] is True
    assert reaching["target_discovered_after_session_start_is_unreachable_from_that_session"] is True
    text = DOC.read_text(encoding="utf-8")
    assert "selection timing, not count" in text
    assert "one organization per session" not in text


def test_doc_states_the_sequence_and_the_urgent_gap():
    text = DOC.read_text(encoding="utf-8")
    assert "scripts/verify_organization_role_deployment.py --org-root" in text
    assert "per organization, in each organization's own `.github`" in text
    assert "dropped, not recorded" in text
    assert "SOURCE_IMPLEMENTED" in text
