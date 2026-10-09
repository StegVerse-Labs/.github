#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
RECORDS = ROOT / "data" / "canonical-task-records"
# Every exemption carries the nine required fields plus exactly these state fields.
EXEMPTION_STATE_FIELDS = {
    "current_disposition": "FAIL_CLOSED",
    "consequence_committed": False,
    "authority_effect": "NONE_REGISTER_ONLY",
}
# Wording equivalent to a prohibited justification, matched in the lower-cased "why" field.
PROHIBITED_JUSTIFICATION_PHRASES = (
    "external machine must be running",
    "external machine is not running",
    "waiting for an external machine",
    "second user-operated device",
    "second device is required",
    "remote computer is unavailable",
    "remote computer is offline",
    "evidence reachability",
    "evidence is not yet reachable",
    "receiver is not always on",
    "receiver is not always-on",
    "receiver is offline",
    "observer has not yet looked",
    "has not yet been observed by an authentic observer",
)
# Surfaces in StegVerse-Labs/TVC are registered from its socket-module review records.
TVC_SURFACE_PREFIX = "StegVerse-Labs/TVC:"
TVC_RECORD_REF = re.compile(r"\bTVC record (?:O2B1-NA-\d{2}|W4-N[123]-\d{2})\b")
TVC_EXEMPTION_EXTENSION = "SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001/N2"

EXPECTED = {
    "user_verification_authority": "KV/SKAP Vault",
    "user_verification_authority_exclusive": True,
    "stegos_device_role": "INTERCHANGEABLE_TRANSPORT_NODE",
    "device_verification_policy": "NONE_PROHIBITED",
    "device_verification_process": "NONE_PROHIBITED",
    "device_attestation_gate": "NONE_PROHIBITED",
    "physical_device_identity_gate": "NONE_PROHIBITED",
    "device_user_verifier_authority": "NONE",
    "node_user_verifier_authority": "NONE",
    "transport_user_verifier_authority": "NONE",
    "local_key_user_verifier_authority": "NONE",
    "secure_enclave_user_verifier_authority": "NONE",
    "execution_surface_connectivity_authority": "NONE_OBSERVATION_ONLY",
    "remote_computer_role": "TRANSPORT_DISCOVERY_ONLY",
    "remote_computer_inventory_semantics": "EVIDENCE_REACHABILITY_ONLY",
    "remote_computer_is_distinct_execution_substrate": False,
    "remote_computer_is_machine_dependency": False,
    "remote_computer_is_completion_predicate": False,
    "ephemeral_capacity_runtime_class": "ADMITTED-EPHEMERAL-STEGOS-NODE",
    "ephemeral_capacity_requires_intr_admission": True,
    "evidence_reachability_may_establish_substrate_unsuitable": False,
    "second_user_operated_device_allowed": False,
    "execution_substrate_selection_authority_effect": "NONE",
    "completion_evidence_contract_version": "v1",
    "completion_language_requires_evidence_class": True,
    "unqualified_complete_or_completed_prohibited": True,
    "stronger_completion_class_inference_prohibited": True,
    "completion_claim_requires_evidence_refs": True,
    "new_or_reconciled_completion_requires_contract_version": True,
    "legacy_unqualified_completion_authority": "NONE_NON_AUTHORITATIVE_PROVENANCE_ONLY",
    "legacy_unqualified_completion_may_support_user_facing_complete": False,
    "legacy_unqualified_completion_may_satisfy_terminal_predicate": False,
    "terminal_complete_default_evidence_class": "END_TO_END",
    "runtime_reality_authority": "Organization",
    "runtime_reality_locus": "ORGANIZATION_LEDGER_ROOT",
    "runtime_reality_lock": "ORGANIZATION_LEDGER_LOCK",
    "runtime_reality_write_mode": "MANIFEST_DIRECTED_APPEND",
    "organization_role_deployment_scope": "PER_ORGANIZATION_IN_ITS_OWN_DOT_GITHUB",
    "master_records_role": "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY",
    "master_records_runtime_reality_authority": "NONE",
    "master_records_transition_authority": "NONE",
    "master_records_may_gate_organization_runtime_reality": False,
    "released_organization_batch_requires_verified_organization_receipt_chain": True,
    "actions_by_manifest_required": True,
    "manifest_determines_destination": True,
    "destination_existence_sufficient_for_ingress_and_egress": True,
    "destination_liveness_is_transition_predicate": False,
    "external_machine_awaiting_allowed": False,
    "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
    "always_on_receiver_required": False,
    "post_closure_authentic_observer_gate_allowed": False,
    "non_conforming_surface_disposition": "DECLARED_EXEMPTION_REQUIRED",
    "transition_authority": "Interlock/InTr",
    "worker_claim_authority": "WorkerCoordinator",
    "credential_authority": "TV/TVC",
}

