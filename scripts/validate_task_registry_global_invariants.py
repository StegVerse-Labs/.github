#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
RECORDS = ROOT / "data" / "canonical-task-records"

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
    "completion_language_requires_evidence_class": True,
    "unqualified_complete_or_completed_prohibited": True,
    "stronger_completion_class_inference_prohibited": True,
    "completion_claim_requires_evidence_refs": True,
    "validated_completion_requires_claimed_completion": True,
}

COMPLETION_CLASSES = [
    "SOURCE_IMPLEMENTED",
    "MERGED",
    "CI_VALIDATED",
    "SANDBOX_RUNTIME_OBSERVED",
    "EXTERNAL_PROVIDER_OBSERVED",
    "MASTER_RECORDS_RECONSTRUCTED",
    "END_TO_END",
]
COMPLETION_RANK = {value: index for index, value in enumerate(COMPLETION_CLASSES)}

REVIEW_ORDER = [
    "STEG-BROWSER-RETAINED-RESIDENT-NODE",
    "STEGOS-CURRENT-DEVICE-NODE",
    "STEG-BROWSER-EPHEMERAL-LEASE",
    "SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER",
    "ADMITTED-EPHEMERAL-STEGOS-NODE",
    "REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT",
]

FORBIDDEN_TRUE_KEYS = {
    "device_is_user_verifier", "node_is_user_verifier", "transport_is_user_verifier",
    "channel_identity_is_user_verifier", "secure_enclave_is_user_verifier",
    "local_key_possession_is_user_verification", "device_verification_required",
    "device_attestation_required", "physical_device_identity_required", "pinned_device_required",
    "remote_computer_is_distinct_execution_substrate", "remote_computer_is_execution_authority",
    "remote_computer_is_machine_dependency", "remote_computer_is_completion_predicate",
    "remote_computer_required", "remote_computer_availability_required",
}

FORBIDDEN_AUTHORIZED_DEVICE_KEYS = {
    "authorized_remote_devices", "authorized_devices", "device_authorized", "device_verified",
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


def validate_completion(path: Path, record: dict) -> None:
    completion = record.get("completion")
    if not isinstance(completion, dict):
        return
    claimed = completion.get("claimed") is True
    validated = completion.get("validated") is True
    evidence_class = completion.get("evidence_class")
    terminal_class = completion.get("terminal_evidence_class")
    evidence_refs = completion.get("evidence_refs")

    if validated and not claimed:
        fail(f"{path.name}: completion.validated=true requires completion.claimed=true")
    if not (claimed or validated):
        return
    if evidence_class not in COMPLETION_RANK:
        fail(f"{path.name}: affirmative completion requires explicit completion.evidence_class")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(isinstance(x, str) and x for x in evidence_refs):
        fail(f"{path.name}: affirmative completion requires non-empty completion.evidence_refs")
    if terminal_class is not None:
        if terminal_class not in COMPLETION_RANK:
            fail(f"{path.name}: unknown completion.terminal_evidence_class={terminal_class}")
        if COMPLETION_RANK[evidence_class] < COMPLETION_RANK[terminal_class]:
            fail(f"{path.name}: completion evidence class {evidence_class} is weaker than declared terminal class {terminal_class}")
    if completion.get("end_to_end_complete") is True and evidence_class != "END_TO_END":
        fail(f"{path.name}: end_to_end_complete=true requires END_TO_END evidence class")


def validate_record(path: Path) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    for location, key, value in walk(record):
        if key in FORBIDDEN_TRUE_KEYS and value is True:
            fail(f"{path.name}: {location}=true contradicts global verifier/node/substrate invariant")
        if key in FORBIDDEN_AUTHORIZED_DEVICE_KEYS:
            fail(f"{path.name}: {location} uses prohibited device authorization/verification semantics")
        if key in {"user_verification_authority", "user_verifier_authority", "user_verification_source"} and value != "KV/SKAP Vault":
            fail(f"{path.name}: {location} must be KV/SKAP Vault")
        if key in {"device_user_verifier_authority", "node_user_verifier_authority", "transport_user_verifier_authority"} and value != "NONE":
            fail(f"{path.name}: {location} must be NONE")
        if key in {"device_verification_policy", "device_verification_process", "device_attestation_gate", "physical_device_identity_gate"} and value != "NONE_PROHIBITED":
            fail(f"{path.name}: {location} must be NONE_PROHIBITED")
        if key == "remote_computer_role" and value != "TRANSPORT_DISCOVERY_ONLY":
            fail(f"{path.name}: {location} must be TRANSPORT_DISCOVERY_ONLY")
        if key == "remote_computer_inventory_semantics" and value != "EVIDENCE_REACHABILITY_ONLY":
            fail(f"{path.name}: {location} must be EVIDENCE_REACHABILITY_ONLY")
        if key == "second_user_operated_device_allowed" and value is not False:
            fail(f"{path.name}: {location} must be false")
        if key == "execution_substrate_selection_authority_effect" and value != "NONE":
            fail(f"{path.name}: {location} must be NONE")
    validate_completion(path, record)


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
    if invariants.get("completion_evidence_classes") != COMPLETION_CLASSES:
        fail("global completion evidence classes mismatch")
    if invariants.get("completion_evidence_strength_order") != COMPLETION_CLASSES:
        fail("global completion evidence strength order mismatch")
    if invariants.get("terminal_complete_default_evidence_class") != "END_TO_END":
        fail("global terminal completion default must be END_TO_END")

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
    }
    missing = sorted(required_prohibitions - prohibitions)
    if missing:
        fail("global invariant missing required prohibitions: " + ", ".join(missing))
    if policy.get("authority_effect") != "NONE_REGISTRY_INVARIANT_ONLY":
        fail("global invariant authority effect mismatch")
    for path in sorted(RECORDS.glob("*.json")):
        validate_record(path)
    print("TASK_REGISTRY_GLOBAL_INVARIANTS_PASS")

if __name__ == "__main__":
    main()
