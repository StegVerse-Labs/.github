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

MASTER_RECORDS_ROLE = "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY"


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


def test_master_records_is_limited_to_organization_records_and_reconstruction_without_reality_authority():
    inv = load_json(POLICY)["invariants"]
    assert inv["master_records_role"] == MASTER_RECORDS_ROLE
    assert inv["master_records_runtime_reality_authority"] == "NONE"
    assert inv["master_records_transition_authority"] == "NONE"
    assert inv["master_records_may_gate_organization_runtime_reality"] is False
    assert inv["released_organization_batch_requires_verified_organization_receipt_chain"] is True
    assert inv["master_records_general_transition_organization_record"] is False
    assert inv["master_records_general_evidence_organization_record"] is False


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
    # This inventory is historical provenance: later semantic-remediation may remove
    # superseded prose from the live tree without rewriting the declaration history.
    prohibited_measured = [item for item in measured if not any(term in item[1].lower() for term in ("organization records", "organization-record", "non-gating", "never gates"))]
    assert set(prohibited_measured).issubset(set(declared)), (
        "new superseded observed/runtime-reality authority prose appeared outside the historical inventory"
    )
    assert inventory["files"] == sorted({entry["path"] for entry in occurrences})


def test_only_organization_record_or_reconstruction_statements_remain_current():
    retained = load_json(DECLARATION)["retained_statements"]
    assert "ORGANIZATION_RECORDS_OR_RECONSTRUCTION" in retained["rule"]
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
    assert "master_records_organization_record_claimed" in body


def test_organization_lane_refuses_a_schema_mismatch_without_touching_the_ledger():
    module = load_custody_module()
    result = module.record_organization_runtime_reality({"schema": "not.the.receipt.schema"})
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH"
    assert result["authority_effect"] == "NONE"


def test_general_transition_submission_to_master_records_is_removed():
    source = CUSTODY.read_text(encoding="utf-8")
    submit = source.index("def submit_state_receipt")
    end = source.index("def require_predecessor_master_records_organization_record", submit)
    body = source[submit:end]
    assert '"organization_runtime_reality": "RECORDED"' in body
    assert '"master_records_submission_performed": False' in body
    assert '"master_records_role": "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY"' in body
    assert "_submit_http(receipt)" not in body
    assert "_submit_local(receipt)" not in body


def test_declaration_doc_states_the_change_and_the_exemption_path():
    text = DOC.read_text(encoding="utf-8")
    assert "runtime_reality_authority:  Organization  (superseding the earlier records-service assignment)" in text
    assert "organization records and reconstruction" in text
    assert "data/organization-role-exemption-register.json" in text
    assert "SOURCE_IMPLEMENTED" in text
    assert "MASTER_RECORDS_RECONSTRUCTED" in text