REVIEW_ORDER = [
    "STEG-BROWSER-RETAINED-RESIDENT-NODE",
    "STEGOS-CURRENT-DEVICE-NODE",
    "STEG-BROWSER-EPHEMERAL-LEASE",
    "SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER",
    "ADMITTED-EPHEMERAL-STEGOS-NODE",
    "REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT",
]

FORBIDDEN_TRUE_KEYS = {
    "device_is_user_verifier",
    "node_is_user_verifier",
    "transport_is_user_verifier",
    "channel_identity_is_user_verifier",
    "secure_enclave_is_user_verifier",
    "local_key_possession_is_user_verification",
    "device_verification_required",
    "device_attestation_required",
    "physical_device_identity_required",
    "pinned_device_required",
    "remote_computer_is_distinct_execution_substrate",
    "remote_computer_is_execution_authority",
    "remote_computer_is_machine_dependency",
    "remote_computer_is_completion_predicate",
    "remote_computer_required",
    "remote_computer_availability_required",
    "external_machine_awaiting_required",
    "always_on_receiver_required",
    "destination_liveness_required",
    "post_closure_authentic_observer_required",
    "master_records_gates_organization_runtime_reality",
    "master_records_is_runtime_reality_authority",
}

FORBIDDEN_AUTHORIZED_DEVICE_KEYS = {
    "authorized_remote_devices",
    "authorized_devices",
    "device_authorized",
    "device_verified",
}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def walk(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{path}.{k}" if path else k
            yield p, k, v
            yield from walk(v, p)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")


PRE_DECLARATION_MASTER_RECORDS_ROLE_RECORDS = {
    # Records written before ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001. Their
    # reconciliation is record-side and gated behind canonical-task-record schema
    # reconciliation and registration-before-mutation. Any *new* occurrence fails here.
    "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json",
}

ALLOWED_MASTER_RECORDS_ROLES = {
    "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY",
    "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY_NON_GATING",
    "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER",
}


def validate_record(path: Path) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    for location, key, value in walk(record):
        if key in FORBIDDEN_TRUE_KEYS and value is True:
            fail(f"{path.name}: {location}=true contradicts global verifier/node/substrate invariant")
        if key in FORBIDDEN_AUTHORIZED_DEVICE_KEYS:
            fail(f"{path.name}: {location} uses prohibited device authorization/verification semantics")
        if key in {"user_verification_authority", "user_verifier_authority", "user_verification_source"}:
            if value != "KV/SKAP Vault":
                fail(f"{path.name}: {location} must be KV/SKAP Vault")
        if key in {"device_user_verifier_authority", "node_user_verifier_authority", "transport_user_verifier_authority"}:
            if value != "NONE":
                fail(f"{path.name}: {location} must be NONE")
        if key in {"device_verification_policy", "device_verification_process", "device_attestation_gate", "physical_device_identity_gate"}:
            if value != "NONE_PROHIBITED":
                fail(f"{path.name}: {location} must be NONE_PROHIBITED")
        if key == "remote_computer_role" and value != "TRANSPORT_DISCOVERY_ONLY":
            fail(f"{path.name}: {location} must be TRANSPORT_DISCOVERY_ONLY")
        if key == "remote_computer_inventory_semantics" and value != "EVIDENCE_REACHABILITY_ONLY":
            fail(f"{path.name}: {location} must be EVIDENCE_REACHABILITY_ONLY")
        if key == "second_user_operated_device_allowed" and value is not False:
            fail(f"{path.name}: {location} must be false")
        if key == "execution_substrate_selection_authority_effect" and value != "NONE":
            fail(f"{path.name}: {location} must be NONE")
        if key == "runtime_reality_authority" and value != "Organization":
            fail(f"{path.name}: {location} must be Organization under ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001")
        if key == "master_records_role" and value not in ALLOWED_MASTER_RECORDS_ROLES:
            if path.name not in PRE_DECLARATION_MASTER_RECORDS_ROLE_RECORDS:
                fail(
                    f"{path.name}: {location} must be an organization-record/reconstruction-only role "
                    "under ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001"
                )


def validate_organization_role_deployment(invariants: dict) -> None:
    declaration_path = ROOT / invariants.get("organization_role_declaration", "")
    register_path = ROOT / invariants.get("organization_role_exemption_register", "")
    if not declaration_path.is_file():
        fail("organization role declaration missing")
    if not register_path.is_file():
        fail("organization role exemption register missing")
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    register = json.loads(register_path.read_text(encoding="utf-8"))
    if declaration.get("schema") != "stegverse.organization-role-runtime-reality-deployment/v1":
        fail("organization role declaration schema mismatch")
    if declaration.get("authority_effect") != "NONE_DECLARATION_ONLY":
        fail("organization role declaration must grant no authority")
    change = declaration.get("role_change") or {}
    if change.get("current_value") != invariants.get("runtime_reality_authority"):
        fail("organization role declaration disagrees with runtime_reality_authority")
    if change.get("reality_locus") != invariants.get("runtime_reality_locus"):
        fail("organization role declaration disagrees with runtime_reality_locus")
    if change.get("reality_lock") != invariants.get("runtime_reality_lock"):
        fail("organization role declaration disagrees with runtime_reality_lock")
    if change.get("reality_write_mode") != invariants.get("runtime_reality_write_mode"):
        fail("organization role declaration disagrees with runtime_reality_write_mode")
    restated = declaration.get("master_records_restated_role") or {}
    if restated.get("role") != invariants.get("master_records_role"):
        fail("organization role declaration disagrees with master_records_role")
    if restated.get("runtime_reality_authority") != "NONE":
        fail("restated master-records role must hold no runtime reality authority")
    if restated.get("may_be_awaited_by_a_transition") is not False:
        fail("restated master-records role may not be awaited by a transition")
    conformance = declaration.get("conformance_standard") or {}
    for key in (
        "actions_by_manifest_required",
        "external_machine_awaiting_allowed",
        "always_on_receiver_required",
        "post_closure_authentic_observer_gate_allowed",
        "receiver_unavailable_disposition",
        "non_conforming_surface_disposition",
    ):
        if conformance.get(key) != invariants.get(key):
            fail(f"organization role conformance standard disagrees with invariant {key}")
    if register.get("schema") != "stegverse.organization-role-exemption-register/v1":
        fail("organization role exemption register schema mismatch")
    if register.get("declaration") != declaration.get("declaration_id"):
        fail("organization role exemption register is not bound to the declaration")
    if register.get("silent_non_conformance_allowed") is not False:
        fail("organization role exemption register must prohibit silent non-conformance")
    if register.get("exemption_grants_authority") is not False:
        fail("organization role exemption grants no authority")
    required_fields = set(register.get("required_fields") or [])
    declared_fields = set((declaration.get("exemption_path") or {}).get("required_fields") or [])
    if not declared_fields or not declared_fields <= required_fields:
        fail("organization role exemption register omits a declared required field")
    prohibited = set(register.get("prohibited_justifications") or [])
    if not prohibited:
        fail("organization role exemption register lists no prohibited justifications")
    tvc_owners = tvc_exemption_owners()
    surfaces: set[str] = set()
    for exemption in register.get("exemptions") or []:
        surface = exemption.get("surface", "<unnamed>")
        missing_fields = sorted(required_fields - set(exemption))
        if missing_fields:
            fail(
                f"organization role exemption {surface} "
                "missing required fields: " + ", ".join(missing_fields)
            )
        unexpected = sorted(set(exemption) - required_fields - set(EXEMPTION_STATE_FIELDS))
        if unexpected:
            fail(f"organization role exemption {surface} has unexpected fields: " + ", ".join(unexpected))
        for key, expected in EXEMPTION_STATE_FIELDS.items():
            if exemption.get(key) != expected:
                fail(f"organization role exemption {surface} {key} must be {expected!r}")
        if surface in surfaces:
            fail(f"organization role exemption {surface} is registered more than once")
        surfaces.add(surface)
        for field in sorted(required_fields):
            value = exemption.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"organization role exemption {surface} {field} must be a non-empty string")
            if any(code in value for code in prohibited):
                fail(f"organization role exemption {surface} {field} uses a prohibited justification")
        why = exemption["why_manifest_bound_state_transition_is_not_yet_possible"].lower()
        for phrase in PROHIBITED_JUSTIFICATION_PHRASES:
            if phrase in why:
                fail(f"organization role exemption {surface} justification is equivalent to a prohibited one: {phrase!r}")
        if surface.startswith(TVC_SURFACE_PREFIX):
            if exemption["owning_existing_goal"] not in tvc_owners:
                fail(f"organization role exemption {surface} owner is not admitted for TVC surfaces")
            if not TVC_RECORD_REF.search(exemption["retry_entrypoint"]):
                fail(f"organization role exemption {surface} names no TVC review record")
        elif not (RECORDS / f"{exemption['owning_existing_goal']}.json").is_file():
            fail(f"organization role exemption {surface} owner has no canonical task record")


