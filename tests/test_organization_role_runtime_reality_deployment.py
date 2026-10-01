"""ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001 source regressions.

Source validation only. Nothing here claims runtime observation, Master Records
closure, or any authority effect.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
DECLARATION = ROOT / "data" / "organization-role-runtime-reality-deployment.json"
REGISTER = ROOT / "data" / "organization-role-exemption-register.json"
CONTRACT = ROOT / ".stegverse" / "transition-ledger" / "org-contract.json"
DOC = ROOT / "docs" / "ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md"
VALIDATOR = ROOT / "scripts" / "validate_task_registry_global_invariants.py"
CUSTODY = ROOT / "workers" / "canonical_state_transition_custody.py"

MASTER_RECORDS_ROLE = "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_global_invariant_assigns_runtime_reality_to_the_organization():
    inv = load_json(POLICY)["invariants"]
    assert inv["runtime_reality_authority"] == "Organization"
    assert inv["runtime_reality_locus"] == "ORGANIZATION_LEDGER_ROOT"
    assert inv["runtime_reality_lock"] == "ORGANIZATION_LEDGER_LOCK"
    assert inv["runtime_reality_write_mode"] == "MANIFEST_DIRECTED_APPEND"
    assert inv["organization_role_deployment_scope"] == "PER_ORGANIZATION_IN_ITS_OWN_DOT_GITHUB"
    # The authorities this deployment does not move.
    assert inv["transition_authority"] == "Interlock/InTr"
    assert inv["worker_claim_authority"] == "WorkerCoordinator"
    assert inv["credential_authority"] == "TV/TVC"
    assert inv["user_verification_authority"] == "KV/SKAP Vault"


def test_master_records_is_restated_as_released_batch_recorder_without_reality_authority():
    inv = load_json(POLICY)["invariants"]
    assert inv["master_records_role"] == MASTER_RECORDS_ROLE
    assert inv["master_records_runtime_reality_authority"] == "NONE"
    assert inv["master_records_transition_authority"] == "NONE"
    assert inv["master_records_may_gate_organization_runtime_reality"] is False
    assert inv["released_organization_batch_requires_verified_organization_receipt_chain"] is True


def test_manifest_bound_state_transition_standard_is_declared_as_invariant():
    inv = load_json(POLICY)["invariants"]
    assert inv["actions_by_manifest_required"] is True
    assert inv["manifest_determines_destination"] is True
    assert inv["destination_existence_sufficient_for_ingress_and_egress"] is True
    assert inv["destination_liveness_is_transition_predicate"] is False
    assert inv["external_machine_awaiting_allowed"] is False
    assert inv["always_on_receiver_required"] is False
    assert inv["receiver_unavailable_disposition"] == "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION"
    assert inv["post_closure_authentic_observer_gate_allowed"] is False


def test_non_conforming_surface_must_hold_a_registered_exemption():
    inv = load_json(POLICY)["invariants"]
    assert inv["non_conforming_surface_disposition"] == "DECLARED_EXEMPTION_REQUIRED"
    assert inv["non_conforming_surface_failure_code"] == "ORGANIZATION_ROLE_CONFORMANCE_NOT_DECLARED"
    register = load_json(REGISTER)
    assert register["silent_non_conformance_allowed"] is False
    assert register["exemption_grants_authority"] is False
    assert register["exemption_may_satisfy_a_terminal_predicate"] is False
    # Every justification the standing standard already forbids is refused here.
    prohibited = set(register["prohibited_justifications"])
    assert "AN_EXTERNAL_MACHINE_MUST_BE_RUNNING" in prohibited
    assert "A_SECOND_USER_OPERATED_DEVICE_IS_REQUIRED" in prohibited
    assert "A_RECEIVER_IS_NOT_ALWAYS_ON" in prohibited
    assert "AN_AUTHENTIC_OBSERVER_HAS_NOT_YET_LOOKED" in prohibited


def test_deployment_prohibitions_are_registered():
    prohibitions = set(load_json(POLICY)["prohibitions"])
    for required in (
        "NO_MASTER_RECORDS_AS_RUNTIME_REALITY_AUTHORITY",
        "NO_MASTER_RECORDS_RECORDING_AS_ORGANIZATION_RUNTIME_REALITY_GATE",
        "NO_ORGANIZATION_BATCH_RELEASE_WITHOUT_VERIFIED_ORGANIZATION_RECEIPT_CHAIN",
        "NO_EXTERNAL_MACHINE_AWAITING_AS_TRANSITION_PREDICATE",
        "NO_DESTINATION_LIVENESS_OR_ALWAYS_ON_RECEIVER_AS_TRANSITION_PREDICATE",
        "NO_POST_CLOSURE_AUTHENTIC_OBSERVER_GATE",
        "NO_SILENTLY_NON_CONFORMING_SURFACE_WITHOUT_REGISTERED_EXEMPTION",
        "NO_EXEMPTION_AS_AUTHORITY_OR_TERMINAL_PROOF",
    ):
        assert required in prohibitions
    # The pre-existing completion-evidence prohibitions are not dropped.
    assert "NO_RUNTIME_OBSERVED_AS_MASTER_RECORDS_RECONSTRUCTED" in prohibitions
    assert "NO_REMOTE_COMPUTER_AS_SECOND_MACHINE_REQUIREMENT" in prohibitions


def test_declaration_grants_no_authority_and_claims_only_source_evidence():
    declaration = load_json(DECLARATION)
    assert declaration["authority_effect"] == "NONE_DECLARATION_ONLY"
    assert declaration["evidence_class"] == "SOURCE_IMPLEMENTED"
    assert declaration["completion_evidence_contract_version"] == "v1"
    assert "MUTATE_ANY_CANONICAL_TASK_RECORD" in declaration["this_declaration_does_not"]
    assert "CLAIM_RUNTIME_OBSERVATION" in declaration["this_declaration_does_not"]
    assert "REQUIRE_AN_EXTERNAL_MACHINE_OR_SECOND_DEVICE" in declaration["this_declaration_does_not"]
    assert declaration["role_change"]["previous_value"] == "Master Records"
    assert declaration["role_change"]["current_value"] == "Organization"


def test_declaration_is_deployed_per_organization_not_system_wide():
    declaration = load_json(DECLARATION)
    assert declaration["organization"] == "StegVerse-Labs"
    assert declaration["deployment_scope"] == (
        "THIS_ORGANIZATION_ONLY_EACH_ORGANIZATION_DEPLOYS_IN_ITS_OWN_DOT_GITHUB"
    )


def test_completion_evidence_class_vocabulary_is_explicitly_unchanged():
    inv = load_json(POLICY)["invariants"]
    assert "MASTER_RECORDS_RECONSTRUCTED" in inv["completion_evidence_classes"]
    assert inv["completion_evidence_classes"] == inv["completion_evidence_strength_order"]
    deferred = load_json(DECLARATION)["deferred_record_side_reconciliation"]
    vocabulary = deferred["completion_evidence_class_vocabulary"]
    assert vocabulary["key"] == "MASTER_RECORDS_RECONSTRUCTED"
    assert vocabulary["disposition"] == "UNCHANGED_IN_THIS_DECLARATION"


def test_superseded_prose_inventory_is_measured_and_still_exact():
    """The enumerated supersession set must match what the tree actually says."""
    inventory = load_json(DECLARATION)["superseded_prose_statements"]
    assert inventory["cross_owner_edit_performed"] is False
    occurrences = inventory["occurrences"]
    assert inventory["count"] == len(occurrences)
    assert occurrences, "supersession inventory may not be silently empty"
    pattern = re.compile(
        r"Master Records\s*(?:remains|is|=)\s*[^.;]*?"
        r"(?:observed[- ]reality|runtime[- ]reality|observed runtime reality)[^.;]*[.;]?"
    )
    measured = []
    for path in [ROOT / "README.md"] + sorted((ROOT / "docs").glob("*.md")):
        if path == DOC:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            for match in pattern.finditer(line):
                measured.append((str(path.relative_to(ROOT)), match.group(0).strip()))
    # Line numbers in the inventory are navigation provenance and drift with any
    # unrelated edit above them; the supersession set itself is path + statement.
    assert inventory["comparison_key"] == "PATH_AND_STATEMENT_TEXT"
    assert inventory["line_numbers_are_provenance_only"] is True
    declared = [(entry["path"], entry["statement"]) for entry in occurrences]
    assert sorted(measured) == sorted(declared), (
        "the superseded-prose set has drifted from the tree; "
        "re-measure it in data/organization-role-runtime-reality-deployment.json"
    )
    assert inventory["files"] == sorted({entry["path"] for entry in occurrences})


def test_retained_custody_only_statements_are_not_claimed_as_superseded():
    retained = load_json(DECLARATION)["retained_statements"]
    assert "CUSTODY_RECONSTRUCTION_ONLY" in retained["rule"]
    statements = [entry["statement"] for entry in load_json(DECLARATION)["superseded_prose_statements"]["occurrences"]]
    for statement in statements:
        assert "observed" in statement or "runtime-reality" in statement or "runtime reality" in statement


def test_organization_ledger_contract_declares_the_reality_locus():
    contract = load_json(CONTRACT)
    assert contract["ledger_root_is_organization_runtime_reality_locus"] is True
    assert contract["runtime_reality_authority"] == "Organization"
    assert contract["ledger_lock"] == "ORGANIZATION_LEDGER_LOCK"
    assert contract["write_mode"] == "MANIFEST_DIRECTED_APPEND"
    assert contract["propagation_role"] == MASTER_RECORDS_ROLE
    assert contract["propagation_gates_organization_runtime_reality"] is False
    assert contract["always_on_receiver_required"] is False
    assert contract["authority_effect"] == "NONE_CONTRACT_ONLY"
    # The pre-existing scope rule is preserved.
    assert contract["organization_scope_rule"] == (
        "EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT"
    )


def test_declaration_and_register_are_reachable_from_the_invariant_block():
    inv = load_json(POLICY)["invariants"]
    assert (ROOT / inv["organization_role_declaration"]).is_file()
    assert (ROOT / inv["organization_role_exemption_register"]).is_file()
    assert load_json(REGISTER)["declaration"] == load_json(DECLARATION)["declaration_id"]


def test_validator_enforces_the_deployment():
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)], cwd=ROOT, text=True, capture_output=True, check=True
    )
    assert "ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT_PASS" in proc.stdout
    assert "TASK_REGISTRY_GLOBAL_VERIFIER_NODE_SUBSTRATE_INVARIANTS_PASS" in proc.stdout


def test_validator_rejects_a_reverted_runtime_reality_authority(tmp_path):
    """Reverting the authority must fail closed rather than pass silently."""
    policy = load_json(POLICY)
    policy["invariants"]["runtime_reality_authority"] = "Master Records"
    original = POLICY.read_text(encoding="utf-8")
    POLICY.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, text=True, capture_output=True)
    finally:
        POLICY.write_text(original, encoding="utf-8")
    assert proc.returncode != 0
    assert "runtime_reality_authority" in proc.stderr


def test_validator_rejects_an_exemption_missing_required_fields():
    register = load_json(REGISTER)
    register["exemptions"] = [{"surface": "unregistered-test-surface"}]
    original = REGISTER.read_text(encoding="utf-8")
    REGISTER.write_text(json.dumps(register, indent=2) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, text=True, capture_output=True)
    finally:
        REGISTER.write_text(original, encoding="utf-8")
    assert proc.returncode != 0
    assert "missing required fields" in proc.stderr


def load_custody_module():
    spec = importlib.util.spec_from_file_location("custody_under_test", CUSTODY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_organization_lane_is_a_standalone_entrypoint_that_awaits_no_receiver():
    module = load_custody_module()
    assert hasattr(module, "record_organization_runtime_reality")
    source = CUSTODY.read_text(encoding="utf-8")
    body = source[source.index("def record_organization_runtime_reality")
                  : source.index("def submit_state_receipt")]
    # The organization lane performs no outbound submission of its own.
    assert "_submit_http" not in body
    assert "urlopen" not in body
    assert "master_records_closure_claimed" in body


def test_organization_lane_refuses_a_schema_mismatch_without_touching_the_ledger():
    module = load_custody_module()
    result = module.record_organization_runtime_reality({"schema": "not.the.receipt.schema"})
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH"
    assert result["authority_effect"] == "NONE"


def test_master_records_boundary_no_longer_reads_as_organization_non_occurrence():
    source = CUSTODY.read_text(encoding="utf-8")
    submit = source.index("def submit_state_receipt")
    blocked = source.index("def blocked(", submit)
    body = source[blocked : source.index("payload = _submit_http(receipt)", blocked)]
    assert '"organization_runtime_reality": "RECORDED"' in body
    assert '"master_records_gates_organization_runtime_reality": False' in body
    assert '"master_records_batch_release_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION"' in body
    # Still a Master Records boundary: the stronger evidence class is not claimed.
    assert '"state": "BOUNDARY"' in body


def test_declaration_doc_states_the_change_and_the_exemption_path():
    text = DOC.read_text(encoding="utf-8")
    assert "runtime_reality_authority:  Master Records  ->  Organization" in text
    assert "recorder of released organization batch receipts" in text
    assert "data/organization-role-exemption-register.json" in text
    assert "SOURCE_IMPLEMENTED" in text
    assert "MASTER_RECORDS_RECONSTRUCTED" in text