# W5 (StegVerse-Labs/TVC#488 6071544608): every confirmed nonconforming TVC surface from the
# socket-module review at StegVerse-Labs/TVC@dcf1a90 (#489), mapped TVC record -> register surface.
# Inherited-only callers are consolidated under their root (the W4-N2-04 inherited_by links under
# their own root). ER-1 reconciles the register with the review at StegVerse-Labs/TVC@bd0fe27:
# the records W7 (#491), W8a (#493) and W8b (#494) retired leave the register (RETIRED_TVC_RECORD_SURFACES).
# ER-2 reconciles it with the review at StegVerse-Labs/TVC@5d0b3f0: W10a (#498) retired W4-N3-01/02, whose
# units stay registered only for the activation residual they inherit (W4-N2-07), and W10b (#497)
# retired W4-N3-06..09. ER-3 reconciles it with the review at StegVerse-Labs/TVC@bf6a61f: W11 (#500, #501)
# retired W4-N2-07 (activation is manifest-selected), so its task_activate entry and the two primary-runtime
# unit residuals that inherited it leave the register. The keys below are exactly the TVC review's live
# non_allow_records.
TVC_RECORD_SURFACES = {
    "O2B1-NA-01": ["scripts/tvc_execute_bea_readonly.py (broker request construction)"],
    "O2B1-NA-02": ["scripts/tvc_run_provider_measurement.py (broker request construction)"],
    "O2B1-NA-03": ["scripts/tvc_run_test_lane_external_candidate.py (broker request construction)"],
    "O2B1-NA-04": ["tvc_external_collab_google_drive_probe_runtime.py (broker request construction)"],
    "O2B1-NA-05": ["tvc_external_collab_google_drive_content_integrity_runtime.py (broker request construction)"],
    "W4-N2-01": ["scripts/tvc_mail_provider_operation.py::execute (ARCHIVE_IDS, TRASH_IDS)"],
    "W4-N2-02": ["scripts/tvc_recipient_admission_resident_signer.py::issue_from_resident_signer"],
    "W4-N2-03": ["tvc_google_drive_vault_session_consumer.py::consume_broker_session"],
    "W4-N2-04": ["tvc_google_drive_external_collaboration_vault_session_consumer.py::consume_broker_session"],
    "W4-N2-05": ["scripts/tvc_ara_graph_operations.py::execute"],
    "W4-N2-06": ["scripts/tvc_ara_graph_resident_intake.py::process"],
    "W4-N3-05": ["deploy/systemd/stegtvc-external-collab-google-drive-consent.service"],
}
# Retired in the TVC review at StegVerse-Labs/TVC@bd0fe27 (ER-1) and @5d0b3f0 (ER-2): the surface no
# longer holds the recorded predicate, so its entry is removed and must not be re-registered.
# O2B1-NA-09 and W7-N1-02 were consolidated into the O2B1-NA-08 and W4-N1-01 entries and retired with
# them. W4-N3-01/02 and W4-N2-07 (W11) are retired; the primary-runtime units no longer inherit any record.
RETIRED_TVC_RECORD_SURFACES = {
    "O2B1-NA-07": ["tvc_workspace_google_drive_probe_runtime.py (broker request construction)"],
    "O2B1-NA-08": ["tvc_primary_runtime_binder.py (discover_primary_runtime)"],
    "W4-N1-01": [
        "tvc_provider_operation_broker.py::forward_to_local_vault_broker",
        "tvc_gmail_provider_operation_broker.py::forward_to_local_vault_broker",
    ],
    "W4-N3-03": ["deploy/systemd/stegtvc-private-source-read.timer"],
    "W4-N3-04": ["deploy/systemd/stegtvc-sv-dn1-repository-authority.timer"],
    "W4-N3-10": ["deploy/systemd/stegtvc-tv-resident-operational-proof.service"],
    "W4-N3-06": ["deploy/systemd/stegtvc-app-store-connect-skap-intr-tunnel.service"],
    "W4-N3-07": ["deploy/systemd/stegtvc-post-return-release-skap-intr-tunnel.service"],
    "W4-N3-08": ["deploy/systemd/stegtvc-skap-browser-ingress.service"],
    "W4-N3-09": ["deploy/systemd/stegtvc-skap-browser-intr-tunnel.service"],
    "W4-N2-07": [
        "tvc_primary_runtime_activation_task.py::task_activate",
        "deploy/systemd/stegtvc-primary-runtime.service",
        "deploy/systemd-user/stegtvc-primary-runtime.service",
    ],
}
RETIRED_TVC_RECORD_IDS = {"O2B1-NA-07", "O2B1-NA-08", "O2B1-NA-09", "W7-N1-02", "W4-N1-01", "W4-N3-01", "W4-N3-02",
                          "W4-N3-03", "W4-N3-04", "W4-N3-06", "W4-N3-07", "W4-N3-08", "W4-N3-09", "W4-N3-10",
                          "W4-N2-07"}
I8_SURFACE = "workers/sdk_manifest_diagnostic_admitted_consumer.py::_prove_ancestry"


def tvc_exemptions() -> list[dict]:
    return [e for e in load_json(REGISTER)["exemptions"] if e["surface"].startswith("StegVerse-Labs/TVC:")]


def test_register_holds_one_entry_per_confirmed_tvc_surface():
    expected = {
        "StegVerse-Labs/TVC:" + surface: record_id
        for record_id, surfaces in TVC_RECORD_SURFACES.items()
        for surface in surfaces
    }
    entries = tvc_exemptions()
    assert len(entries) == len(expected) == 12
    actual = {}
    for entry in entries:
        refs = re.findall(r"TVC record (O2B1-NA-\d{2}|W4-N[123]-\d{2})", entry["retry_entrypoint"])
        assert len(refs) == 1, entry["surface"]
        actual[entry["surface"]] = refs[0]
    assert actual == expected
    assert len(TVC_RECORD_SURFACES) == 12 and not set(TVC_RECORD_SURFACES) & RETIRED_TVC_RECORD_IDS


def test_tvc_exemptions_are_fail_closed_register_only_under_admitted_owners():
    owners = {"TVC-CREDENTIAL-MODEL-CONSISTENCY-20260826", "TVC-PROVIDER-OPERATION-BROKER-003"}
    for entry in tvc_exemptions():
        assert len(entry) == 12
        assert entry["owning_existing_goal"] in owners
        assert entry["current_disposition"] == "FAIL_CLOSED"
        assert entry["consequence_committed"] is False
        assert entry["authority_effect"] == "NONE_REGISTER_ONLY"
        # Source review is never presented as an observed runtime attempt.
        assert "no runtime attempt was made or is claimed" in entry["why_manifest_bound_state_transition_is_not_yet_possible"]