def tvc_exemption_owners() -> set[str]:
    """Owners admitted for TVC surfaces by the N2 bounded extension of the predicate owner."""
    record = json.loads((RECORDS / f"{TVC_EXEMPTION_EXTENSION.split('/')[0]}.json").read_text(encoding="utf-8"))
    for extension in record.get("bounded_extensions") or []:
        if extension.get("extension_id") == TVC_EXEMPTION_EXTENSION:
            owners = set(extension.get("input_owners") or [])
            missing = sorted(owner for owner in owners if not (RECORDS / f"{owner}.json").is_file())
            if missing:
                fail("TVC exemption owners have no canonical task record: " + ", ".join(missing))
            return owners
    fail(f"bounded extension {TVC_EXEMPTION_EXTENSION} missing")
    return set()


def main() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy.get("schema") != "stegverse.task-registry-global-invariants/v1":
        fail("global invariant schema mismatch")
    if policy.get("applies_to") != "ALL_CANONICAL_TASKS_EXISTING_AND_NEW":
        fail("global invariant scope mismatch")
    invariants = policy.get("invariants") or {}
    for key, expected in EXPECTED.items():
        if invariants.get(key) != expected:
            fail(f"global invariant {key} mismatch")
    if invariants.get("runtime_substrate_review_order") != REVIEW_ORDER:
        fail("global runtime substrate review order mismatch")
    expected_classes = ["SOURCE_IMPLEMENTED","MERGED","CI_VALIDATED","SANDBOX_RUNTIME_OBSERVED","EXTERNAL_PROVIDER_OBSERVED","MASTER_RECORDS_RECONSTRUCTED","END_TO_END"]
    if invariants.get("completion_evidence_classes") != expected_classes:
        fail("global completion evidence classes mismatch")
    if invariants.get("completion_evidence_strength_order") != expected_classes:
        fail("global completion evidence strength order mismatch")
    prohibitions = set(policy.get("prohibitions") or [])
    required_prohibitions = {
        "NO_DEVICE_VERIFICATION_POLICY_OR_PROCESS",
        "NO_DEVICE_ATTESTATION_OR_PHYSICAL_DEVICE_IDENTITY_GATE",
        "NO_CONNECTOR_DEVICE_LIST_AS_AUTHORIZATION_OR_VERIFICATION",
        "NO_REMOTE_COMPUTER_AS_DISTINCT_EXECUTION_AUTHORITY",
        "NO_REMOTE_COMPUTER_AVAILABILITY_AS_TASK_STATE",
        "NO_REMOTE_COMPUTER_INVENTORY_AS_SUBSTRATE_UNSUITABILITY",
        "NO_REMOTE_COMPUTER_AS_SECOND_MACHINE_REQUIREMENT",
        "NO_EPHEMERAL_CAPACITY_EXECUTION_BEFORE_INTERLOCK_INTR_ADMISSION",
        "NO_EVIDENCE_REACHABILITY_GAP_AS_EXTERNAL_DEVICE_REQUIREMENT",
        "NO_UNQUALIFIED_COMPLETE_OR_COMPLETED_STATUS",
        "NO_SOURCE_IMPLEMENTED_AS_RUNTIME_COMPLETE",
        "NO_MERGED_AS_RUNTIME_COMPLETE",
        "NO_CI_VALIDATED_AS_RUNTIME_COMPLETE",
        "NO_RUNTIME_OBSERVED_AS_MASTER_RECORDS_RECONSTRUCTED",
        "NO_PROVIDER_OBSERVED_AS_END_TO_END_COMPLETE",
        "NO_STRONGER_COMPLETION_CLASS_WITHOUT_NATIVE_EVIDENCE",
        "NO_LEGACY_UNQUALIFIED_COMPLETION_AS_CURRENT_TERMINAL_PROOF",
        "NO_MASTER_RECORDS_AS_RUNTIME_REALITY_AUTHORITY",
        "NO_MASTER_RECORDS_RECORDING_AS_ORGANIZATION_RUNTIME_REALITY_GATE",
        "NO_ORGANIZATION_BATCH_RELEASE_WITHOUT_VERIFIED_ORGANIZATION_RECEIPT_CHAIN",
        "NO_EXTERNAL_MACHINE_AWAITING_AS_TRANSITION_PREDICATE",
        "NO_DESTINATION_LIVENESS_OR_ALWAYS_ON_RECEIVER_AS_TRANSITION_PREDICATE",
        "NO_POST_CLOSURE_AUTHENTIC_OBSERVER_GATE",
        "NO_SILENTLY_NON_CONFORMING_SURFACE_WITHOUT_REGISTERED_EXEMPTION",
        "NO_EXEMPTION_AS_AUTHORITY_OR_TERMINAL_PROOF",
    }
    missing = sorted(required_prohibitions - prohibitions)
    if missing:
        fail("global invariant missing required prohibitions: " + ", ".join(missing))
    if policy.get("authority_effect") != "NONE_REGISTRY_INVARIANT_ONLY":
        fail("global invariant authority effect mismatch")
    validate_organization_role_deployment(invariants)
    for path in sorted(RECORDS.glob("*.json")):
        validate_record(path)
    print("TASK_REGISTRY_GLOBAL_VERIFIER_NODE_SUBSTRATE_INVARIANTS_PASS")
    print("ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT_PASS")

if __name__ == "__main__":
    main()