def test_inherited_callers_are_consolidated_and_the_i8_surface_is_not_reregistered():
    register = load_json(REGISTER)
    surfaces = [e["surface"] for e in register["exemptions"]]
    # I-8 was repaired and its exemption removed by #3026 (20e2f44); W5 must not re-add it.
    assert not any(s.endswith(I8_SURFACE) for s in surfaces)
    assert not any("tvc_primary_runtime_activation_task.py (task_preflight)" in s for s in surfaces)


def test_retired_tvc_records_are_not_registered_and_activation_is_no_longer_exempt():
    surfaces = {e["surface"]: e for e in tvc_exemptions()}
    retired = {"StegVerse-Labs/TVC:" + s for group in RETIRED_TVC_RECORD_SURFACES.values() for s in group}
    assert len(retired) == 14 and not retired & set(surfaces)
    for entry in surfaces.values():
        named = set(re.findall(r"TVC record ([A-Z0-9]+-[A-Z0-9]+-\d{2})", entry["retry_entrypoint"]))
        assert not named & RETIRED_TVC_RECORD_IDS, entry["surface"]
        # A retired receiver predicate is never re-registered under another surface.
        assert entry["failure_code"] not in {"UNIT_ALWAYS_ON_RECEIVER_PREDICATE", "UNIT_RECEIVER_LIVENESS_POLLING"} or \
            entry["surface"].endswith(TVC_RECORD_SURFACES["W4-N3-05"][0])
        # W11 made primary-runtime activation manifest-selected; no entry re-registers that predicate.
        assert entry["failed_predicate"] != "RUNTIME_ACTIVATION_WITHOUT_MANIFEST_SELECTION", entry["surface"]
        assert "starts the self-heal supervisor" not in entry["why_manifest_bound_state_transition_is_not_yet_possible"]


def run_validator_with_register(register: dict) -> subprocess.CompletedProcess:
    original = REGISTER.read_text(encoding="utf-8")
    REGISTER.write_text(json.dumps(register, indent=2) + "\n", encoding="utf-8")
    try:
        return subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, text=True, capture_output=True)
    finally:
        REGISTER.write_text(original, encoding="utf-8")


def mutated_tvc_register(**changes) -> dict:
    register = load_json(REGISTER)
    index = next(i for i, e in enumerate(register["exemptions"]) if e["surface"].startswith("StegVerse-Labs/TVC:"))
    register["exemptions"][index].update(changes)
    return register


def test_validator_rejects_an_allow_or_committed_exemption():
    proc = run_validator_with_register(mutated_tvc_register(current_disposition="ALLOW"))
    assert proc.returncode != 0 and "current_disposition" in proc.stderr
    proc = run_validator_with_register(mutated_tvc_register(consequence_committed=True))
    assert proc.returncode != 0 and "consequence_committed" in proc.stderr


def test_validator_rejects_a_prohibited_or_equivalent_justification():
    proc = run_validator_with_register(
        mutated_tvc_register(why_manifest_bound_state_transition_is_not_yet_possible="A_RECEIVER_IS_NOT_ALWAYS_ON")
    )
    assert proc.returncode != 0 and "prohibited justification" in proc.stderr
    proc = run_validator_with_register(
        mutated_tvc_register(why_manifest_bound_state_transition_is_not_yet_possible="The receiver is not always on.")
    )
    assert proc.returncode != 0 and "equivalent to a prohibited one" in proc.stderr


def test_validator_rejects_an_unadmitted_owner_a_missing_record_ref_or_a_duplicate():
    proc = run_validator_with_register(mutated_tvc_register(owning_existing_goal="UNADMITTED-OWNER-001"))
    assert proc.returncode != 0 and "owner is not admitted" in proc.stderr
    proc = run_validator_with_register(mutated_tvc_register(retry_entrypoint="StegVerse-Labs/TVC:somewhere"))
    assert proc.returncode != 0 and "names no TVC review record" in proc.stderr
    register = load_json(REGISTER)
    register["exemptions"].append(dict(register["exemptions"][0]))
    proc = run_validator_with_register(register)
    assert proc.returncode != 0 and "registered more than once" in proc.stderr


def test_validator_rejects_an_unexpected_exemption_field():
    proc = run_validator_with_register(mutated_tvc_register(grants="ALLOW"))
    assert proc.returncode != 0 and "unexpected fields" in proc.stderr
